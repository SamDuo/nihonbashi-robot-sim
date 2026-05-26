"""OSM walking network for Nihonbashi, used to route agents along real streets.

First call downloads the walking graph from OpenStreetMap via OSMnx and caches
it to outputs/networks/nihonbashi_walk.graphml. Subsequent calls reload from
the cache (no network needed). Used by sim/testbed/czml.py to produce smooth
agent motion that follows actual streets rather than crow flies straight lines.
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Final

log = logging.getLogger("testbed.osm")

# Bounding box wraps the Nihonbashi study area with comfortable margin.
BBOX_NORTH: Final[float] = 35.6905
BBOX_SOUTH: Final[float] = 35.6775
BBOX_EAST:  Final[float] = 139.7860
BBOX_WEST:  Final[float] = 139.7690

DEFAULT_CACHE = Path("outputs/networks/nihonbashi_walk.graphml")


def load_or_download_network(cache_path: Path = DEFAULT_CACHE):
    """Load the cached walking graph, or download and cache it."""
    import osmnx as ox

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    if cache_path.exists():
        log.info("loading cached OSM walking network: %s", cache_path)
        return ox.load_graphml(cache_path)
    log.info("downloading OSM walking network for Nihonbashi")
    g = ox.graph_from_bbox(
        bbox=(BBOX_WEST, BBOX_SOUTH, BBOX_EAST, BBOX_NORTH),
        network_type="walk",
    )
    ox.save_graphml(g, cache_path)
    log.info("saved network: %d nodes, %d edges", g.number_of_nodes(), g.number_of_edges())
    return g


def route_latlng(g, start_lat: float, start_lng: float,
                 end_lat: float, end_lng: float) -> list[tuple[float, float]]:
    """Shortest walking route, returned as a list of (lng, lat) points."""
    import networkx as nx
    import osmnx as ox

    try:
        u = ox.distance.nearest_nodes(g, X=start_lng, Y=start_lat)
        v = ox.distance.nearest_nodes(g, X=end_lng, Y=end_lat)
        path = nx.shortest_path(g, u, v, weight="length")
        return [(float(g.nodes[n]["x"]), float(g.nodes[n]["y"])) for n in path]
    except (nx.NetworkXNoPath, KeyError, ValueError):
        return [(start_lng, start_lat), (end_lng, end_lat)]


def resample_polyline(points: list[tuple[float, float]],
                      n_samples: int) -> list[tuple[float, float]]:
    """Resample a polyline to N evenly spaced points by arc length."""
    if not points:
        return []
    if len(points) == 1 or n_samples < 2:
        return [points[0]] * max(1, n_samples)
    dists = [0.0]
    for i in range(1, len(points)):
        dx = points[i][0] - points[i - 1][0]
        dy = points[i][1] - points[i - 1][1]
        dists.append(dists[-1] + math.hypot(dx, dy))
    total = dists[-1]
    if total == 0.0:
        return [points[0]] * n_samples
    out: list[tuple[float, float]] = []
    for i in range(n_samples):
        target = (i / (n_samples - 1)) * total
        for j in range(1, len(dists)):
            if dists[j] >= target:
                seg = dists[j] - dists[j - 1]
                t = (target - dists[j - 1]) / seg if seg > 0 else 0
                lng = points[j - 1][0] + t * (points[j][0] - points[j - 1][0])
                lat = points[j - 1][1] + t * (points[j][1] - points[j - 1][1])
                out.append((lng, lat))
                break
        else:
            out.append(points[-1])
    return out
