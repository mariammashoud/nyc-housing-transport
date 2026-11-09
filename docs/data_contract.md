# Data contract

## Shared keys and coverage
- One row per **`zip_code` + `year`**, with no duplicate pair.
- `zip_code`: five-digit text; load CSVs with `dtype={"zip_code": str}`.
- `year`: integer, **2022-2025**. No partial 2026 comparisons.
- `borough`: BRONX, BROOKLYN, MANHATTAN, QUEENS or STATEN ISLAND.
- Column names: lowercase_with_underscores; CSV: UTF-8.
- Raw downloads are explicitly cached in ignored `data/raw/`. JSON sidecars record source, time and count. Delete caches intentionally to refresh. Never silently substitute fabricated/sample data after a network failure.
- Source schemas were checked against the live API during the correction. Row counts are computed, not hard-coded: the source can change.

## Housing source and ZIP assignment
[H5: DOB NOW Build Job Application Filings](https://data.cityofnewyork.us/Housing-Development/DOB-NOW-Build-Job-Application-Filings/w9ak-ipjd).

**Correction to the earlier contract:** the live source includes `postcode` (building postcode) and `job_type`. Use building `postcode` first. The separate `zip` is a mailing-address field and is **never** the building join key.

For missing/invalid postcode only, use the existing nearest-SIRTA-crash method within 0.01 degrees, flagged `nearest_crash`. This is approximate, not a boundary lookup or a validated building-level accuracy estimate. ZIP screening uses broad numeric NYC ranges, not a USPS directory. Invalid coordinates become missing. Drop filings only when no usable building ZIP can be obtained, or their identifying/date/borough keys are unusable.

**Measurements:** missing units/heights/costs are not zero. Quarantine impossible measures without deleting otherwise usable filings. Units must be non-negative integers; values above 10,000 are conservatively quarantined as suspicious, not replaced with guessed corrections. Keep plausible outliers and flag them using IQR on `log1p` cost, proposed units and floor area, preserving the team's log-scale refinement.

## `data/clean/housing_clean.csv`
Produced by [Member 1's notebook](../notebooks/Member1_Housing.ipynb).

| Columns | Meaning |
|---|---|
| `zip_code`, `year`, `borough` | Shared keys/location |
| `filing_count` | Distinct application filing IDs, including amendments; not completed homes |
| `new_construction_filings` | Filings explicitly labelled `New Building` in `job_type`; not a zero-existing-units proxy |
| `permit_issued_count` | Filings currently labelled Permit Issued or LOC Issued |
| `unique_job_count` | Base jobs first observed in this ZIP-year within the 2022-2025 window |
| `jobs_with_known_units` | Those jobs with a complete existing/proposed unit pair |
| `proposed_units_total`, `existing_units_total`, `net_new_units` | Reported units counted **once per base job**, not per amendment |
| `initial_cost_total`, `initial_cost_median` | Sum/median of reported **filing-level** declared costs (USD); related filings may overlap |
| `total_floor_area` | Sum of reported filing-level construction area (sq ft); not unique building area |
| `avg_proposed_stories`, `avg_proposed_height` | Means of known reports; height in feet |
| `avg_latitude`, `avg_longitude` | Mean known filing coordinates, not official ZIP centroids |
| `outlier_filing_count`, `outlier_filing_share` | Count/share flagged by log-scale IQR on cost, proposed units or area |
| `official_zip_filings`, `approximate_zip_filings` | ZIP provenance; sum equals `filing_count` |
| `is_outlier_zip_year` | IQR flag on ZIP-year filing count |

### Job-unit accounting
The base job ID is the part of `job_filing_number` before its suffix. Choose one complete unit pair from the latest valid filing in the window, and attribute it to the ZIP/year of the job's first observed filing in this window. Do not mix existing/proposed values from different filings.

This is a **window-defined cohort**, not necessarily the original lifetime filing year. Four-year totals do not repeat a base job, but the reported units are still not completed housing supply. Negative net changes are allowed.

If jobs exist but none have complete unit pairs, unit totals are unknown. Partial totals cover reporting jobs only. If a ZIP-year contains filings but no first-observed jobs, its job-cohort unit totals are zero.

## `data/clean/transport_clean.csv`
Produced by [Member 2's notebook](../notebooks/Member2_Transportation_SIRTA.ipynb).

[T4: SIRTA](https://data.cityofnewyork.us/Transportation/Serious-Injury-Response-Tracking-Analysis-Program-/xeqp-qz8h) covers recorded serious/fatal crashes, not all road collisions.

Columns:
`zip_code`, `year`, `borough`, `crash_count`, `severe_injuries_total`, `non_severe_injuries_total`, `fatalities_total`, `fatal_crash_count`, `severe_per_crash`, `night_crash_share`, `night_crash_count`, `crashes_with_known_time`, `avg_latitude`, `avg_longitude`, `is_outlier_zip_year`.

Nighttime is hours **00-05 and 22-23**. Unknown times are excluded from the share denominator, not treated as daytime. Aggregate nighttime shares using `sum(night_crash_count) / sum(crashes_with_known_time)`, never the unweighted mean of ZIP percentages. A zero denominator gives a missing share.

Secondary injury/death counts remain unknown if the whole source group is unknown. Missing ZIP recovery is coordinate-based and approximate. `transport_clean_row_level.csv` contains the retained crash records for auditing/reference.

## `data/clean/integrated_dataset.csv`
**Only [Member 3's notebook](../notebooks/Member3_Integration.ipynb) writes this file.** Other members read it or create exploratory in-memory merges; they must never overwrite it.

- Outer join on the shared keys; retain the union of both input key sets.
- Housing-only row: zero **recorded** serious-crash counts under the source-coverage assumption, but undefined crash shares/rates stay missing. This is not proof of no real-world crashes.
- Transport-only row: housing coverage is unknown; do **not** fill housing metrics with zero.
- Preserve `has_housing_data` and `has_crash_data` flags.
- Check borough conflicts explicitly before export; do not silently select contradictory labels.
- Replace source coordinates with `zip_latitude`/`zip_longitude`: fixed descriptive map points from source means, not official ZIP centroids.
- Official ZIPs without any source coordinates remain in the data with blank map points. Maps must omit only those points and report the excluded coverage; other charts/counts retain those rows. Never invent coordinates or drop otherwise valid records just to make a map.
- Preserve separate `is_outlier_housing` and `is_outlier_transport` flags.
- Include all nonredundant source metrics above.

Derived columns:
| Column | Meaning |
|---|---|
| `crashes_per_100_filings` | Recorded crashes / filings x 100; missing for zero/missing denominator; **not individual risk** |
| `filing_change_yoy`, `crash_change_yoy` | Same-ZIP differences matched on the actual preceding calendar year |
| `crashes_next_year` | Same-ZIP crash count in year + 1; missing where the next key is absent |
| `severe_injuries_per_1000_units` | Descriptive ratio per 1,000 reported proposed job-cohort units; **not risk per resident/new home** |

All source count/unit totals must reconcile through the merge. Ratios must never be infinite. Nullable counts remain blank where coverage is unknown.

## Reproduction and final notebook
Run `python notebooks/run_notebooks.py` from the repository root, then `python -m unittest discover -s tests -v`.

[Member 4's final notebook](../notebooks/Member4_Story_and_Final.ipynb) consolidates the full preparation/integration pipeline, all Members 1-4 research questions, and Member 4's two additional charts and synthesis. It runs top to bottom. Member 5 website/deployment is intentionally deferred.
