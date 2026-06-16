from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return min(high, max(low, value))


@dataclass(frozen=True)
class Coordinate:
    lat: float
    lng: float

    def as_leaflet(self) -> dict[str, float]:
        return {'lat': round(self.lat, 6), 'lng': round(self.lng, 6)}


@dataclass(frozen=True)
class EdgeScores:
    greenery_score: float = 0.5
    air_quality_score: float = 0.5
    noise_score: float = 0.5

    def clamped(self) -> 'EdgeScores':
        return EdgeScores(
            greenery_score=clamp(self.greenery_score),
            air_quality_score=clamp(self.air_quality_score),
            noise_score=clamp(self.noise_score),
        )


@dataclass
class GraphNode:
    id: str
    coordinate: Coordinate


@dataclass
class GraphEdge:
    id: str
    u: str
    v: str
    geometry: list[Coordinate]
    length_m: float
    scores: EdgeScores = field(default_factory=EdgeScores)
    bidirectional: bool = True
    tags: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AdjacencyRef:
    edge_id: str
    target: str
    forward: bool


@dataclass
class RoutingGraph:
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: dict[str, GraphEdge] = field(default_factory=dict)
    adjacency: dict[str, list[AdjacencyRef]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    node_spatial_index: dict[tuple[int, int], list[str]] = field(default_factory=dict, repr=False)
    node_projected_xy: dict[str, tuple[float, float]] = field(default_factory=dict, repr=False)
    node_grid_size_m: float = field(default=250.0, repr=False)

    def clone(self) -> 'RoutingGraph':
        return deepcopy(self)

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.id] = node
        self.adjacency.setdefault(node.id, [])

    def add_edge(self, edge: GraphEdge) -> None:
        self.edges[edge.id] = edge
        self.adjacency.setdefault(edge.u, [])
        self.adjacency.setdefault(edge.v, [])
        self.adjacency[edge.u].append(AdjacencyRef(edge_id=edge.id, target=edge.v, forward=True))
        if edge.bidirectional:
            self.adjacency[edge.v].append(AdjacencyRef(edge_id=edge.id, target=edge.u, forward=False))

    def remove_edge(self, edge_id: str) -> None:
        edge = self.edges.pop(edge_id)
        self.adjacency[edge.u] = [ref for ref in self.adjacency[edge.u] if ref.edge_id != edge_id]
        if edge.bidirectional:
            self.adjacency[edge.v] = [ref for ref in self.adjacency[edge.v] if ref.edge_id != edge_id]


@dataclass(frozen=True)
class UserWeights:
    greenery: float = 0.0
    air_quality: float = 0.0
    noise: float = 0.0

    @staticmethod
    def from_payload(payload: dict[str, Any]) -> 'UserWeights':
        return UserWeights(
            greenery=clamp(float(payload.get('greenery', 0.0))),
            air_quality=clamp(float(payload.get('air_quality', 0.0))),
            noise=clamp(float(payload.get('noise', 0.0))),
        )


@dataclass
class SnapResult:
    original: Coordinate
    snapped: Coordinate
    edge_id: str
    distance_m: float
    distance_along_m: float
    snapped_node_id: str | None = None


@dataclass(frozen=True)
class PathStep:
    edge_id: str
    from_node: str
    to_node: str
    forward: bool


@dataclass(frozen=True)
class RoutingError(Exception):
    code: str
    message: str
    status_code: int = 400
