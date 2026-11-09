"""Download the complete 2022-2025 housing window; cache it in data/raw/."""
import io
import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd
import truststore

BASE_URL = "https://data.cityofnewyork.us/resource/w9ak-ipjd.csv"
REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "data" / "raw" / "w9ak-ipjd.csv"

WHERE_CLAUSE = "filing_date >= '2022-01-01T00:00:00' AND filing_date < '2026-01-01T00:00:00'"
PAGE_SIZE = 25_000
MAX_PAGES = 40              # safety stop (1,000,000 rows)

EXPECTED_COLUMNS = [
    "job_filing_number", "filing_date", "filing_status", "borough",
    "block", "lot", "bin", "commmunity_board", "house_no", "street_name",
    "zip", "building_type", "initial_cost", "total_construction_floor_area",
    "existing_stories", "existing_height", "existing_dwelling_units",
    "proposed_no_of_stories", "proposed_height", "proposed_dwelling_units",
    "latitude", "longitude", "council_district", "census_tract", "nta",
    "first_permit_date", "approved_date", "current_status_date",
    "work_on_floor", "apt_condo_no_s", "special_inspection_agency_number",
    "signoff_date", "built_1_information_value", "built_2_information_value",
    "built_2_a_information_value", "built_2_b_information_value",
    "postcode", "job_type",
]


def fetch_csv(params):
    """Fetch public data with system certificate validation; errors stay explicit."""
    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "nyc-housing-transport-student-project"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(
                request, timeout=180, context=truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ) as response:
                return pd.read_csv(io.BytesIO(response.read()), low_memory=False)
        except urllib.error.HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise
            print(f"API HTTP {error.code}; retry {attempt + 1}/2 in {2 ** (attempt + 1)}s.", flush=True)
            time.sleep(2 ** (attempt + 1))


def main():
    expected_count = int(fetch_csv({"$select": "count(*)", "$where": WHERE_CLAUSE}).iloc[0, 0])
    print(f"Downloading all {expected_count:,} filings in 2022-2025.", flush=True)
    pages = []
    for page_number in range(MAX_PAGES):
        page = fetch_csv({
            "$select": ",".join(EXPECTED_COLUMNS),
            "$where": WHERE_CLAUSE,
            "$order": ":id",                      # stable order so paging is repeatable
            "$limit": PAGE_SIZE,
            "$offset": page_number * PAGE_SIZE,
        })
        pages.append(page)
        print(f"   page {page_number + 1}: {len(page):,} rows", flush=True)
        if len(page) < PAGE_SIZE:
            break

    else:
        raise RuntimeError("Pagination safety limit reached; refusing to save a truncated dataset.")
    data = pd.concat(pages, ignore_index=True)
    if len(data) != expected_count:
        raise RuntimeError(f"Expected {expected_count} rows, downloaded {len(data)}; retry the download.")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(OUTPUT_PATH, index=False)
    OUTPUT_PATH.with_suffix(".json").write_text(json.dumps({
        "source": BASE_URL, "where": WHERE_CLAUSE, "rows": len(data),
        "downloaded_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "columns": list(data.columns),
    }, indent=2), encoding="utf-8")

    print(f"\n3) Saved {len(data):,} rows x {data.shape[1]} columns to:\n   {OUTPUT_PATH}")
    years = pd.to_datetime(data["filing_date"], errors="coerce").dt.year
    print("\nFilings per year:\n" + years.value_counts().sort_index().to_string())
    print("Next: re-run notebooks/Member1_Housing.ipynb from the top.")


if __name__ == "__main__":
    main()
