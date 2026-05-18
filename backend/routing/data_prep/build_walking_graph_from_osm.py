from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import networkx as nx
import osmnx as ox
from shapely.geometry import LineString

WARSAW_PLACE_NAME = "Warsaw, Poland"
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "data" / "warsaw_walk_base.json"
WALK_TAG_FIELDS = (
    "highway",
    "foot",
    "access",
    "sidewalk",
    "surface",
    "name",
    "service",
)
NON_WALKABLE_VALUES = {"no", "private"}


def _remove_clearly_non_walkable_edges(graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
    filtered = graph.copy()
    to_remove: list[tuple[Any, Any, Any]] = []

    for u, v, key, data in filtered.edges(keys=True, data=True):
        foot = str(data.get("foot", "")).lower()
        access = str(data.get("access", "")).lower()

        if foot in NON_WALKABLE_VALUES or access in NON_WALKABLE_VALUES:
            to_remove.append((u, v, key))

    filtered.remove_edges_from(to_remove)
    return filtered


def _largest_connected_component(graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
    if graph.number_of_nodes() == 0:
        raise ValueError("The OSM walking graph is empty.")

    largest_component = max(nx.weakly_connected_components(graph), key=len)
    return graph.subgraph(largest_component).copy()


def _line_coordinates(
    geometry: LineString | None,
    start_lon: float,
    start_lat: float,
    end_lon: float,
    end_lat: float,
) -> list[dict[str, float]]:
    if geometry is None:
        return [
            {"lat": round(start_lat, 6), "lng": round(start_lon, 6)},
            {"lat": round(end_lat, 6), "lng": round(end_lon, 6)},
        ]

    return [
        {"lat": round(lat, 6), "lng": round(lng, 6)}
        for lng, lat in geometry.coords
    ]


def _stringify(value: Any) -> str:
    return str(value)


def build_warsaw_walk_base(output_path: Path, place_name: str = WARSAW_PLACE_NAME) -> Path:
    graph_wgs84 = ox.graph_from_place(
        place_name,
        network_type="walk",
        simplify=True,
        retain_all=True,
        truncate_by_edge=True,
    )
    graph_wgs84 = _remove_clearly_non_walkable_edges(graph_wgs84)
    graph_wgs84 = _largest_connected_component(graph_wgs84)
    graph_metric = ox.project_graph(graph_wgs84)

    nodes_wgs84, edges_wgs84 = ox.graph_to_gdfs(graph_wgs84, nodes=True, edges=True)
    _, edges_metric = ox.graph_to_gdfs(graph_metric, nodes=True, edges=True)

    node_payload = [
        {
            "id": _stringify(node_id),
            "lat": round(node.geometry.y, 6),
            "lng": round(node.geometry.x, 6),
        }
        for node_id, node in nodes_wgs84.iterrows()
    ]

    edge_payload: list[dict[str, Any]] = []

    for edge_index, edge_row in edges_wgs84.iterrows():
        u, v, key = edge_index
        metric_row = edges_metric.loc[edge_index]
        start_node = nodes_wgs84.loc[u]
        end_node = nodes_wgs84.loc[v]

        geometry = edge_row.geometry if isinstance(edge_row.geometry, LineString) else None
        tags = {
            field: edge_row[field]
            for field in WALK_TAG_FIELDS
            if field in edge_row and edge_row[field] not in (None, "")
        }

        edge_payload.append(
            {
                "id": f"{u}-{v}-{key}",
                "u": _stringify(u),
                "v": _stringify(v),
                "geometry": _line_coordinates(
                    geometry=geometry,
                    start_lon=start_node.geometry.x,
                    start_lat=start_node.geometry.y,
                    end_lon=end_node.geometry.x,
                    end_lat=end_node.geometry.y,
                ),
                "length_m": round(float(metric_row.geometry.length), 3),
                # Keep directed edges exactly as OSMnx returned them.
                "bidirectional": False,
                "tags": tags,
            }
        )

    payload = {
        "metadata": {
            "graph_version": "warsaw-walk-base-v1",
            "source": "OpenStreetMap via OSMnx",
            "place_name": place_name,
            "network_type": "walk",
            "simplify": True,
            "edge_mode": "directed_osm_edges",
        },
        "nodes": node_payload,
        "edges": edge_payload,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Warsaw base walking graph from OpenStreetMap.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to the output JSON file.",
    )
    parser.add_argument(
        "--place",
        default=WARSAW_PLACE_NAME,
        help="Place name passed to OSMnx.",
    )
    args = parser.parse_args()

    output_path = build_warsaw_walk_base(output_path=args.output, place_name=args.place)
    print(f"Saved base walking graph to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
