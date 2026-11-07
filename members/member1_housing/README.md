# Member 1 - Housing dataset (H5: DOB NOW Build Job Application Filings)

**Follow the same structure Member 2 used** (see `notebooks/Member2_Transportation_SIRTA.ipynb`) and `docs/data_contract.md`.

## Read this first: H5 has no building ZIP
`Zip` in H5 is the **owner's** address ZIP, not the building. Do **not** use it. Assign the building ZIP from the coordinates with `assign_zip_from_sirta.py` (in this folder, needs `data/clean/transport_clean_row_level.csv`). Explain this decision and its ~10 % error in the notebook.

## Inputs
- Dataset H5 (confirm the ID from the dataset URL). Filter `filing_date` to **2022-2025** with `$where`, choose columns with `$select`, set `$limit`; justify the sample in the notebook.
- Data dictionary: `DOB_NOW_Build_Job_Application_Filings_Data_Dictionary.xlsx`

## Output files
- `notebooks/Member1_Housing.ipynb`
- `data/clean/housing_clean.csv` (ZIP x year, keys and columns exactly as in `docs/data_contract.md`)

## Checklist
- [ ] Dataset overview: rows, columns (at least 9), geographic + temporal columns, known issues, why H5, link
- [ ] EDA: shape, dtypes, missing values (with chart), descriptive stats, duplicates, inconsistencies, initial plots
- [ ] Remove empty rows and duplicates (`Job Filing Number` is the unique ID)
- [ ] Standardize: `Filing Date` -> datetime and `year`, `borough` UPPERCASE, lowercase_with_underscores
- [ ] Assign `zip_code` (5-digit **string**) from coordinates; report how many filings got a ZIP and how many did not
- [ ] Domain checks: negative units, impossible heights/costs, coordinates outside NYC, borough vs. coordinates
- [ ] Missing values: drop columns above 60 % missing (many are empty: sign-off dates, built-energy fields); justify every drop vs. impute
- [ ] Outliers: IQR / domain rules on `Initial Cost`, `Proposed Dwelling Units`, floor area (flag, justify keep or remove)
- [ ] Validation: before vs. after table and plots
- [ ] Aggregate to ZIP x year (`filing_count`, units, `net_new_units`, `new_construction_filings`, centroid, outlier flag)
- [ ] Export `housing_clean.csv` and **post the final column names in the group**
- [ ] 2 research questions + 2 visualizations on `integrated_dataset.csv` (after Member 3)
- [ ] Prompts recorded in `docs/prompts.md`, contribution lines added to the README table

**Deadline:** `housing_clean.csv` by **Sunday noon**.
