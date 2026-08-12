import type { Consent } from "./types"

export const consentsSeed: Consent[] = [
  {
    id: "bc1",
    scope: "Bank statement analysis",
    sourceType: "BANK_STATEMENT",
    version: "2.1",
    grantedAt: "2025-03-02T09:12:00Z",
    expiresAt: "2025-09-02T09:12:00Z",
    revokedAt: null,
    status: "GRANTED",
  },
  {
    id: "bc2",
    scope: "E-wallet transaction analysis",
    sourceType: "EWALLET",
    version: "2.1",
    grantedAt: "2025-03-02T09:13:00Z",
    expiresAt: "2025-09-02T09:13:00Z",
    revokedAt: null,
    status: "GRANTED",
  },
  {
    id: "bc3",
    scope: "Utility payment history",
    sourceType: "UTILITY",
    version: "2.1",
    grantedAt: "2025-03-02T09:14:00Z",
    expiresAt: "2025-09-02T09:14:00Z",
    revokedAt: null,
    status: "GRANTED",
  },
  {
    id: "bc4",
    scope: "Automated decision-making disclosure",
    sourceType: "MANUAL",
    version: "2.1",
    grantedAt: "2025-03-02T09:15:00Z",
    expiresAt: null,
    revokedAt: null,
    status: "GRANTED",
  },
]
