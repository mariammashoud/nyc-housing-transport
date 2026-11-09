# Member 1 - Housing (H5)

Deliverable: [Member1_Housing.ipynb](../../notebooks/Member1_Housing.ipynb).

## Implemented
- Full-window paginated source download, explicit cache/provenance, EDA (types/memory/missingness/duplicates/distributions, owner-versus-building ZIP and domain audits).
- Justified drop-versus-missing decisions and validation plots.
- Official building `postcode`, with flagged nearest-crash fallback only when missing. Owner `zip` is never used.
- Tested cleaning/aggregation helpers in [housing_pipeline.py](housing_pipeline.py).
- Invalid measures are quarantined without discarding otherwise usable filings; missing units are not zero.
- Unit pairs counted once per base job across amendments/years, attributed to first observation in 2022-2025; reporting coverage is exported.
- Real `job_type` identifies new-building filings.
- Two research questions with reporting-coverage heatmaps, descriptive borough correlations, unit-change groups and calculated interpretations.
- Tested, non-mutating [diagnostics](housing_diagnostics.py) compare proposed area/unit/cost exclusions as sensitivity scenarios only. The 300 sq ft per added unit, low-rise >500 units and small-house >$25M rules do not change exported data or outlier flags.
- Only housing outputs are written here; Member 3 owns the integrated CSV.

## Team review
The earlier sample narrative, unit duplication and integrated-file overwrite have been corrected with AI assistance. Review the cohort definition, conservative >10,000-unit screening threshold and generated findings before submission. Construction floor area is not necessarily the finished residential area represented by building-level unit counts; sensitivity thresholds identify review candidates, not proven errors. Reported units are not completed homes.

See the [data contract](../../docs/data_contract.md) and [prompt log](../../docs/prompts.md).
