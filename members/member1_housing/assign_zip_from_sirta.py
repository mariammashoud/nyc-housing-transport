"""Give every H5 filing a building ZIP code.

WHY: in DOB NOW Build Job Application Filings the column called `Zip` is the ZIP of the
OWNER'S business address (owners often live elsewhere), NOT the ZIP of the building.
The building location is only given by Borough/Block/Lot/BIN and Latitude/Longitude.

METHOD: SIRTA (Member 2) has ~7,000 crashes with a verified ZIP + coordinates. For each filing we take the
ZIP of the nearest SIRTA crash (1-nearest-neighbour on latitude/longitude). Tested on SIRTA itself
(hide a crash's ZIP, predict it from its neighbours) this recovers the right ZIP about 91 % of the time.
Filings farther than `max_distance_deg` (0.01 degrees, ~1 km) from any crash stay missing.

LIMITATION to write in the notebook: ZIPs near ZIP boundaries can be wrong (about 9 %), and areas with
no crashes get no ZIP. This is an approximation, not an official ZIP lookup.

USAGE (notebook):
    from assign_zip_from_sirta import assign_building_zip
    df_housing = assign_building_zip(df_housing, "data/clean/transport_clean_row_level.csv")
"""
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors


def assign_building_zip(housing, sirta_row_level_csv, lat_col="latitude", lon_col="longitude",
                        max_distance_deg=0.01):
    """Return a copy of `housing` with a new `zip_code` column (5-digit string, NaN if too far)."""
    crashes = pd.read_csv(sirta_row_level_csv, dtype={"zip_code": str}).dropna(
        subset=["zip_code", "latitude", "longitude"])
    out = housing.copy()
    lat = pd.to_numeric(out[lat_col], errors="coerce")
    lon = pd.to_numeric(out[lon_col], errors="coerce")
    usable = lat.notna() & lon.notna()

    nn = NearestNeighbors(n_neighbors=1).fit(crashes[["latitude", "longitude"]].to_numpy())
    distance, index = nn.kneighbors(np.c_[lat[usable], lon[usable]])
    zips = crashes["zip_code"].to_numpy()[index[:, 0]].astype(object)
    zips[distance[:, 0] > max_distance_deg] = np.nan

    out["zip_code"] = pd.Series(np.nan, index=out.index, dtype=object)
    out.loc[usable, "zip_code"] = zips
    share = out["zip_code"].notna().mean()
    print(f"ZIP assigned to {share:.1%} of filings ({out['zip_code'].isna().sum():,} left missing).")
    return out
