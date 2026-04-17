"""
fetch_osm_features.py
---------------------
Run this script LOCALLY (outside the notebook sandbox) to extract
OpenStreetMap features for each monitoring station.

Requirements:
    pip install osmnx geopandas shapely pandas

Usage:
    python fetch_osm_features.py

Input:
    metadata_coords.csv  — two-column CSV with station coordinates.
                           Generated automatically by 01_data.ipynb (Section 2,
                           first cell) before the OSMnx loop.
                           Columns: stacja, lat, lon

Output:
    metadata5000best.csv — same rows + three new columns:
                               nearest_road_dist_m
                               total_road_length_km
                               building_count
                           Place this file next to 01_data.ipynb before
                           running Section 3 onward.

Notes:
    - Already-computed rows (non-NaN) are skipped on re-run.
    - Progress is saved to metadata5000best.csv after every station
      so the script can be safely interrupted and resumed.
"""

import os
import time

import numpy as np
import pandas as pd
import geopandas as gpd
import osmnx as ox
from shapely.geometry import Point

# ── Configuration ────────────────────────────────────────────────────────────
INPUT_CSV   = "metadata_coords.csv"   # produced by 01_data.ipynb Section 2
OUTPUT_CSV  = "metadata5000best.csv"
BUFFER_M    = 5000                    # buffer radius in metres
SLEEP_S     = 2                       # pause between stations (be polite to OSM)

ox.settings.use_cache   = True
ox.settings.log_console = False
# ─────────────────────────────────────────────────────────────────────────────


def compute_osm_features(lat: float, lon: float, buffer_radius: int = BUFFER_M) -> tuple:
    """
    Extract road and building features from OpenStreetMap within a circular
    buffer around (lat, lon).

    Returns
    -------
    (nearest_road_dist_m, total_road_length_km, building_count)
    All values are np.nan on failure.
    """
    try:
        pt         = Point(lon, lat)
        buffer_poly = ox.utils_geo.buffer_geometry(pt, buffer_radius)

        buffer_3857 = gpd.GeoSeries([buffer_poly], crs="EPSG:4326").to_crs(epsg=3857).iloc[0]
        pt_3857     = gpd.GeoSeries([pt],          crs="EPSG:4326").to_crs(epsg=3857).iloc[0]

        # Roads
        try:
            G = ox.graph_from_point((lat, lon), dist=buffer_radius, network_type="drive")
            _, edges = ox.graph_to_gdfs(G)
            edges    = edges.to_crs(epsg=3857)
            edges_in = edges[edges.geometry.intersects(buffer_3857)]

            total_road_length_km = edges_in.length.sum() / 1000 if not edges_in.empty else np.nan
            nearest_road_dist_m  = edges_in.distance(pt_3857).min() if not edges_in.empty else np.nan
        except Exception as e:
            print(f"    [road error] ({lat}, {lon}): {e}")
            total_road_length_km = np.nan
            nearest_road_dist_m  = np.nan

        # Buildings
        try:
            buildings    = ox.features_from_polygon(buffer_poly, tags={"building": True})
            buildings    = buildings[
                buildings.geometry.geom_type.isin(["Polygon", "MultiPolygon"])
            ].to_crs(epsg=3857)
            buildings_in = buildings[buildings.geometry.intersects(buffer_3857)]
            building_count = len(buildings_in)
        except Exception as e:
            print(f"    [building error] ({lat}, {lon}): {e}")
            building_count = np.nan

        return nearest_road_dist_m, total_road_length_km, building_count

    except Exception as e:
        print(f"    [general error] ({lat}, {lon}): {e}")
        return np.nan, np.nan, np.nan


def main():
    # Load input coordinates
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(
            f"{INPUT_CSV} not found.\n"
            "Run Section 2 of 01_data.ipynb first — it saves this file automatically."
        )

    df = pd.read_csv(INPUT_CSV, index_col=0)
    df.index.name = "stacja"

    # Resume from previous run if output already exists
    if os.path.exists(OUTPUT_CSV):
        df_out = pd.read_csv(OUTPUT_CSV, index_col=0)
        df_out.index.name = "stacja"
        print(f"Resuming from {OUTPUT_CSV}")
    else:
        df_out = df.copy()
        df_out["nearest_road_dist_m"]  = np.nan
        df_out["total_road_length_km"] = np.nan
        df_out["building_count"]       = np.nan

    # Only process rows still missing OSMnx data
    rows_todo = df_out[
        df_out[["nearest_road_dist_m", "total_road_length_km", "building_count"]]
        .isna().any(axis=1)
    ]
    print(f"Stations to process: {len(rows_todo)} / {len(df_out)}\n")

    for i, (station, row) in enumerate(rows_todo.iterrows(), 1):
        print(f"[{i}/{len(rows_todo)}] {station} ({row['lat']:.4f}, {row['lon']:.4f})")
        nr, trl, bc = compute_osm_features(row["lat"], row["lon"])

        df_out.at[station, "nearest_road_dist_m"]  = nr
        df_out.at[station, "total_road_length_km"] = trl
        df_out.at[station, "building_count"]        = bc

        # Save after every station so progress is not lost on interruption
        df_out.to_csv(OUTPUT_CSV)

        remaining_nans = df_out[["nearest_road_dist_m", "total_road_length_km", "building_count"]].isna().any(axis=1).sum()
        print(f"    road_dist={nr:.1f} m  road_len={trl:.1f} km  buildings={bc}  (remaining NaN: {remaining_nans})")

        time.sleep(SLEEP_S)

    print(f"\nDone. Saved {OUTPUT_CSV} ({len(df_out)} stations)")
    nan_count = df_out[["nearest_road_dist_m", "total_road_length_km", "building_count"]].isna().any(axis=1).sum()
    if nan_count:
        print(f"WARNING: {nan_count} stations still have NaN — re-run the script to retry them.")
    else:
        print("All stations have complete OSMnx features.")


if __name__ == "__main__":
    main()
