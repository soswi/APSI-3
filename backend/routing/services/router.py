from __future__ import annotations

from .constants import WARSAW_BOUNDS
from .graph_loader import load_graph
from .models import Coordinate, RoutingError, UserWeights
from .response import build_response_payload, build_route_geometry
from .search import dijkstra
from .snapping import create_temporary_overlay, snap_to_graph


def _coordinate_from_payload(payload: dict) -> Coordinate:
    return Coordinate(lat=float(payload['lat']), lng=float(payload['lng']))


def _ensure_inside_service_area(point: Coordinate) -> None:
    if not (
        WARSAW_BOUNDS['min_lat'] <= point.lat <= WARSAW_BOUNDS['max_lat']
        and WARSAW_BOUNDS['min_lng'] <= point.lng <= WARSAW_BOUNDS['max_lng']
    ):
        raise RoutingError(
            code='POINT_OUTSIDE_SERVICE_AREA',
            message='Routing is currently supported only in Warsaw.',
            status_code=400,
        )


def calculate_route(start_payload: dict, end_payload: dict, weights_payload: dict | None = None) -> dict:
    graph = load_graph()

    start = _coordinate_from_payload(start_payload)
    end = _coordinate_from_payload(end_payload)
    _ensure_inside_service_area(start)
    _ensure_inside_service_area(end)

    weights = UserWeights.from_payload(weights_payload or {})

    start_snap = snap_to_graph(graph, start, 'start')
    end_snap = snap_to_graph(graph, end, 'end')
    overlay_graph, resolved_nodes = create_temporary_overlay(
        base_graph=graph,
        snap_points={'start': start_snap, 'end': end_snap},
    )

    path_steps = dijkstra(
        graph=overlay_graph,
        source=resolved_nodes['start'],
        target=resolved_nodes['end'],
        weights=weights,
    )

    route_coordinates, route_edges = build_route_geometry(
        graph=overlay_graph,
        path_steps=path_steps,
        original_start=start,
        original_end=end,
    )

    return build_response_payload(
        route_coordinates=route_coordinates,
        route_edges=route_edges,
        start_snap=start_snap,
        end_snap=end_snap,
        algorithm_name='dijkstra',
        cost_model_version=overlay_graph.metadata.get('cost_model_version', 'development-v1'),
    )
