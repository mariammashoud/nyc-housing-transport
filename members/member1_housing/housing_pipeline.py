"""Reproducible housing cleaning and job-level unit accounting."""
import numpy as np
import pandas as pd

from assign_zip_from_sirta import assign_building_zip

BOROUGHS = {"BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND"}
UNIT_LIMIT = 10_000
NUMERIC = [
    "initial_cost", "total_construction_floor_area", "existing_stories",
    "existing_height", "existing_dwelling_units", "proposed_no_of_stories",
    "proposed_height", "proposed_dwelling_units", "latitude", "longitude",
]


def clean_housing(raw, transport_path):
    """Keep valid filings; quarantine invalid measures instead of inventing zeros."""
    frame = raw.copy()
    frame.columns = frame.columns.str.strip().str.lower()
    required = {
        "job_filing_number", "filing_date", "current_status_date", "borough",
        "postcode", "job_type", "filing_status", *NUMERIC,
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Housing source is missing required columns: {sorted(missing)}")
    audit = []

    def record(step, note):
        audit.append({"step": step, "rows": len(frame), "note": note})

    record("Raw", "Complete 2022-2025 download, not a row-limited sample")
    frame = frame.dropna(how="all").drop_duplicates()
    frame["job_filing_number"] = frame["job_filing_number"].astype("string").str.strip()
    frame = frame[frame["job_filing_number"].str.fullmatch(r"[BMQSX]\d+-[A-Z]\d+", na=False)].copy()
    for column in ["filing_date", "current_status_date", "first_permit_date", "approved_date"]:
        if column in frame:
            frame[column] = pd.to_datetime(frame[column], format="mixed", errors="coerce")
    frame = (frame.sort_values(["current_status_date", "filing_date"], na_position="first")
             .drop_duplicates("job_filing_number", keep="last").copy())
    frame["year"] = frame["filing_date"].dt.year
    frame["borough"] = frame["borough"].astype("string").str.strip().str.upper()
    frame = frame[frame["year"].between(2022, 2025) & frame["borough"].isin(BOROUGHS)].copy()
    frame["year"] = frame["year"].astype(int)
    if frame.empty:
        raise ValueError("No housing filings remain with valid identifiers, dates and boroughs.")
    record("Keys and duplicates", "Drop invalid IDs/dates/boroughs; keep latest status per filing ID")

    sparse = [c for c in frame if c not in required and frame[c].isna().mean() > 0.60]
    frame = frame.drop(columns=sparse)
    record("Sparse optional columns", f"Drop >60% missing optional columns: {sparse}")
    for column in NUMERIC:
        text = frame[column].astype("string").str.replace(r"[$,]", "", regex=True)
        frame[column] = pd.to_numeric(text, errors="coerce").astype(float)
    unit_columns = ["existing_dwelling_units", "proposed_dwelling_units"]
    invalid_units = frame[unit_columns].lt(0) | frame[unit_columns].gt(UNIT_LIMIT)
    invalid_units |= frame[unit_columns].mod(1).ne(0) & frame[unit_columns].notna()
    frame["unit_value_quarantined"] = invalid_units.any(axis=1)
    frame[unit_columns] = frame[unit_columns].mask(invalid_units)
    for column, maximum in [
        ("existing_height", 2000), ("proposed_height", 2000),
        ("existing_stories", 150), ("proposed_no_of_stories", 150),
        ("initial_cost", np.inf), ("total_construction_floor_area", np.inf),
    ]:
        frame[column] = frame[column].where(frame[column].between(0, maximum))
    record("Invalid measures", f"Keep filings; set impossible measures to NaN. "
           f"{frame['unit_value_quarantined'].sum()} filings have invalid unit values (limit {UNIT_LIMIT:,}).")
    valid_coords = frame["latitude"].between(40.49, 40.92) & frame["longitude"].between(-74.26, -73.69)
    frame.loc[~valid_coords, ["latitude", "longitude"]] = np.nan
    prefix_borough = frame["job_filing_number"].str[0].map(
        {"B": "BROOKLYN", "M": "MANHATTAN", "Q": "QUEENS", "S": "STATEN ISLAND", "X": "BRONX"})
    frame = frame[frame["borough"].eq(prefix_borough)].copy()
    record("Location consistency", "Drop borough/job-prefix conflicts; invalid coordinates become NaN")

    postcode = (frame["postcode"].astype("string").str.strip()
                .str.replace(r"\.0$", "", regex=True))
    number = pd.to_numeric(postcode, errors="coerce")
    valid_zip = postcode.str.fullmatch(r"\d{5}", na=False)
    valid_zip &= number.between(10001, 10499) | number.between(11001, 11699)
    frame["zip_code"] = postcode.where(valid_zip)
    frame["zip_assignment_method"] = pd.Series("official_postcode", index=frame.index, dtype="string")
    missing_zip = frame["zip_code"].isna()
    if missing_zip.any():
        approximate = assign_building_zip(frame.loc[missing_zip], transport_path)
        frame.loc[missing_zip, "zip_code"] = approximate["zip_code"].astype("string")
        frame.loc[missing_zip, "zip_assignment_method"] = "nearest_crash"
    unassigned = int(frame["zip_code"].isna().sum())
    frame = frame.dropna(subset=["zip_code"]).copy()
    if frame.empty:
        raise ValueError("No housing filings have a usable building ZIP after official/fallback assignment.")
    frame["zip_code"] = frame["zip_code"].astype(str)
    record("Building ZIP", f"Official postcode first; {frame['zip_assignment_method'].eq('nearest_crash').sum()} "
           f"flagged approximations; drop {unassigned} unassigned filings. Owner zip is never used.")

    for column, flag in [
        ("initial_cost", "outlier_initial_cost"),
        ("proposed_dwelling_units", "outlier_proposed_units"),
        ("total_construction_floor_area", "outlier_floor_area"),
    ]:
        logged = np.log1p(frame[column])
        q1, q3 = logged.quantile([0.25, 0.75])
        frame[flag] = logged > q3 + 1.5 * (q3 - q1)
    frame["outlier_flag"] = frame[
        ["outlier_initial_cost", "outlier_proposed_units", "outlier_floor_area"]].any(axis=1)
    frame["job_id"] = frame["job_filing_number"].str.split("-").str[0]
    frame["is_new_construction"] = frame["job_type"].astype("string").str.strip().str.casefold().eq("new building").fillna(False)
    frame["net_new_units_row"] = frame["proposed_dwelling_units"] - frame["existing_dwelling_units"]
    record("Outliers", "Keep high but plausible values and flag using log1p IQR; job_type identifies new-building filings")
    return frame.reset_index(drop=True), pd.DataFrame(audit)


def aggregate_housing(frame):
    """Count every filing, but attribute each job's reported unit pair only once."""
    keys = ["zip_code", "year"]
    aggregate = frame.groupby(keys).agg(
        borough=("borough", lambda s: s.mode().iloc[0]),
        filing_count=("job_filing_number", "size"),
        new_construction_filings=("is_new_construction", "sum"),
        permit_issued_count=("filing_status", lambda s: s.isin(["Permit Issued", "LOC Issued"]).sum()),
        initial_cost_total=("initial_cost", lambda s: s.sum(min_count=1)),
        initial_cost_median=("initial_cost", "median"),
        total_floor_area=("total_construction_floor_area", lambda s: s.sum(min_count=1)),
        avg_proposed_stories=("proposed_no_of_stories", "mean"),
        avg_proposed_height=("proposed_height", "mean"),
        avg_latitude=("latitude", "mean"), avg_longitude=("longitude", "mean"),
        outlier_filing_count=("outlier_flag", "sum"), outlier_filing_share=("outlier_flag", "mean"),
        official_zip_filings=("zip_assignment_method", lambda s: s.eq("official_postcode").sum()),
        approximate_zip_filings=("zip_assignment_method", lambda s: s.eq("nearest_crash").sum()),
    )
    ordered = frame.sort_values(["filing_date", "job_filing_number"])
    cohort = ordered.drop_duplicates("job_id").set_index("job_id")[keys]
    paired = ordered.dropna(subset=["existing_dwelling_units", "proposed_dwelling_units"])
    latest = (paired.sort_values(["filing_date", "current_status_date", "job_filing_number"], na_position="first")
              .drop_duplicates("job_id", keep="last").set_index("job_id"))
    jobs = cohort.join(latest[["existing_dwelling_units", "proposed_dwelling_units"]])
    jobs["net_new_units"] = jobs["proposed_dwelling_units"] - jobs["existing_dwelling_units"]
    units = jobs.groupby(keys).agg(
        unique_job_count=("proposed_dwelling_units", "size"),
        jobs_with_known_units=("proposed_dwelling_units", "count"),
        proposed_units_total=("proposed_dwelling_units", lambda s: s.sum(min_count=1)),
        existing_units_total=("existing_dwelling_units", lambda s: s.sum(min_count=1)),
        net_new_units=("net_new_units", lambda s: s.sum(min_count=1)),
    )
    aggregate = aggregate.join(units)
    no_jobs = aggregate["unique_job_count"].isna()
    unit_totals = ["proposed_units_total", "existing_units_total", "net_new_units"]
    aggregate.loc[no_jobs, unit_totals] = 0
    for column in ["unique_job_count", "jobs_with_known_units"]:
        aggregate[column] = aggregate[column].fillna(0).astype(int)
    q1, q3 = aggregate["filing_count"].quantile([0.25, 0.75])
    aggregate["is_outlier_zip_year"] = aggregate["filing_count"] > q3 + 1.5 * (q3 - q1)
    aggregate = aggregate.reset_index().sort_values(keys).reset_index(drop=True)
    assert aggregate["filing_count"].sum() == len(frame)
    assert aggregate["unique_job_count"].sum() == frame["job_id"].nunique()
    assert aggregate["jobs_with_known_units"].sum() == len(latest)
    assert np.isclose(aggregate["proposed_units_total"].sum(), latest["proposed_dwelling_units"].sum())
    assert np.isclose(aggregate["existing_units_total"].sum(), latest["existing_dwelling_units"].sum())
    assert not aggregate.duplicated(keys).any()
    return aggregate, jobs.reset_index()
