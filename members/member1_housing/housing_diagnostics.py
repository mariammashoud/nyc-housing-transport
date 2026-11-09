"""Exploratory housing checks; never change the exported cleaning policy."""
import numpy as np
import pandas as pd

from housing_pipeline import NUMERIC, UNIT_LIMIT, aggregate_housing

MIN_SQFT_PER_NEW_UNIT = 300
LOW_RISE_STORIES = 4
LOW_RISE_UNIT_LIMIT = 500
SMALL_HOUSE_COST_LIMIT = 25_000_000


def housing_domain_flags(frame):
    """Flag observed violations and review candidates, excluding unknown values."""
    numeric = frame[NUMERIC].apply(pd.to_numeric, errors="coerce")
    units = numeric[["existing_dwelling_units", "proposed_dwelling_units"]]
    net = units["proposed_dwelling_units"] - units["existing_dwelling_units"]
    area = numeric["total_construction_floor_area"]
    latitude, longitude = numeric["latitude"], numeric["longitude"]
    borough = frame["borough"].astype("string").str.strip().str.upper()
    prefix_borough = frame["job_filing_number"].astype("string").str[0].map(
        {"B": "BROOKLYN", "M": "MANHATTAN", "Q": "QUEENS", "S": "STATEN ISLAND", "X": "BRONX"})
    flags = {
        "Negative units, cost or floor area": numeric[
            ["existing_dwelling_units", "proposed_dwelling_units",
             "initial_cost", "total_construction_floor_area"]].lt(0).any(axis=1),
        "Non-integer reported dwelling units": (units.notna() & units.mod(1).ne(0)).any(axis=1),
        f"Dwelling units above {UNIT_LIMIT:,}": units.gt(UNIT_LIMIT).any(axis=1),
        "Height above 2,000 ft": numeric[["existing_height", "proposed_height"]].gt(2000).any(axis=1),
        "Stories above 150": numeric[["existing_stories", "proposed_no_of_stories"]].gt(150).any(axis=1),
        "Small-house high cost (review only)": (
            frame["building_type"].isin(["1 Family", "2 Family", "3 Family"])
            & numeric["initial_cost"].gt(SMALL_HOUSE_COST_LIMIT)),
        "Low-rise high units (review only)": (
            numeric["proposed_no_of_stories"].le(LOW_RISE_STORIES)
            & units["proposed_dwelling_units"].gt(LOW_RISE_UNIT_LIMIT)),
        "Unit gain with low construction area (review only)": (
            net.gt(0) & area.notna() & area.lt(MIN_SQFT_PER_NEW_UNIT * net)),
        "Observed coordinates outside NYC bounds": (
            (latitude.notna() & ~latitude.between(40.49, 40.92))
            | (longitude.notna() & ~longitude.between(-74.26, -73.69))),
        "Known borough differs from known job prefix": (
            borough.notna() & prefix_borough.notna() & borough.ne(prefix_borough)),
    }
    return pd.DataFrame(flags, index=frame.index).fillna(False).astype(bool)


def housing_sensitivity(frame):
    """Compare hypothetical exclusions on copies using unchanged job accounting."""
    flags = housing_domain_flags(frame)
    area = flags["Unit gain with low construction area (review only)"]
    low_rise = flags["Low-rise high units (review only)"]
    cost = flags["Small-house high cost (review only)"]
    none = pd.Series(False, index=frame.index)
    scenarios = [
        ("Baseline: exported policy", none, none),
        ("Construction area rule only", area, none),
        ("Low-rise unit rule only", low_rise, none),
        ("Small-house cost rule only", none, cost),
        ("All three review rules", area | low_rise, cost),
    ]
    rows = []
    for label, unit_mask, cost_mask in scenarios:
        candidate = frame.copy()
        candidate.loc[unit_mask, ["existing_dwelling_units", "proposed_dwelling_units"]] = np.nan
        candidate.loc[cost_mask, "initial_cost"] = np.nan
        aggregate, _ = aggregate_housing(candidate)
        rows.append({
            "scenario": label,
            "flagged_filings": int((unit_mask | cost_mask).sum()),
            "filing_count": int(aggregate["filing_count"].sum()),
            "jobs_with_known_units": int(aggregate["jobs_with_known_units"].sum()),
            "reported_net_units": aggregate["net_new_units"].sum(min_count=1),
            "reported_cost_usd": aggregate["initial_cost_total"].sum(min_count=1),
        })
    summary = pd.DataFrame(rows).set_index("scenario")
    summary["net_units_vs_baseline"] = summary["reported_net_units"] - summary.iloc[0]["reported_net_units"]
    return summary


def unit_change_groups(net_units):
    """Keep equal unit changes together; leave unreported changes unknown."""
    groups = pd.Series(pd.NA, index=net_units.index, dtype="string")
    groups.loc[net_units.lt(0)] = "Reported loss"
    groups.loc[net_units.eq(0)] = "No reported change"
    groups.loc[net_units.gt(0)] = "Reported gain"
    return pd.Series(pd.Categorical(
        groups, categories=["Reported loss", "No reported change", "Reported gain"], ordered=True),
        index=net_units.index, name="unit_change_group")
