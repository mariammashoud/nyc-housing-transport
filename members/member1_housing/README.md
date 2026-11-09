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
- Original integrated RQ1: proposed-story profile groups versus seriously injured people per recorded serious crash, using shared dashboard box plots, pooled ratios and calculated findings. This replaces the housing-only unit-change heatmap and is clearly labelled on the website.
- RQ2 retains the descriptive filing/crash association, borough correlations and unit-change groups. The two questions now address building profiles/event injury burden and activity counts, respectively.
- Tested, non-mutating [diagnostics](housing_diagnostics.py) compare proposed area/unit/cost exclusions as sensitivity scenarios only. The 300 sq ft per added unit, low-rise >500 units and small-house >$25M rules do not change exported data or outlier flags.
- Only housing outputs are written here; Member 3 owns the integrated CSV.

## Execution dependency
Run transportation cleaning and Member 1 preparation/export first, then Member 3's integration, then Member 1's research section. The shared [runner](../../notebooks/run_notebooks.py) splits preparation and research to enforce this order. The new research reads the authoritative integrated CSV without writing it; the final consolidated notebook likewise places Member 1 research after integration.

Profile groups use annual NYC-wide positive proposed-story averages before filters or zero-crash exclusions. Missing profiles and zero-crash denominators remain unavailable, not zero injury burdens. Boxes describe ZIP-year ratios, while diamonds pool injury/crash counts. Filing-derived profiles are not actual construction or personal-risk measures.

## Team review
The earlier sample narrative, unit duplication and integrated-file overwrite have been corrected with AI assistance. Review the cohort definition, conservative >10,000-unit screening threshold and generated findings before submission. Construction floor area is not necessarily the finished residential area represented by building-level unit counts; sensitivity thresholds identify review candidates, not proven errors. Reported units are not completed homes.

See the [data contract](../../docs/data_contract.md) and [prompt log](../../docs/prompts.md).
