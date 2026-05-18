from __future__ import annotations

from .constants import DEFAULT_WALKING_SPEED_MPS
from .geometry import dedupe_coordinates, haversine_m
from .models import Coordinate, GraphEdge, PathStep, RoutingGraph, SnapResult
from .scoring import aggregate_route_scores


def build_route_geometry(
    graph: RoutingGraph,
    path_steps: list[PathStep],
    original_start: Coordinate,
    original_end: Coordinate,
) -> tuple[list[Coordinate], list[GraphEdge]]:
    route_coordinates: list[Coordinate] = []
    edges: list[GraphEdge] = []

    for step in path_steps:
        graph_edge = graph.edges[step.edge_id]
        edges.append(graph_edge)
        edge_geometry = graph_edge.geometry if step.forward else list(reversed(graph_edge.geometry))
        if route_coordinates and route_coordinates[-1] == edge_geometry[0]:
            route_coordinates.extend(edge_geometry[1:])
        else:
            route_coordinates.extend(edge_geometry)

    if not route_coordinates:
        route_coordinates = [original_start, original_end]
    else:
        if route_coordinates[0] != original_start:
            route_coordinates.insert(0, original_start)
        if route_coordinates[-1] != original_end:
            route_coordinates.append(original_end)

    return dedupe_coordinates(route_coordinates), edges


def route_distance_m(coordinates: list[Coordinate]) -> float:
    return round(sum(haversine_m(coordinates[index], coordinates[index + 1]) for index in range(len(coordinates) - 1)), 1)


def build_response_payload(
    route_coordinates: list[Coordinate],
    route_edges: list[GraphEdge],
    start_snap: SnapResult,
    end_snap: SnapResult,
    algorithm_name: str,
    cost_model_version: str,
) -> dict:
    distance_m = route_distance_m(route_coordinates)
    return {
        'route': [coordinate.as_leaflet() for coordinate in route_coordinates],
        'distance_m': distance_m,
        'estimated_duration_s': int(distance_m / DEFAULT_WALKING_SPEED_MPS),
        'scores': aggregate_route_scores(route_edges),
        'debug': {
            'start_snapped_distance_m': round(start_snap.distance_m, 2),
            'end_snapped_distance_m': round(end_snap.distance_m, 2),
            'algorithm': algorithm_name,
            'cost_model_version': cost_model_version,
        },
    }
