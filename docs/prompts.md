# Prompts used

Every prompt used in the project (AI or otherwise) is listed here, per member, with the step it supported.

## Member 2 - Transportation dataset (SIRTA, T4)
An AI assistant (Claude) was used to help write and debug the code in this section; the results were run and reviewed by the author.

- Which transportation dataset from the catalog should I choose, and do I pick only one? (chose T4 / SIRTA, ID `xeqp-qz8h`)
- How do I download the SIRTA dataset? (shared the data dictionary and the CSV)
- Build the notebook for the T4 dataset covering all project requirements: dataset overview, EDA, pre-integration cleaning (missing values, duplicates, inconsistencies, formats, outliers), validation, ZIP x year aggregation, and 2 research questions.
- Fix this error from the API download: `KeyError: No column contains ('collision',)`.

## Member 1 - Housing dataset
Original housing notebook prompt summaries (historical; implementation/claims have since been corrected):
- Construct a Socrata SoQL query for `w9ak-ipjd.csv` filtering 2022-2025 and selecting building, unit, cost, coordinate and sparse energy columns.
- Audit the owner `zip` against borough and integrate `assign_building_zip` using Member 2's row-level crashes.
- Design an outlier strategy that removes impossible entry errors while retaining plausible high-rise developments.
- Propose two cross-domain questions and visualizations joining the housing and transportation aggregates.

The correction work below was requested by Member 5; do not attribute new prompts or approval to Member 1.

The following teammate-supplied log describes the earlier implementation and its snapshot, not the current corrected methodology or regenerated results. Its log-scale IQR improvement is retained; official-postcode priority, measure quarantine and window-cohort accounting follow the current data contract.

### Member 1's additional original-development log from the latest team update (DOB NOW: Build – Job Application Filings, H5)
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
- Check Pierre's correction PRs and finish my integration fixes now that Member 1's work is merged: update the notebook text to the regenerated data, remove the old provisional wording, and keep ZIP codes that never appear in the crash file out of the research questions. (checked against the live API that H5 does have a building postcode; replaced stale hard-coded counts and placeholder markdown; 37 mostly single-building ZIPs excluded from the RQs only; RQ1 r = -0.07 over 183 ZIPs; RQ2 between-ZIP rho = 0.61, within-ZIP r = 0.06; integrated CSV unchanged; synced the same cells into the Member 4 notebook)

## Member 4 - Analysis, storytelling, final notebook
**Scope:** consolidate the analytical workflow, develop cross-domain research questions, and communicate findings responsibly.

**Attribution:** the final notebook was assembled with AI assistance during the cross-member correction pass documented below. The briefs below professionally restate that documented scope; they are not verbatim historical prompts or evidence of separate Member 4 authorization. Individual Member 4 approval and contribution name remain unconfirmed.

### Professional prompt briefs
1. **Consolidate the reproducible workflow.** Assemble a final Jupyter notebook that runs from top to bottom and presents data acquisition, source-specific cleaning, ZIP-year aggregation, integration, and analysis in dependency order. Reuse the established helpers and data contract, retain source links and original contribution credits, and preserve Member 3's ownership of the integrated CSV.

2. **Compare borough-level activity and crash shares.** Examine how each borough's share of housing application filings compares with its share of recorded serious crashes. Produce a clearly labelled comparison chart, calculate findings from the current data, and explain why differences in these shares do not establish individual risk or a causal construction effect.

3. **Evaluate comparable trends over time.** Compare indexed housing-filing and serious-crash trends over 2022-2025 using a consistently housing-covered ZIP panel and a 2022 baseline of 100. Explain the panel-selection rule and excluded coverage, preserve unknown values, and interpret the indexed series as relative change rather than equivalent event volumes.

4. **Develop an evidence-based narrative.** Synthesize the research findings into a coherent account of housing application activity and street safety in NYC. Distinguish application filings and reported job-cohort units from completed homes, and SIRTA serious-crash records from all collisions. Discuss missing unit reports, approximate ZIP assignment, exposure differences, and the limits of observational associations.

5. **Validate and prepare the website handoff.** Execute the consolidated notebook, confirm key uniqueness and reconciliation of source totals, and replace stale or hard-coded findings with calculated interpretations. Prepare concise findings, limitations, and responsible NYC relevance statements for Member 5's dashboard without implying that original contributors have approved the correction pass.

**Documented outcome:** the final notebook consolidates the preparation and integration pipeline, includes Members 1-3's research questions and Member 4's two additional analyses, and provides a findings-and-limitations handoff for the website. Contributor review remains required before submission.

## Member 5 - Website and deployment
**Scope:** implement an interactive, coverage-aware dashboard, two additional research analyses, and deployment preparation.

**Attribution:** an AI assistant using Copilot SDK in VS Code assisted after the user approved the implementation scope. The briefs below are professionally edited summaries of the recorded planning, technology, environment, deployment, and branch requests and their approved implementation scope; they are not verbatim quotations or additional authorization. Original team members should review the result before submission.

### Professional prompt briefs
1. **Define the implementation plan before development.** Review the integrated dataset and Member 4's analytical handoff, then propose the dashboard structure, supported filters, five chart types, CSV export, two additional research questions, validation strategy, and deployment prerequisites. Explain the deliverables and implementation sequence before making changes.

2. **Select and explain the development stack.** Use Python, Dash, Plotly, Pandas, CSS, and unittest, with Gunicorn and Render for the proposed production setup. Explain the role of each component and why a database or separate JavaScript application is unnecessary for this CSV-backed project. Use local VS Code/Jupyter development, distinguish optional Colab notebook use from web hosting, and provide reproducible setup instructions.

3. **Implement consistent report interactions.** Provide borough, year, housing-measure, and transportation-measure dropdowns alongside validated search. Apply changes only when Generate Report is selected, keep charts, summary cards, findings, and downloads aligned with the last applied selection, and provide clear pending-selection, reset, and invalid-input feedback. Keep report state isolated between user sessions.

4. **Present accessible, coverage-aware visualizations.** Implement scatter, grouped-bar, aligned-line, heatmap, and map views with informative labels, hover details, zoom, and PNG export. Support responsive layouts and keyboard interaction. Read the integrated CSV without modifying it; preserve unknown housing values and undefined ratios, disclose missing map coordinates, and retain those records in non-map outputs and downloads.

5. **Develop two reproducible cross-domain analyses.** Examine the share of recorded serious crashes associated with high-filing ZIP-years and identify ZIPs repeatedly meeting both high-filing and high-crash thresholds. Share calculations between the dashboard and research notebook. Define high activity as positive values at or above the annual NYC-wide 75th percentile before user filters, retain ties, and define recurrence as joint high activity in at least two selected years. Report coverage and interpret co-occurrence without causal claims.

6. **Validate the application and document its boundaries.** Test filtering, search validation, applied-report state, exact benchmark thresholds, missingness, session isolation, HTTP callbacks, and CSV downloads. Execute the research notebook and verify that findings use the same calculations as the dashboard. Document data limitations, dependency requirements, startup instructions, and the distinction between local verification and production verification.

7. **Prepare deployment within the approved scope.** Implement the approved local work on the requested branch derived from the previous branch; the recorded implementation used `feat/member-5-dashboard` based on `fix/member-4`. Prepare the Render configuration and deployment guide, but do not treat preparation as a completed public deployment. Obtain explicit authorization for account access, billing decisions, publishing, and any commit or push not separately requested; never request passwords or place credentials in code or prompts.

**Documented outcome:** the approved local implementation includes validated search, applied-report state, four dropdowns, five Plotly chart types, coverage-aware summaries, per-session CSV export, responsive styling, shared annual benchmarks, two executed research charts, regression and HTTP tests, minimal web dependencies, and Render configuration. Search and filter errors remain visible; unknown housing and undefined ratios are not represented as zero. Benchmark ties and map omissions are disclosed. No automatic commit, push, or public deployment was included in the original implementation request. Public deployment and second-device live checks remain pending authorization.

## Cross-member correction pass requested by Member 5
An AI assistant using Copilot SDK in VS Code assisted with this work. The original contributors should review the changes before submission. No claim is made that they authored or approved this correction pass.

- "review what members have been finished their part and tell me what to do i am member 5" - inspected saved notebooks, data schemas, coverage and incomplete placeholders.
- "can you fix every member part then tell me what you exactly did as i dont understand anything" - requested completion and a plain-language explanation.
- Scope clarification: **"Fix Members 1-4 only; leave my website for later."**
- Housing methodology clarification: **"Use official building ZIPs, with flagged coordinate fallback when missing (recommended)."**

Implementation supported by those requests:
- Verified live source schemas; corrected the earlier claim that H5 lacks building postcode/job type; retained owner-ZIP exclusion.
- Corrected job-unit duplication, missing-as-zero assumptions, implausible unit handling, source download failures and integrated-file overwrite.
- Replaced Member 2's research placeholders, fixed shared paths and nighttime denominators, and calculated actual interpretations.
- Regenerated integration with dynamic key/total checks and honest exploratory interpretation; no causal claims or independent-observation inference from repeated ZIP-years.
- Assembled Member 4's final pipeline, added two questions/charts and a website-ready findings/limitations/impact handoff.
- Added regression tests and an ordered notebook runner; updated related documentation. Website/deployment intentionally left untouched.


## Reconciliation before publishing branches
- The user requested stacked branches for Members 1-3 and Member 4, and approved reconciling newer remote changes before pushing.
- Latest teammate changes corrected Member 1's name to Mostafa, refined housing outlier flags using log-scale IQR, removed integrated-file overwriting, updated source TLS handling, and recorded additional original-development prompts.
- Preserved Mostafa's name and prompt history and incorporated log-scale IQR. Retained the validated operating-system TLS solution and sole Member 3 integrated export.
- Regenerated outputs with the reconciled flag calculation. The current documented window-cohort unit accounting and measure quarantine differ from the teammate's earlier initial-filing-only/whole-row-removal approach; the original prompt history is retained for transparent review.

## Member 1 EDA enhancement
- "Without altering the code yet compare the current implementation of Member1's notebook to the proposed member1 final notebook. Which one has a better implementation and EDA." - compared source, outputs, data definitions and read-only execution.
- "implement your recomendation in a new branch" - retain the tested export policy, adopt richer EDA and reporting-coverage charts, and expose proposed plausibility exclusions as non-mutating sensitivity scenarios rather than new cleaning rules.
- Correct missing-value domain counts, avoid arbitrary tie-breaking in unit-change groups, show group sample sizes, and omit independent-observation confidence bands for repeated ZIP-years. Regenerate and validate the notebook without changing the existing housing exports.
