# Data Notes For Routing

This note is for the person preparing environmental data for routing.

The project currently uses:

- a walking graph prepared from OpenStreetMap
- node-level environmental scores prepared separately
- conversion from node scores to edge scores before routing

The routing algorithm needs node-level scores for:

- `greenery_score`
- `air_quality_score`
- `noise_score`

## Required format

Prepare a JSON file like:

- `backend/routing/data/warsaw_node_scores.json`

Example shape:

```json
{
  "nodes": [
    {
      "id": "123456",
      "scores": {
        "greenery_score": 0.72,
        "air_quality_score": 0.64,
        "noise_score": 0.58
      }
    },
    {
      "id": "123457",
      "scores": {
        "greenery_score": 0.81,
        "air_quality_score": 0.69,
        "noise_score": 0.61
      }
    }
  ]
}
```

Rules:

- `id` must match the node ids from the walking graph
- all score values must be normalized to `0.0-1.0`
- `1.0` always means better
- `0.0` always means worse

Meaning:

- `greenery_score = 1.0` means very green
- `air_quality_score = 1.0` means cleaner air
- `noise_score = 1.0` means quieter

## Recommended sources

### Greenery

Good source priority:

- Warsaw greenery datasets
- Warsaw WMS/WFS layers
- Warsaw Open Data
- OpenStreetMap green polygons

Useful layer types:

- parks
- forests
- grass / green areas
- tree areas
- individual trees, if available

Simple idea:

- compute a greenery value near each node
- normalize it to `0.0-1.0`

### Air quality

Good source priority:

- GIOS air-quality API
- Warsaw municipal air-quality data
- long-term pollution maps
- modeled pollution rasters
- traffic-based pollution proxy layers

Important:

- do not use live API calls per route request
- prepare a static or cached node score layer instead

Simple idea:

- estimate how clean the air is near each node
- convert it into `air_quality_score`
- normalize to `0.0-1.0`

### Noise

Good source priority:

- Warsaw strategic noise map
- other official city acoustic layers

Important:

- raw noise is usually in dB
- higher dB is worse
- final stored `noise_score` must still be higher-is-better

Simple idea:

- sample noise around each node
- convert dB to quietness
- normalize to `0.0-1.0`

## How it connects to the algorithm

The live routing code reads scores from **edges**, not nodes.

So your node scores will later be converted like this:

```text
edge.greenery_score = (u.greenery_score + v.greenery_score) / 2
edge.air_quality_score = (u.air_quality_score + v.air_quality_score) / 2
edge.noise_score = (u.noise_score + v.noise_score) / 2
```

That conversion is handled by:

- [apply_node_scores_to_edges.py](</D:/main/Desktop/apsi/APSI-3/backend/routing/data_prep/apply_node_scores_to_edges.py:1>)

The walking graph itself is prepared separately and later combined with this score file.

The final enriched graph used by routing is:

- `backend/routing/data/warsaw_walk_enriched.json`

The algorithm then loads that final graph and uses edge scores during routing.

If needed, you can use this example file:

- [warsaw_node_scores.example.json](</D:/main/Desktop/apsi/APSI-3/backend/routing/data/warsaw_node_scores.example.json:1>)
