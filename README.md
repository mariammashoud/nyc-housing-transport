# NYC Housing & Transportation: a Data Story

**Course:** Data Engineering and Visualization, Winter 2026 - German International University (GIU)

**Milestone 1:** source exploration, cleaning, integration, analysis and an interactive website.

## Main question
How do development application activity and recorded serious road crashes vary together across New York City ZIP codes in 2022-2025?

| Domain | Source | Catalog |
|---|---|---|
| Housing/development | [DOB NOW Build Job Application Filings](https://data.cityofnewyork.us/Housing-Development/DOB-NOW-Build-Job-Application-Filings/w9ak-ipjd) | H5 |
| Transportation | [Serious Injury Response, Tracking & Analysis Program (SIRTA)](https://data.cityofnewyork.us/Transportation/Serious-Injury-Response-Tracking-Analysis-Program-/xeqp-qz8h) | T4 |

Both sources are aggregated to **ZIP code x year**, then outer-joined. Housing uses official building `postcode` first and flags approximate ZIP fallback. The owner's `zip` is never used. Unit reports are counted once per base job, not once per amendment; they are **not completed homes**. See the [data contract](docs/data_contract.md).

## Start here
- [Final notebook: Members 1-4](notebooks/Member4_Story_and_Final.ipynb) contains the complete pipeline, eight research questions with charts, calculated findings, limitations and NYC relevance.
- Individual notebooks: [Housing](notebooks/Member1_Housing.ipynb), [Transportation](notebooks/Member2_Transportation_SIRTA.ipynb), [Integration](notebooks/Member3_Integration.ipynb).
- [Cleaned datasets](data/clean/) feed the future website.
- [Member 5 checklist](members/member5_website/README.md): website and deployment are **not implemented yet**, intentionally deferred.

## Setup (Python 3.10+)
### Windows PowerShell
```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m jupyter lab
```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m jupyter lab
```

Select the `.venv` interpreter/kernel in VS Code. Jupyter opens notebooks for reading and execution; saved output is included for inspection.

## Reproduce and test
From the repository root, using the environment above:
```powershell
.\.venv\Scripts\python.exe notebooks\run_notebooks.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
On macOS/Linux, use `python notebooks/run_notebooks.py` and `python -m unittest discover -s tests -v`.

The runner executes transportation preparation, housing, integration, transportation research, then the final consolidated notebook. It saves results and stops on cell errors. The final notebook can also run independently, top to bottom.

First execution needs internet and downloads the complete 2022-2025 housing/transport windows. Raw CSVs and source/time/count JSON records are cached in ignored `data/raw/`. Delete the specific cache files intentionally to refresh. Downloads validate source row counts and fail explicitly, rather than silently using an incomplete sample. TLS uses the operating system certificate store.

Only Member 3 writes [integrated_dataset.csv](data/clean/integrated_dataset.csv). Other members must not overwrite it. Tests cover amendment deduplication, missing units, implausible units, official ZIP priority, flagged fallback, key union, reconciled totals and valid denominators.

### Verified correction results
The full source window downloaded 598,706 housing filings. After documented cleaning, the integrated snapshot contains **881 ZIP-year rows, 40 columns and 222 ZIP codes**: 597,934 retained filings and 10,531 retained serious crashes. Housing ZIP assignment is official for 597,761 filings and approximate for 173.

The expanded ZIP coverage differs from the earlier all-nearest-crash snapshot. ZIP 10044 has no usable source coordinates: retain its records in non-map analyses and disclose its omission from maps. All four notebooks were executed, including the final notebook independently from top to bottom; **17 regression/consistency tests passed**. These are snapshot results, not permanent row-count constraints.

## Interpretation
- Application filings are not necessarily residential projects, construction activity or completed housing.
- Job-level unit reports are incomplete and attributed to their first observed filing in this four-year window.
- SIRTA includes serious/fatal crashes, not all collisions; missing/approximate ZIPs affect coverage.
- Unknown housing coverage remains missing; a structural zero means no retained serious-crash record, not proof of no crashes.
- There are no population/traffic denominators. Event ratios are not individual risk.
- Correlation is not causation. Repeated ZIP-years, spatial dependence and a short window limit inference.

## Team contributions
The original notebooks have been corrected/assembled with AI assistance at the user's request. Contributors should review the regenerated results before submission; this table does not imply individual approval.

| Member | Role | Deliverable |
|---|---|---|
| Member 1 - Mostafa | Housing | EDA, justified cleaning, official building ZIP/fallback, job-deduplicated unit aggregation, two questions/charts |
| Member 2 - Mariam | Transportation | SIRTA EDA/cleaning, validation, weighted nighttime-share inputs, two completed cross-domain questions/charts |
| Member 3 - Aya Sweed | Integration | Join justification, outer merge, post-join cleaning, derived measures, total reconciliation, two questions/charts |
| Member 4 - name to confirm | Story/final notebook | Consolidated pipeline, two additional questions/charts, calculated findings, limitations and NYC impact |
| Member 5 - name to confirm | Website/deployment | **Pending:** Dash filters, search, Generate Report, story, deployment and live testing |

## Website / deployment
No app or live deployment is included yet. Member 5 should use the current integrated CSV and its coverage/provenance flags; see the [website checklist](members/member5_website/README.md). Hosting instructions and the live URL must be added after implementation and testing.

## Collaboration
- Follow the [data contract](docs/data_contract.md), [workflow](docs/WORKFLOW.md) and member-specific notes.
- Record AI assistance/prompts in [docs/prompts.md](docs/prompts.md).
- Never commit raw downloads, secrets, environments or files over 100 MB.
- Keep final notebook outputs and clean CSVs in sync by running the reproduction command before submission.
