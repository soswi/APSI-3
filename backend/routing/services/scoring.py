from .models import EdgeScores, GraphEdge, UserWeights

COST_MODEL_VERSION = 'preference-penalty-v2'

PREFERENCE_STRENGTH = {
    'greenery': 3.0,
    'air_quality': 0.75,
    'noise': 1.0,
}

MAX_ENV_PENALTY = 4.0


def normalized_scores(edge: GraphEdge) -> EdgeScores:
    return edge.scores.clamped()


def preference_intensity(weight: float) -> float:
    return weight * weight


def edge_cost(edge: GraphEdge, weights: UserWeights) -> float:
    scores = normalized_scores(edge)
    penalty_sum = (
        PREFERENCE_STRENGTH['greenery']
        * preference_intensity(weights.greenery)
        * (1.0 - scores.greenery_score)
        + PREFERENCE_STRENGTH['air_quality']
        * preference_intensity(weights.air_quality)
        * (1.0 - scores.air_quality_score)
        + PREFERENCE_STRENGTH['noise']
        * preference_intensity(weights.noise)
        * (1.0 - scores.noise_score)
    )
    penalty = min(penalty_sum, MAX_ENV_PENALTY)
    return float(edge.length_m) * (1.0 + penalty)


def aggregate_route_scores(edges: list[GraphEdge]) -> dict[str, float]:
    if not edges:
        return {
            'greenery': 0.5,
            'air_quality': 0.5,
            'noise': 0.5,
        }

    total_length = sum(edge.length_m for edge in edges) or 1.0

    def weighted_average(field_name: str) -> float:
        return round(sum(getattr(edge.scores.clamped(), field_name) * edge.length_m for edge in edges) / total_length, 3)

    return {
        'greenery': weighted_average('greenery_score'),
        'air_quality': weighted_average('air_quality_score'),
        'noise': weighted_average('noise_score'),
    }
