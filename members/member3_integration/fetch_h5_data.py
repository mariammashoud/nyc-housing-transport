"""Download the REAL DOB NOW Build Job Application Filings (H5) data for 2022-2025.

WHY THIS SCRIPT EXISTS
Member1_Housing.ipynb (cell 4) tries the NYC Open Data API and, if that fails for any reason,
silently falls back to a local file `data/raw/w9ak-ipjd.csv` that is not in the repository.
This script creates that exact file from the live API, and tells you clearly if something goes wrong
(HTTP error, no internet, a column the notebook expects that does not exist in the real dataset).

USAGE (from the repository root, with the .venv active):
    python members/member3_integration/fetch_h5_data.py

OUTPUT: data/raw/w9ak-ipjd.csv   (data/raw/ is git-ignored, so it is never committed)
"""
import io
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

BASE_URL = "https://data.cityofnewyork.us/resource/w9ak-ipjd.csv"
REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "data" / "raw" / "w9ak-ipjd.csv"

WHERE_CLAUSE = "filing_date >= '2022-01-01T00:00:00' AND filing_date < '2026-01-01T00:00:00'"
PAGE_SIZE = 50_000          # rows per request; the API returns only 1,000 if $limit is not set
MAX_PAGES = 20              # safety stop (1,000,000 rows)

# Columns Member1_Housing.ipynb asks for (SELECT_COLS in cell 4).
EXPECTED_COLUMNS = [
    "job_filing_number", "filing_date", "filing_status", "borough",
    "block", "lot", "bin", "community_board", "house_no", "street_name",
    "zip", "building_type", "initial_cost", "total_construction_floor_area",
    "existing_stories", "existing_height", "existing_dwelling_units",
    "proposed_no_of_stories", "proposed_height", "proposed_dwelling_units",
    "latitude", "longitude", "council_district", "census_tract", "nta",
    "first_permit_date", "approved_date", "current_status_date",
    "work_on_floor", "apt_condo_no_s", "special_inspection_agency_number",
    "signed_off_date", "built_1_information_value", "built_2_information_value",
    "built_2_a_information_value", "built_2_b_information_value",
]


def fetch_csv(params):
    """GET one page from the Socrata API and return it as a DataFrame. Exits with a clear message on failure."""
    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "nyc-housing-transport-student-project"})
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return pd.read_csv(io.BytesIO(response.read()), low_memory=False)
    except urllib.error.HTTPError as error:
        print(f"\nHTTP ERROR {error.code} from the API. Server message:\n{error.read().decode(errors='replace')[:600]}")
    except Exception as error:  # no internet, VPN, SSL, timeout ...
        print(f"\nCONNECTION PROBLEM: {type(error).__name__}: {error}")
        print("Turn off any VPN, check your internet, then run the script again.")
    sys.exit(1)


def main():
    print("1) Asking the API for 5 rows to learn the REAL column names ...")
    sample = fetch_csv({"$limit": 5})
    real_columns = list(sample.columns)
    print(f"   The dataset has {len(real_columns)} columns.")

    missing = [c for c in EXPECTED_COLUMNS if c not in real_columns]
    if missing:
        print(f"\n   WARNING: {len(missing)} column(s) the notebook asks for DO NOT EXIST in the real dataset:")
        for column in missing:
            print(f"     - {column}")
        print("   (The notebook's own API call will fail because of this; the script skips them.)")
    selected = [c for c in EXPECTED_COLUMNS if c in real_columns]

    print(f"\n2) Downloading filings from 2022 to 2025 ({len(selected)} columns, pages of {PAGE_SIZE:,}) ...")
    pages = []
    for page_number in range(MAX_PAGES):
        page = fetch_csv({
            "$select": ",".join(selected),
            "$where": WHERE_CLAUSE,
            "$order": ":id",                      # stable order so paging is repeatable
            "$limit": PAGE_SIZE,
            "$offset": page_number * PAGE_SIZE,
        })
        pages.append(page)
        print(f"   page {page_number + 1}: {len(page):,} rows")
        if len(page) < PAGE_SIZE:
            break

    data = pd.concat(pages, ignore_index=True)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(OUTPUT_PATH, index=False)

    print(f"\n3) Saved {len(data):,} rows x {data.shape[1]} columns to:\n   {OUTPUT_PATH}")
    years = pd.to_datetime(data["filing_date"], errors="coerce").dt.year
    print("\nFilings per year:\n" + years.value_counts().sort_index().to_string())
    print("\nThe snapshot used by Member 1 had 18,500 rows. Tell the team how this number compares.")
    print("Next: re-run notebooks/Member1_Housing.ipynb from the top.")


if __name__ == "__main__":
    main()
