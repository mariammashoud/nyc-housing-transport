# Prompts used

Every prompt used in the project (AI or otherwise) is listed here, per member, with the step it supported.

## Member 2 - Transportation dataset (SIRTA, T4)
An AI assistant (Claude) was used to help write and debug the code in this section; the results were run and reviewed by the author.

- Which transportation dataset from the catalog should I choose, and do I pick only one? (chose T4 / SIRTA, ID `xeqp-qz8h`)
- How do I download the SIRTA dataset? (shared the data dictionary and the CSV)
- Build the notebook for the T4 dataset covering all project requirements: dataset overview, EDA, pre-integration cleaning (missing values, duplicates, inconsistencies, formats, outliers), validation, ZIP x year aggregation, and 2 research questions.
- Fix this error from the API download: `KeyError: No column contains ('collision',)`.

## Member 1 - Housing dataset (DOB NOW: Build – Job Application Filings, H5)
An AI assistant was used to help write, debug, and refine the code and analysis in this section; all outputs were executed and verified by the author.

- Compare the candidate housing datasets (H1–H5) and justify why DOB NOW: Build – Job Application Filings (H5, `w9ak-ipjd`) best fits our study. (selected H5 because it records citywide construction filings with coordinates, costs, and existing vs. proposed dwelling units)
- Run EDA on the 2022–2025 H5 extract (`data/raw/w9ak-ipjd.csv`, 598,706 rows × 34 columns) covering types, missingness against the 60% threshold, descriptive statistics, and duplicates. (verified only 5 columns exceed 60% missingness—`apt_condo_no_s` at 99.2% and four `built_*` fields at 89.8%—while `special_inspection_agency_number` at 37.7% and `work_on_floor` at 9.2% are kept)
- Audit the raw owner `zip` column against `borough` and use `assign_building_zip` (`assign_zip_from_sirta.py`) to assign a 5-digit building `zip_code` from coordinates. (confirmed a 63.7% borough mismatch on raw `zip`; assigned building ZIPs to 98.6% of filings within 0.01° and noted the ~9–10% boundary error)
- Update domain checks 4a–4d so blank (`NaN`) heights, stories, and units on interior or plumbing jobs are kept rather than dropped. (Check 4a removes 0 rows, Check 4b removes 633 impossible height/story rows, Check 4c removes 0 rows, and Check 4d removes 24 borough-prefix mismatches)
- Fix the Tier-1 typo rules to match `"1 Family"`, `"2 Family"`, `"3 Family"` for the > $25M cost check, add a rule removing rows with existing or proposed units > 10,000, and print counts per rule. (removed 52 rows total: 10 from cost, 20 from low-rise > 500 units, and 22 from the > 10,000 unit cap)
- Replace the raw-scale Tukey fence in Tier 2 with a log-scale IQR rule (`log1p`) so normal renovations are not flagged as outliers while large developments remain flagged and kept. (reduced flagged filings from 32.9% to 2.0%, or 11,820 filings)
- Compute `proposed_units_total`, `existing_units_total`, and `net_new_units` in the `zip_code × year` aggregation from one `-I1` filing per job instead of summing across amendments, keeping `filing_count` and output columns unchanged. (verified `housing_clean.csv` has 736 rows = 184 ZIPs × 4 years and plausible yearly `net_new_units` of 54k–101k)
- Update the markdown text and research question findings in `Member1_Housing.ipynb` to match the 598,706-row outputs without causal claims, and write outputs only to the root `data/clean/` folder. (updated RQ1 to $r = 0.38$ across 701 cells and RQ2 with the true yearly trajectory and top 5 dual-hotspot ZIPs)

## Member 3 - Integration
An AI assistant (Claude) was used to help write and debug the code in this section; the results were run and reviewed by the author.

- Check whether the housing data Member 1 used is the real H5 table, and download the full dataset for 2022-2025. (found the local snapshot was an 18,500-row sample with columns that don't exist in H5; wrote `members/member3_integration/fetch_h5_data.py`, which downloaded 598,706 rows)
- Re-run Member 1's housing notebook on the real data and fix any errors. (fixed the import path for `assign_zip_from_sirta`, a pandas 3 dtype check, and domain checks 4a/4b, which were dropping 316,671 filings with blank height or units; checked that only 633 rows are now removed and that `housing_clean.csv` has 736 rows = 184 ZIPs x 4 years)
- What exactly should Member 1 fix after the regeneration? (list: dwelling units double-counted across filings of the same job, an uncaught 111,111,111 typo, markdown cells written about the old sample)
- Draft a task-based plan for my integration work that I can approve step by step. (tasks: key checks, outer merge, post-integration cleaning, derived columns, validation/export, 2 research questions)
- Create the integration notebook with its goal, inputs/outputs, and a markdown section explaining why we join on ZIP code x year and which alternatives we rejected. (reviewed the reasoning: record level not allowed, borough x year only 20 rows, spatial join and monthly grain considered; noted the nearest-crash ZIP assignment as a limitation)
- Load both cleaned files and check the join keys before merging: 5-digit text ZIP codes, integer years 2022-2025, unique (zip_code, year) pairs, uppercase boroughs. (all checks passed: housing 736 rows / 184 ZIPs, transport 703 rows / 185 ZIPs; found 4 columns present in both files to resolve after the merge)
- Merge the two files with an outer join on zip_code + year, chart how many ZIP-years matched / are housing-only / transport-only, and list the one-sided ZIP codes. (738 rows: 701 matched, 35 housing-only, 2 transport-only; checked that every housing-only ZIP has crashes in other years and that the transport-only ZIP 10282 has no filings because of nearest-crash ZIP assignment)
- Do the post-integration cleaning: resolve the duplicated columns, fill the missing values created by the join, add source flags, and fix data types. For ZIP 10282 (no housing row), use a flag instead of filling filing_count with 0. (0 borough conflicts; replaced 4 coordinate columns with one centroid per ZIP; crash counts set to 0 on 35 housing-only rows but crash rates left blank; added has_housing_data / has_crash_data; checked the before/after missing-value table)
- Add derived columns: crashes per 100 filings, year-over-year change in filings and crashes, next-year crashes, and severe injuries per 1,000 units (marked provisional until Member 1's unit fix). (year links matched on year +/- 1, not row order; checked each column is blank only where it should be, e.g. crashes_next_year blank for 2025; verified ZIP 11207 by hand)
- Validate the integrated table and export integrated_dataset.csv: row count, unique keys, totals matching the source files, data contract, plus a column summary for Members 4 and 5. (738 rows x 34 columns; all filing and crash totals equal the source files; re-read the saved CSV to confirm ZIP codes stay 5-digit text)
- Research question 1: did ZIP codes whose construction activity grew most between 2022 and 2025 also see a larger change in serious crashes? Make a scatter chart with title, axis labels and trend line. (184 ZIP codes; no relationship, Pearson r = -0.07, p = 0.37; checked regression to the mean and per-borough results; wrote limitations, no causal claims)
- Research question 2: is a ZIP code's construction activity in one year associated with its serious crashes the following year? Compare between ZIP codes and within each ZIP code, with a two-panel box-plot chart. (552 ZIP-years; between ZIP codes Spearman rho = 0.63, within ZIP codes r = 0.04, p = 0.37; regression: 100 extra filings go with +0.14 crashes next year; interpreted as a ZIP-size effect, not a construction effect)
- Review my prompt log, add a prompts section to the notebook, and draft my 2-3 line contribution entry for the README. (checked the wording and added my name)

## Member 4 - Analysis, storytelling, final notebook
_(add prompts here)_

## Member 5 - Website and deployment
_(add prompts here)_
