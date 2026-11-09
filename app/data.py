"""Validated selections and shared dashboard/research calculations."""
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
import re

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "clean" / "integrated_dataset.csv"
BOROUGHS = ("BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND")
YEARS = (2022, 2023, 2024, 2025)
HOUSING_METRICS = {
    "filing_count": "Application filings",
    "new_construction_filings": "New-building filings",
    "permit_issued_count": "Permit / LOC-status filings",
}
TRANSPORT_METRICS = {
    "crash_count": "Recorded serious crashes",
    "severe_injuries_total": "People seriously injured",
    "fatalities_total": "Fatalities",
}
QUARTILES = ("Q1 / lowest", "Q2", "Q3", "Q4 / highest")
BENCHMARK_NOTE = (
    "Groups use each year's NYC-wide, housing-covered ZIPs, before your filters. "
    "High means a positive value at or above the 75th percentile; ties stay together, "
    "so the high group is not necessarily exactly 25% of ZIPs."
)


class SelectionError(ValueError):
    """A selection/search that the visitor can correct."""


@dataclass(frozen=True)
class Selection:
    boroughs: tuple[str, ...] = BOROUGHS
    years: tuple[int, ...] = YEARS
    housing_metric: str = "filing_count"
    transport_metric: str = "crash_count"
    mode: str = "filters"
    query: str = ""
    zip_codes: tuple[str, ...] = ()

    def to_dict(self):
        return asdict(self)


@dataclass
class Report:
    selection: Selection
    rows: pd.DataFrame
    totals: dict
    concentration: pd.DataFrame
    recurrence: pd.DataFrame
    coverage: dict
    crash_covered_zips: frozenset[str]


def load_dataset(path=DATA_PATH):
    frame = pd.read_csv(path, dtype={"zip_code": str})
    required = {
        "zip_code", "year", "borough", "has_housing_data", "has_crash_data",
        "zip_latitude", "zip_longitude", "official_zip_filings", "approximate_zip_filings",
        "net_new_units", "unique_job_count", "jobs_with_known_units",
        "night_crash_count", "crashes_with_known_time",
        *HOUSING_METRICS, *TRANSPORT_METRICS,
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Integrated dataset is missing columns: {sorted(missing)}")
    if frame.empty or frame.duplicated(["zip_code", "year"]).any():
        raise ValueError("Integrated dataset must be nonempty with unique ZIP/year keys.")
    if not frame["zip_code"].str.fullmatch(r"\d{5}", na=False).all():
        raise ValueError("Every ZIP must be five-digit text.")
    if (not pd.api.types.is_integer_dtype(frame["year"]) or not frame["year"].isin(YEARS).all()
            or not frame["borough"].isin(BOROUGHS).all()):
        raise ValueError("Dataset contains unsupported years or borough labels.")
    if frame.groupby("zip_code")["borough"].nunique().gt(1).any():
        raise ValueError("A ZIP maps to conflicting boroughs.")
    for flag in ["has_housing_data", "has_crash_data"]:
        if not pd.api.types.is_bool_dtype(frame[flag]) or frame[flag].isna().any():
            raise ValueError(f"{flag} must contain explicit True/False values.")
    numeric = [*HOUSING_METRICS, *TRANSPORT_METRICS, "official_zip_filings", "approximate_zip_filings",
               "unique_job_count", "jobs_with_known_units", "night_crash_count", "crashes_with_known_time"]
    for column in numeric:
        if not pd.api.types.is_numeric_dtype(frame[column]):
            raise ValueError(f"{column} must be numeric.")
        values = frame[column].dropna()
        if not np.isfinite(values).all() or (values < 0).any() or values.mod(1).ne(0).any():
            raise ValueError(f"{column} must contain finite, non-negative whole counts.")
    units = frame["net_new_units"]
    if not pd.api.types.is_numeric_dtype(units):
        raise ValueError("net_new_units must be numeric.")
    known_units = units.dropna()
    if not np.isfinite(known_units).all() or known_units.mod(1).ne(0).any():
        raise ValueError("net_new_units must contain finite whole counts or missing values.")
    known = frame["has_housing_data"]
    if frame.loc[known, list(HOUSING_METRICS)].isna().any().any():
        raise ValueError("Housing-covered rows have unknown required filing counts.")
    if frame.loc[~known, list(HOUSING_METRICS)].notna().any().any():
        raise ValueError("Unknown housing coverage must remain missing, not zero.")
    if frame[list(TRANSPORT_METRICS)].isna().any().any():
        raise ValueError("Dashboard event counts must be known or documented structural zeros.")
    if frame.loc[~frame["has_crash_data"], list(TRANSPORT_METRICS)].ne(0).any().any():
        raise ValueError("Rows without retained crash records must have structural zero counts.")
    provenance = frame["official_zip_filings"] + frame["approximate_zip_filings"]
    if not provenance[known].eq(frame.loc[known, "filing_count"]).all():
        raise ValueError("Housing ZIP provenance counts do not reconcile.")
    latitude, longitude = frame["zip_latitude"], frame["zip_longitude"]
    if not latitude.isna().equals(longitude.isna()):
        raise ValueError("Map coordinates must be present or missing as a pair.")
    located = latitude.notna()
    if not (latitude[located].between(40.45, 40.95) & longitude[located].between(-74.30, -73.65)).all():
        raise ValueError("Map coordinates fall outside the NYC screening bounds.")
    return frame.sort_values(["zip_code", "year"]).reset_index(drop=True)


def dataset_fingerprint(path=DATA_PATH):
    return sha256(Path(path).read_bytes()).hexdigest()[:12]


def validate_selection(selection, frame):
    if (not selection.boroughs or not all(isinstance(b, str) for b in selection.boroughs)
            or not set(selection.boroughs).issubset(BOROUGHS)):
        raise SelectionError("Select at least one valid borough.")
    if (not selection.years or any(type(y) is not int for y in selection.years)
            or not set(selection.years).issubset(YEARS)):
        raise SelectionError("Select at least one year between 2022 and 2025.")
    if not isinstance(selection.housing_metric, str) or selection.housing_metric not in HOUSING_METRICS:
        raise SelectionError("Choose a supported housing measure.")
    if not isinstance(selection.transport_metric, str) or selection.transport_metric not in TRANSPORT_METRICS:
        raise SelectionError("Choose a supported transportation measure.")
    if not isinstance(selection.mode, str) or selection.mode not in {"filters", "search"}:
        raise SelectionError("Choose dropdown mode or search mode.")
    if not isinstance(selection.query, str) or len(selection.query) > 160:
        raise SelectionError("Search must be text with at most 160 characters.")
    if not all(isinstance(z, str) for z in selection.zip_codes):
        raise SelectionError("ZIP codes must be five-digit text.")
    if len(set(selection.years)) != len(selection.years):
        raise SelectionError("Select each year only once.")
    if any(z not in set(frame["zip_code"]) for z in selection.zip_codes):
        raise SelectionError("A requested ZIP does not exist in this dataset.")
    return selection


def selection_from_controls(frame, boroughs, years, housing_metric, transport_metric, mode, query):
    if query is not None and not isinstance(query, str):
        raise SelectionError("Search must be text.")
    selection = Selection(
        tuple(boroughs or ()), tuple(years or ()), housing_metric, transport_metric,
        mode, (query or "").strip(),
    )
    if mode != "search":
        validate_selection(selection, frame)
    elif (not isinstance(housing_metric, str) or not isinstance(transport_metric, str)
          or housing_metric not in HOUSING_METRICS or transport_metric not in TRANSPORT_METRICS):
        raise SelectionError("Choose supported housing and transportation measures.")
    return parse_search(selection, frame) if mode == "search" else selection


def parse_search(selection, frame):
    query = selection.query
    if not query:
        raise SelectionError("Enter a ZIP or a supported phrase, for example Brooklyn 2024 new buildings.")
    if len(query) > 160:
        raise SelectionError("Keep the search to 160 characters or fewer.")
    remaining = re.sub(r"[-,;]+", " ", query.casefold())
    zip_codes = tuple(dict.fromkeys(re.findall(r"(?<!\d)\d{5}(?!\d)", remaining)))
    remaining = re.sub(r"(?<!\d)\d{5}(?!\d)", " ", remaining)
    years = tuple(dict.fromkeys(int(y) for y in re.findall(r"(?<!\d)20\d{2}(?!\d)", remaining)))
    remaining = re.sub(r"(?<!\d)20\d{2}(?!\d)", " ", remaining)
    boroughs = []
    for phrase, borough in [
        ("staten island", "STATEN ISLAND"), ("the bronx", "BRONX"),
        ("brooklyn", "BROOKLYN"), ("manhattan", "MANHATTAN"),
        ("queens", "QUEENS"), ("bronx", "BRONX"),
    ]:
        pattern = rf"\b{phrase}\b"
        if re.search(pattern, remaining):
            boroughs.append(borough)
            remaining = re.sub(pattern, " ", remaining)

    def extract_metric(phrases, default, domain):
        nonlocal remaining
        matches = set()
        for phrase, metric in phrases:
            pattern = rf"\b{phrase}\b"
            if re.search(pattern, remaining):
                matches.add(metric)
                remaining = re.sub(pattern, " ", remaining)
        if len(matches) > 1:
            raise SelectionError(f"Search names multiple {domain} measures; choose just one.")
        return next(iter(matches)) if matches else default

    housing = extract_metric([
        ("new buildings", "new_construction_filings"), ("new building", "new_construction_filings"),
        ("new construction", "new_construction_filings"), ("permits", "permit_issued_count"),
        ("applications", "filing_count"), ("filings", "filing_count"),
    ], selection.housing_metric, "housing")
    transport = extract_metric([
        ("serious crashes", "crash_count"), ("crashes", "crash_count"),
        ("severe injuries", "severe_injuries_total"), ("injuries", "severe_injuries_total"),
        ("fatalities", "fatalities_total"), ("deaths", "fatalities_total"),
    ], selection.transport_metric, "transportation")
    remaining = re.sub(r"\b(and|in|for)\b", " ", remaining).strip()
    if remaining:
        raise SelectionError(f"Unrecognized search text: {remaining!r}. Use a ZIP, borough, year, or supported measure.")
    if not (zip_codes or years or boroughs or housing != selection.housing_metric
            or transport != selection.transport_metric
            or re.search(r"\b(filings|applications|crashes|injuries|fatalities|deaths|permits|new)\b", query.casefold())):
        raise SelectionError("Search needs a ZIP, borough, year, or supported measure.")
    effective = Selection(
        tuple(dict.fromkeys(boroughs)) or selection.boroughs,
        years or selection.years, housing, transport, selection.mode, query, zip_codes,
    )
    return validate_selection(effective, frame)


def selection_from_store(payload, frame):
    if not isinstance(payload, dict) or set(payload) != set(Selection.__dataclass_fields__):
        raise SelectionError("Generate a new report before downloading.")
    for key in ["boroughs", "years", "zip_codes"]:
        if not isinstance(payload[key], (list, tuple)):
            raise SelectionError("Invalid saved selection; generate a new report.")
    if not isinstance(payload["query"], str):
        raise SelectionError("Invalid saved search; generate a new report.")
    selection = Selection(
        tuple(payload["boroughs"]), tuple(payload["years"]),
        payload["housing_metric"], payload["transport_metric"],
        payload["mode"], payload["query"], tuple(payload["zip_codes"]),
    )
    return validate_selection(selection, frame)


def annual_benchmarks(frame, housing_metric, transport_metric):
    """Use full-city annual benchmarks, never recompute ranks after user filters."""
    data = frame.copy()
    eligible = data["has_housing_data"]
    data["housing_quartile"] = pd.Series(pd.NA, index=data.index, dtype="string")
    for flag in ["housing_high", "transport_high", "joint_high"]:
        data[flag] = pd.Series(pd.NA, index=data.index, dtype="boolean")
    for _, group in data.loc[eligible].groupby("year"):
        housing = group[housing_metric]
        transport = group[transport_metric]
        q25, q50, q75 = housing.quantile([.25, .5, .75])
        labels = np.select(
            [housing.gt(0) & housing.ge(q75), housing.gt(0) & housing.ge(q50),
             housing.gt(0) & housing.ge(q25)],
            [QUARTILES[3], QUARTILES[2], QUARTILES[1]], default=QUARTILES[0],
        )
        data.loc[group.index, "housing_quartile"] = labels
        high_h = housing.gt(0) & housing.ge(q75)
        high_t = transport.gt(0) & transport.ge(transport.quantile(.75))
        data.loc[group.index, "housing_high"] = high_h
        data.loc[group.index, "transport_high"] = high_t
        data.loc[group.index, "joint_high"] = high_h & high_t
    return data


def build_report(frame, selection):
    validate_selection(selection, frame)
    annotated = annual_benchmarks(frame, selection.housing_metric, selection.transport_metric)
    mask = annotated["borough"].isin(selection.boroughs) & annotated["year"].isin(selection.years)
    if selection.zip_codes:
        mask &= annotated["zip_code"].isin(selection.zip_codes)
    rows = annotated.loc[mask].copy()
    if rows.empty:
        raise SelectionError("No records match this combination. Try another borough, year or ZIP.")
    totals = {}
    for metric in [*HOUSING_METRICS, *TRANSPORT_METRICS]:
        value = rows[metric].sum(min_count=1)
        totals[metric] = None if pd.isna(value) else int(value)
    totals["zip_count"] = rows["zip_code"].nunique()
    known = rows[rows["has_housing_data"]].copy()
    concentration = known.groupby("housing_quartile").agg(
        zip_years=("zip_code", "size"),
        transport_events=(selection.transport_metric, "sum"),
    ).reindex(QUARTILES, fill_value=0)
    denominator = concentration["transport_events"].sum()
    concentration["event_share"] = concentration["transport_events"] / denominator if denominator > 0 else np.nan
    concentration["record_share"] = concentration["zip_years"] / len(known) if len(known) else np.nan
    recurrence = known.groupby(["zip_code", "borough"]).agg(
        observed_years=("year", "nunique"), joint_years=("joint_high", "sum"),
        housing_total=(selection.housing_metric, "sum"),
    ).reset_index().sort_values(
        ["joint_years", "housing_total", "zip_code"], ascending=[False, False, True],
    )
    located = rows["zip_latitude"].notna()
    coverage = {
        "rows": len(rows),
        "unknown_housing_rows": int((~rows["has_housing_data"]).sum()),
        "structural_crash_zeros": int((~rows["has_crash_data"]).sum()),
        "approximate_zip_filings": int(rows["approximate_zip_filings"].sum()),
        "missing_map_zips": sorted(rows.loc[~located, "zip_code"].unique().tolist()),
        "known_housing_rows": len(known),
    }
    crash_covered_zips = frozenset(frame.loc[frame["has_crash_data"], "zip_code"])
    return Report(selection, rows, totals, concentration, recurrence, coverage, crash_covered_zips)


def report_csv(report):
    """Export the last applied rows, preserving unknowns and provenance flags."""
    return report.rows.to_csv(index=False, lineterminator="\n")
