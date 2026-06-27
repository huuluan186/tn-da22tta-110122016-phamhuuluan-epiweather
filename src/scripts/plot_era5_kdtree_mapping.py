"""Vẽ Hình 3.4 — minh họa ánh xạ KD-tree nearest centroid từ lưới ERA5 thật.

Dùng lưới điểm ERA5 thật (data/weather/era5_raw/era5_2010) và centroid quốc gia
tính từ ranh giới quốc gia thật (tải GeoJSON), không dùng số liệu giả lập.
Chỉ một số quốc gia đại diện (một quốc gia mỗi châu lục) được nối tới điểm lưới
gần nhất để hình dễ đọc — KD-tree vẫn build trên toàn bộ lưới thật.
"""
import json
import urllib.request

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from scipy.spatial import cKDTree
from shapely.geometry import shape

OUTPUT_FILE = "docs/diagrams/hinh_3_4_kdtree_mapping.png"
ERA5_SAMPLE_FILE = "data/weather/era5_raw/era5_2010/data_stream-oper_stepType-instant.nc"
WORLD_GEOJSON_URL = (
    "https://raw.githubusercontent.com/python-visualization/folium/"
    "main/examples/data/world-countries.json"
)
REPRESENTATIVE_COUNTRIES = [
    "Vietnam",
    "Brazil",
    "Nigeria",
    "France",
    "Australia",
    "Canada",
]


def load_world_boundaries() -> gpd.GeoDataFrame:
    with urllib.request.urlopen(WORLD_GEOJSON_URL, timeout=15) as resp:
        data = json.loads(resp.read())
    records = [
        {"name": f["properties"]["name"], "geometry": shape(f["geometry"])}
        for f in data["features"]
    ]
    return gpd.GeoDataFrame(records, crs="EPSG:4326")


def load_era5_grid_points():
    ds = xr.open_dataset(ERA5_SAMPLE_FILE)
    lats = ds["latitude"].values
    lons = ds["longitude"].values
    lons_180 = ((lons + 180) % 360) - 180
    lon_grid, lat_grid = [g.ravel() for g in np.meshgrid(lons_180, lats)]
    return lon_grid, lat_grid


def plot_world_overview(ax, world, grid_lon, grid_lat, tree):
    world.boundary.plot(ax=ax, color="#9aa0a6", linewidth=0.4)

    step = 3
    ax.scatter(
        grid_lon[::step], grid_lat[::step],
        s=2, c="#a5d8ff", alpha=0.6,
    )

    zoom_target = None
    for name in REPRESENTATIVE_COUNTRIES:
        match = world[world["name"] == name]
        if match.empty:
            print(f"[WARN] Không tìm thấy quốc gia '{name}' trong GeoJSON, bỏ qua.")
            continue
        centroid = match.geometry.iloc[0].centroid
        c_lon, c_lat = centroid.x, centroid.y
        _, idx = tree.query([c_lon, c_lat])
        n_lon, n_lat = grid_lon[idx], grid_lat[idx]

        ax.plot([c_lon, n_lon], [c_lat, n_lat], color="#e8590c", linewidth=1.2, zorder=4)
        ax.scatter([c_lon], [c_lat], s=45, c="#1864ab", marker="*", zorder=5)
        ax.scatter([n_lon], [n_lat], s=35, c="#e8590c", marker="o", zorder=5)
        ax.annotate(name, (c_lon, c_lat), textcoords="offset points",
                    xytext=(5, 5), fontsize=8, color="#1864ab")
        if name == "Vietnam":
            zoom_target = (c_lon, c_lat, n_lon, n_lat)

    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xlabel("Kinh độ")
    ax.set_ylabel("Vĩ độ")
    ax.set_title("(a) Toàn cầu — 6 quốc gia đại diện")
    ax.scatter([], [], s=8, c="#a5d8ff", label="Điểm lưới ERA5 (1°×1°)")
    ax.scatter([], [], s=45, c="#1864ab", marker="*", label="Centroid quốc gia")
    ax.scatter([], [], s=35, c="#e8590c", marker="o", label="Điểm lưới ERA5 gần nhất")
    ax.legend(loc="lower left", fontsize=7, framealpha=0.9)
    return zoom_target


def plot_zoom_inset(ax, world, grid_lon, grid_lat, zoom_target):
    c_lon, c_lat, n_lon, n_lat = zoom_target
    pad = 4
    mask = (
        (grid_lon >= c_lon - pad) & (grid_lon <= c_lon + pad)
        & (grid_lat >= c_lat - pad) & (grid_lat <= c_lat + pad)
    )

    world.plot(ax=ax, color="#e9ecef", edgecolor="#9aa0a6", linewidth=0.6)
    ax.scatter(grid_lon[mask], grid_lat[mask], s=22, c="#a5d8ff",
               edgecolor="#4a9eed", linewidth=0.4, zorder=3,
               label="Điểm lưới ERA5 (1°×1°)")
    ax.plot([c_lon, n_lon], [c_lat, n_lat], color="#e8590c", linewidth=1.5, zorder=4)
    ax.scatter([c_lon], [c_lat], s=160, c="#1864ab", marker="*", zorder=5,
               label="Centroid quốc gia (Việt Nam)")
    ax.scatter([n_lon], [n_lat], s=90, c="#e8590c", marker="o", zorder=5,
               edgecolor="#1e1e1e", linewidth=0.6,
               label="Điểm lưới ERA5 gần nhất")

    ax.set_xlim(c_lon - pad, c_lon + pad)
    ax.set_ylim(c_lat - pad, c_lat + pad)
    ax.set_xlabel("Kinh độ")
    ax.set_ylabel("Vĩ độ")
    ax.set_title("(b) Cận cảnh Việt Nam — khoảng cách centroid → điểm lưới gần nhất")
    ax.legend(loc="upper left", fontsize=7, framealpha=0.9)


def main():
    world = load_world_boundaries()
    grid_lon, grid_lat = load_era5_grid_points()
    tree = cKDTree(list(zip(grid_lon, grid_lat)))

    fig, (ax_world, ax_zoom) = plt.subplots(1, 2, figsize=(14, 6))
    zoom_target = plot_world_overview(ax_world, world, grid_lon, grid_lat, tree)
    if zoom_target is not None:
        plot_zoom_inset(ax_zoom, world, grid_lon, grid_lat, zoom_target)

    fig.suptitle("Hình 3.4 — Ánh xạ KD-tree nearest centroid: quốc gia → điểm lưới ERA5", y=1.02)
    fig.tight_layout()
    fig.savefig(OUTPUT_FILE, dpi=200, bbox_inches="tight")
    print(f"[DONE] Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
