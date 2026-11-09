"""Run locally with python -m app.app; deploy with gunicorn app.app:server."""
from datetime import datetime, timezone
import os
from pathlib import Path

from dash import Dash, Input, Output, State, ctx, dcc, html, no_update
from flask import jsonify

from app.charts import report_figures
from app.data import (
    BENCHMARK_NOTE, BOROUGHS, DATA_PATH, HOUSING_METRICS, TRANSPORT_METRICS, YEARS,
    PROFILE_BENCHMARK_NOTE, RQ1_QUESTION,
    Selection, SelectionError, build_report, building_profile_findings, dataset_fingerprint, load_dataset,
    report_csv, selection_from_controls, selection_from_store,
)

GRAPH_CONFIG = {"displaylogo": False, "responsive": True,
                "toImageButtonOptions": {"format": "png", "scale": 2}}


def controls_for(selection):
    return {
        "boroughs": list(selection.boroughs), "years": list(selection.years),
        "housing_metric": selection.housing_metric, "transport_metric": selection.transport_metric,
        "mode": selection.mode, "query": selection.query,
    }


def number(value):
    return "Unknown" if value is None else f"{value:,}"


def graph_card(title, subtitle, figure, graph_id, wide=False, children=None):
    return html.Section([
        html.Div([html.H2(title), html.P(subtitle)], className="chart-heading"),
        dcc.Graph(id=graph_id, figure=figure, config=GRAPH_CONFIG, responsive=True,
                  style={"height": f"{figure.layout.height}px", "width": "100%"}),
        *(children or []),
    ], className="chart-card" + (" chart-wide" if wide else ""))


def render_story(report, profile_finding, profile_surprise, association, concentration_finding):
    coverage = report.coverage
    return html.Section([
        html.Span("THE STORY / EVIDENCE BEFORE ASSUMPTIONS", className="eyebrow"),
        html.H2("Development profiles. Recorded crashes. Better questions."),
        html.P("Read the five-part story, then explore its evidence in the ten research questions. "
               "Every discovery below follows the last generated selection.", className="chart-footnote"),
        html.Div([
            html.Article([
                html.H3("1. The question"),
                html.P(RQ1_QUESTION),
                html.P("Why it matters to New Yorkers: development changes the places where people live and travel. "
                       "Housing and street-safety reviews should be coordinated, but a busy or taller-development "
                       "area should not automatically be labelled more dangerous."),
                html.P("RQ1 asks about injury burden per recorded event, not just whether busy ZIPs have more of everything. "
                       "RQ2, RQ5 and RQ6 separately examine counts, changes and a one-year lag."),
                html.A("Start with the new integrated RQ1", href="#building-profile-chart"),
            ], className="story-step", id="story-question"),
            html.Article([
                html.H3("2. The data"),
                html.P([
                    html.A("DOB NOW Build Job Application Filings (H5)",
                           href="https://data.cityofnewyork.us/Housing-Development/DOB-NOW-Build-Job-Application-Filings/w9ak-ipjd",
                           target="_blank", rel="noopener noreferrer"),
                    " describes applications, reported building profiles and job-cohort units. ",
                    html.A("SIRTA serious/fatal crash records (T4)",
                           href="https://data.cityofnewyork.us/Transportation/Serious-Injury-Response-Tracking-Analysis-Program-/xeqp-qz8h",
                           target="_blank", rel="noopener noreferrer"),
                    " supplies recorded crash and injury outcomes.",
                ]),
                html.P("We aggregate each source to ZIP code x year for 2022-2025 and outer-join the keys, retaining "
                       "unmatched rows. This connects places and years, not individual projects to individual crashes."),
                html.Ul([
                    html.Li("Cleaning: standardize dates, boroughs and five-digit ZIPs; remove duplicate filing IDs; "
                            "deduplicate unit reports by base job across amendments. Unusable identifiers/date/location "
                            "keys are excluded; impossible measurements are quarantined without discarding otherwise usable filings."),
                    html.Li("Location: prefer official building postcode, never the owner's mailing ZIP. Missing building ZIPs "
                            "can use a flagged nearest-crash approximation. Source-mean map points are not ZIP boundaries."),
                    html.Li("Assumptions: housing-only rows have zero retained serious-crash records, not proof of no real crashes. "
                            "Transport-only housing stays unknown. Missing map coordinates exclude points only, not totals or downloads."),
                ]),
                html.P(
                    f"RQ1 uses {coverage['building_profile_rows']:,} paired ZIP-years. It excludes "
                    f"{coverage['unknown_housing_rows']} rows with unknown housing, "
                    f"{coverage['unknown_building_profile_rows']} housing-covered rows without a positive reported profile, and "
                    f"{coverage['zero_crash_profile_rows']} profiled rows with no retained serious-crash record. "
                    "Excluded RQ1 rows remain in the applied dataset and CSV.",
                    id="story-profile-coverage",
                ),
            ], className="story-step", id="story-data"),
            html.Article([
                html.H3("3. The discovery"),
                html.P(profile_finding, id="story-profile-finding"),
                html.P([html.Strong("What challenges the simple story: "), profile_surprise],
                       id="story-profile-surprise"),
                html.P("The RQ1 boxes describe ZIP-year distributions; orange diamonds divide pooled injury counts "
                       "by pooled crash counts. These are different summaries, not two estimates of personal risk."),
                html.P(association),
                html.P(concentration_finding),
                html.Div([
                    html.A("RQ1: profiles and injury burden", href="#building-profile-chart"),
                    html.A("RQ2: raw count association", href="#relationship-chart"),
                    html.A("RQ9: event concentration", href="#concentration-chart"),
                ], className="story-links"),
            ], className="story-step story-wide", id="story-discovery"),
            html.Article([
                html.H3("4. The limits"),
                html.P("Correlation is not causation. We do not observe population, pedestrian/traffic exposure, street "
                       "design or actual construction/work-zone timing. Nothing here estimates a development effect or an individual's risk."),
                html.P("Proposed-story averages describe reported filings, not every building or completed construction. "
                       "Filings include amendments and non-residential work; job-unit totals are incomplete and are not completed homes. "
                       "SIRTA covers serious/fatal crashes, not all collisions."),
                html.P("Missing and approximate ZIPs can bias comparisons. Unequal group sizes, tied quartiles, repeated ZIP-years, "
                       "spatial dependence and four years of data limit inference. Equal medians do not prove equal distributions. "
                       "A zero crash denominator is excluded from RQ1, not treated as zero injury burden."),
            ], className="story-step", id="story-limits"),
            html.Article([
                html.H3("5. The impact"),
                html.Ul([
                    html.Li("DOT and city/housing planners: coordinate development reviews with street-level safety checks. "
                            "Use these charts and the map to frame further investigation, then obtain traffic/pedestrian counts "
                            "and actual construction dates before changing street design or permitting decisions."),
                    html.Li("DOB and data stewards: prioritize missing building profiles, unit pairs and uncertain ZIP assignments "
                            "for verification. RQ8 shows where reporting gaps weaken housing-unit conclusions."),
                    html.Li("Community boards and residents: use the applied CSV and map to request local evidence and field reviews, "
                            "not to label a ZIP safe/unsafe or blame development. Application volume alone is not a danger score."),
                ]),
                html.Div([
                    html.A("Check reporting gaps in RQ8", href="#unit-reporting-chart"),
                    html.A("Locate the evidence on the map", href="#map-chart"),
                ], className="story-links"),
            ], className="story-step", id="story-impact"),
        ], className="story-grid"),
    ], className="story-card", id="story")


def render_report(report, fingerprint):
    selection, totals, coverage = report.selection, report.totals, report.coverage
    figures = report_figures(report)
    selected_boroughs = "All five boroughs" if len(selection.boroughs) == 5 else ", ".join(b.title() for b in selection.boroughs)
    selected_years = ", ".join(str(y) for y in sorted(selection.years))
    scope = f"{selected_boroughs} | {selected_years}"
    if selection.zip_codes:
        scope += " | ZIP " + ", ".join(selection.zip_codes)
    cards = []
    for metric, label in [
        ("filing_count", "Application filings"), ("crash_count", "Serious crashes"),
        ("severe_injuries_total", "Severe injuries"), ("fatalities_total", "Fatalities"),
        ("zip_count", "ZIP codes"),
    ]:
        cards.append(html.Div([
            html.Span(label, className="stat-label"),
            html.Strong(number(totals[metric]), className="stat-value", id=f"total-{metric}"),
            html.Span("Known reports only" if metric == "filing_count" else "In this selection", className="stat-caption"),
        ], className="stat-card"))
    high_share = report.concentration.loc["Q4 / highest", "event_share"]
    concentration_finding = (
        "Event share is undefined: there are no selected events with known housing coverage."
        if high_share != high_share else
        f"The highest housing-activity group contains {high_share:.1%} of selected "
        f"{TRANSPORT_METRICS[selection.transport_metric].lower()} with known housing coverage."
    )
    recurring = int(report.recurrence["joint_years"].ge(2).sum())
    recurrence_finding = (
        "Select at least two years to assess recurrence."
        if len(selection.years) < 2 else
        f"{recurring} ZIPs meet both high-activity thresholds in at least two selected years."
    )
    missing_map = coverage["missing_map_zips"]
    map_note = (
        f"Map omits {len(missing_map)} ZIP(s) without source coordinates: {', '.join(missing_map)}. "
        "Their records remain in other charts and totals."
        if missing_map else "All selected ZIPs have a source map point."
    )
    paired = report.rows.dropna(subset=[selection.housing_metric, selection.transport_metric])
    varied = len(paired) > 1 and paired[selection.housing_metric].nunique() > 1 and paired[selection.transport_metric].nunique() > 1
    association = (
        f"In this selection, the pooled descriptive correlation is {paired[selection.housing_metric].corr(paired[selection.transport_metric]):.2f}."
        if varied else "This selection has too little variation for a meaningful correlation."
    )
    profile_finding, profile_surprise = building_profile_findings(report)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return [
        html.Div([
            html.Div([html.Span("APPLIED REPORT", className="eyebrow"),
                      html.H2(scope, id="applied-scope"),
                      html.P(f"{HOUSING_METRICS[selection.housing_metric]} + {TRANSPORT_METRICS[selection.transport_metric]}",
                             id="applied-metrics")]),
            html.Span(f"{coverage['rows']:,} ZIP-year records", className="pill"),
        ], className="report-heading"),
        html.Div(cards, className="stats-grid"),
        html.Div([
            html.Strong("Read the coverage, not just the counts. "),
            f"{coverage['unknown_housing_rows']} ZIP-year rows have unknown housing coverage; "
            f"{coverage['structural_crash_zeros']} have no retained serious-crash record. "
            f"{coverage['approximate_zip_filings']:,} housing filings use approximate ZIP assignment. "
            "Unknown housing is never replaced with zero.",
        ], className="coverage-note", id="coverage-notice"),
        render_story(report, profile_finding, profile_surprise, association, concentration_finding),
        html.Section([
            html.Div([
                html.Div([html.Span("THE TEAM'S RESEARCH", className="eyebrow"),
                          html.H2("10 research questions")]),
                html.P("Members 1-5 / two questions each. All charts use the applied borough, year and ZIP scope. "
                       "Each question names its measures; fixed-outcome questions keep those measures when dropdowns change."),
            ], className="report-heading"),
            html.Div([
                graph_card("RQ1 / Building profile and injury burden", RQ1_QUESTION,
                           figures["building-profile"], "building-profile-chart", wide=True,
                           children=[
                               html.P(profile_finding, className="finding", id="building-profile-finding"),
                               html.P(profile_surprise, className="finding", id="building-profile-surprise"),
                               html.P("Each box summarizes ZIP-year injury/crash ratios, with individual observations shown. "
                                      "Orange diamonds are ratios of pooled counts, not averages of ZIP ratios. "
                                      "Zero-crash rows cannot define this ratio. Both RQ1 measures stay fixed when metric dropdowns change. "
                                      + PROFILE_BENCHMARK_NOTE, className="chart-footnote"),
                           ]),
                graph_card("RQ2 / Housing and transportation",
                           "Are ZIP-years with more housing activity also those with more recorded transportation events?",
                           figures["relationship"], "relationship-chart",
                           children=[html.P(association, className="finding"),
                                     html.P("One point per ZIP-year. Defaults reproduce the filing/serious-crash question. "
                                            "Repeated ZIP-years are not independent; association is not causation.",
                                            className="chart-footnote")]),
                graph_card("RQ3 / Fatal-crash share",
                           "Does the percentage of fatal crashes differ across housing-activity groups?",
                           figures["fatal-share"], "fatal-share-chart",
                           children=[html.P("Sum of fatal crashes / sum of recorded serious crashes, not fatalities per crash "
                                            "or an average of ZIP percentages. The outcome stays fixed regardless of the transportation dropdown. "
                                            f"{coverage['unknown_fatal_status_rows']} housing-covered ZIP-year rows with unknown fatal-crash status "
                                            "are excluded from both numerator and denominator. Zero-crash shares are undefined. "
                                            "This is event severity, not individual risk. " + BENCHMARK_NOTE,
                                            className="chart-footnote")]),
                graph_card("RQ4 / Nighttime crashes",
                           "Does the observed nighttime crash share differ across housing-activity groups within each borough?",
                           figures["nighttime"], "nighttime-chart",
                           children=[html.P("Nighttime = 00:00-05:59 and 22:00-23:59. Shares use summed nighttime crashes / "
                                            "summed known-time crashes, never averages of ZIP percentages. "
                                            "Blank cells have no usable denominator. " + BENCHMARK_NOTE,
                                            className="chart-footnote")]),
                graph_card("RQ5 / Changes within ZIPs",
                           "Did ZIPs whose housing activity grew most also see a larger change in recorded transportation events?",
                           figures["changes"], "changes-chart",
                           children=[html.P("Last minus first selected year, using known housing at both endpoints. "
                                            "ZIPs never present in the full snapshot's crash source are excluded. "
                                            "Defaults compare filings and serious crashes in 2022 and 2025.",
                                            className="chart-footnote")]),
                graph_card("RQ6 / A one-year lag",
                           "Is a ZIP's housing activity in one year associated with its recorded transportation events in the following year?",
                           figures["lagged"], "lagged-chart",
                           children=[html.P("Only exact consecutive-year pairs inside the applied selection are used, in crash-source ZIPs. "
                                            "The second view subtracts each ZIP's own paired-year mean; a single pair gives zero deviations. "
                                            "These descriptive comparisons cannot establish causation.",
                                            className="chart-footnote")]),
                graph_card("RQ7 / Development mix",
                           "Do high-crash areas have a different mix of new-building versus other application filings?",
                           figures["development-mix"], "development-mix-chart",
                           children=[html.P("New-building filings / all application filings in each crash-volume group; "
                                            "other filings are the remainder, not necessarily renovations or residential work. "
                                            "High crash volume is positive and at/above the annual NYC-wide 75th percentile among housing-covered ZIPs, "
                                            "computed before filters with ties retained. Both measures stay fixed regardless of the metric dropdowns. "
                                            "Zero-filing shares remain undefined.",
                                            className="chart-footnote")]),
                graph_card("RQ8 / Unit-reporting gaps",
                           "Where is reported housing-unit information most incomplete across boroughs and cohort years?",
                           figures["unit-reporting"], "unit-reporting-chart",
                           children=[html.P("First-observed jobs missing a complete existing/proposed unit pair / all first-observed jobs, "
                                            "weighted by job counts rather than ZIP percentages. A zero-job cohort has no defined share. "
                                            "Metric dropdowns do not change this reporting-quality question. "
                                            "Missing reports limit unit-change conclusions; they are not zero units.",
                                            className="chart-footnote")]),
                graph_card("RQ9 / Concentration",
                           "How much of the selected transportation activity falls in the highest housing-activity group?",
                           figures["concentration"], "concentration-chart",
                           children=[html.P(concentration_finding, className="finding", id="concentration-finding"),
                                     html.P(BENCHMARK_NOTE, className="chart-footnote")]),
                graph_card("RQ10 / Recurring high activity",
                           "Which ZIPs repeatedly meet both citywide annual high-activity thresholds?",
                           figures["recurrence"], "recurrence-chart",
                           children=[html.P(recurrence_finding, className="finding", id="recurrence-finding"),
                                     html.P("Up to 20 ZIPs, ordered by high-activity years, then housing total and ZIP. "
                                            "Pale = not both high; blank = unknown/no row. " + BENCHMARK_NOTE,
                                            className="chart-footnote")]),
            ], className="charts-grid"),
        ], id="research-questions"),
        html.Div([html.H2("Explore the context")], className="report-heading"),
        html.Div([
            graph_card("The changing city", "Independent count axes, aligned years. Missing housing totals stay unknown.",
                       figures["trend"], "trend-chart"),
            graph_card("Put the selection on the map", "One descriptive source-mean point per ZIP, not a ZIP boundary. Size = transportation; color = housing.",
                       figures["map"], "map-chart",
                       children=[html.P(map_note, className="chart-footnote", id="map-coverage"),
                                 html.P("Basemap: CARTO / OpenStreetMap. Public map tiles require internet. "
                                        "A small minimum marker keeps zero-count ZIPs visible; gray means housing unknown.",
                                        className="chart-footnote")]),
        ], className="charts-grid"),
        html.Footer([
            html.Span(f"Source snapshot {fingerprint} | Generated {generated}"),
            html.Span("2022-2025 complete years / Recorded events, not individual risk"),
        ], className="report-footer"),
    ]


def filter_control(label, component, name):
    return html.Div([
        html.Label(label, id=f"{name}-label", htmlFor=name),
        component,
    ], className="field", role="group", **{"aria-labelledby": f"{name}-label"})


def create_app(data_path=DATA_PATH):
    frame = load_dataset(data_path)
    fingerprint = dataset_fingerprint(data_path)
    dashboard = Dash(
        __name__, title="NYC / Housing + Street Safety",
        assets_folder=str(Path(__file__).parent / "assets"),
        update_title="Generating report...",
    )
    dashboard.server.config["MAX_CONTENT_LENGTH"] = 1_000_000
    initial = build_report(frame, Selection())

    def layout():
        return html.Div([
            dcc.Store(id="applied-selection", data=initial.selection.to_dict(), storage_type="memory"),
            dcc.Download(id="report-download"),
            html.A("Skip to report", href="#report-panel", className="skip-link"),
            html.Header([
                html.A([html.Span("NYC", className="brand-mark"), html.Span("CITY / SIGNAL", className="brand-name")],
                       href="#top", className="brand"),
                html.Div([html.A("Explore", href="#report-panel"),
                          html.A("Research questions", href="#research-questions"), html.A("The story", href="#story"),
                          html.Span("2022 - 2025", className="period-tag")], className="nav-links"),
            ], className="topbar", id="top"),
            html.Section([
                html.Div([
                    html.Span("HOUSING + TRANSPORTATION / NYC OPEN DATA", className="eyebrow"),
                    html.H1(["A city in motion.", html.Br(), html.Span("A city being built.", className="hero-accent")]),
                    html.P("Explore where development applications and serious road crashes overlap. "
                           "Find patterns, ask better questions, and keep the limitations in view."),
                ]),
                html.Div([
                    html.Span("THE QUESTION", className="eyebrow"),
                    html.P("How do development profiles and serious road-crash outcomes overlap across NYC ZIP codes?"),
                    html.Div([html.Span("2 public datasets"), html.Span("4 complete years"),
                              html.Span(f"{frame['zip_code'].nunique()} ZIP codes")], className="hero-facts"),
                ], className="question-card"),
            ], className="hero"),
            html.Div([
                html.Aside([
                    html.Div([html.Span("01", className="section-number"), html.H2("Shape your report")], className="sidebar-heading"),
                    html.P("Choose your scope, then generate. Charts do not change until you apply your selections.", className="muted"),
                    html.Fieldset([
                        html.Legend("Selection mode"),
                        dcc.RadioItems(id="selection-mode", options=[
                            {"label": " Dropdowns", "value": "filters"}, {"label": " Search", "value": "search"}],
                            value="filters", className="mode-options"),
                    ]),
                    filter_control("Borough", dcc.Dropdown(
                        id="borough-filter", options=[{"label": b.title(), "value": b} for b in BOROUGHS],
                        value=list(BOROUGHS), multi=True, clearable=True), "borough-filter"),
                    filter_control("Year", dcc.Dropdown(
                        id="year-filter", options=[{"label": str(y), "value": y} for y in YEARS],
                        value=list(YEARS), multi=True, clearable=True), "year-filter"),
                    filter_control("Housing measure", dcc.Dropdown(
                        id="housing-filter", options=[{"label": label, "value": key} for key, label in HOUSING_METRICS.items()],
                        value="filing_count", clearable=False, searchable=False), "housing-filter"),
                    filter_control("Transportation measure", dcc.Dropdown(
                        id="transport-filter", options=[{"label": label, "value": key} for key, label in TRANSPORT_METRICS.items()],
                        value="crash_count", clearable=False, searchable=False), "transport-filter"),
                    filter_control("ZIP or supported phrase", dcc.Input(
                        id="search-query", value="", type="text", debounce=False,
                        placeholder="Brooklyn 2024 new buildings", maxLength=160,
                        disabled=True, className="search-input"), "search-query"),
                    html.P("Search examples: 11201; Queens 2023; Brooklyn 2024 new buildings; "
                           "Manhattan 2025 fatalities. Named fields override dropdowns; other fields stay selected.",
                           className="search-help"),
                    html.Button("Generate Report", id="generate-button", n_clicks=0, className="button button-primary"),
                    html.Button("Reset all", id="reset-button", n_clicks=0, className="button button-secondary"),
                    html.Div(id="pending-notice", className="pending-notice", role="status", **{"aria-live": "polite"}),
                    html.Div(id="form-errors", className="form-errors", role="alert"),
                    html.Hr(),
                    html.Button("Download report CSV", id="download-button", n_clicks=0, className="button button-download"),
                    html.P("Downloads the last generated selection, including coverage and benchmark flags.", className="search-help"),
                    html.Div(id="download-error", className="form-errors", role="alert"),
                    html.Div([
                        html.Strong("A note on the data"),
                        html.P("Applications are not completed homes. Crash counts are not personal-risk estimates."),
                        html.A("Housing source", href="https://data.cityofnewyork.us/resource/w9ak-ipjd", target="_blank", rel="noopener noreferrer"),
                        html.Span(" / "),
                        html.A("SIRTA source", href="https://data.cityofnewyork.us/resource/xeqp-qz8h", target="_blank", rel="noopener noreferrer"),
                    ], className="sidebar-note"),
                ], className="sidebar"),
                html.Main([
                    dcc.Loading(
                        html.Div(id="report-panel", children=render_report(initial, fingerprint), tabIndex=-1),
                        type="circle", color="#187a73",
                    ),
                ], className="report-main"),
            ], className="workspace"),
        ], className="page")

    dashboard.layout = layout

    @dashboard.server.get("/healthz")
    def health():
        return jsonify(status="ok", rows=len(frame), snapshot=fingerprint)

    @dashboard.callback(
        Output("report-panel", "children"), Output("applied-selection", "data"),
        Output("form-errors", "children"), Output("download-button", "disabled"),
        Output("borough-filter", "value"), Output("year-filter", "value"),
        Output("housing-filter", "value"), Output("transport-filter", "value"),
        Output("selection-mode", "value"), Output("search-query", "value"),
        Input("generate-button", "n_clicks"), Input("reset-button", "n_clicks"),
        State("borough-filter", "value"), State("year-filter", "value"),
        State("housing-filter", "value"), State("transport-filter", "value"),
        State("selection-mode", "value"), State("search-query", "value"),
        prevent_initial_call=True,
    )
    def apply_report(_generate, _reset, boroughs, years, housing, transport, mode, query):
        try:
            selection = Selection() if ctx.triggered_id == "reset-button" else selection_from_controls(
                frame, boroughs, years, housing, transport, mode, query,
            )
            report = build_report(frame, selection)
        except SelectionError as error:
            return (html.Div([html.H2("No active report"), html.P(str(error))], className="empty-report"),
                    None, str(error), True, *([no_update] * 6))
        controls = controls_for(selection)
        return (
            render_report(report, fingerprint), selection.to_dict(), "", False,
            controls["boroughs"], controls["years"], controls["housing_metric"],
            controls["transport_metric"], controls["mode"], controls["query"],
        )

    @dashboard.callback(
        Output("pending-notice", "children"), Output("search-query", "disabled"),
        Input("borough-filter", "value"), Input("year-filter", "value"),
        Input("housing-filter", "value"), Input("transport-filter", "value"),
        Input("selection-mode", "value"), Input("search-query", "value"),
        Input("applied-selection", "data"),
    )
    def pending(boroughs, years, housing, transport, mode, query, payload):
        controls = {"boroughs": boroughs, "years": years, "housing_metric": housing,
                    "transport_metric": transport, "mode": mode, "query": (query or "").strip()}
        applied = None if payload is None else {k: payload[k] for k in controls}
        message = "No active report. Correct the selection and generate again." if payload is None else (
            "Unapplied changes - click Generate Report." if controls != applied else "Selections applied."
        )
        return message, mode != "search"

    @dashboard.callback(
        Output("report-download", "data"), Output("download-error", "children"),
        Input("download-button", "n_clicks"), Input("applied-selection", "data"),
        prevent_initial_call=True,
    )
    def download(_clicks, payload):
        if ctx.triggered_id != "download-button":
            return no_update, ""
        try:
            selection = selection_from_store(payload, frame)
            report = build_report(frame, selection)
        except SelectionError as error:
            return no_update, str(error)
        return dcc.send_string(report_csv(report), "nyc_housing_transport_report.csv"), ""

    return dashboard


app = create_app()
server = app.server

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8050")), debug=False)
