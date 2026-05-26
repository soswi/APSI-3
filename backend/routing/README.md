# Routing Backend Notes

This folder now contains:

- the pure routing core in `services/`
- a minimal Django endpoint for testing real shortest paths from the frontend

## Current test flow

Frontend currently calls:

```http
POST /api/routes/walking
```

Implemented in:

- [views.py](</D:/main/Desktop/apsi/APSI-3/backend/routing/views.py:1>)
- [urls.py](</D:/main/Desktop/apsi/APSI-3/backend/routing/urls.py:1>)

This endpoint calculates a walking route on the graph and accepts optional user preference weights.

It currently does:

- accept `start` and `end`
- accept optional `weights`
- run weighted shortest path on the loaded graph
- return ordered `{lat, lng}` route coordinates

## Current request shape

```json
{
  "start": { "lat": 52.2297, "lng": 21.0122 },
  "end": { "lat": 52.21, "lng": 21.03 },
  "weights": {
    "greenery": 0.7,
    "air_quality": 0.6,
    "noise": 0.5
  }
}
```

## Current response shape

```json
{
  "route": [
    { "lat": 52.2297, "lng": 21.0122 },
    { "lat": 52.225, "lng": 21.018 },
    { "lat": 52.21, "lng": 21.03 }
  ],
  "distance_m": 2400.5,
  "estimated_duration_s": 1920,
  "scores": {
    "greenery": 0.5,
    "air_quality": 0.5,
    "noise": 0.5
  },
  "debug": {
    "start_snapped_distance_m": 18.3,
    "end_snapped_distance_m": 12.7,
    "algorithm": "dijkstra",
    "cost_model_version": "..."
  }
}
```

## How the algorithm works

The route is calculated on a walking graph:

- graph nodes are points on Warsaw walking paths and streets
- graph edges are walkable path segments between those points
- each edge has a length in meters
- enriched edges can also have environmental scores for greenery, air quality, and noise

When a user asks for a route:

1. The backend snaps the selected start and end coordinates to the nearest walkable graph edges.
2. It creates temporary start/end graph nodes at those snapped locations.
3. It runs Dijkstra search from start to end.
4. Dijkstra does not always use plain distance. It uses an edge cost:

```text
edge cost = edge length * (1 + preference penalty)
```

The preference penalty is higher when an edge does not match the user's preferences. For example, when greenery preference is `100%`, low-greenery edges become much more expensive, so a longer but greener park route can beat a shorter street route.

Important: preferences only work when the loaded graph has environmental scores. If the backend falls back to `warsaw_walk_base.json`, every edge uses neutral default scores, so the route behaves like a shortest path.

## Which graph file is used

The loader checks:

1. `backend/routing/data/warsaw_walk_enriched.json`
2. if that does not exist, it falls back to `backend/routing/data/warsaw_walk_base.json`

Implemented in:

- [graph_loader.py](</D:/main/Desktop/apsi/APSI-3/backend/routing/services/graph_loader.py:1>)

This means:

- for shortest-path testing, `warsaw_walk_base.json` is enough
- for preference-aware routing, `warsaw_walk_enriched.json` is required
- if only `warsaw_walk_base.json` is present, all edge scores default to `0.5`, so preference weights do not meaningfully change route selection
- at 100% greenery preference, the cost model strongly penalizes low-greenery edges, so a longer route through parks can win over a shorter street route

## Why `warsaw_walk_base.json` is not in git

The base graph file is too large to keep in the repository.

So each person who needs it should generate it locally.

File path:

- `backend/routing/data/warsaw_walk_base.json`

## How to create `warsaw_walk_base.json`

Use:

- [build_walking_graph_from_osm.py](</D:/main/Desktop/apsi/APSI-3/backend/routing/data_prep/build_walking_graph_from_osm.py:1>)

From the backend directory:

```powershell
cd D:\main\Desktop\apsi\APSI-3\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install osmnx networkx shapely geopandas pyproj
python routing\data_prep\build_walking_graph_from_osm.py
```

After that, this file should exist:

- `backend/routing/data/warsaw_walk_base.json`

If PowerShell blocks venv activation, use:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

## Files involved

- [services/router.py](</D:/main/Desktop/apsi/APSI-3/backend/routing/services/router.py:1>)
  main routing flow
- [services/snapping.py](</D:/main/Desktop/apsi/APSI-3/backend/routing/services/snapping.py:1>)
  snap start/end to nearest walkable edge
- [services/search.py](</D:/main/Desktop/apsi/APSI-3/backend/routing/services/search.py:1>)
  Dijkstra search
- [services/response.py](</D:/main/Desktop/apsi/APSI-3/backend/routing/services/response.py:1>)
  builds final route output
- [services/scoring.py](</D:/main/Desktop/apsi/APSI-3/backend/routing/services/scoring.py:1>)
  applies user preference weights to edge costs and aggregates returned route scores

## Preference data step

To make preferences affect routes, generate node scores and then enrich the base graph:

```powershell
python routing\data_prep\prepare_node_scores.py
python routing\data_prep\apply_node_scores_to_edges.py
```

After that, this file should exist:

- `backend/routing/data/warsaw_walk_enriched.json`
