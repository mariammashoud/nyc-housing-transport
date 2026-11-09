from dataclasses import replace
import io
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd
import nbformat

from app.charts import report_figures
from app.data import (
    BOROUGHS, HOUSING_METRICS, TRANSPORT_METRICS, YEARS, Selection, SelectionError,
    annual_benchmarks, build_report, load_dataset, report_csv, selection_from_controls,
    selection_from_store,
)

RESEARCH_GRAPHS = [
    "net-units", "relationship", "fatal-share", "nighttime", "changes",
    "lagged", "development-mix", "unit-reporting", "concentration", "recurrence",
]


def component_nodes(node):
    if isinstance(node, dict):
        if "type" in node and "props" in node:
            yield node
        for value in node.values():
            yield from component_nodes(value)
    elif isinstance(node, list):
        for item in node:
            yield from component_nodes(item)


class DashboardDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frame = load_dataset()

    def controls(self, **changes):
        defaults = dict(boroughs=list(BOROUGHS), years=list(YEARS), housing_metric="filing_count",
                        transport_metric="crash_count", mode="filters", query="")
        return selection_from_controls(self.frame, **(defaults | changes))

    def research_rows(self):
        frame = self.frame[self.frame["has_housing_data"]].drop_duplicates("zip_code").head(4).copy()
        frame["year"] = 2022
        frame["borough"] = "BRONX"
        frame["filing_count"] = 100
        frame["new_construction_filings"] = [10, 20, 30, 80]
        frame["crash_count"] = [1, 9, 10, 20]
        frame["fatal_crash_count"] = [1, 0, 1, 2]
        frame["unique_job_count"] = [1, 9, 10, 20]
        frame["jobs_with_known_units"] = [0, 9, 0, 20]
        return frame

    def test_default_totals_reconcile_with_source(self):
        report = build_report(self.frame, Selection())
        self.assertEqual(len(report.rows), len(self.frame))
        self.assertEqual(report.totals["filing_count"], int(self.frame["filing_count"].sum()))
        self.assertEqual(report.totals["crash_count"], int(self.frame["crash_count"].sum()))
        self.assertEqual(report.totals["zip_count"], self.frame["zip_code"].nunique())

    def test_reports_do_not_mutate_shared_source_or_each_other(self):
        source = self.frame.copy(deep=True)
        first = build_report(self.frame, self.controls(boroughs=["BRONX"]))
        second = build_report(self.frame, self.controls(boroughs=["QUEENS"]))
        first.rows.loc[:, "crash_count"] = 0
        pd.testing.assert_frame_equal(self.frame, source)
        self.assertEqual(second.totals["crash_count"], source.loc[source["borough"] == "QUEENS", "crash_count"].sum())

    def test_multiple_borough_and_year_filters(self):
        report = build_report(self.frame, self.controls(boroughs=["BRONX", "QUEENS"], years=[2023, 2025]))
        expected = self.frame[self.frame["borough"].isin(["BRONX", "QUEENS"]) & self.frame["year"].isin([2023, 2025])]
        self.assertEqual(len(report.rows), len(expected))
        self.assertEqual(report.totals["crash_count"], expected["crash_count"].sum())

    def test_zip_and_supported_phrase_searches(self):
        for query, boroughs, years, housing in [
            ("Brooklyn 2024 new buildings", ("BROOKLYN",), (2024,), "new_construction_filings"),
            ("Staten-Island 2023 permits", ("STATEN ISLAND",), (2023,), "permit_issued_count"),
            ("The Bronx and Queens 2022", ("BRONX", "QUEENS"), (2022,), "filing_count"),
        ]:
            with self.subTest(query=query):
                selection = self.controls(mode="search", query=query)
                self.assertEqual(selection.boroughs, boroughs)
                self.assertEqual(selection.years, years)
                self.assertEqual(selection.housing_metric, housing)
        report = build_report(self.frame, self.controls(mode="search", query="11201 2024"))
        self.assertEqual(set(report.rows["zip_code"]), {"11201"})
        self.assertEqual(set(report.rows["year"]), {2024})
        self.assertEqual(self.controls(mode="search", query="Manhattan 2025 fatalities").transport_metric, "fatalities_total")

    def test_search_overrides_named_fields_and_keeps_other_controls(self):
        selection = self.controls(mode="search", query="Brooklyn 2024", boroughs=[], years=[])
        self.assertEqual(selection.boroughs, ("BROOKLYN",))
        self.assertEqual(selection.years, (2024,))
        selection = self.controls(mode="search", query="11201", boroughs=["BROOKLYN"], years=[2025])
        self.assertEqual(selection.years, (2025,))

    def test_invalid_queries_and_empty_filters_fail_explicitly(self):
        for query in ["", "and", "Brooklyn bananas", "2026", "00000", "crashes fatalities", "x" * 161]:
            with self.subTest(query=query), self.assertRaises(SelectionError):
                self.controls(mode="search", query=query)
        for fields in [dict(boroughs=[]), dict(years=[]), dict(years=[True]), dict(years=[2024, 2024]),
                       dict(housing_metric="net_new_units"), dict(mode="anything")]:
            with self.subTest(fields=fields), self.assertRaises(SelectionError):
                self.controls(**fields)

    def test_valid_but_empty_combination_has_no_success_shaped_report(self):
        selection = self.controls(mode="search", query="Brooklyn 10001")
        with self.assertRaisesRegex(SelectionError, "No records"):
            build_report(self.frame, selection)

    def test_unknown_housing_is_not_zero_and_still_has_transport_totals(self):
        selection = self.controls(mode="search", query="10111 2022")
        report = build_report(self.frame, selection)
        self.assertIsNone(report.totals["filing_count"])
        self.assertEqual(report.coverage["unknown_housing_rows"], 1)
        self.assertEqual(report.coverage["known_housing_rows"], 0)
        self.assertTrue(report.rows["filing_count"].isna().all())
        self.assertTrue(report.recurrence.empty)
        self.assertIsNotNone(report.totals["crash_count"])
        self.assertEqual(len(report_figures(report)), 12)

    def test_citywide_thresholds_do_not_change_after_filters(self):
        full = build_report(self.frame, Selection())
        local = build_report(self.frame, self.controls(boroughs=["BROOKLYN"], years=[2024]))
        keys = ["zip_code", "year"]
        expected = full.rows.set_index(keys).loc[local.rows.set_index(keys).index]
        for column in ["housing_quartile", "housing_high", "transport_high", "joint_high", "crash_high"]:
            pd.testing.assert_series_equal(local.rows.set_index(keys)[column], expected[column])

    def test_exact_75th_percentile_threshold_and_zero_ties(self):
        small = self.frame[self.frame["has_housing_data"]].head(4).copy()
        small["year"] = 2022
        small["filing_count"] = [1, 2, 3, 3]
        small["crash_count"] = [0, 0, 0, 0]
        rows = annual_benchmarks(small, "filing_count", "crash_count")
        self.assertEqual(rows["housing_high"].tolist(), [False, False, True, True])
        self.assertEqual(rows["housing_quartile"].eq("Q4 / highest").sum(), 2)
        self.assertFalse(rows["transport_high"].any())
        self.assertFalse(rows["joint_high"].any())

    def test_concentration_denominators_exclude_unknown_housing_only(self):
        report = build_report(self.frame, Selection())
        known = report.rows[report.rows["has_housing_data"]]
        self.assertEqual(report.concentration["zip_years"].sum(), len(known))
        self.assertEqual(report.concentration["transport_events"].sum(), known["crash_count"].sum())
        self.assertAlmostEqual(report.concentration["event_share"].sum(), 1)
        self.assertAlmostEqual(report.concentration["record_share"].sum(), 1)

    def test_zero_event_denominator_stays_undefined(self):
        frame = self.frame.copy()
        frame["fatalities_total"] = 0
        report = build_report(frame, replace(Selection(), transport_metric="fatalities_total"))
        self.assertTrue(report.concentration["event_share"].isna().all())
        self.assertEqual(report.totals["fatalities_total"], 0)
        self.assertFalse(report.rows["transport_high"].any())

    def test_recurrence_matches_flags_and_never_exceeds_observed_years(self):
        report = build_report(self.frame, Selection())
        counts = report.rows.groupby("zip_code")["joint_high"].sum()
        for row in report.recurrence.itertuples():
            self.assertEqual(row.joint_years, counts.loc[row.zip_code])
            self.assertLessEqual(row.joint_years, row.observed_years)

    def test_map_omission_does_not_remove_records_from_export_or_totals(self):
        report = build_report(self.frame, self.controls(mode="search", query="10044"))
        self.assertEqual(report.coverage["missing_map_zips"], ["10044"])
        exported = pd.read_csv(io.StringIO(report_csv(report)), dtype={"zip_code": str})
        self.assertEqual(len(exported), len(report.rows))
        self.assertEqual(set(exported["zip_code"]), {"10044"})
        self.assertGreater(report.totals["filing_count"], 0)
        self.assertFalse(report_figures(report)["map"].data)

    def test_all_nine_measure_combinations_produce_valid_figures(self):
        for housing in HOUSING_METRICS:
            for transport in TRANSPORT_METRICS:
                report = build_report(self.frame, replace(Selection(), housing_metric=housing, transport_metric=transport))
                figures = report_figures(report)
                self.assertEqual(set(figures), {*RESEARCH_GRAPHS, "trend", "map"})
                for figure in figures.values():
                    self.assertTrue(figure.to_json())

    def test_unit_heatmap_preserves_signed_changes_and_unknowns(self):
        frame = self.frame[self.frame["has_housing_data"]].drop_duplicates("zip_code").head(2).copy()
        frame["year"] = 2022
        frame["borough"] = "BRONX"
        frame["net_new_units"] = [-12, np.nan]
        figure = report_figures(build_report(frame, replace(
            Selection(), boroughs=("BRONX",), years=(2022,),
        )))["net-units"]
        self.assertEqual(figure.data[0].z[0][0], -12)
        frame["net_new_units"] = np.nan
        figure = report_figures(build_report(frame, Selection()))["net-units"]
        self.assertFalse(figure.data)
        self.assertIn("No reported", figure.layout.annotations[0].text)

    def test_nighttime_share_is_weighted_and_zero_denominators_are_undefined(self):
        frame = self.frame[self.frame["has_housing_data"]].drop_duplicates("zip_code").head(2).copy()
        frame["year"] = 2022
        frame["borough"] = "BRONX"
        frame["filing_count"] = 100
        frame["night_crash_count"] = [1, 9]
        frame["crashes_with_known_time"] = [1, 99]
        figure = report_figures(build_report(frame, replace(
            Selection(), boroughs=("BRONX",), years=(2022,),
        )))["nighttime"]
        self.assertAlmostEqual(figure.data[0].z[0][3], 10)
        frame["crashes_with_known_time"] = 0
        frame["night_crash_count"] = 0
        figure = report_figures(build_report(frame, Selection()))["nighttime"]
        self.assertFalse(figure.data)
        self.assertIn("No known-time crashes", figure.layout.annotations[0].text)

    def test_endpoint_changes_match_same_zip_and_selected_years(self):
        selection = replace(Selection(), years=(2023, 2025))
        report = build_report(self.frame, selection)
        figure = report_figures(report)["changes"]
        known = report.rows[
            report.rows["has_housing_data"] & report.rows["zip_code"].isin(report.crash_covered_zips)
        ].set_index(["zip_code", "year"])
        count = 0
        for trace in figure.data:
            for zip_data, x, y in zip(trace.customdata, trace.x, trace.y):
                zip_code = zip_data[0]
                self.assertEqual(x, known.loc[(zip_code, 2025), "filing_count"] - known.loc[(zip_code, 2023), "filing_count"])
                self.assertEqual(y, known.loc[(zip_code, 2025), "crash_count"] - known.loc[(zip_code, 2023), "crash_count"])
                count += 1
        self.assertGreater(count, 0)

    def test_lag_uses_only_exact_consecutive_years_in_applied_scope(self):
        report = build_report(self.frame, replace(Selection(), years=(2022, 2023)))
        figure = report_figures(report)["lagged"]
        source = self.frame.set_index(["zip_code", "year"])
        pooled = figure.data[0]
        self.assertGreater(len(pooled.x), 0)
        for (zip_code, year), x, y in zip(pooled.customdata, pooled.x, pooled.y):
            self.assertEqual(year, 2022)
            self.assertEqual(x, source.loc[(zip_code, 2022), "filing_count"])
            self.assertEqual(y, source.loc[(zip_code, 2023), "crash_count"])
        np.testing.assert_array_equal(figure.data[1].x, 0)
        np.testing.assert_array_equal(figure.data[1].y, 0)
        gaps = report_figures(build_report(self.frame, replace(Selection(), years=(2022, 2024))))["lagged"]
        self.assertFalse(gaps.data)
        self.assertIn("consecutive years", gaps.layout.annotations[0].text)

    def test_fatal_share_pools_crashes_not_zip_percentages_or_people(self):
        frame = self.research_rows()
        frame["fatalities_total"] = 50
        report = build_report(frame, Selection())
        self.assertAlmostEqual(report.fatal_share.loc["Q4 / highest", "fatal_crash_share"], 4 / 40)
        figure = report_figures(report)["fatal-share"]
        self.assertAlmostEqual(figure.data[0].y[3], 10)
        frame.loc[frame.index[0], "fatal_crash_count"] = np.nan
        report = build_report(frame, Selection())
        self.assertAlmostEqual(report.fatal_share.loc["Q4 / highest", "fatal_crash_share"], 3 / 39)
        self.assertEqual(report.coverage["unknown_fatal_status_rows"], 1)

    def test_development_mix_compares_filing_types_with_fixed_crash_groups(self):
        report = build_report(self.research_rows(), Selection())
        self.assertAlmostEqual(report.development_mix.loc["Other crash volume", "new_building_share"], .2)
        self.assertAlmostEqual(report.development_mix.loc["High crash volume", "new_building_share"], .8)
        figure = report_figures(report)["development-mix"]
        np.testing.assert_allclose(figure.data[0].y, [20, 80])
        np.testing.assert_allclose(figure.data[1].y, [80, 20])
        selection = replace(Selection(), housing_metric="new_construction_filings", transport_metric="fatalities_total")
        alternate = build_report(self.research_rows(), selection)
        pd.testing.assert_frame_equal(report.development_mix, alternate.development_mix)
        pd.testing.assert_frame_equal(report.unit_reporting, alternate.unit_reporting)

    def test_unit_reporting_weights_jobs_and_respects_borough_year_scope(self):
        report = build_report(self.research_rows(), Selection())
        self.assertAlmostEqual(report.unit_reporting.loc[("BRONX", 2022), "missing_unit_share"], 11 / 40)
        figure = report_figures(report)["unit-reporting"]
        self.assertAlmostEqual(figure.data[0].z[0][0], 27.5)
        selection = self.controls(boroughs=["QUEENS"], years=[2024])
        local = build_report(self.frame, selection)
        self.assertEqual(local.unit_reporting.index.tolist(), [("QUEENS", 2024)])
        expected = local.rows["unique_job_count"].sum() - local.rows["jobs_with_known_units"].sum()
        self.assertEqual(local.unit_reporting.loc[("QUEENS", 2024), "jobs_missing_units"], expected)

    def test_replacements_handle_zero_denominators_and_unknown_coverage(self):
        frame = self.research_rows()
        frame["crash_count"] = 0
        frame["fatal_crash_count"] = 0
        frame["filing_count"] = 0
        frame["new_construction_filings"] = 0
        frame["unique_job_count"] = 0
        frame["jobs_with_known_units"] = 0
        reports = [
            build_report(frame, Selection()),
            build_report(self.frame, self.controls(mode="search", query="10111 2022")),
        ]
        for report in reports:
            figures = report_figures(report)
            for key in ["fatal-share", "development-mix", "unit-reporting"]:
                with self.subTest(question=key):
                    self.assertFalse(figures[key].data)
                    self.assertTrue(figures[key].layout.annotations[0].text)

    def test_replacements_cannot_duplicate_relationship_when_injuries_are_selected(self):
        report = build_report(self.frame, replace(Selection(), transport_metric="severe_injuries_total"))
        figures = report_figures(report)
        self.assertTrue(all(trace.type == "scatter" for trace in figures["relationship"].data))
        self.assertTrue(all(trace.type == "bar" for trace in figures["fatal-share"].data))
        self.assertTrue(all(trace.type == "bar" for trace in figures["development-mix"].data))
        self.assertEqual(figures["unit-reporting"].data[0].type, "heatmap")
        default = build_report(self.frame, Selection())
        pd.testing.assert_frame_equal(default.fatal_share, report.fatal_share)
        pd.testing.assert_frame_equal(default.development_mix, report.development_mix)
        pd.testing.assert_frame_equal(default.unit_reporting, report.unit_reporting)

    def test_single_year_reports_explain_unavailable_time_comparisons(self):
        figures = report_figures(build_report(self.frame, replace(Selection(), years=(2024,))))
        for key in ["changes", "lagged"]:
            with self.subTest(question=key):
                self.assertFalse(figures[key].data)
                self.assertTrue(figures[key].layout.annotations[0].text)
        for key in ["fatal-share", "development-mix", "unit-reporting"]:
            self.assertTrue(figures[key].data)

    def test_saved_selection_round_trip_and_tampered_values(self):
        selection = self.controls(mode="search", query="Brooklyn 2024 new buildings")
        payload = json.loads(json.dumps(selection.to_dict()))
        self.assertEqual(selection_from_store(payload, self.frame), selection)
        for bad in [None, {}, payload | {"years": [2026]}, payload | {"zip_codes": "11201"},
                    payload | {"housing_metric": ["filing_count"]}, payload | {"query": 123}]:
            with self.subTest(payload=bad), self.assertRaises(SelectionError):
                selection_from_store(bad, self.frame)

    def test_dataset_schema_errors_are_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            for frame in [
                self.frame.drop(columns="filing_count"),
                self.frame.drop(columns="net_new_units"),
                self.frame.drop(columns="night_crash_count"),
                self.frame.drop(columns="fatal_crash_count"),
                self.frame.assign(fatal_crash_count=self.frame["crash_count"] + 1),
                self.frame.assign(new_construction_filings=self.frame["filing_count"] + 1),
                self.frame.assign(jobs_with_known_units=self.frame["unique_job_count"] + 1),
                self.frame.assign(unique_job_count=np.nan),
                self.frame.assign(net_new_units=np.inf),
                pd.concat([self.frame, self.frame.iloc[:1]], ignore_index=True),
                self.frame.assign(has_housing_data="unknown"),
                self.frame.assign(crash_count=-1),
            ]:
                frame.to_csv(path, index=False)
                with self.assertRaises(ValueError):
                    load_dataset(path)


class DashboardHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app.app import create_app
        cls.dashboard = create_app()
        cls.client = cls.dashboard.server.test_client()
        cls.frame = load_dataset()

    def invoke(self, prefix, values, trigger):
        key, callback = next((k, v) for k, v in self.dashboard.callback_map.items() if k.startswith(prefix))
        outputs = callback["output"]
        if not isinstance(outputs, list):
            outputs = [outputs]
        result = self.client.post("/_dash-update-component", json={
            "output": key,
            "outputs": [{"id": o.component_id, "property": o.component_property} for o in outputs],
            "inputs": [{"id": i["id"], "property": i["property"], "value": values[i["id"]]} for i in callback["inputs"]],
            "state": [{"id": i["id"], "property": i["property"], "value": values[i["id"]]} for i in callback["state"]],
            "changedPropIds": [trigger],
        })
        self.assertEqual(result.status_code, 200, result.get_data(as_text=True)[:1000])
        return result.json["response"]

    def generate(self, query="", mode="filters", **changes):
        values = {
            "generate-button": 1, "reset-button": 0, "borough-filter": list(BOROUGHS),
            "year-filter": list(YEARS), "housing-filter": "filing_count",
            "transport-filter": "crash_count", "selection-mode": mode, "search-query": query,
        } | changes
        return self.invoke("..report-panel", values, "generate-button.n_clicks")

    def assert_research_questions(self, panel):
        nodes = list(component_nodes(panel))
        headings = [
            node["props"]["children"] for node in nodes
            if node["type"] == "H2" and isinstance(node["props"].get("children"), str)
            and node["props"]["children"].startswith("RQ")
        ]
        self.assertEqual([heading.split(" / ")[0] for heading in headings],
                         [f"RQ{n}" for n in range(1, 11)])
        self.assertEqual(headings[2], "RQ3 / Fatal-crash share")
        self.assertEqual(headings[6], "RQ7 / Development mix")
        self.assertEqual(headings[7], "RQ8 / Unit-reporting gaps")
        graphs = [node["props"]["id"] for node in nodes if node["type"] == "Graph"]
        self.assertEqual(len(graphs), 12)
        self.assertEqual(len(graphs), len(set(graphs)))
        for key in RESEARCH_GRAPHS:
            self.assertIn(f"{key}-chart", graphs)

    def test_page_layout_assets_and_health(self):
        for path in ["/", "/_dash-layout", "/_dash-dependencies", "/assets/style.css", "/healthz"]:
            with self.client.get(path) as response:
                self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/healthz").json["rows"], len(self.frame))
        self.assert_research_questions(self.client.get("/_dash-layout").json)

    def test_generate_search_refreshes_every_chart_and_controls(self):
        response = self.generate("Brooklyn 2024 new buildings", "search")
        self.assertEqual(response["borough-filter"]["value"], ["BROOKLYN"])
        self.assertEqual(response["year-filter"]["value"], [2024])
        self.assertEqual(response["housing-filter"]["value"], "new_construction_filings")
        panel = json.dumps(response["report-panel"])
        for graph in ["relationship", "concentration", "trend", "recurrence", "map"]:
            self.assertIn(f"{graph}-chart", panel)
        self.assert_research_questions(response["report-panel"])
        graphs = [node["props"] for node in component_nodes(response["report-panel"]) if node["type"] == "Graph"]
        for graph in graphs:
            self.assertGreaterEqual(int(graph["style"]["height"].removesuffix("px")), 300)
            self.assertTrue(graph["responsive"])
        self.assertFalse(response["download-button"]["disabled"])
        self.assertEqual(response["form-errors"]["children"], "")

    def test_invalid_search_clears_report_and_disables_download(self):
        response = self.generate("Brooklyn bananas", "search")
        self.assertIsNone(response["applied-selection"]["data"])
        self.assertTrue(response["download-button"]["disabled"])
        self.assertIn("Unrecognized", response["form-errors"]["children"])
        self.assertIn("No active report", json.dumps(response["report-panel"]))

    def test_reset_restores_all_default_controls_and_report(self):
        values = {
            "generate-button": 1, "reset-button": 1, "borough-filter": ["QUEENS"],
            "year-filter": [2024], "housing-filter": "permit_issued_count",
            "transport-filter": "fatalities_total", "selection-mode": "search", "search-query": "bad",
        }
        response = self.invoke("..report-panel", values, "reset-button.n_clicks")
        self.assertEqual(response["borough-filter"]["value"], list(BOROUGHS))
        self.assertEqual(response["year-filter"]["value"], list(YEARS))
        self.assertEqual(response["selection-mode"]["value"], "filters")
        self.assertEqual(response["search-query"]["value"], "")
        self.assert_research_questions(response["report-panel"])

    def test_all_ten_questions_remain_visible_for_sparse_selections(self):
        for query in ["10111 2022", "10044", "11201 2024"]:
            with self.subTest(query=query):
                response = self.generate(query, "search")
                self.assert_research_questions(response["report-panel"])
                self.assertFalse(response["download-button"]["disabled"])

    def test_download_uses_only_last_applied_selection(self):
        applied = self.generate("11201 2024", "search")["applied-selection"]["data"]
        response = self.invoke("..report-download", {"download-button": 1, "applied-selection": applied},
                               "download-button.n_clicks")
        csv = response["report-download"]["data"]["content"]
        frame = pd.read_csv(io.StringIO(csv), dtype={"zip_code": str})
        self.assertEqual(set(frame["zip_code"]), {"11201"})
        self.assertEqual(set(frame["year"]), {2024})
        self.assertIn("has_housing_data", frame)
        self.assertIn("joint_high", frame)
        response = self.invoke("..report-download", {"download-button": 1, "applied-selection": None},
                               "download-button.n_clicks")
        self.assertIn("Generate a new report", response["download-error"]["children"])


class DashboardNotebookTests(unittest.TestCase):
    def test_replacement_notebooks_share_dashboard_logic_and_have_fresh_outputs(self):
        root = Path(__file__).resolve().parents[1]
        expected = {
            "Member2_Transportation_SIRTA.ipynb": {"60278402": "fatal_share_figure"},
            "Member4_Story_and_Final.ipynb": {
                "60278402": "fatal_share_figure",
                "24aff1bb": "development_mix_figure",
                "0381bf69": "unit_reporting_figure",
            },
        }
        sources = []
        for name, cells in expected.items():
            notebook = nbformat.read(root / "notebooks" / name, as_version=4)
            nbformat.validate(notebook)
            by_id = {cell.id: cell for cell in notebook.cells}
            sources.append(by_id["60278402"].source)
            for cell_id, function in cells.items():
                with self.subTest(notebook=name, question=function):
                    cell = by_id[cell_id]
                    self.assertIn(function, cell.source)
                    self.assertIn("build_report", cell.source)
                    self.assertIsNotNone(cell.execution_count)
                    self.assertFalse(any(o.output_type == "error" for o in cell.outputs))
                    plot_outputs = [o["data"]["application/vnd.plotly.v1+json"] for o in cell.outputs
                                    if "application/vnd.plotly.v1+json" in o.get("data", {})]
                    self.assertEqual(len(plot_outputs), 1)
                    self.assertTrue(plot_outputs[0]["data"])
                    self.assertTrue(any("text/markdown" in o.get("data", {}) for o in cell.outputs))
        self.assertEqual(sources[0], sources[1])

    def test_member5_notebook_has_two_executed_interactive_charts(self):
        path = Path(__file__).resolve().parents[1] / "notebooks" / "Member5_Website_Research.ipynb"
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        cells = [c for c in notebook.cells if c.cell_type == "code"]
        self.assertTrue(all(c.execution_count is not None for c in cells))
        self.assertFalse(any(o.output_type == "error" for c in cells for o in c.outputs))
        figures = sum("application/vnd.plotly.v1+json" in o.get("data", {}) for c in cells for o in c.outputs)
        self.assertEqual(figures, 2)


if __name__ == "__main__":
    unittest.main()
