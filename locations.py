"""Demo campus gazetteer.

Every place the system can recognise lives here, together with the geometry used
to draw the simulated campus map on the dashboard (SVG viewBox 0 0 400 290).

Future version: replace `pin`/`geom` with real GPS coordinates.
"""
from __future__ import annotations

import re

# kind: building | open | gate | road
#   sensitive -> crowded / high-footfall place, adds a little to the priority score
#   road      -> road-facing place (traffic / security may be needed)
#   geom      -> [x, y, w, h] on the map;  pin -> [x, y] where incident markers go
LOCATIONS = {
    "Sports Ground": {
        "display": ["sports ground", "the sports ground", "playground", "cricket ground", "ground"],
        "patterns": [
            r"\bsports?\s+(?:ground|complex|field)\b", r"\bplay\s*ground\b",
            r"\b(?:cricket|football|volleyball|basketball)\s+(?:ground|court)\b",
            r"\bstadium\b", r"\bground\b(?!\s*floor)",
        ],
        "kind": "open", "sensitive": False, "road": False, "geom": [35, 30, 135, 46],
    },
    "Hostel": {
        "display": ["hostel", "the hostel", "boys hostel", "girls hostel", "hostel area"],
        "patterns": [r"\bhostels?\b", r"\bdorm(?:itory|itories|s)?\b"],
        "kind": "building", "sensitive": True, "road": False, "geom": [290, 34, 75, 80],
    },
    "Academic Block": {
        "display": ["academic block", "the academic block", "Academic Block", "classroom", "main building"],
        "patterns": [
            r"\bacademic(?:\s+(?:block|building))?\b", r"\bclass\s*rooms?\b",
            r"\blecture\s+hall\b", r"\bseminar\s+hall\b", r"\bmain\s+building\b",
            r"\bcollege\s+building\b", r"\bdepartment\b",
        ],
        "kind": "building", "sensitive": True, "road": False, "geom": [60, 92, 110, 55],
    },
    "Lab Block": {
        "display": ["lab block", "the lab block", "computer lab", "chemistry lab", "laboratory"],
        "patterns": [
            r"\blab\s+block\b", r"\blaborator(?:y|ies)\b",
            r"\b(?:computer|chemistry|physics|electronics)\s+lab\b", r"\blabs?\b",
        ],
        "kind": "building", "sensitive": True, "road": False, "geom": [190, 92, 75, 45],
    },
    "Admin Block": {
        "display": ["admin block", "the admin block", "admin office", "principal office"],
        "patterns": [
            r"\badmin(?:istration|istrative)?(?:\s+(?:block|building|office))?\b",
            r"\bprincipal'?s?\s+office\b", r"\boffice\b",
        ],
        "kind": "building", "sensitive": False, "road": False, "geom": [60, 166, 62, 40],
    },
    "Library": {
        "display": ["library", "the library", "Library", "reading room"],
        "patterns": [r"\blibrary\b", r"\breading\s+room\b"],
        "kind": "building", "sensitive": True, "road": False, "geom": [137, 166, 63, 40],
    },
    "Canteen": {
        "display": ["canteen", "the canteen", "cafeteria", "food court", "mess"],
        "patterns": [r"\bcanteen\b", r"\bcafeteria\b", r"\bfood\s+court\b", r"\bmess\b", r"\btuck\s+shop\b"],
        "kind": "building", "sensitive": True, "road": False, "geom": [215, 156, 55, 40],
    },
    "Sector 4": {
        "display": ["sector 4", "Sector 4", "sector-4", "staff quarters"],
        "patterns": [r"\bsector[\s-]*(?:4|four)\b", r"\bstaff\s+(?:quarters|colony)\b"],
        "kind": "building", "sensitive": False, "road": False, "geom": [290, 142, 75, 73],
    },
    "Parking": {
        "display": ["parking", "the parking", "parking area", "parking lot"],
        "patterns": [r"\bparking\b"],
        "kind": "open", "sensitive": False, "road": True, "geom": [140, 218, 120, 30],
    },
    "Main Gate": {
        "display": ["main gate", "the main gate", "Main Gate", "gate 1", "mukhya gate"],
        "patterns": [
            r"\bmain\s*gate\b", r"\bgate\s*(?:no\.?\s*|number\s*|-\s*)?(?:1|one)\b",
            r"\bmukhya\s+gate\b", r"\bgate\b",
        ],
        "kind": "gate", "sensitive": True, "road": True, "geom": None, "pin": [95, 257],
    },
    "Gate 2": {
        "display": ["gate 2", "Gate 2", "gate number 2", "gate no 2", "the second gate"],
        "patterns": [
            r"\bgate\s*(?:no\.?\s*|number\s*|-\s*)?(?:2|two)\b", r"\bsecond\s+gate\b",
            r"\bdusra\s+gate\b", r"\bback\s+gate\b",
        ],
        "kind": "gate", "sensitive": True, "road": True, "geom": None, "pin": [380, 128],
    },
    "Main Road": {
        "display": ["main road", "the main road", "Main Road", "highway"],
        "patterns": [r"\bmain\s+road\b", r"\bhighway\b", r"\bsadak\b", r"\bcampus\s+road\b", r"\broad\b"],
        "kind": "road", "sensitive": False, "road": True, "geom": [0, 262, 400, 22], "pin": [290, 273],
    },
}

for _info in LOCATIONS.values():
    _info["_rx"] = [re.compile(p, re.I) for p in _info["patterns"]]


def pin_of(name: str):
    info = LOCATIONS[name]
    if info.get("pin"):
        return info["pin"]
    x, y, w, h = info["geom"]
    return [x + w / 2, y + h / 2]


def extract_location(text: str):
    """Return the best matching location name, or None. Longest match wins."""
    best = None
    for name, info in LOCATIONS.items():
        for rx in info["_rx"]:
            m = rx.search(text)
            if m:
                key = (len(m.group(0)), -m.start())
                if best is None or key > best[0]:
                    best = (key, name)
    return best[1] if best else None


def public_view():
    """What the browser needs to draw the map (no regexes)."""
    out = {}
    for name, info in LOCATIONS.items():
        out[name] = {
            "kind": info["kind"],
            "geom": info["geom"],
            "pin": pin_of(name),
            "sensitive": info["sensitive"],
        }
    return out


# ---------------------------------------------------------------------------
# Fixed resource stations (V1.2): simulated, so the system can point to a
# "nearest" one and estimate a rough travel time. Positions are on the same
# 400x290 map. Future version: replace with real depot / vehicle GPS.
# ---------------------------------------------------------------------------
RESOURCE_POINTS = {
    "Fire Station": {"resource": "Fire Response", "pos": [28, 250], "speed_m_per_min": 500},
    "Ambulance Bay": {"resource": "Ambulance", "pos": [372, 250], "speed_m_per_min": 500},
    "Security Post": {"resource": "Security", "pos": [200, 24], "speed_m_per_min": 150},
    "Traffic Post": {"resource": "Traffic/Security", "pos": [372, 24], "speed_m_per_min": 150},
    "Maintenance Depot": {"resource": "Maintenance", "pos": [28, 24], "speed_m_per_min": 120},
}
# Resources not based at their own station borrow the nearest general-purpose one.
_FALLBACK_STATION = {
    "Medical Team": "Ambulance Bay", "Rescue Team": "Fire Station",
    "Electrician": "Maintenance Depot", "Plumber": "Maintenance Depot",
}
METRES_PER_MAP_UNIT = 3.5   # simulated scale: the 400-unit-wide map is about 1.4 km across


def resource_points_view():
    return {name: {"resource": info["resource"], "pos": info["pos"]} for name, info in RESOURCE_POINTS.items()}


def nearest_resource(resource_name: str, location_name: str):
    """Nearest station that can supply `resource_name`, with distance/eta to `location_name`."""
    if not location_name or location_name not in LOCATIONS:
        return None
    target = pin_of(location_name)
    candidates = [
        (name, info) for name, info in RESOURCE_POINTS.items()
        if info["resource"] == resource_name
    ]
    if not candidates:
        fb = _FALLBACK_STATION.get(resource_name)
        if fb:
            candidates = [(fb, RESOURCE_POINTS[fb])]
    if not candidates:
        return None
    name, info = candidates[0]
    dx, dy = info["pos"][0] - target[0], info["pos"][1] - target[1]
    dist_m = ((dx ** 2 + dy ** 2) ** 0.5) * METRES_PER_MAP_UNIT
    eta_min = max(1, round(dist_m / info["speed_m_per_min"]))
    return {"station": name, "distance_m": round(dist_m), "eta_min": eta_min}

