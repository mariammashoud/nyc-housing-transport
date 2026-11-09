# Member 2 - Transportation (T4/SIRTA) - Mariam

Deliverable: [Member2_Transportation_SIRTA.ipynb](../../notebooks/Member2_Transportation_SIRTA.ipynb).

## Implemented
- Full 2022-2025 download with explicit cache and source-count validation.
- EDA, documented cleaning, missing-ZIP recovery, outlier flags and validation.
- Shared output paths under `data/clean/`, independent of notebook working directory.
- Nighttime share excludes unknown times; export numerator/denominator for proper weighting.
- Two completed cross-domain questions: fatal-crash percentage by annual filing-activity group (website RQ3); nighttime share by filing-volume group and borough (website RQ4).
- Fatal-crash percentages pool fatal/serious-crash counts using the shared dashboard logic, rather than repeating the filing/crash count association. Unknown fatal-crash status is excluded from both numerator and denominator; zero-crash shares stay undefined.
- Actual shared dataset path/columns, calculated chart interpretations, housing source link and limitations.

## Team review
Review regenerated findings before submission. SIRTA covers serious/fatal crashes, not all collisions; ZIP recovery is approximate and no population/traffic risk denominator is available.

See the [data contract](../../docs/data_contract.md) and [prompt log](../../docs/prompts.md).
