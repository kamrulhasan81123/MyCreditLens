import type {
  ApplicationStatus,
  BorrowerSegment,
  DataSourceType,
  RiskBand,
} from './types'

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-MY', {
    style: 'currency',
    currency: 'MYR',
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatPercent(value: number, digits = 1): string {
  return `${(value * 100).toFixed(digits)}%`
}

export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(iso))
}

export function formatDateTime(iso: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))
}

export const RISK_BAND_LABEL: Record<RiskBand, string> = {
  LOW: 'Low Risk',
  MEDIUM: 'Medium Risk',
  HIGH: 'High Risk',
}

export const SEGMENT_LABEL: Record<BorrowerSegment, string> = {
  GIG_WORKER: 'Gig Worker',
  MICRO_ENTREPRENEUR: 'Micro-Entrepreneur',
  SMALL_MERCHANT: 'Small Merchant',
  THIN_FILE: 'Thin-File',
  SALARIED: 'Salaried',
}

export const STATUS_LABEL: Record<ApplicationStatus, string> = {
  DRAFT: 'Draft',
  SUBMITTED: 'Submitted',
  DATA_PENDING: 'Data Pending',
  VALIDATION_FAILED: 'Validation Failed',
  READY_FOR_SCORING: 'Ready for Scoring',
  SCORING: 'Scoring',
  SCORED: 'Scored',
  MANUAL_REVIEW: 'Manual Review',
  INFORMATION_REQUESTED: 'Information Requested',
  APPROVED: 'Approved',
  REJECTED: 'Rejected',
  APPEALED: 'Appealed',
  WITHDRAWN: 'Withdrawn',
  ARCHIVED: 'Archived',
}

export const DATA_SOURCE_LABEL: Record<DataSourceType, string> = {
  BANK_STATEMENT: 'Bank Statement',
  EWALLET: 'E-Wallet',
  UTILITY: 'Utility Payments',
  GIG_INCOME: 'Gig Income',
  POS: 'POS / Marketplace',
  REMITTANCE: 'Remittance',
  MANUAL: 'Manual Entry',
}

export function riskBandFromPd(pd: number): RiskBand {
  if (pd < 0.15) return 'LOW'
  if (pd < 0.3) return 'MEDIUM'
  return 'HIGH'
}
