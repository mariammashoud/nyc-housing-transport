# Workflow: who works when (deadline: Monday 9/11)

## Correction/reproduction order
The original schedule below is historical. Members 1-3 now have revised deliverables; Member 4 follows on the stacked `fix/member-4` branch; see the individual member READMEs and run `python notebooks/run_notebooks.py` to validate/reproduce them.

Preparation order is **transport cleaning -> housing -> integration -> transport research -> final notebook**. Only Member 3 may write the final integrated CSV. Housing uses official building postcode first; units are job-deduplicated. Member 5 website/deployment remains deferred at the user's request.

```
Member 1 (housing)  ----\
                         >---> Member 3 (integration) ---> Members 1, 2, 3, 4, 5: research questions + visualizations ---> Member 4: final notebook ---> Member 5: deploy ---> submit
Member 2 (transport) ---/            |
        DONE                         +--> Member 5 builds the website with dummy data in parallel
```

| When | Who | What |
|---|---|---|
| Sat night | Member 1 | Finish EDA + cleaning, deliver `housing_clean.csv` following `docs/data_contract.md` |
| Sat night | Member 3 | Write the join code using `transport_clean.csv` (ready) + a sample of housing |
| Sat-Sun | Member 5 | Website skeleton (dropdowns, search, Generate Report) on dummy data with the agreed columns |
| Sun noon | Member 1 | `housing_clean.csv` uploaded + final column names announced |
| Sun afternoon | Member 3 | `integrated_dataset.csv` + post-integration cleaning uploaded |
| Sun evening | Members 1, 2, 3, 4, 5 | Each: **2 research questions + 2 visualizations** on `integrated_dataset.csv` |
| Sun 12 AM | Everyone | **Code freeze** (only bug fixes after this) |
| Mon morning | Member 4 | Merge all parts into the final notebook, write findings/limitations/impact |
| Mon morning | Member 5 | Connect final data, deploy, test the live link, finish README |
| Mon by noon | Member 5 / Member 4 | Send the submission email |

## How to upload (no Git needed)
Repo -> the right folder -> **Add file -> Upload files** -> **Commit changes**. Use the exact file names from `docs/data_contract.md` (same name = the old file gets replaced).
