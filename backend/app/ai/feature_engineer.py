"""
Feature Engineering Module
Extracts credit-relevant features from transaction data.
"""
import math
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict


class FeatureEngineer:
    """Engineers features from bank transaction data for credit scoring."""

    @staticmethod
    def engineer_features(transactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Extract features from a list of transaction records.
        Each transaction should have: date, amount, transaction_type, description, balance_after
        """
        if not transactions:
            return FeatureEngineer._empty_features()

        features = {}

        # Sort transactions by date
        sorted_txns = sorted(transactions, key=lambda x: x.get("date", date.today()))

        # 1. Income features
        income_features = FeatureEngineer._extract_income_features(sorted_txns)
        features.update(income_features)

        # 2. Expense features
        expense_features = FeatureEngineer._extract_expense_features(sorted_txns)
        features.update(expense_features)

        # 3. Balance features
        balance_features = FeatureEngineer._extract_balance_features(sorted_txns)
        features.update(balance_features)

        # 4. Cash flow features
        cashflow_features = FeatureEngineer._extract_cashflow_features(sorted_txns)
        features.update(cashflow_features)

        # 5. Stability features
        stability_features = FeatureEngineer._extract_stability_features(sorted_txns)
        features.update(stability_features)

        # 6. Behavioral features
        behavioral_features = FeatureEngineer._extract_behavioral_features(sorted_txns)
        features.update(behavioral_features)

        # 7. Derived ratios
        ratio_features = FeatureEngineer._extract_ratio_features(features)
        features.update(ratio_features)

        return features

    @staticmethod
    def _empty_features() -> Dict[str, float]:
        """Return default features when no data is available."""
        return {
            "monthly_income_mean": 0.0,
            "monthly_income_std": 0.0,
            "monthly_income_count": 0,
            "monthly_expense_mean": 0.0,
            "monthly_expense_std": 0.0,
            "avg_balance": 0.0,
            "min_balance": 0.0,
            "max_balance": 0.0,
            "balance_trend": 0.0,
            "net_monthly_cashflow": 0.0,
            "cashflow_volatility": 0.0,
            "days_of_data": 0,
            "transaction_count": 0,
            "income_stability_score": 0.0,
            "expense_stability_score": 0.0,
            "overdraft_count": 0,
            "large_transaction_ratio": 0.0,
            "weekend_spending_ratio": 0.0,
            "dti_ratio": 0.0,
            "savings_rate": 0.0,
            "buffer_months": 0.0,
            "income_expense_ratio": 0.0,
        }

    @staticmethod
    def _extract_income_features(transactions: List[Dict]) -> Dict[str, float]:
        """Extract income-related features."""
        credits = [t for t in transactions if t.get("amount", 0) > 0]

        if not credits:
            return {
                "monthly_income_mean": 0.0,
                "monthly_income_std": 0.0,
                "monthly_income_count": 0,
            }

        # Group by month
        monthly_income = defaultdict(float)
        for t in credits:
            d = t.get("date")
            if d:
                month_key = d.strftime("%Y-%m")
                monthly_income[month_key] += t.get("amount", 0)

        incomes = list(monthly_income.values())
        mean_income = sum(incomes) / len(incomes) if incomes else 0.0
        variance = sum((x - mean_income) ** 2 for x in incomes) / len(incomes) if incomes else 0.0

        return {
            "monthly_income_mean": round(mean_income, 2),
            "monthly_income_std": round(math.sqrt(variance), 2),
            "monthly_income_count": len(incomes),
        }

    @staticmethod
    def _extract_expense_features(transactions: List[Dict]) -> Dict[str, float]:
        """Extract expense-related features."""
        debits = [t for t in transactions if t.get("amount", 0) < 0]

        if not debits:
            return {
                "monthly_expense_mean": 0.0,
                "monthly_expense_std": 0.0,
            }

        monthly_expense = defaultdict(float)
        for t in debits:
            d = t.get("date")
            if d:
                month_key = d.strftime("%Y-%m")
                monthly_expense[month_key] += abs(t.get("amount", 0))

        expenses = list(monthly_expense.values())
        mean_expense = sum(expenses) / len(expenses) if expenses else 0.0
        variance = sum((x - mean_expense) ** 2 for x in expenses) / len(expenses) if expenses else 0.0

        return {
            "monthly_expense_mean": round(mean_expense, 2),
            "monthly_expense_std": round(math.sqrt(variance), 2),
        }

    @staticmethod
    def _extract_balance_features(transactions: List[Dict]) -> Dict[str, float]:
        """Extract balance-related features."""
        balances = [t.get("balance_after") for t in transactions if t.get("balance_after") is not None]

        if not balances:
            return {
                "avg_balance": 0.0,
                "min_balance": 0.0,
                "max_balance": 0.0,
                "balance_trend": 0.0,
            }

        avg_balance = sum(balances) / len(balances)
        min_balance = min(balances)
        max_balance = max(balances)

        # Balance trend (simple linear regression slope)
        n = len(balances)
        if n > 1:
            x_mean = (n - 1) / 2
            y_mean = avg_balance
            numerator = sum((i - x_mean) * (balances[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            trend = numerator / denominator if denominator != 0 else 0.0
        else:
            trend = 0.0

        return {
            "avg_balance": round(avg_balance, 2),
            "min_balance": round(min_balance, 2),
            "max_balance": round(max_balance, 2),
            "balance_trend": round(trend, 4),
        }

    @staticmethod
    def _extract_cashflow_features(transactions: List[Dict]) -> Dict[str, float]:
        """Extract cash flow features."""
        monthly_net = defaultdict(float)
        for t in transactions:
            d = t.get("date")
            if d:
                month_key = d.strftime("%Y-%m")
                monthly_net[month_key] += t.get("amount", 0)

        net_flows = list(monthly_net.values())
        if not net_flows:
            return {
                "net_monthly_cashflow": 0.0,
                "cashflow_volatility": 0.0,
            }

        mean_net = sum(net_flows) / len(net_flows)
        variance = sum((x - mean_net) ** 2 for x in net_flows) / len(net_flows) if net_flows else 0.0

        return {
            "net_monthly_cashflow": round(mean_net, 2),
            "cashflow_volatility": round(math.sqrt(variance), 2),
        }

    @staticmethod
    def _extract_stability_features(transactions: List[Dict]) -> Dict[str, float]:
        """Extract stability features."""
        if not transactions:
            return {
                "days_of_data": 0,
                "transaction_count": 0,
                "income_stability_score": 0.0,
                "expense_stability_score": 0.0,
            }

        dates = [t.get("date") for t in transactions if t.get("date")]
        if not dates:
            return {
                "days_of_data": 0,
                "transaction_count": len(transactions),
                "income_stability_score": 0.0,
                "expense_stability_score": 0.0,
            }

        days_of_data = (max(dates) - min(dates)).days

        # Income stability: consistency of income deposits
        credits = [t for t in transactions if t.get("amount", 0) > 0]
        if len(credits) >= 2:
            credit_dates = sorted([t.get("date") for t in credits if t.get("date")])
            if len(credit_dates) >= 2:
                intervals = [(credit_dates[i+1] - credit_dates[i]).days for i in range(len(credit_dates)-1)]
                mean_interval = sum(intervals) / len(intervals)
                interval_variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
                income_stability = 1.0 / (1.0 + math.sqrt(interval_variance) / max(mean_interval, 1))
            else:
                income_stability = 0.5
        else:
            income_stability = 0.0

        # Expense stability
        debits = [t for t in transactions if t.get("amount", 0) < 0]
        if len(debits) >= 2:
            debit_dates = sorted([t.get("date") for t in debits if t.get("date")])
            if len(debit_dates) >= 2:
                intervals = [(debit_dates[i+1] - debit_dates[i]).days for i in range(len(debit_dates)-1)]
                mean_interval = sum(intervals) / len(intervals)
                interval_variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
                expense_stability = 1.0 / (1.0 + math.sqrt(interval_variance) / max(mean_interval, 1))
            else:
                expense_stability = 0.5
        else:
            expense_stability = 0.0

        return {
            "days_of_data": days_of_data,
            "transaction_count": len(transactions),
            "income_stability_score": round(income_stability, 4),
            "expense_stability_score": round(expense_stability, 4),
        }

    @staticmethod
    def _extract_behavioral_features(transactions: List[Dict]) -> Dict[str, float]:
        """Extract behavioral features."""
        if not transactions:
            return {
                "overdraft_count": 0,
                "large_transaction_ratio": 0.0,
                "weekend_spending_ratio": 0.0,
            }

        # Overdraft count
        overdrafts = sum(1 for t in transactions if t.get("balance_after") is not None and t.get("balance_after") < 0)

        # Large transaction ratio (top 10% of amounts)
        amounts = [abs(t.get("amount", 0)) for t in transactions if t.get("amount", 0) != 0]
        if amounts:
            threshold = sorted(amounts)[int(len(amounts) * 0.9)] if len(amounts) >= 10 else max(amounts)
            large_count = sum(1 for a in amounts if a >= threshold)
            large_ratio = large_count / len(amounts)
        else:
            large_ratio = 0.0

        # Weekend spending ratio
        weekend_txns = sum(1 for t in transactions if t.get("date") and t.get("date").weekday() >= 5)
        weekend_ratio = weekend_txns / len(transactions) if transactions else 0.0

        return {
            "overdraft_count": overdrafts,
            "large_transaction_ratio": round(large_ratio, 4),
            "weekend_spending_ratio": round(weekend_ratio, 4),
        }

    @staticmethod
    def _extract_ratio_features(features: Dict[str, float]) -> Dict[str, float]:
        """Extract derived ratio features."""
        monthly_income = features.get("monthly_income_mean", 0)
        monthly_expense = features.get("monthly_expense_mean", 0)
        avg_balance = features.get("avg_balance", 0)

        # DTI (Debt-to-Income) ratio
        dti = monthly_expense / monthly_income if monthly_income > 0 else 1.0

        # Savings rate
        savings_rate = (monthly_income - monthly_expense) / monthly_income if monthly_income > 0 else 0.0

        # Buffer months (how many months can survive with current balance)
        buffer_months = avg_balance / monthly_expense if monthly_expense > 0 else 12.0

        # Income to expense ratio
        ie_ratio = monthly_income / monthly_expense if monthly_expense > 0 else 2.0

        return {
            "dti_ratio": round(min(dti, 2.0), 4),
            "savings_rate": round(max(savings_rate, -1.0), 4),
            "buffer_months": round(min(buffer_months, 24.0), 2),
            "income_expense_ratio": round(min(ie_ratio, 10.0), 2),
        }