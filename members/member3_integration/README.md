# Member 3 - Data integration

## Inputs
- `data/clean/transport_clean.csv` (ready)
- `data/clean/housing_clean.csv` (from Member 1, due Sunday noon)

## Output files
- `notebooks/Member3_Integration.ipynb`
- `data/clean/integrated_dataset.csv`

## Checklist
- [ ] Explain the join: key `zip_code` + `year`, why this granularity, why not record-level, alternatives considered (borough x year, spatial join)
- [ ] Check keys first: both `zip_code` are 5-digit strings, both `year` are integers, the pair is unique in each file
- [ ] Merge (outer recommended); report how many ZIP-years matched / only housing / only transport (chart)
- [ ] **Post-integration cleaning (required):** new missing values from the join (crash 0 / filing 0 + flags), inconsistent `borough`, redundant or duplicated columns, data type mismatches
- [ ] Derived columns (e.g. severe injuries per 1,000 new units, next-year crashes)
- [ ] Validation: row counts before/after, no duplicate keys, summary of the final columns
- [ ] Upload `integrated_dataset.csv` and **announce it in the group** (Members 1, 2, 4, 5 are waiting for it)
- [ ] 2 research questions + 2 visualizations
- [ ] Prompts + contribution line

**Deadline:** `integrated_dataset.csv` by **Sunday afternoon**. Start now with a sample of housing data.
