from __future__ import annotations

from .constants import WARSAW_BOUNDS
from .graph_loader import load_graph
from .models import Coordinate, RoutingError, UserWeights
from .response import build_response_payload, build_route_geometry
from .scoring import COST_MODEL_VERSION
from .search import dijkstra
from .snapping import snap_to_graph


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

    path_steps = dijkstra(
        graph=graph,
        source=start_snap.snapped_node_id or '',
        target=end_snap.snapped_node_id or '',
        weights=weights,
    )

    route_coordinates, route_edges = build_route_geometry(
        graph=graph,
        path_steps=path_steps,
        original_start=start,
        original_end=end,
    )

    response_payload = build_response_payload(
        route_coordinates=route_coordinates,
        route_edges=route_edges,
        start_snap=start_snap,
        end_snap=end_snap,
        algorithm_name='dijkstra',
        cost_model_version=graph.metadata.get('cost_model_version', COST_MODEL_VERSION),
    )
    response_payload['debug']['graph_version'] = graph.metadata.get('graph_version', 'unknown')
    response_payload['debug']['environmental_scores_available'] = bool(
        graph.metadata.get('environmental_scores_available')
    )
    response_payload['debug']['node_score_source'] = graph.metadata.get('node_score_source')
    response_payload['debug']['preference_weights'] = {
        'greenery': weights.greenery,
        'air_quality': weights.air_quality,
        'noise': weights.noise,
    }
    return response_payload
