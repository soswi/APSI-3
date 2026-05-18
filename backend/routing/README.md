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

Right now this endpoint is used only to test whether the walking graph works correctly.

It currently does:

- accept `start` and `end`
- ignore preferences for now
- run shortest path on the loaded graph
- return ordered `{lat, lng}` route coordinates

## Current request shape

```json
{
  "start": { "lat": 52.2297, "lng": 21.0122 },
  "end": { "lat": 52.21, "lng": 21.03 }
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

## Which graph file is used

The loader checks:

1. `backend/routing/data/warsaw_walk_enriched.json`
2. if that does not exist, it falls back to `backend/routing/data/warsaw_walk_base.json`

Implemented in:

- [graph_loader.py](</D:/main/Desktop/apsi/APSI-3/backend/routing/services/graph_loader.py:1>)

This means:

- for shortest-path testing, `warsaw_walk_base.json` is enough
- later, when node/edge environmental scores are ready, use `warsaw_walk_enriched.json`

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
  currently still present, but frontend test route ignores user preferences for now

## Next later step

When environmental data is ready, the endpoint can start using weights again:

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

But for now, the goal is simpler:

- confirm the graph loads
- confirm snapping works
- confirm the returned route follows the walking graph instead of a straight line
