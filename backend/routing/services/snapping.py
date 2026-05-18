from __future__ import annotations

from collections import defaultdict

from .constants import MAX_SNAP_DISTANCE_M
from .geometry import dedupe_coordinates, locate_point_on_polyline, polyline_length_m, split_polyline_by_distances
from .models import Coordinate, GraphEdge, GraphNode, RoutingError, RoutingGraph, SnapResult


def snap_to_graph(graph: RoutingGraph, point: Coordinate, point_name: str) -> SnapResult:
    best_result: SnapResult | None = None

    for edge in graph.edges.values():
        snapped, distance_m, distance_along_m = locate_point_on_polyline(point, edge.geometry)
        if best_result is None or distance_m < best_result.distance_m:
            best_result = SnapResult(
                original=point,
                snapped=snapped,
                edge_id=edge.id,
                distance_m=distance_m,
                distance_along_m=distance_along_m,
            )

    if best_result is None or best_result.distance_m > MAX_SNAP_DISTANCE_M:
        raise RoutingError(
            code=f'{point_name.upper()}_TOO_FAR_FROM_WALKING_NETWORK',
            message=f'The selected {point_name} point is too far from a walkable path.',
            status_code=400,
        )

    return best_result


def _temp_node_id(label: str, index: int) -> str:
    return f'temp-{label}-{index}'


def create_temporary_overlay(
    base_graph: RoutingGraph,
    snap_points: dict[str, SnapResult],
) -> tuple[RoutingGraph, dict[str, str]]:
    overlay = base_graph.clone()
    resolved_nodes: dict[str, str] = {}
    grouped_snaps: dict[str, list[tuple[str, SnapResult]]] = defaultdict(list)

    for label, snap in snap_points.items():
        grouped_snaps[snap.edge_id].append((label, snap))

    for edge_id, items in grouped_snaps.items():
        edge = overlay.edges[edge_id]
        unique_splits: list[tuple[float, str, Coordinate]] = []

        for label, snap in sorted(items, key=lambda item: item[1].distance_along_m):
            if snap.distance_along_m <= 1.0:
                resolved_nodes[label] = edge.u
                continue

            if snap.distance_along_m >= edge.length_m - 1.0:
                resolved_nodes[label] = edge.v
                continue

            existing = next(
                ((distance, node_id, coordinate) for distance, node_id, coordinate in unique_splits if abs(distance - snap.distance_along_m) <= 1.0),
                None,
            )

            if existing:
                resolved_nodes[label] = existing[1]
                continue

            node_id = _temp_node_id(label, len(unique_splits))
            overlay.add_node(GraphNode(id=node_id, coordinate=snap.snapped))
            unique_splits.append((snap.distance_along_m, node_id, snap.snapped))
            resolved_nodes[label] = node_id

        if not unique_splits:
            continue

        split_distances = [distance for distance, _, _ in unique_splits]
        split_geometries = split_polyline_by_distances(edge.geometry, split_distances)
        chain_nodes = [edge.u, *[node_id for _, node_id, _ in unique_splits], edge.v]

        overlay.remove_edge(edge_id)

        for index in range(len(chain_nodes) - 1):
            segment_geometry = dedupe_coordinates(split_geometries[index])
            segment_edge = GraphEdge(
                id=f'{edge.id}-split-{index}',
                u=chain_nodes[index],
                v=chain_nodes[index + 1],
                geometry=segment_geometry,
                length_m=polyline_length_m(segment_geometry),
                scores=edge.scores,
                bidirectional=edge.bidirectional,
                tags=dict(edge.tags),
            )
            overlay.add_edge(segment_edge)

    return overlay, resolved_nodes
