import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import osmnx as ox
import requests
from shapely.geometry import Point
from shapely.strtree import STRtree

BASE_GRAPH = Path(__file__).resolve().parent.parent / "data" / "warsaw_walk_base.json"
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "warsaw_node_scores.json"
PLACE = "Warsaw, Poland"
METRIC_CRS = 2180
GREENERY_RADIUS_M = 50
LIGHTING_RADIUS_M = 50
GIOS_BASE = "https://api.gios.gov.pl/pjp-api/v1/rest"


def load_nodes():
    return json.loads(BASE_GRAPH.read_text(encoding="utf-8"))["nodes"]


def nodes_to_gdf(nodes):
    return gpd.GeoDataFrame(
        {"id": [n["id"] for n in nodes]},
        geometry=[Point(n["lng"], n["lat"]) for n in nodes],
        crs="EPSG:4326",
    ).to_crs(epsg=METRIC_CRS)


def distance_scores(points, features, radius_m):
    feature_geoms = features.geometry.values
    tree = STRtree(feature_geoms)
    point_geoms = points.geometry.values
    nearest_idx = tree.nearest(point_geoms)
    distances = np.array([
        p.distance(feature_geoms[i])
        for p, i in zip(point_geoms, nearest_idx)
    ])
    scores = np.clip(1 - distances / radius_m, 0.0, 1.0).round(6).tolist()
    return dict(zip(points["id"].values, scores))


def greenery_scores(points):
    tags = {
        "leisure": ["park", "garden"],
        "landuse": ["forest", "grass", "meadow"],
        "natural": ["wood", "grassland"],
    }
    features = ox.features_from_place(PLACE, tags=tags).to_crs(epsg=METRIC_CRS)
    features = features[features.geometry.type.isin(["Polygon", "MultiPolygon"])]
    return distance_scores(points, features, GREENERY_RADIUS_M)


def lighting_scores(points):
    features = ox.features_from_place(PLACE, tags={"lit": "yes"}).to_crs(epsg=METRIC_CRS)
    features = features[features.geometry.type != "Point"]
    return distance_scores(points, features, LIGHTING_RADIUS_M)


def air_quality_scores(nodes):
    all_stations = []
    page = 0
    while True:
        resp = requests.get(f"{GIOS_BASE}/station/findAll", params={"size": 100, "page": page}).json()
        all_stations.extend(resp.get("Lista stacji pomiarowych", []))
        total = resp.get("totalPages") or 1
        page += 1
        if page >= total:
            break

    warsaw = [s for s in all_stations if "Warszaw" in (s.get("Nazwa miasta") or "")]

    data = []
    for s in warsaw:
        resp = requests.get(f"{GIOS_BASE}/aqindex/getIndex/{s['Identyfikator stacji']}").json()
        level = (resp.get("AqIndex") or {}).get("Wartość indeksu")
        if level is not None and level >= 0:
            data.append((float(s["WGS84 φ N"]), float(s["WGS84 λ E"]), level))

    if not data:
        raise RuntimeError("GIOS returned no valid air quality data for Warsaw stations")

    scores = {}
    for n in nodes:
        weights, values = [], []
        for slat, slng, lvl in data:
            d2 = (slat - n["lat"]) ** 2 + (slng - n["lng"]) ** 2
            if d2 < 1e-12:
                weights, values = [1.0], [lvl]
                break
            weights.append(1 / d2)
            values.append(lvl)
        interp = sum(w * v for w, v in zip(weights, values)) / sum(weights)
        scores[n["id"]] = round(max(0.0, min(1.0, 1 - interp / 5)), 6)
    return scores


def main():
    nodes = load_nodes()
    print(f"Loaded {len(nodes)} nodes")

    points = nodes_to_gdf(nodes)

    greenery = greenery_scores(points)
    print("Greenery done")

    air = air_quality_scores(nodes)
    print("Air quality done")

    lighting = lighting_scores(points)
    print("Lighting done")

    payload = {
        "nodes": [
            {
                "id": n["id"],
                "scores": {
                    "greenery_score": greenery[n["id"]],
                    "air_quality_score": air[n["id"]],
                    "noise_score": lighting[n["id"]],
                },
            }
            for n in nodes
        ]
    }
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved to {OUTPUT}")


if __name__ == "__main__":
    main()
