# Data contract (everyone follows this exactly)

All files are aggregated to **ZIP code x year**, years **2022-2025**, so they can be joined without surprises.

## Shared rules
| Item | Rule |
|---|---|
| `zip_code` | 5-digit **string** (e.g. `"10001"`), never a number. Invalid ZIPs (e.g. `10000`, non-NYC) -> missing, then fixed or dropped and explained |
| `year` | integer, 2022-2025 only |
| `borough` | UPPERCASE: `BRONX`, `BROOKLYN`, `MANHATTAN`, `QUEENS`, `STATEN ISLAND` |
| column names | lowercase_with_underscores |
| file format | CSV, UTF-8, one row per `zip_code` + `year` (the pair must be unique) |
| missing values | never fill with 0 unless "no record" truly means zero (and say so in markdown) |

## File 1: `data/clean/transport_clean.csv` (Member 2, DONE)
One row per ZIP x year (703 rows, 185 ZIP codes).
`zip_code, year, borough, crash_count, severe_injuries_total, non_severe_injuries_total, fatalities_total, fatal_crash_count, severe_per_crash, night_crash_share, avg_latitude, avg_longitude, is_outlier_zip_year`

## File 2: `data/clean/housing_clean.csv` (Member 1, dataset H5)
Same keys, same format as File 1.

**IMPORTANT - H5 has no building ZIP column.** In the H5 data dictionary, `Zip` is the ZIP of the *owner's business address* and `Filing Representative Zip` is the representative's address. Neither says where the building is. **Do not use them as `zip_code`.** The building location is given by `Borough`, `Block`, `LOT`, `Bin`, `Latitude`, `Longitude`, `Community - Board`, `Council District`, `Census Tract`, `NTA`.
Solution: assign the building ZIP from the coordinates with `members/member1_housing/assign_zip_from_sirta.py` (nearest SIRTA crash, ~90 % accurate when tested on SIRTA itself). Document this and its limits in the notebook.

Required output columns (check the real names with `df.columns`, then **post the final names in the group**):

| Column | Built from (H5 dictionary names) |
|---|---|
| `zip_code`, `year`, `borough` | ZIP from coordinates; `year` from `Filing Date`; `Borough` UPPERCASE |
| `filing_count` | number of filings in that ZIP and year |
| `proposed_units_total` | sum of `Proposed Dwelling Units` |
| `existing_units_total` | sum of `Existing Dwelling Units` |
| `net_new_units` | `proposed_units_total - existing_units_total` (can be negative; explain) |
| `new_construction_filings` | filings with `Existing Dwelling Units` = 0 and `Proposed Dwelling Units` > 0 (H5 has no "job type" column, so this is a proxy; say so) |
| `legalization_filings` | filings with `Request Legalization` = Yes (optional) |
| `median_initial_cost` | median of `Initial Cost` (optional; heavy outliers, use the median) |
| `avg_latitude`, `avg_longitude` | centroid of the filings |
| `is_outlier_zip_year` | IQR flag on `filing_count` |

Same cleaning standard as Member 2: remove empty rows and duplicates (`Job Filing Number` is the unique ID), standardize formats, domain checks (negative units, impossible heights/costs, coordinates outside NYC), missing-value decisions justified in markdown, outliers flagged, validation plots before/after.

Load H5 with a filter, it is large: `$where=filing_date >= '2022-01-01T00:00:00' AND filing_date < '2026-01-01T00:00:00'` and `$limit` (use `$select` to keep only the columns you need).

## File 3: `data/clean/integrated_dataset.csv` (Member 3)
Join on `zip_code` + `year` (never row-by-row). One row per ZIP x year = all columns of file 1 and file 2.
Post-integration cleaning to document:
- ZIP-years present in only one file: decide (outer join recommended) and explain. A missing crash row means *no serious crash recorded* -> `crash_count = 0`; a missing housing row -> `filing_count = 0`. Add `has_crash_data` / `has_housing_data` flags.
- `borough`: take it from either file, resolve conflicts (same ZIP, different borough).
- Remove duplicated/redundant columns (e.g. two `avg_latitude`) and fix dtypes (`zip_code` string, `year` int).
- Derived columns (examples): `severe_injuries_per_1000_units`, `crashes_next_year` (lag).

## Name your files exactly
`Member1_Housing.ipynb`, `Member2_Transportation_SIRTA.ipynb`, `Member3_Integration.ipynb`, `Member4_Story_and_Final.ipynb`, website in `app/`.
