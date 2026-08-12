# Dataset Comparison Report (Phase 2C)

Last updated: 2026-08-12

Weighted comparison of credit-risk datasets as candidates for the **deployed**
MyCreditLens application-PD model. Scores are 0–1 per dimension.

**Weights:** target validity 20% · provenance/documentation 15% · inference
compatibility 20% · sample size 10% · leakage risk (higher = safer) 15% ·
temporal validity 10% · feature relevance 10%.

> The weighted score is advisory. Inference compatibility is *also* a hard gate
> (Phase 2D): a dataset that scores well but cannot be reproduced at MyCreditLens
> inference time cannot be deployed regardless of its total. **We do not select a
> dataset because it has the highest score or the highest AUC.**

## Scores

| Dimension (weight) | LoanDataset (active 2.0.0) | Home Credit (app-only, safe subset) | UCI Default (Taiwan) | Microloan India | South German* |
|---|---|---|---|---|---|
| Target validity (20%) | 0.60 | 0.95 | 0.95 | 0.70 | 0.85 |
| Provenance/docs (15%) | 0.30 | 0.95 | 0.90 | 0.30 | 0.85 |
| Inference compatibility (20%) | **1.00** | **0.20** | 0.05 | 0.30 | 0.10 |
| Sample size (10%) | 0.50 | 1.00 | 0.50 | 0.30 | 0.10 |
| Leakage risk – safer (15%) | 0.90 | 0.70 | 0.80 | 0.60 | 0.80 |
| Temporal validity (10%) | 0.20 | 0.30 | 0.30 | 0.10 | 0.20 |
| Feature relevance (10%) | 0.90 | 0.50 | 0.10 | 0.30 | 0.40 |
| **Weighted total** | **0.660** | **0.658** | 0.545 | 0.405 | 0.470 |

\* South German Credit was **not collected and not executed against** — this row
is scored **from published documentation only** (unlike every other row, which is
backed by executed code). It was skipped deliberately: ≈1,000 rows (too small for
a primary model) and German-specific credit attributes that do not map to the
MyCreditLens application (inference-incompatible → benchmark-only). Fetching it
would not change any decision.

## Reading the result

- **LoanDataset (0.660) and Home Credit (0.658) are effectively tied.** Home
  Credit wins decisively on **provenance, target validity, and sample size**;
  LoanDataset wins decisively on **inference compatibility and feature relevance**.
- The tie is broken by the **inference-compatibility gate** (Phase 2D) and by
  **executed evidence** (see `MODEL_2_1_EVALUATION.md`):
  - A Home Credit application-only model, trained on the inference-safe feature
    subset and **excluding the proprietary `external_source_*` scores**, achieves
    only **ROC-AUC 0.626** on its own held-out test set — well below the active
    model's **0.867**. Home Credit's predictive power lives in bureau /
    `external_source` features that MyCreditLens cannot reproduce at inference.
  - **0.0%** of Home Credit loans fall within MyCreditLens's real loan range
    (RM 5k–25k); Home Credit's median loan is **~513,000**. A model trained on
    Home Credit would extrapolate on *every* real MyCreditLens application, and
    the distance-based OOD detector does not even flag these inputs (silent
    extrapolation).
- **UCI, Microloan, South German** are all inference-incompatible with the
  MyCreditLens application form and serve only as external benchmarks or context.

## Conclusion

No available dataset improves the **deployed** model on the dimensions that
matter for MyCreditLens (inference-safe features at a compatible input scale)
without a large, empirically confirmed loss in discrimination and deployment
validity. Home Credit is the strongest **research/benchmark** dataset but is not
a better deployment source. See `RETRAINING_DECISION.md`.
