"""Approximate a building ZIP only when the official housing postcode is unavailable.

Use the nearest retained SIRTA crash with a ZIP and coordinates, within the supplied
degree-distance limit. This is not a boundary lookup; it may misclassify border areas
or omit places with no nearby retained crashes. A crash-level self-test is not a
validated building-level accuracy estimate. housing_pipeline.py applies this helper
only to missing/invalid official postcodes and records the assignment method.
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
    out["zip_code"] = pd.Series(np.nan, index=out.index, dtype=object)
    if crashes.empty:
        raise ValueError("ZIP assignment requires reference crashes with ZIPs and coordinates.")
    if not usable.any():
        print(f"ZIP assigned to 0 filings: all {len(out):,} targets lack coordinates.")
        return out

    nn = NearestNeighbors(n_neighbors=1).fit(crashes[["latitude", "longitude"]].to_numpy())
    distance, index = nn.kneighbors(np.c_[lat[usable], lon[usable]])
    zips = crashes["zip_code"].to_numpy()[index[:, 0]].astype(object)
    zips[distance[:, 0] > max_distance_deg] = np.nan

    out.loc[usable, "zip_code"] = zips
    share = out["zip_code"].notna().mean()
    print(f"ZIP assigned to {share:.1%} of filings ({out['zip_code'].isna().sum():,} left missing).")
    return out
