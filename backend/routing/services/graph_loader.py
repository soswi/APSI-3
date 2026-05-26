from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock

from .models import Coordinate, EdgeScores, GraphEdge, GraphNode, RoutingGraph

_GRAPH_CACHE: RoutingGraph | None = None
_GRAPH_LOCK = Lock()
_DEFAULT_GRAPH_FILE = Path(__file__).resolve().parent.parent / 'data' / 'warsaw_walk_enriched.json'
_BASE_GRAPH_FILE = Path(__file__).resolve().parent.parent / 'data' / 'warsaw_walk_base.json'


def _graph_file() -> Path:
    override = os.environ.get('ROUTING_GRAPH_FILE')
    return Path(override) if override else _DEFAULT_GRAPH_FILE


def _deserialize_graph(payload: dict) -> RoutingGraph:
    raw_edges = payload.get('edges', [])
    graph = RoutingGraph(
        metadata={
            **payload.get('metadata', {}),
            'environmental_scores_available': any(
                isinstance(raw_edge.get('scores'), dict)
                for raw_edge in raw_edges
            ),
        }
    )

    for raw_node in payload.get('nodes', []):
        graph.add_node(
            GraphNode(
                id=raw_node['id'],
                coordinate=Coordinate(lat=float(raw_node['lat']), lng=float(raw_node['lng'])),
            )
        )

    for raw_edge in raw_edges:
        graph.add_edge(
            GraphEdge(
                id=raw_edge['id'],
                u=raw_edge['u'],
                v=raw_edge['v'],
                geometry=[
                    Coordinate(lat=float(coordinate['lat']), lng=float(coordinate['lng']))
                    for coordinate in raw_edge['geometry']
                ],
                length_m=float(raw_edge['length_m']),
                scores=EdgeScores(
                    greenery_score=float(raw_edge.get('scores', {}).get('greenery_score', 0.5)),
                    air_quality_score=float(raw_edge.get('scores', {}).get('air_quality_score', 0.5)),
                    noise_score=float(raw_edge.get('scores', {}).get('noise_score', 0.5)),
                ),
                bidirectional=bool(raw_edge.get('bidirectional', True)),
            )
        )

    return graph


def load_graph() -> RoutingGraph:
    global _GRAPH_CACHE

    with _GRAPH_LOCK:
        if _GRAPH_CACHE is not None:
            return _GRAPH_CACHE

        graph_file = _graph_file()
        if not graph_file.exists() and graph_file == _DEFAULT_GRAPH_FILE and _BASE_GRAPH_FILE.exists():
            graph_file = _BASE_GRAPH_FILE

        if not graph_file.exists():
            raise FileNotFoundError(
                f'Graph file not found: {graph_file}. Prepare warsaw_walk_base.json or warsaw_walk_enriched.json before running routing.'
            )

        payload = json.loads(graph_file.read_text(encoding='utf-8'))
        _GRAPH_CACHE = _deserialize_graph(payload)
        return _GRAPH_CACHE


def reset_graph_cache() -> None:
    global _GRAPH_CACHE
    with _GRAPH_LOCK:
        _GRAPH_CACHE = None
