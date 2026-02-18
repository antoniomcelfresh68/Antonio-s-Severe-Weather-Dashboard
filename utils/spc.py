import re
import requests

SPC_BASE = "https://mapservices.weather.noaa.gov/vector/rest/services/outlooks/SPC_wx_outlks/MapServer"

HEADERS = {
    "User-Agent": "Antonio Severe Dashboard (contact: mcelfreshantonio@ou.edu)",
    "Accept": "application/json",
}

# -------- basic HTTP --------
def _get_json(url: str, params: dict | None = None, timeout: int = 25) -> dict:
    r = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json()

_service_info_cache: dict | None = None

def spc_service_info() -> dict:
    global _service_info_cache
    if _service_info_cache is None:
        _service_info_cache = _get_json(SPC_BASE, params={"f": "pjson"})
    return _service_info_cache

def find_layer_id(day_label: str, contains: str) -> int | None:
    """
    Find a layer ID by matching substrings in the layer name.
    Example: day_label="Day 1", contains="Categorical"
    """
    day = day_label.lower()
    key = contains.lower()
    for lyr in spc_service_info().get("layers", []) or []:
        name = (lyr.get("name") or "").lower()
        if day in name and key in name:
            return int(lyr["id"])
    # fallback for "probabilistic" naming variations
    if key == "probabilistic":
        for lyr in spc_service_info().get("layers", []) or []:
            name = (lyr.get("name") or "").lower()
            if day in name and ("prob" in name or "probability" in name):
                return int(lyr["id"])
    return None

def layer_geojson(layer_id: int) -> dict:
    url = f"{SPC_BASE}/{layer_id}/query"
    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "geojson",
    }
    return _get_json(url, params=params)

# -------- geometry: point in polygon (no extra deps) --------
def _point_in_ring(x: float, y: float, ring: list) -> bool:
    # ray casting
    inside = False
    n = len(ring)
    if n < 3:
        return False
    for i in range(n):
        x1, y1 = ring[i][0], ring[i][1]
        x2, y2 = ring[(i + 1) % n][0], ring[(i + 1) % n][1]
        # check crossing
        if ((y1 > y) != (y2 > y)):
            xinters = (x2 - x1) * (y - y1) / ((y2 - y1) if (y2 - y1) != 0 else 1e-12) + x1
            if x < xinters:
                inside = not inside
    return inside

def _point_in_polygon(x: float, y: float, coords: list) -> bool:
    # coords = [outer_ring, hole1, hole2...]
    if not coords:
        return False
    outer = coords[0]
    if not _point_in_ring(x, y, outer):
        return False
    # must not be inside any hole
    for hole in coords[1:]:
        if _point_in_ring(x, y, hole):
            return False
    return True

def point_in_geometry(lon: float, lat: float, geom: dict) -> bool:
    if not geom:
        return False
    gtype = geom.get("type")
    coords = geom.get("coordinates")
    if not coords:
        return False

    if gtype == "Polygon":
        return _point_in_polygon(lon, lat, coords)
    if gtype == "MultiPolygon":
        for poly in coords:
            if _point_in_polygon(lon, lat, poly):
                return True
        return False
    return False

# -------- outlook interpretation --------
_CAT_RANK = {"TSTM": 1, "MRGL": 2, "SLGT": 3, "ENH": 4, "MDT": 5, "HIGH": 6}

def _extract_label(props: dict) -> str:
    for k in ("LABEL", "label", "CAT", "cat", "RISK", "risk", "Name", "name"):
        v = props.get(k)
        if v not in (None, "", " "):
            return str(v).strip()
    return ""

def _extract_percent(props: dict) -> int | None:
    # Most services include LABEL like "5%" or "15%"
    lab = _extract_label(props)
    m = re.search(r"(\d{1,2})\s*%?", lab)
    if m:
        val = int(m.group(1))
        if 0 < val <= 100:
            return val

    # fallback: scan numeric fields that look like percents
    for v in props.values():
        if isinstance(v, (int, float)) and 0 < v <= 100:
            return int(v)
        if isinstance(v, str):
            s = v.strip().replace("%", "")
            if s.isdigit():
                val = int(s)
                if 0 < val <= 100:
                    return val
    return None

def point_day1_3_category(lat: float, lon: float, day: str) -> str:
    layer_id = find_layer_id(day, "Categorical")
    if layer_id is None:
        return "—"
    gj = layer_geojson(layer_id)

    best = None
    best_rank = 0

    for feat in gj.get("features", []) or []:
        if not point_in_geometry(lon, lat, feat.get("geometry", {})):
            continue
        lab = _extract_label(feat.get("properties", {}) or "").upper()
        rank = _CAT_RANK.get(lab, 0)
        if rank > best_rank:
            best_rank = rank
            best = lab

    return best if best else "NONE"

def point_day_prob(lat: float, lon: float, day: str) -> int | None:
    """
    For Day 4–7 probabilistic outlooks: returns the highest percent polygon containing the point.
    Typical values: 15/30/45.
    """
    layer_id = find_layer_id(day, "Probabilistic")
    if layer_id is None:
        # sometimes called "Probability"
        layer_id = find_layer_id(day, "Probability")
    if layer_id is None:
        return None

    gj = layer_geojson(layer_id)
    best = None

    for feat in gj.get("features", []) or []:
        if not point_in_geometry(lon, lat, feat.get("geometry", {})):
            continue
        pct = _extract_percent(feat.get("properties", {}) or {})
        if pct is None:
            continue
        if best is None or pct > best:
            best = pct

    return best

def get_spc_point_summary(lat: float, lon: float) -> dict:
    """
    Returns:
      - day1/day2/day3 categorical risk at point
      - day4-7 probabilistic percent at point
    """
    out = {
        "day1_cat": point_day1_3_category(lat, lon, "Day 1"),
        "day2_cat": point_day1_3_category(lat, lon, "Day 2"),
        "day3_cat": point_day1_3_category(lat, lon, "Day 3"),
        "day4_pct": point_day_prob(lat, lon, "Day 4"),
        "day5_pct": point_day_prob(lat, lon, "Day 5"),
        "day6_pct": point_day_prob(lat, lon, "Day 6"),
        "day7_pct": point_day_prob(lat, lon, "Day 7"),
    }
    return out

def _find_layer_id_any(day_label: str, keywords: list[str]) -> int | None:
    """
    More flexible layer finder: all keywords must appear in layer name.
    """
    day = day_label.lower()
    keys = [k.lower() for k in keywords]
    for lyr in spc_service_info().get("layers", []) or []:
        name = (lyr.get("name") or "").lower()
        if day in name and all(k in name for k in keys):
            return int(lyr["id"])
    return None


def point_hazard_percent(lat: float, lon: float, day: str, hazard: str) -> int | None:
    """
    Returns highest hazard % polygon containing the point for Day 1/2.
    hazard: "tornado" | "wind" | "hail"
    """
    hz = hazard.lower()

    # Try common naming patterns in the NOAA service
    # (service layer names vary; this approach is resilient)
    layer_id = (
        _find_layer_id_any(day, [hz, "prob"]) or
        _find_layer_id_any(day, [hz, "probability"]) or
        _find_layer_id_any(day, [hz, "probabilistic"]) or
        _find_layer_id_any(day, [hz])  # last resort
    )

    if layer_id is None:
        return None

    gj = layer_geojson(layer_id)

    best = None
    for feat in gj.get("features", []) or []:
        if not point_in_geometry(lon, lat, feat.get("geometry", {})):
            continue
        pct = _extract_percent(feat.get("properties", {}) or {})
        if pct is None:
            continue
        if best is None or pct > best:
            best = pct

    return best


def get_spc_location_percents(lat: float, lon: float) -> dict:
    """
    v1-style numbers for the location.
    Day 1/2: tornado/wind/hail %
    Day 4–7: general probability %
    """
    return {
        "d1_tor": point_hazard_percent(lat, lon, "Day 1", "tornado"),
        "d1_wind": point_hazard_percent(lat, lon, "Day 1", "wind"),
        "d1_hail": point_hazard_percent(lat, lon, "Day 1", "hail"),

        "d2_tor": point_hazard_percent(lat, lon, "Day 2", "tornado"),
        "d2_wind": point_hazard_percent(lat, lon, "Day 2", "wind"),
        "d2_hail": point_hazard_percent(lat, lon, "Day 2", "hail"),

        # keep your existing day4-7 general prob
        "d4_prob": point_day_prob(lat, lon, "Day 4"),
        "d5_prob": point_day_prob(lat, lon, "Day 5"),
        "d6_prob": point_day_prob(lat, lon, "Day 6"),
        "d7_prob": point_day_prob(lat, lon, "Day 7"),
    }
