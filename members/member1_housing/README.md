# Member 1 - Housing (H5)

Deliverable: [Member1_Housing.ipynb](../../notebooks/Member1_Housing.ipynb).

## Implemented
- Full-window paginated source download, explicit cache/provenance, EDA (columns/types/missingness/duplicates/distributions).
- Justified drop-versus-missing decisions and validation plots.
- Official building `postcode`, with flagged nearest-crash fallback only when missing. Owner `zip` is never used.
- Tested cleaning/aggregation helpers in [housing_pipeline.py](housing_pipeline.py).
- Invalid measures are quarantined without discarding otherwise usable filings; missing units are not zero.
- Unit pairs counted once per base job across amendments/years, attributed to first observation in 2022-2025; reporting coverage is exported.
- Real `job_type` identifies new-building filings.
- Two research questions/charts with calculated interpretation and limitations.
- Only housing outputs are written here; Member 3 owns the integrated CSV.

## Team review
The earlier sample narrative, unit duplication and integrated-file overwrite have been corrected with AI assistance. Review the cohort definition, conservative >10,000-unit screening threshold and generated findings before submission. Reported units are not completed homes.

See the [data contract](../../docs/data_contract.md) and [prompt log](../../docs/prompts.md).
