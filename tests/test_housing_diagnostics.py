import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "members" / "member1_housing"))
from housing_diagnostics import housing_domain_flags, housing_sensitivity, unit_change_groups
from housing_pipeline import clean_housing
from test_data_pipeline import filing


class HousingDiagnosticsTests(unittest.TestCase):
    def test_fractional_check_excludes_unknown_units(self):
        frame = pd.DataFrame([
            filing(existing_dwelling_units=np.nan, proposed_dwelling_units=np.nan),
            filing(existing_dwelling_units=2, proposed_dwelling_units=3),
            filing(existing_dwelling_units=np.nan, proposed_dwelling_units=2.5),
        ])
        flags = housing_domain_flags(frame)
        self.assertEqual(flags["Non-integer reported dwelling units"].tolist(), [False, False, True])

    def test_review_rules_handle_unknowns_losses_and_exact_thresholds(self):
        frame = pd.DataFrame([
            filing(existing_dwelling_units=0, proposed_dwelling_units=2,
                   total_construction_floor_area=600),
            filing(existing_dwelling_units=0, proposed_dwelling_units=2,
                   total_construction_floor_area=599),
            filing(existing_dwelling_units=0, proposed_dwelling_units=2,
                   total_construction_floor_area=np.nan),
            filing(existing_dwelling_units=4, proposed_dwelling_units=2,
                   total_construction_floor_area=0),
            filing(existing_dwelling_units=500, proposed_dwelling_units=500,
                   proposed_no_of_stories=4, building_type="1 Family", initial_cost=25_000_000),
            filing(existing_dwelling_units=501, proposed_dwelling_units=501,
                   proposed_no_of_stories=4, building_type="1 Family", initial_cost=25_000_001),
            filing(existing_dwelling_units=np.nan, proposed_dwelling_units=501,
                   proposed_no_of_stories=np.nan, building_type="Other", initial_cost=25_000_001),
        ])
        flags = housing_domain_flags(frame)
        self.assertEqual(flags["Unit gain with low construction area (review only)"].tolist(),
                         [False, True, False, False, False, False, False])
        self.assertEqual(flags["Low-rise high units (review only)"].tolist(),
                         [False, False, False, False, False, True, False])
        self.assertEqual(flags["Small-house high cost (review only)"].tolist(),
                         [False, False, False, False, False, True, False])

    def test_sensitivity_does_not_mutate_filings_or_double_count_jobs(self):
        raw = pd.DataFrame([
            filing(existing_dwelling_units=0, proposed_dwelling_units=2,
                   total_construction_floor_area=600),
            filing("M00000001-P1", filing_date="2023-01-01",
                   existing_dwelling_units=0, proposed_dwelling_units=10,
                   total_construction_floor_area=100),
            filing("M00000002-I1", existing_dwelling_units=4, proposed_dwelling_units=6,
                   total_construction_floor_area=600, building_type="1 Family",
                   initial_cost=25_000_001),
        ])
        frame, _ = clean_housing(raw, "unused.csv")
        original = frame.copy(deep=True)
        summary = housing_sensitivity(frame)
        assert_frame_equal(frame, original)
        baseline = summary.loc["Baseline: exported policy"]
        area = summary.loc["Construction area rule only"]
        cost = summary.loc["Small-house cost rule only"]
        self.assertTrue(summary["filing_count"].eq(3).all())
        self.assertEqual(baseline["reported_net_units"], 12)
        self.assertEqual(area["reported_net_units"], 4)
        self.assertEqual(area["jobs_with_known_units"], 2)
        self.assertEqual(area["net_units_vs_baseline"], -8)
        self.assertEqual(cost["reported_net_units"], 12)
        self.assertEqual(cost["reported_cost_usd"], 2000)

    def test_all_unknown_unit_pairs_stay_unknown_in_sensitivity(self):
        frame, _ = clean_housing(pd.DataFrame([
            filing(existing_dwelling_units=np.nan, proposed_dwelling_units=np.nan),
        ]), "unused.csv")
        self.assertTrue(housing_sensitivity(frame)["reported_net_units"].isna().all())

    def test_unit_change_groups_keep_ties_together_and_unknowns_missing(self):
        units = pd.Series([-2, 0, 0, 1, np.nan])
        groups = unit_change_groups(units)
        self.assertEqual(groups.iloc[:4].tolist(),
                         ["Reported loss", "No reported change", "No reported change", "Reported gain"])
        self.assertTrue(pd.isna(groups.iloc[4]))
        pd.testing.assert_series_equal(groups, unit_change_groups(units.sample(frac=1, random_state=7)).sort_index())


if __name__ == "__main__":
    unittest.main()
