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
Install Python 3.10 or newer, then create an isolated environment from the repository root.

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
jupyter lab
```

**Windows PowerShell**
```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
jupyter lab
```

In VS Code, choose the `.venv` interpreter and the matching notebook kernel. Re-run `python -m pip install -r requirements.txt` after pulling changes to the dependency file. To run the website once `app/app.py` exists:
```bash
python app/app.py
```

## Deployment
_(Member 5: add the hosting platform, build/start command, and the live link.)_

## Team contributions
| Member | Role | Contribution |
|---|---|---|
| Member 1 - Mostafa | Housing dataset and EDA | Selected and documented the DOB NOW: Build Job Application Filings dataset (H5, `w9ak-ipjd`); EDA on the 598,706-row 2022–2025 extract; pre-integration cleaning (deduplication on `job_filing_number`, dropping >60% missing columns, standardized dates/borough/types, domain-rule checks, owner `zip` audit and 5-digit building `zip_code` assignment from SIRTA coordinates via 1-NN, Tier-1 corruption typo removal and Tier-2 log-scale IQR outlier flagging); validation table and plots; one-filing-per-job (`-I1`) unit aggregation to ZIP x year (`housing_clean.csv`); 2 research questions and 2 visualizations. |
| Member 2 - Mariam | Transportation dataset and EDA | Selected and documented the SIRTA dataset (T4); EDA; pre-integration cleaning (empty rows, duplicates, standardized dates/borough/5-digit ZIP, domain-rule checks, ZIP recovery from coordinates, IQR outlier flagging); validation plots; aggregation to ZIP x year (`transport_clean.csv`); 2 research questions and 2 visualizations. |
| Member 3 - Aya Sweed | Data integration | Found that the housing data was a 3% sample, downloaded the full H5 dataset (598,706 filings, `fetch_h5_data.py`) and regenerated `housing_clean.csv` (fixed a bug that dropped 316k filings with blank fields). Joined housing and SIRTA crashes on ZIP code x year (justified vs. borough-level, record-level and spatial joins) with key checks and an outer merge; post-integration cleaning (duplicated columns, join-created missing values with source flags, dtypes), derived columns (YoY changes, next-year crashes, rates) and validation (totals reconcile with both sources) -> `integrated_dataset.csv`; 2 research questions and 2 visualizations (change over time and one-year lag, between vs. within ZIP codes). |
| Member 4 - _name_ | Analysis, storytelling, final notebook | _(2-3 lines: findings, limitations, impact, notebook assembly, 2 questions and visualizations)_ |
| Member 5 - _name_ | Website and deployment | _(2-3 lines: Dash app, filters, search, Generate Report, deployment, README, 2 questions and visualizations)_ |

## Team rules
- Everyone uploads their own files through the GitHub website: **Add file -> Upload files -> Commit changes** (no Git needed).
- Use the exact file names in `docs/data_contract.md`; uploading the same name replaces the old file.
- Follow `docs/data_contract.md` (keys and formats) and `docs/WORKFLOW.md` (who works when).
- Each member has a checklist in `members/<member>/README.md`.
- Never commit secrets (`.env`) or files over 100 MB.
- Every prompt used is recorded in `docs/prompts.md`.
