# Alternative-Data Dataset Research

Last updated: 2026-08-12

Question: does a **defensible public dataset** exist that pairs *transaction
history* with a *verified future loan repayment / default outcome* for the same
individuals — enough to train a real alternative-data PD model?

## Search performed

Queried for: alternative-data credit scoring datasets, bank-transaction default
datasets, cash-flow underwriting datasets, microfinance repayment datasets, gig-
worker credit-risk datasets, and financial-transaction loan-default datasets.

## Findings

| Candidate | What it actually contains | Usable as transaction→default PD? |
|---|---|---|
| **LendingClub** (2007–2020, ~2.9M loans) | Loan-account attributes, credit-history summaries, issuing conditions, and repayment status/outcome | **Partly.** Real repayment outcomes, but **loan-account level**, not raw individual bank-transaction streams. No cash-flow transaction series. |
| **Freddie Mac Single-Family** | Monthly **mortgage** performance (delinquency/default) | No. Mortgage account performance, not consumer transaction history; product mismatch. |
| **UCI Default of Credit Card Clients** | Credit-card bill/payment history + next-month default (Taiwan, 30k) | No. Account payment history, not bank transactions; inference-incompatible with MyCreditLens. |
| **Home Credit Default Risk** (already local) | Application + bureau + prior-loan + installment/POS/credit-card **behaviour** tables + default target | **Behavioural, not raw transactions.** Rich, but bureau/behaviour features are not reproducible at MyCreditLens inference (see `RETRAINING_DECISION.md`). |
| Academic transaction-representation work (e.g. arXiv:2404.02047 "Learning Transactions Representations …") | Methods trained on **proprietary** bank transaction data | No public data released. |
| **AI-BAAM** (arXiv:2510.16066, "AI-Driven Bank Statement Analytics as Alternative Data for Malaysian MSME Credit Scoring") | Directly on-thesis for MyCreditLens (Malaysian MSME, bank-statement alternative data) | Methodology reference; no released public labelled dataset confirmed. |
| Kaggle "fraud" transaction datasets | Transaction streams with **fraud** flags | No. **Fraud ≠ default** — must not be used as a PD label. |

## Conclusion

> **Public transaction-level datasets with verified future repayment/default
> labels are limited; therefore alternative-data risk modelling remains a future
> validation task.**

No credible, well-documented, openly-licensed dataset was found that pairs raw
individual **bank-transaction history** with a **verified future default/repayment
outcome** at usable scale. The closest (LendingClub) is loan-account level;
transaction-native work relies on proprietary bank data.

**Therefore the alternative-data model is not trained and is not faked.** The
existing transaction pipeline (ingestion, normalisation, cash-flow features, data
reliability, integrity signals, stress/counterfactual context — synthetic
`gig_*`/`transactions.csv`) is preserved as **analyst context only**, explicitly
**not** a statistically validated PD predictor. A real `AlternativeDataRiskModel`
will be trained only when a dataset containing *historical transaction behaviour +
verified future default/repayment outcome* becomes available (ideally
Malaysian/RM-scale, e.g. a partner-bank statement dataset or a released version of
the AI-BAAM-style corpus).

Sources:
- [LendingClub / credit-risk datasets overview](https://www.listendata.com/2019/08/datasets-for-credit-risk-modeling.html)
- [Learning Transactions Representations (arXiv:2404.02047)](https://arxiv.org/pdf/2404.02047)
- [AI-BAAM: Bank Statement Analytics for Malaysian MSME Credit Scoring (arXiv:2510.16066)](https://arxiv.org/pdf/2510.16066)
- [UCI Default of Credit Card Clients](https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients)
