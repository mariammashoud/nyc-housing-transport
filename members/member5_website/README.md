# Member 5 - Website and deployment

## Deliverables
- [Dash application](../../app/app.py), shared [data/research logic](../../app/data.py), [Plotly charts](../../app/charts.py), and responsive [CSS](../../app/assets/style.css).
- [Member5_Website_Research.ipynb](../../notebooks/Member5_Website_Research.ipynb): two executed research questions/charts with calculated findings and limitations.
- [Render blueprint](../../render.yaml) and minimal [web dependencies](../../app/requirements.txt).
- [Tests](../../tests/test_dashboard.py), [setup/deployment guide](../../README.md), and [prompt log](../../docs/prompts.md).

## Implemented
- [x] Multiple dropdowns: boroughs, years, housing and transportation measures.
- [x] Dropdown/search modes, with supported ZIP/borough/year/measure phrases and explicit invalid-input feedback.
- [x] Generate Report updates all ten research charts plus the two context charts, cards, findings and coverage notices together.
- [x] Unapplied-selection notice; reset restores the default report.
- [x] CSV download uses only the last applied selection and preserves missing values/source/benchmark flags.
- [x] Scatter, grouped bars, aligned lines, heatmap and map; hover/zoom and PNG chart export.
- [x] Housing/transportation relationship chart and a clear story/limitations/NYC relevance section.
- [x] Responsive desktop/mobile layout, keyboard focus styles, labels and live status/error notices.
- [x] Tests for business logic, exact thresholds, missingness, state isolation, Dash HTTP callbacks and downloads.
- [x] All ten team research questions displayed as RQ1-RQ10; Member 5's two visualizations are shared between notebook and website.
- [x] Render configuration, dependency pins, README instructions, contribution and AI prompt documentation.
- [ ] Public Render deployment (requires user's GitHub/Render authorization and pushed code).
- [ ] Test the public HTTPS link on another device and add the verified URL to the README.

## Run locally (repository root)
```powershell
.\.venv\Scripts\python.exe -m pip install -r app\requirements.txt
.\.venv\Scripts\python.exe -m app.app
```
Open http://127.0.0.1:8050/. Stop with `Ctrl+C`. Use Python 3.12; no raw downloads or notebook execution are required to run the web app.

## Research questions
The website displays Members 1-4's eight questions first: reported job-cohort unit change, housing/transportation association, fatal-crash percentage, nighttime shares, within-ZIP endpoint changes, one-year-lag comparisons, development mix and unit-reporting gaps. The three replacements (RQ3/RQ7/RQ8) use distinct outcomes and denominators, with matching regenerated notebook questions and outputs. See the [complete question list and filtering rules](../../README.md#ten-research-questions).

Member 5 adds:

9. What share of recorded serious crashes falls in the highest-filing activity group? Grouped bars compare event share with the share of selected housing-covered ZIP-years.
10. Which ZIPs repeatedly meet both high-filing and high-crash thresholds? A ZIP/year heatmap shows recurring co-occurrence.

Thresholds are positive values at/above the annual NYC-wide 75th percentile, computed before user filters. Ties are retained, so "high" need not mean exactly 25%. Unknown housing is excluded only from paired-domain research, not erased from dashboard totals/downloads. A recurring ZIP is jointly high in at least two selected years. Metric dropdowns generalize the same comparisons to other supported event counts.

## Coverage and deployment cautions
Applications are not completed homes; crashes are serious/fatal SIRTA records, not all collisions or individual risk. Preserve unknowns and source flags. Coordinate-less ZIPs remain in non-map outputs; basemap tiles require internet. Do not infer causation from co-occurrence.

Render's Linux/Gunicorn production startup and public second-device checks must be verified after authorized deployment. No credentials should be added to code or prompts. No commit/push/deployment is performed automatically.
