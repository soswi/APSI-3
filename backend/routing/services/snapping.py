from __future__ import annotations

import math
from collections import defaultdict

from .constants import MAX_SNAP_DISTANCE_M
from .geometry import dedupe_coordinates, haversine_m, local_xy, polyline_length_m, split_polyline_by_distances
from .models import Coordinate, GraphEdge, GraphNode, RoutingError, RoutingGraph, SnapResult


def snap_to_graph(graph: RoutingGraph, point: Coordinate, point_name: str) -> SnapResult:
    if not graph.node_spatial_index or not graph.node_projected_xy:
        raise RoutingError(
            code='GRAPH_INDEX_NOT_READY',
            message='The routing graph index is not available.',
            status_code=503,
        )

    point_x, point_y = local_xy(point)
    grid_size_m = graph.node_grid_size_m
    origin_cell = (int(point_x // grid_size_m), int(point_y // grid_size_m))
    max_ring = max(1, math.ceil(MAX_SNAP_DISTANCE_M / grid_size_m))
    best_node_id: str | None = None
    best_distance_sq = float('inf')

    for ring in range(max_ring + 1):
        candidate_found = False

        for cell_x in range(origin_cell[0] - ring, origin_cell[0] + ring + 1):
            for cell_y in range(origin_cell[1] - ring, origin_cell[1] + ring + 1):
                if ring > 0 and abs(cell_x - origin_cell[0]) < ring and abs(cell_y - origin_cell[1]) < ring:
                    continue

                for node_id in graph.node_spatial_index.get((cell_x, cell_y), []):
                    candidate_found = True
                    node_x, node_y = graph.node_projected_xy[node_id]
                    distance_sq = (node_x - point_x) ** 2 + (node_y - point_y) ** 2
                    if distance_sq < best_distance_sq:
                        best_distance_sq = distance_sq
                        best_node_id = node_id

        if candidate_found and best_node_id is not None:
            break

    if best_node_id is None:
        for node_id, (node_x, node_y) in graph.node_projected_xy.items():
            distance_sq = (node_x - point_x) ** 2 + (node_y - point_y) ** 2
            if distance_sq < best_distance_sq:
                best_distance_sq = distance_sq
                best_node_id = node_id

    if best_node_id is None:
        raise RoutingError(
            code=f'{point_name.upper()}_TOO_FAR_FROM_WALKING_NETWORK',
            message=f'The selected {point_name} point is too far from a walkable path.',
            status_code=400,
        )

    snapped_node = graph.nodes[best_node_id]
    distance_m = haversine_m(point, snapped_node.coordinate)

    if distance_m > MAX_SNAP_DISTANCE_M:
        raise RoutingError(
            code=f'{point_name.upper()}_TOO_FAR_FROM_WALKING_NETWORK',
            message=f'The selected {point_name} point is too far from a walkable path.',
            status_code=400,
        )

    return SnapResult(
        original=point,
        snapped=snapped_node.coordinate,
        edge_id='',
        distance_m=distance_m,
        distance_along_m=0.0,
        snapped_node_id=best_node_id,
    )


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
