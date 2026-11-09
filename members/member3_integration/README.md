# Member 3 - Data integration - Aya Sweed

Deliverable: [Member3_Integration.ipynb](../../notebooks/Member3_Integration.ipynb).

## Implemented
- ZIP x year join justification and alternatives.
- Key validation and outer merge with coverage visualization.
- Explicit borough-conflict checks, redundant-column cleanup and descriptive ZIP map points.
- Structural crash zeros distinguished from unknown housing/source measurements; source flags retained.
- Corrected job-unit columns and nighttime numerator/denominator carried through.
- Calendar-keyed year-over-year/next-year measures; undefined ratios remain missing.
- Dynamic key-union checks and source-total reconciliation, not hard-coded snapshot counts.
- Two research questions/charts with calculated findings and cautions about repeated ZIP-years.
- **Sole producer of `integrated_dataset.csv`.**

## Team review
Review regenerated correlations before submission. They are descriptive, not causal; simple exploratory p-values do not account for spatial dependence or clustered repeated observations.

See the [data contract](../../docs/data_contract.md) and [prompt log](../../docs/prompts.md).
