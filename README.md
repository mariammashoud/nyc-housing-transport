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
- [Member 5 research](notebooks/Member5_Website_Research.ipynb) adds two questions/charts on concentration and recurring high activity, using the same functions as the dashboard. The website displays all ten team questions as RQ1-RQ10.
- [Cleaned datasets](data/clean/) feed the future website.
- [Member 5 dashboard and checklist](members/member5_website/README.md): local website implemented; public deployment and a second-device live check remain pending.

## Setup (Python 3.12 recommended)
### Windows PowerShell
```powershell
py -3.12 -m venv .venv
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

The runner executes transportation preparation, housing, integration, transportation research, the final consolidated notebook, then Member 5's research notebook. It saves PNG or interactive Plotly results and stops on cell errors. The final notebook and Member 5 notebook can also run independently.

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
| Member 5 - name to confirm | Website/deployment | Dash filters/search, atomic Generate Report, all ten team research questions with interactive charts, story/coverage notices, CSV download, two additional research questions/charts, tests and Render configuration; public deployment pending |

## Website / deployment

### Run the dashboard locally
The web app needs only the committed integrated CSV, not raw downloads or notebook execution. Its small dependency manifest is separate from the notebook dependencies.

```powershell
.\.venv\Scripts\python.exe -m pip install -r app\requirements.txt
.\.venv\Scripts\python.exe -m app.app
```

Open **http://127.0.0.1:8050/**. Stop with `Ctrl+C`. On macOS/Linux use `python -m pip install -r app/requirements.txt` and `python -m app.app` in the activated environment. Run from the repository root, not from inside `app/`. The web stack is pinned/tested on Python 3.12; the pinned Pandas version needs Python 3.11 or newer.

### How to use it
1. Choose boroughs, years, a housing measure and a transportation measure.
2. Optionally select **Search** mode. Supported examples:
   - `11201 2024`
   - `Brooklyn 2024 new buildings`
   - `Staten Island 2023 permits`
   - `Manhattan 2025 fatalities`
3. Click **Generate Report**. All charts, findings and cards update together. Changed controls do not apply until this button is clicked.
4. **Download report CSV** exports the last applied selection, even if you have edited controls since then. **Reset all** restores the full default report.

Search is a strict, documented parser, not general natural-language AI. It accepts known ZIPs, boroughs, years and measure keywords. Named fields override dropdowns; unspecified fields retain the dropdown selections. Unsupported text, conflicting measures, empty filters and empty results produce a visible error, clear the active report and disable downloading. Queries are limited to 160 characters.

### Ten research questions
The website shows all ten questions, with one interactive chart per question, in team order:

1. **RQ1 / Member 1:** reported net unit change by borough and first-observed job year (diverging heatmap).
2. **RQ2 / Member 1:** housing activity and recorded transportation events by ZIP-year (scatter).
3. **RQ3 / Member 2:** housing activity and people seriously injured (scatter).
4. **RQ4 / Member 2:** nighttime crash share by borough and housing-activity group (weighted-share heatmap).
5. **RQ5 / Member 3:** within-ZIP changes between the first and last selected years (scatter).
6. **RQ6 / Member 3:** housing activity and following-year transportation events, pooled and within-ZIP views (two-panel scatter).
7. **RQ7 / Member 4:** borough shares of housing and transportation activity (grouped bars).
8. **RQ8 / Member 4:** indexed trends using a consistent, housing-covered ZIP panel (lines).
9. **RQ9 / Member 5:** transportation concentration across annual housing-activity groups (grouped bars).
10. **RQ10 / Member 5:** recurring jointly high activity, up to 20 ZIPs (heatmap).

All questions follow the applied borough/year/ZIP scope. Measure dropdowns generalize the original filing/crash comparisons; RQ1 always uses reported units, and RQ3 always uses serious injuries. RQ4 uses the dashboard's fixed annual NYC activity groups rather than re-ranking pooled selected ZIP-years; it divides summed nighttime counts by summed known-time crash counts. RQ5 excludes ZIPs without housing at both selected endpoints. RQ5/RQ6 exclude ZIPs never present in the full snapshot's crash source. RQ6 only pairs exact consecutive years within the selection; RQ8 uses ZIPs with housing coverage in every selected year and indexes to the first selected year. Missing coverage, insufficient years and undefined denominators produce explicit chart notices, not fabricated zeros; all ten question headings remain visible.

Two supplementary context charts remain available: yearly totals on independent count axes, and a map of descriptive source-mean ZIP points. Map size encodes transportation and color encodes housing; gray marks unknown housing.

Annual benchmarks use all NYC housing-covered ZIPs **before filters**. High activity means a positive value at/above the year's 75th percentile; tied values stay together, so the high group is not necessarily exactly 25%. Unknown housing is excluded from paired-domain research, not turned into zero. Multi-year bar denominators count ZIP-years, not distinct residents. A recurring ZIP is jointly high in at least two selected years.

The default snapshot's highest-filing group accounts for approximately **40.7%** of serious crashes among housing-covered ZIP-years; **32 ZIPs** are jointly high in at least two years. These are descriptive patterns, not causal effects or risk estimates. Figures, findings and denominators are recalculated for each applied selection.

Coverage notices distinguish unknown housing, structural crash zeros and approximate housing ZIPs. ZIP 10044 has no map coordinates but remains in other charts/totals/downloads. The basemap uses CARTO/OpenStreetMap public tiles and requires internet; it is not an authoritative boundary map.

### Tests
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
Dashboard tests cover all ten question headings on initial, filtered, sparse and reset reports; all twelve chart containers; weighted nighttime denominators; endpoint/lag matching; consistent-panel indexing; filtering, search, exact percentile/tie handling, missingness, state isolation, all nine measure combinations, actual Dash HTTP callbacks, downloads and the two executed Member 5 notebook charts. Existing data-pipeline checks remain included.

Latest dashboard verification: **31 dashboard tests passed**. Desktop (1440px) and mobile (390px) page loads displayed all ten questions without horizontal overflow. Browser search and reset retained all ten question cards; callback tests also covered missing-data selections and CSV downloads. Explicit graph container heights prevent charts collapsing on mobile.

### Deploy on Render (account authorization required)
**Status: configuration ready; no public deployment or live URL has been created.**

1. Commit and push the Member 5 branch when ready. Render cannot deploy uncommitted local files.
2. Sign in to Render with GitHub and authorize only the required repository.
3. Create a **Blueprint** from this repository and select the branch containing [render.yaml](render.yaml).
4. Review the proposed service and currently available free plan/limits. Confirm any account or billing choice yourself; do not enable paid services without checking.
5. Keep the service root at the repository root. The blueprint specifies:
   - Python: `3.12.10`
   - Build: `pip install -r app/requirements.txt`
   - Start: `gunicorn app.app:server --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --access-logfile -`
   - Health check: `/healthz`
6. Deploy, open the assigned HTTPS URL, and check `/healthz` returns `status: "ok"` and the expected snapshot/row count.
7. Test search, Generate Report, charts and CSV download on the public URL and on another device. Add that verified live URL here.

For manual service creation, use the same commands/settings. No API tokens, database, external data downloads or secrets are required at runtime. Gunicorn is the Linux production server; use the local Dash command on Windows. The WSGI export and health endpoint are tested locally; actual Linux/Render startup and second-device live testing remain pending deployment authorization.

If a free service sleeps, the first request may take longer. If deployment fails, inspect the Render logs: confirm the selected branch includes `app/` and `data/clean/integrated_dataset.csv`, use the repository root, and verify Python/dependency versions. Do not bypass data validation or TLS checks to hide errors.

## Collaboration
- Follow the [data contract](docs/data_contract.md), [workflow](docs/WORKFLOW.md) and member-specific notes.
- Record AI assistance/prompts in [docs/prompts.md](docs/prompts.md).
- Never commit raw downloads, secrets, environments or files over 100 MB.
- Keep final notebook outputs and clean CSVs in sync by running the reproduction command before submission.
