import csv
import hashlib
import io
from datetime import datetime
from typing import List, Dict, Any, TYPE_CHECKING
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, UploadFile
from app.models.application import Application
from app.models.borrower import Borrower
from app.models.data_source import DataSource
from app.models.consent import Consent
from app.models.transaction import Transaction
from app.schemas.data_source import DataSourceUploadResponse
from app.config import settings
from app.services.audit_service import add_audit_log

if TYPE_CHECKING:
    from app.models.user import User


class DataSourceService:
    """Service for uploading and validating bank statement / transaction data."""

    SUPPORTED_TYPES = {"bank_statement", "transaction_csv", "payslip", "tax_return"}

    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload(
        self, application: Application, current_user: "User", source_type: str, file: UploadFile
    ) -> DataSourceUploadResponse:
        """Upload and validate a data source file.

        `application` has already been authorised by the caller
        (`get_accessible_application`), so this method no longer performs an
        owner-only ownership check — that was the cause of the staff-404 bug.
        """
        application_id = application.id
        user_id = current_user.id
        if source_type not in self.SUPPORTED_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported source type. Supported: {', '.join(self.SUPPORTED_TYPES)}",
            )

        consent_result = await self.db.execute(
            select(Consent).where(
                Consent.application_id == application_id,
                Consent.data_source_type == source_type,
                Consent.granted.is_(True),
            )
        )
        if not consent_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Active consent is required before uploading this data source",
            )
        content = await file.read()
        file_size = len(content)

        if file_size == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
        if file_size > settings.max_upload_size_mb * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File is too large")

        file_hash = hashlib.sha256(content).hexdigest()
        duplicate = await self._find_duplicate(application_id, file_hash)
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate file detected for this application",
            )

        # Persist the raw file to Supabase Storage when configured (private
        # bucket + signed-URL retrieval); otherwise keep the local storage path.
        storage_bucket = "local"
        storage_path = None
        from app.services.storage_service import SupabaseStorageService

        if SupabaseStorageService.is_configured():
            import uuid

            object_path = SupabaseStorageService.object_path(
                application.borrower_id, application_id, f"{uuid.uuid4().hex}_{file.filename or 'upload'}"
            )
            meta = SupabaseStorageService.upload("financial-documents", object_path, content, file.content_type)
            storage_bucket = meta["bucket"]
            storage_path = meta["path"]

        # Parse CSV content
        records, issues, warnings = self._parse_file(source_type, content)

        # Calculate reliability score
        reliability_score = self._calculate_reliability(records, issues)

        # Calculate missing rate
        missing_rate = self._calculate_missing_rate(records)

        # Determine date coverage
        date_start, date_end = self._get_date_coverage(records)

        # Create data source record
        data_source = DataSource(
            application_id=application_id,
            source_type=source_type,
            file_name=file.filename,
            file_hash=file_hash,
            mime_type=file.content_type,
            size_bytes=file_size,
            storage_bucket=storage_bucket,
            storage_path=storage_path,
            validation_status="validated" if not issues else "issues_found",
            reliability_score=reliability_score,
            missing_rate=missing_rate,
            date_coverage_start=date_start,
            date_coverage_end=date_end,
            record_count=len(records),
            issues=str(issues) if issues else None,
            warnings=str(warnings) if warnings else None,
        )
        self.db.add(data_source)
        await self.db.flush()

        # Store transactions
        self._store_transactions(application_id, data_source.id, records)

        add_audit_log(
            self.db,
            user_id=user_id,
            action="data_source.uploaded",
            resource_type="data_source",
            resource_id=data_source.id,
            details={"application_id": application_id, "record_count": len(records)},
        )

        await self.db.commit()
        await self.db.refresh(data_source)

        return DataSourceUploadResponse(
            id=data_source.id,
            file_name=file.filename,
            source_type=source_type,
            validation_status=data_source.validation_status,
            record_count=len(records),
            issues=str(issues) if issues else None,
            warnings=str(warnings) if warnings else None,
            reliability_score=reliability_score,
        )

    async def list_for_application(self, application_id: str, user_id: str) -> list[DataSource]:
        await self._ensure_application_owner(application_id, user_id)
        result = await self.db.execute(
            select(DataSource)
            .where(DataSource.application_id == application_id)
            .order_by(DataSource.created_at.desc())
        )
        return list(result.scalars().all())

    def _parse_file(self, source_type: str, content: bytes) -> tuple:
        """Parse uploaded CSV/TSV file into records."""
        records = []
        issues = []
        warnings = []

        try:
            text_content = content.decode("utf-8")
            # Try to detect delimiter
            delimiter = "," if "," in text_content.split("\n")[0] else "\t"
            reader = csv.DictReader(io.StringIO(text_content), delimiter=delimiter)

            required_fields = {"date", "description", "amount"}
            headers = set(reader.fieldnames or [])

            if not required_fields.issubset(headers):
                missing = required_fields - headers
                issues.append(f"Missing required fields: {missing}")

            for row_num, row in enumerate(reader, start=2):
                try:
                    record = self._validate_row(row, row_num)
                    if record:
                        records.append(record)
                except ValueError as e:
                    issues.append(f"Row {row_num}: {str(e)}")

        except UnicodeDecodeError:
            issues.append("File encoding not supported. Please use UTF-8.")
        except Exception as e:
            issues.append(f"File parsing error: {str(e)}")

        if len(records) < 3:
            warnings.append("Very few records found. Scoring confidence may be low.")

        return records, issues, warnings

    def _validate_row(self, row: Dict[str, str], row_num: int) -> Dict[str, Any]:
        """Validate a single CSV row."""
        record = {}

        # Parse date
        date_str = row.get("date", "").strip()
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
            try:
                record["date"] = datetime.strptime(date_str, fmt).date()
                break
            except ValueError:
                continue
        if "date" not in record:
            raise ValueError(f"Invalid date format: {date_str}")

        # Parse amount
        amount_str = row.get("amount", "0").strip().replace(",", "").replace("$", "").replace("RM", "")
        try:
            record["amount"] = float(amount_str)
        except ValueError:
            raise ValueError(f"Invalid amount: {amount_str}")

        # Parse description
        record["description"] = row.get("description", "").strip()

        # Parse balance (optional)
        balance_str = row.get("balance", "").strip()
        if balance_str:
            try:
                record["balance_after"] = float(balance_str.replace(",", "").replace("$", "").replace("RM", ""))
            except ValueError:
                record["balance_after"] = None
        else:
            record["balance_after"] = None

        # Determine transaction type
        record["transaction_type"] = "credit" if record["amount"] > 0 else "debit"

        # Parse category (optional)
        record["category"] = row.get("category", "").strip() or None

        return record

    def _calculate_reliability(self, records: List[Dict], issues: List[str]) -> float:
        """Calculate data reliability score (0-1)."""
        if not records:
            return 0.0

        score = 1.0
        if issues:
            score -= min(len(issues) * 0.1, 0.5)

        # Check for gaps in dates
        if len(records) > 1:
            dates = sorted([r["date"] for r in records if "date" in r])
            if dates:
                total_days = (dates[-1] - dates[0]).days
                expected_records = max(total_days, 1)
                coverage = len(dates) / expected_records
                if coverage < 0.5:
                    score -= 0.2

        return max(0.0, min(1.0, score))

    def _calculate_missing_rate(self, records: List[Dict]) -> float:
        """Calculate missing data rate."""
        if not records:
            return 1.0

        total_fields = 0
        missing_fields = 0
        for record in records:
            for key in ["date", "amount", "description", "balance_after"]:
                total_fields += 1
                if record.get(key) is None or record.get(key) == "":
                    missing_fields += 1

        return missing_fields / max(total_fields, 1)

    def _get_date_coverage(self, records: List[Dict]) -> tuple:
        """Get date range of records."""
        dates = [r["date"] for r in records if "date" in r]
        if dates:
            return min(dates), max(dates)
        return None, None

    def _store_transactions(
        self, application_id: str, data_source_id: str, records: List[Dict]
    ) -> None:
        """Store parsed transactions in the database."""
        for record in records:
            transaction = Transaction(
                data_source_id=data_source_id,
                transaction_date=record.get("date"),
                description=record.get("description", ""),
                amount=record.get("amount", 0.0),
                direction=record.get("transaction_type", "debit"),
                category=record.get("category"),
                raw_data=str(record),
            )
            self.db.add(transaction)

    async def _find_duplicate(self, application_id: str, file_hash: str) -> DataSource | None:
        result = await self.db.execute(
            select(DataSource).where(
                DataSource.application_id == application_id,
                DataSource.file_hash == file_hash,
            )
        )
        return result.scalar_one_or_none()

    async def _ensure_application_owner(self, application_id: str, user_id: str) -> Application:
        result = await self.db.execute(
            select(Application)
            .join(Borrower, Application.borrower_id == Borrower.id)
            .where(Application.id == application_id, Borrower.user_id == user_id)
        )
        application = result.scalar_one_or_none()
        if not application:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
        return application
