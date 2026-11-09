import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import nbformat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "members" / "member1_housing"))
from housing_pipeline import aggregate_housing, clean_housing
from assign_zip_from_sirta import assign_building_zip


def filing(identifier="M00000001-I1", **changes):
    row = {
        "job_filing_number": identifier, "filing_date": "2022-01-01",
        "current_status_date": "2022-02-01", "borough": "Manhattan",
        "postcode": "10001", "zip": "90210", "job_type": "Alteration",
        "filing_status": "Permit Issued", "initial_cost": 1000,
        "total_construction_floor_area": 100, "existing_stories": 3,
        "existing_height": 30, "existing_dwelling_units": 4,
        "proposed_no_of_stories": 3, "proposed_height": 30,
        "proposed_dwelling_units": 6, "latitude": 40.75, "longitude": -73.99,
    }
    return row | changes


class HousingTests(unittest.TestCase):
    def clean(self, rows):
        return clean_housing(pd.DataFrame(rows), "unused.csv")[0]

    def test_official_zip_not_owner_and_no_coordinate_requirement(self):
        frame = self.clean([filing(latitude=np.nan, longitude=np.nan)])
        self.assertEqual(frame.iloc[0]["zip_code"], "10001")
        self.assertEqual(frame.iloc[0]["zip_assignment_method"], "official_postcode")

    def test_unit_pairs_counted_once_per_job_across_amendments_and_years(self):
        frame = self.clean([
            filing(),
            filing("M00000001-P1", filing_date="2023-02-01", proposed_dwelling_units=9),
            filing("M00000002-I1", proposed_dwelling_units=3, existing_dwelling_units=5),
        ])
        aggregate, jobs = aggregate_housing(frame)
        self.assertEqual(aggregate["filing_count"].sum(), 3)
        self.assertEqual(aggregate["unique_job_count"].sum(), 2)
        self.assertEqual(aggregate["proposed_units_total"].sum(), 12)
        self.assertEqual(aggregate["existing_units_total"].sum(), 9)
        self.assertEqual(aggregate["net_new_units"].sum(), 3)
        self.assertEqual(aggregate.loc[aggregate["year"] == 2023, "proposed_units_total"].iloc[0], 0)
        self.assertEqual(len(jobs), 2)

    def test_missing_units_are_not_zero_or_new_building(self):
        frame = self.clean([filing(existing_dwelling_units=np.nan, proposed_dwelling_units=6)])
        aggregate, _ = aggregate_housing(frame)
        self.assertTrue(pd.isna(frame.iloc[0]["existing_dwelling_units"]))
        self.assertEqual(aggregate["jobs_with_known_units"].sum(), 0)
        self.assertTrue(pd.isna(aggregate.iloc[0]["proposed_units_total"]))
        self.assertEqual(aggregate.iloc[0]["new_construction_filings"], 0)

    def test_corrupt_units_quarantined_without_deleting_filing(self):
        frame = self.clean([filing(proposed_dwelling_units=111_111_111)])
        aggregate, _ = aggregate_housing(frame)
        self.assertEqual(aggregate["filing_count"].sum(), 1)
        self.assertTrue(frame.iloc[0]["unit_value_quarantined"])
        self.assertTrue(pd.isna(aggregate.iloc[0]["proposed_units_total"]))

    def test_exact_unit_screen_boundary_and_fractional_units(self):
        frame = self.clean([
            filing(proposed_dwelling_units=10_000),
            filing("M00000002-I1", proposed_dwelling_units=10_001),
            filing("M00000003-I1", proposed_dwelling_units=2.5),
        ])
        self.assertEqual(frame["proposed_dwelling_units"].notna().tolist(), [True, False, False])
        self.assertEqual(frame.iloc[0]["proposed_dwelling_units"], 10_000)

    def test_invalid_key_only_input_fails_explicitly(self):
        with self.assertRaisesRegex(ValueError, "No housing filings remain"):
            self.clean([filing(identifier="not-a-job-id")])

    def test_outlier_flags_use_team_log_scale_rule(self):
        frame = self.clean([
            filing(f"M{i:08d}-I1", initial_cost=cost)
            for i, cost in enumerate([10, 100, 1000, 10000, 100000, 1000000], start=1)
        ])
        logged = np.log1p(frame["initial_cost"])
        q1, q3 = logged.quantile([0.25, 0.75])
        self.assertTrue(frame["outlier_initial_cost"].equals(logged.gt(q3 + 1.5 * (q3 - q1))))

    def test_latest_valid_pair_is_not_built_from_different_filings(self):
        frame = self.clean([
            filing(existing_dwelling_units=4, proposed_dwelling_units=np.nan),
            filing("M00000001-P1", filing_date="2023-01-01",
                   existing_dwelling_units=np.nan, proposed_dwelling_units=8),
        ])
        aggregate, _ = aggregate_housing(frame)
        self.assertEqual(aggregate["jobs_with_known_units"].sum(), 0)

    def test_new_building_uses_actual_job_type_not_positive_unit_change(self):
        frame = self.clean([filing(), filing("M00000002-I1", job_type="New Building")])
        aggregate, _ = aggregate_housing(frame)
        self.assertEqual(aggregate["new_construction_filings"].sum(), 1)

    def test_coordinate_fallback_is_flagged_and_does_not_override_official(self):
        def fake_assignment(frame, _):
            return frame.assign(zip_code="10002")
        with patch("housing_pipeline.assign_building_zip", side_effect=fake_assignment):
            frame = self.clean([filing(), filing("M00000002-I1", postcode=np.nan)])
        self.assertEqual(frame["zip_code"].tolist(), ["10001", "10002"])
        self.assertEqual(frame["zip_assignment_method"].tolist(), ["official_postcode", "nearest_crash"])

    def test_no_coordinates_can_return_missing_without_neighbor_query(self):
        crashes = pd.DataFrame({"zip_code": ["10001"], "latitude": [40.75], "longitude": [-73.99]})
        with patch("assign_zip_from_sirta.pd.read_csv", return_value=crashes):
            result = assign_building_zip(pd.DataFrame({"latitude": [np.nan], "longitude": [np.nan]}), "unused.csv")
        self.assertTrue(result["zip_code"].isna().all())


class ExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.housing = pd.read_csv(ROOT / "data" / "clean" / "housing_clean.csv", dtype={"zip_code": str})
        cls.transport = pd.read_csv(ROOT / "data" / "clean" / "transport_clean.csv", dtype={"zip_code": str})
        cls.integrated = pd.read_csv(ROOT / "data" / "clean" / "integrated_dataset.csv", dtype={"zip_code": str})

    def test_keys_are_unique_and_union_preserved(self):
        keys = ["zip_code", "year"]
        expected = set(map(tuple, self.housing[keys].to_numpy())) | set(map(tuple, self.transport[keys].to_numpy()))
        self.assertEqual(expected, set(map(tuple, self.integrated[keys].to_numpy())))
        for frame in [self.housing, self.transport, self.integrated]:
            self.assertFalse(frame.duplicated(keys).any())
            self.assertTrue(frame["zip_code"].str.fullmatch(r"\d{5}").all())
            self.assertTrue(frame["year"].isin([2022, 2023, 2024, 2025]).all())

    def test_counts_and_units_reconcile(self):
        for source, columns in [
            (self.housing, ["filing_count", "unique_job_count", "jobs_with_known_units",
                            "proposed_units_total", "existing_units_total", "net_new_units"]),
            (self.transport, ["crash_count", "fatalities_total", "severe_injuries_total",
                              "night_crash_count", "crashes_with_known_time"]),
        ]:
            for column in columns:
                self.assertAlmostEqual(source[column].sum(), self.integrated[column].sum())

    def test_unknown_housing_not_zero_and_ratios_finite(self):
        frame = self.integrated
        self.assertTrue(frame.loc[~frame["has_housing_data"], "filing_count"].isna().all())
        self.assertTrue(frame.loc[~frame["has_crash_data"], "crash_count"].eq(0).all())
        numeric = frame.select_dtypes(include="number")
        self.assertFalse(np.isinf(numeric.to_numpy()).any())
        self.assertTrue(frame.loc[frame["year"] == 2025, "crashes_next_year"].isna().all())

    def test_nighttime_denominator_and_zip_provenance(self):
        transport = self.transport
        ratio = transport["night_crash_count"] / transport["crashes_with_known_time"].replace(0, np.nan)
        np.testing.assert_allclose(ratio, transport["night_crash_share"], equal_nan=True)
        self.assertTrue(transport["crashes_with_known_time"].le(transport["crash_count"]).all())
        housing = self.housing
        self.assertTrue(housing["official_zip_filings"].add(housing["approximate_zip_filings"]).eq(housing["filing_count"]).all())
        self.assertTrue(housing["jobs_with_known_units"].le(housing["unique_job_count"]).all())


class NotebookTests(unittest.TestCase):
    def test_all_four_notebooks_executed_without_errors(self):
        names = [
            "Member1_Housing.ipynb", "Member2_Transportation_SIRTA.ipynb",
            "Member3_Integration.ipynb", "Member4_Story_and_Final.ipynb",
        ]
        for name in names:
            with self.subTest(notebook=name):
                notebook = nbformat.read(ROOT / "notebooks" / name, as_version=4)
                nbformat.validate(notebook)
                cells = [c for c in notebook.cells if c.cell_type == "code"]
                self.assertTrue(cells)
                self.assertTrue(all(c.execution_count is not None for c in cells))
                self.assertFalse(any(o.output_type == "error" for c in cells for o in c.outputs))
                figures = sum("image/png" in o.get("data", {}) for c in cells for o in c.outputs)
                self.assertGreaterEqual(figures, 2)

    def test_only_member3_pipeline_writes_integrated_file(self):
        notebook = nbformat.read(ROOT / "notebooks" / "Member1_Housing.ipynb", as_version=4)
        for cell in notebook.cells:
            if cell.cell_type == "code":
                self.assertFalse("integrated_dataset" in cell.source and "to_csv" in cell.source)


if __name__ == "__main__":
    unittest.main()
