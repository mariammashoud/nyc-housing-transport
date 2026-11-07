# NYC Housing & Transportation: a Data Story

**Course:** Data Engineering and Visualization, Winter 2026 - German International University (GIU)
**Milestone 1:** cleaning, integration, and an interactive website

## Question
How do housing development and serious traffic crashes relate across New York City ZIP codes? _(Team: refine this sentence once the research questions are final.)_

## Datasets
| Domain | Dataset | Catalog ID | Link |
|---|---|---|---|
| Housing & Development | DOB NOW: Build Job Application Filings | H5 | _add link (the dataset ID is in its URL)_ |
| Transportation | Serious Injury Response, Tracking & Analysis Program (SIRTA) | T4 | https://data.cityofnewyork.us/Transportation/Serious-Injury-Response-Tracking-Analysis-Program-/xeqp-qz8h |

**Integration:** both datasets are aggregated to **ZIP code x year** (2022-2025) and joined on `zip_code` + `year`. H5 has no building ZIP, so its ZIP is assigned from latitude/longitude (see `docs/data_contract.md`).

## Repository structure
```
notebooks/   Jupyter notebooks (one per member + the final merged notebook)
members/     checklist and instructions for each member

data/clean/  cleaned and aggregated CSVs (housing_clean.csv, transport_clean.csv, integrated dataset)
data/raw/    raw downloads (not committed; the notebooks download them)
app/         the Dash website
docs/        prompts.md and other documentation
```

## Data contract (agreed column names)
- `zip_code`: 5-digit **string**
- `year`: integer
- `borough`: UPPERCASE (BRONX, BROOKLYN, MANHATTAN, QUEENS, STATEN ISLAND)
- all column names: lowercase_with_underscores

## Setup
```bash
git clone <repo-url>
cd nyc-housing-transport
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook          # open the notebooks
python app/app.py         # run the website locally (after Member 5 adds it)
```

## Deployment
_(Member 5: add the hosting platform, build/start command, and the live link.)_

## Team contributions
| Member | Role | Contribution |
|---|---|---|
| Member 1 - _name_ | Housing dataset and EDA | _(2-3 lines: dataset, cleaning, 2 research questions and visualizations)_ |
| Member 2 - Mariam | Transportation dataset and EDA | Selected and documented the SIRTA dataset (T4); EDA; pre-integration cleaning (empty rows, duplicates, standardized dates/borough/5-digit ZIP, domain-rule checks, ZIP recovery from coordinates, IQR outlier flagging); validation plots; aggregation to ZIP x year (`transport_clean.csv`); 2 research questions and 2 visualizations. |
| Member 3 - _name_ | Data integration | _(2-3 lines: join key, aggregation, merge, post-integration cleaning, 2 questions and visualizations)_ |
| Member 4 - _name_ | Analysis, storytelling, final notebook | _(2-3 lines: findings, limitations, impact, notebook assembly, 2 questions and visualizations)_ |
| Member 5 - _name_ | Website and deployment | _(2-3 lines: Dash app, filters, search, Generate Report, deployment, README, 2 questions and visualizations)_ |

## Team rules
- Everyone uploads their own files through the GitHub website: **Add file -> Upload files -> Commit changes** (no Git needed).
- Use the exact file names in `docs/data_contract.md`; uploading the same name replaces the old file.
- Follow `docs/data_contract.md` (keys and formats) and `docs/WORKFLOW.md` (who works when).
- Each member has a checklist in `members/<member>/README.md`.
- Never commit secrets (`.env`) or files over 100 MB.
- Every prompt used is recorded in `docs/prompts.md`.
