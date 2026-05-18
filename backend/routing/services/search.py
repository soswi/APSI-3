from __future__ import annotations

import heapq

from .models import PathStep, RoutingError, RoutingGraph, UserWeights
from .scoring import edge_cost


def dijkstra(graph: RoutingGraph, source: str, target: str, weights: UserWeights) -> list[PathStep]:
    queue: list[tuple[float, str]] = [(0.0, source)]
    distances = {source: 0.0}
    previous: dict[str, tuple[str, PathStep]] = {}

    while queue:
        current_distance, node_id = heapq.heappop(queue)

        if node_id == target:
            break

        if current_distance > distances.get(node_id, float('inf')):
            continue

        for adjacency_ref in graph.adjacency.get(node_id, []):
            graph_edge = graph.edges[adjacency_ref.edge_id]
            next_distance = current_distance + edge_cost(graph_edge, weights)

            if next_distance < distances.get(adjacency_ref.target, float('inf')):
                distances[adjacency_ref.target] = next_distance
                previous[adjacency_ref.target] = (
                    node_id,
                    PathStep(
                        edge_id=adjacency_ref.edge_id,
                        from_node=node_id,
                        to_node=adjacency_ref.target,
                        forward=adjacency_ref.forward,
                    ),
                )
                heapq.heappush(queue, (next_distance, adjacency_ref.target))

    if target not in distances:
        raise RoutingError(
            code='NO_ROUTE_FOUND',
            message='No connected walking route was found between the selected points.',
            status_code=404,
        )

    path_steps: list[PathStep] = []
    cursor = target

    while cursor != source:
        parent_node, step = previous[cursor]
        path_steps.append(step)
        cursor = parent_node

    path_steps.reverse()
    return path_steps
