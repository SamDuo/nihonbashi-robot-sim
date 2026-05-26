"""Build Cesium CZML packets from the testbed agent log.

CZML is Cesium's native time aware JSON format. By emitting position samples
per agent with linear interpolation, Cesium animates agents moving between
cells. Status (home, working, sheltering) drives color over time.

If an OSM walking network is supplied, agents follow real streets between
their hourly cell positions. Otherwise the fallback is straight line motion.
"""
from __future__ import annotations

from typing import Final

from .osm_network import resample_polyline, route_latlng

CZML_EPOCH: Final[str] = "2026-05-25T00:00:00Z"
CZML_END:   Final[str] = "2026-05-26T00:00:00Z"

STATUS_RGBA: Final[dict[str, list[int]]] = {
    "home":       [127, 127, 127, 255],
    "working":    [230,  85,  13, 255],
    "sheltering": [ 44, 127, 184, 255],
}


def _route_segment(g, prev: dict, cur: dict, samples_per_hour: int) -> list[tuple[float, float]]:
    if g is None:
        return [
            (float(prev["lng"]), float(prev["lat"])),
            (float(cur["lng"]),  float(cur["lat"])),
        ]
    path = route_latlng(g, float(prev["lat"]), float(prev["lng"]),
                        float(cur["lat"]),  float(cur["lng"]))
    return resample_polyline(path, samples_per_hour + 1)


def _agent_packet(agent_id: str, rows: list[dict], g, route_cache: dict,
                  samples_per_hour: int) -> dict:
    pos_samples: list[float] = []
    color_samples: list[float] = []
    vuln = 0.0

    for i, row in enumerate(rows):
        t = float(row["hour"] * 3600)
        rgba = STATUS_RGBA.get(row["status"], STATUS_RGBA["home"])
        color_samples.extend([t, *rgba])
        vuln = float(row["vulnerability_score"])

        if i == 0:
            pos_samples.extend([t, float(row["lng"]), float(row["lat"]), 2.0])
            continue

        prev = rows[i - 1]
        if (prev["cell_x"], prev["cell_y"]) == (row["cell_x"], row["cell_y"]):
            pos_samples.extend([t, float(row["lng"]), float(row["lat"]), 2.0])
            continue

        key = ((prev["cell_x"], prev["cell_y"]), (row["cell_x"], row["cell_y"]))
        if key not in route_cache:
            route_cache[key] = _route_segment(g, prev, row, samples_per_hour)
        path = route_cache[key]

        t_prev = float(prev["hour"] * 3600)
        n = len(path)
        if n < 2:
            pos_samples.extend([t, float(row["lng"]), float(row["lat"]), 2.0])
            continue
        for k in range(1, n):
            tk = t_prev + (k / (n - 1)) * (t - t_prev)
            lng, lat = path[k]
            pos_samples.extend([tk, lng, lat, 2.0])

    if rows:
        last = rows[-1]
        pos_samples.extend([86400.0, float(last["lng"]), float(last["lat"]), 2.0])
        color_samples.extend([86400.0, *STATUS_RGBA.get(last["status"], STATUS_RGBA["home"])])

    return {
        "id": f"agent-{agent_id}",
        "name": agent_id,
        "description": f"Agent {agent_id}. Vulnerability {vuln:.2f}.",
        "availability": f"{CZML_EPOCH}/{CZML_END}",
        "position": {
            "epoch": CZML_EPOCH,
            "cartographicDegrees": pos_samples,
            "interpolationAlgorithm": "LINEAR",
        },
        "point": {
            "color": {"epoch": CZML_EPOCH, "rgba": color_samples},
            "pixelSize": 6.0 + 10.0 * vuln,
            "outlineColor": {"rgba": [255, 255, 255, 255]},
            "outlineWidth": 1,
            "heightReference": "RELATIVE_TO_GROUND",
        },
    }


def build_czml(runs: dict, scenario: str, network=None,
               multiplier: int = 600, samples_per_hour: int = 6) -> list[dict]:
    """Return a CZML packet list for one scenario.

    multiplier controls Cesium playback speed. 600 means one real second
    equals ten simulated minutes, so the 24 hour day plays back in about
    2 minutes 24 seconds.

    samples_per_hour controls how many intermediate points are sampled
    along each route segment between two consecutive hour positions.
    Higher = smoother motion, more bytes in the CZML.
    """
    log = runs[scenario]["agent_log"]
    by_agent: dict[str, list[dict]] = {}
    for row in log:
        by_agent.setdefault(row["agent_id"], []).append(row)

    packets: list[dict] = [{
        "id": "document",
        "name": f"Nihonbashi agents {scenario}",
        "version": "1.0",
        "clock": {
            "interval":    f"{CZML_EPOCH}/{CZML_END}",
            "currentTime": f"{CZML_EPOCH[:11]}06:00:00Z",
            "multiplier":  multiplier,
            "range":       "LOOP_STOP",
            "step":        "SYSTEM_CLOCK_MULTIPLIER",
        },
    }]
    route_cache: dict = {}
    for aid in sorted(by_agent.keys()):
        hourly = sorted(by_agent[aid], key=lambda r: r["hour"])
        packets.append(_agent_packet(aid, hourly, network, route_cache, samples_per_hour))
    return packets
