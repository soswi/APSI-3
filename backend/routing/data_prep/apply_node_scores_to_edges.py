from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_BASE_GRAPH = Path(__file__).resolve().parent.parent / "data" / "warsaw_walk_base.json"
DEFAULT_NODE_SCORES = Path(__file__).resolve().parent.parent / "data" / "warsaw_node_scores.json"
DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "data" / "warsaw_walk_enriched.json"
SCORE_FIELDS = ("greenery_score", "air_quality_score", "noise_score")


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))


def _normalize_score_payload(payload: dict[str, Any]) -> dict[str, dict[str, float]]:
    if "scores" in payload and isinstance(payload["scores"], dict):
        node_scores: dict[str, dict[str, float]] = {}
        for node_id, score_values in payload["scores"].items():
            node_scores[str(node_id)] = {
                field: _clamp(float(score_values.get(field, 0.5)))
                for field in SCORE_FIELDS
            }
        return node_scores

    if "nodes" in payload and isinstance(payload["nodes"], list):
        node_scores = {}
        for row in payload["nodes"]:
            node_scores[str(row["id"])] = {
                field: _clamp(float(row.get("scores", {}).get(field, 0.5)))
                for field in SCORE_FIELDS
            }
        return node_scores

    raise ValueError("Node score file must contain either 'scores' mapping or 'nodes' list.")


def _average_edge_scores(
    start_scores: dict[str, float] | None,
    end_scores: dict[str, float] | None,
) -> dict[str, float]:
    return {
        field: round(
            (
                (start_scores or {}).get(field, 0.5)
                + (end_scores or {}).get(field, 0.5)
            ) / 2,
            6,
        )
        for field in SCORE_FIELDS
    }


def enrich_graph_with_node_scores(
    base_graph_path: Path,
    node_scores_path: Path,
    output_path: Path,
) -> Path:
    base_graph = json.loads(base_graph_path.read_text(encoding="utf-8"))
    node_scores_payload = json.loads(node_scores_path.read_text(encoding="utf-8"))
    node_scores = _normalize_score_payload(node_scores_payload)

    enriched_edges: list[dict[str, Any]] = []
    for edge in base_graph.get("edges", []):
        start_scores = node_scores.get(str(edge["u"]))
        end_scores = node_scores.get(str(edge["v"]))
        enriched_edge = dict(edge)
        enriched_edge["scores"] = _average_edge_scores(start_scores, end_scores)
        enriched_edges.append(enriched_edge)

    enriched_payload = {
        "metadata": {
            **base_graph.get("metadata", {}),
            "graph_version": "warsaw-walk-enriched-v1",
            "node_score_source": str(node_scores_path.name),
            "edge_score_rule": "edge_score = average(node_u_score, node_v_score)",
        },
        "nodes": base_graph.get("nodes", []),
        "edges": enriched_edges,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(enriched_payload, indent=2), encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert node scores into edge scores for the routing graph.")
    parser.add_argument("--base-graph", type=Path, default=DEFAULT_BASE_GRAPH)
    parser.add_argument("--node-scores", type=Path, default=DEFAULT_NODE_SCORES)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    output_path = enrich_graph_with_node_scores(
        base_graph_path=args.base_graph,
        node_scores_path=args.node_scores,
        output_path=args.output,
    )
    print(f"Saved enriched walking graph to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
