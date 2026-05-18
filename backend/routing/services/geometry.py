from __future__ import annotations

import math

from .constants import WARSAW_CENTER_LAT
from .models import Coordinate


def haversine_m(start: Coordinate, end: Coordinate) -> float:
    radius_m = 6371000.0
    lat1 = math.radians(start.lat)
    lat2 = math.radians(end.lat)
    d_lat = lat2 - lat1
    d_lng = math.radians(end.lng - start.lng)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(d_lng / 2) ** 2
    )
    return 2 * radius_m * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def local_xy(point: Coordinate, ref_lat: float = WARSAW_CENTER_LAT) -> tuple[float, float]:
    meters_per_lat = 111320.0
    meters_per_lng = 111320.0 * math.cos(math.radians(ref_lat))
    return point.lng * meters_per_lng, point.lat * meters_per_lat


def interpolate(start: Coordinate, end: Coordinate, fraction: float) -> Coordinate:
    return Coordinate(
        lat=start.lat + (end.lat - start.lat) * fraction,
        lng=start.lng + (end.lng - start.lng) * fraction,
    )


def polyline_length_m(geometry: list[Coordinate]) -> float:
    return sum(haversine_m(geometry[index], geometry[index + 1]) for index in range(len(geometry) - 1))


def nearest_point_on_segment(point: Coordinate, start: Coordinate, end: Coordinate) -> tuple[Coordinate, float, float]:
    px, py = local_xy(point)
    sx, sy = local_xy(start)
    ex, ey = local_xy(end)

    dx = ex - sx
    dy = ey - sy
    denom = dx * dx + dy * dy

    if denom == 0:
        return start, haversine_m(point, start), 0.0

    raw_t = ((px - sx) * dx + (py - sy) * dy) / denom
    t = max(0.0, min(1.0, raw_t))
    snapped = interpolate(start, end, t)
    return snapped, haversine_m(point, snapped), t


def locate_point_on_polyline(point: Coordinate, geometry: list[Coordinate]) -> tuple[Coordinate, float, float]:
    best_point = geometry[0]
    best_distance = float('inf')
    best_distance_along = 0.0
    traversed = 0.0

    for index in range(len(geometry) - 1):
        start = geometry[index]
        end = geometry[index + 1]
        segment_length = haversine_m(start, end)
        snapped, distance, fraction = nearest_point_on_segment(point, start, end)

        if distance < best_distance:
            best_distance = distance
            best_point = snapped
            best_distance_along = traversed + segment_length * fraction

        traversed += segment_length

    return best_point, best_distance, best_distance_along


def split_polyline_by_distances(
    geometry: list[Coordinate],
    split_distances: list[float],
) -> list[list[Coordinate]]:
    if not split_distances:
        return [geometry[:]]

    targets = sorted(split_distances)
    segments: list[list[Coordinate]] = []
    current_segment = [geometry[0]]
    traversed = 0.0
    target_index = 0

    for index in range(len(geometry) - 1):
        start = geometry[index]
        end = geometry[index + 1]
        segment_length = haversine_m(start, end)

        while target_index < len(targets) and traversed <= targets[target_index] <= traversed + segment_length:
            split_distance = targets[target_index]
            fraction = 0.0 if segment_length == 0 else (split_distance - traversed) / segment_length
            split_point = interpolate(start, end, fraction)
            if current_segment[-1] != split_point:
                current_segment.append(split_point)
            segments.append(current_segment)
            current_segment = [split_point]
            target_index += 1

        if current_segment[-1] != end:
            current_segment.append(end)
        traversed += segment_length

    segments.append(current_segment)
    return segments


def dedupe_coordinates(coordinates: list[Coordinate]) -> list[Coordinate]:
    deduped: list[Coordinate] = []
    for coordinate in coordinates:
        if not deduped or deduped[-1] != coordinate:
            deduped.append(coordinate)
    return deduped
