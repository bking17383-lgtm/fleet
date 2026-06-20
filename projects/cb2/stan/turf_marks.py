#!/usr/bin/env python3
"""Yard turf marks — geofence + water savings (redneck edition)."""
from __future__ import annotations

import json
import math
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

from bus_lane import STAN, safe_mkdir

DATA = STAN / "turf_wall" / "yards.json"
GALLONS_PER_MARK = 1.6  # avg modern flush avoided (EPA ~1.28–1.6 gal)
MAX_YARDS = 200
MAX_MARKS_PER_YARD = 2000
MAX_STATIONS = 24


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").lower().strip()).strip("-")
    return (s[:24] or secrets.token_urlsafe(4))


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _load() -> dict:
    if not DATA.is_file():
        return {}
    try:
        return json.loads(DATA.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    safe_mkdir(DATA.parent)
    if len(data) > MAX_YARDS:
        data = dict(list(data.items())[-MAX_YARDS:])
    DATA.write_text(json.dumps(data, indent=0), encoding="utf-8")


def _valid_id(yard_id: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_-]{8,32}", yard_id or ""))


def _point_in_polygon(lat: float, lng: float, ring: list[list[float]]) -> bool:
    """Ray casting — ring is [[lat,lng], ...] closed or open."""
    if len(ring) < 3:
        return False
    x, y = lng, lat
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][1], ring[i][0]
        xj, yj = ring[j][1], ring[j][0]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def _point_in_circle(lat: float, lng: float, center: list[float], radius_m: float) -> bool:
    clat, clng = center
    # haversine meters
    r = 6371000.0
    p1, p2 = math.radians(clat), math.radians(lat)
    dlat = math.radians(lat - clat)
    dlng = math.radians(lng - clng)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlng / 2) ** 2
    dist = 2 * r * math.asin(min(1.0, math.sqrt(a)))
    return dist <= radius_m


def _inside_yard(lat: float, lng: float, yard: dict) -> bool:
    mode = yard.get("mode") or "polygon"
    if mode == "circle":
        c = yard.get("center")
        r = float(yard.get("radius_m") or 0)
        if not c or r <= 0:
            return False
        return _point_in_circle(lat, lng, c, r)
    ring = yard.get("polygon") or []
    return _point_in_polygon(lat, lng, ring)


def get_yard(yard_id: str) -> dict | None:
    if not _valid_id(yard_id):
        return None
    return _load().get(yard_id)


def save_yard(
    yard_id: str,
    *,
    name: str = "",
    mode: str = "polygon",
    polygon: list | None = None,
    center: list | None = None,
    radius_m: float | None = None,
) -> dict:
    if not _valid_id(yard_id):
        yard_id = secrets.token_urlsafe(10)
    data = _load()
    entry = data.get(yard_id) or {"id": yard_id, "marks": [], "stations": [], "created": _now()}
    entry["name"] = (name or entry.get("name") or "My dirt")[:60]
    entry["mode"] = mode if mode in ("polygon", "circle") else "polygon"
    entry["updated"] = _now()
    if entry["mode"] == "circle" and center and radius_m:
        entry["center"] = [float(center[0]), float(center[1])]
        entry["radius_m"] = min(max(float(radius_m), 5.0), 500.0)
        entry.pop("polygon", None)
    elif polygon and len(polygon) >= 3:
        clean = [[float(p[0]), float(p[1])] for p in polygon[:40]]
        entry["polygon"] = clean
        entry.pop("center", None)
        entry.pop("radius_m", None)
    data[yard_id] = entry
    _save(data)
    return entry


def add_mark(
    yard_id: str,
    lat: float,
    lng: float,
    label: str = "",
    callsign: str = "",
    method: str = "gps",
    station_id: str = "",
) -> dict:
    yard = get_yard(yard_id)
    if not yard:
        raise ValueError("yard not found")
    if not _inside_yard(lat, lng, yard):
        raise ValueError("outside yer property line — coons don't count it")
    marks = yard.get("marks") or []
    if len(marks) >= MAX_MARKS_PER_YARD:
        marks = marks[-MAX_MARKS_PER_YARD + 1 :]
    mark = {
        "id": secrets.token_urlsafe(6),
        "lat": round(float(lat), 7),
        "lng": round(float(lng), 7),
        "label": (label or "")[:40],
        "callsign": (callsign or "Anonymous Redneck")[:40],
        "method": method if method in ("gps", "peg", "barn") else "gps",
        "station_id": (station_id or "")[:16],
        "at": _now(),
    }
    marks.append(mark)
    yard["marks"] = marks
    data = _load()
    data[yard_id] = yard
    _save(data)
    return {"mark": mark, "stats": stats(yard_id)}


def add_station(yard_id: str, name: str, lat: float, lng: float) -> dict:
    yard = get_yard(yard_id)
    if not yard:
        raise ValueError("yard not found")
    if not _inside_yard(lat, lng, yard):
        raise ValueError("peg must be inside the fence line")
    stations = yard.get("stations") or []
    if len(stations) >= MAX_STATIONS:
        raise ValueError("too many pegs — coons only read 24 signs")
    clean_name = (name or "Peg").strip()[:40]
    slug = _slug(clean_name)
    for s in stations:
        if s.get("slug") == slug:
            slug = f"{slug}-{secrets.token_urlsafe(3)}"
    station = {
        "id": secrets.token_urlsafe(6),
        "name": clean_name,
        "slug": slug,
        "lat": round(float(lat), 7),
        "lng": round(float(lng), 7),
        "created": _now(),
    }
    stations.append(station)
    yard["stations"] = stations
    yard["updated"] = _now()
    data = _load()
    data[yard_id] = yard
    _save(data)
    return station


def find_station(yard: dict, station_id: str = "", slug: str = "") -> dict | None:
    stations = yard.get("stations") or []
    if station_id:
        for s in stations:
            if s.get("id") == station_id:
                return s
    if slug:
        slug = slug.lower().strip()
        for s in stations:
            if s.get("slug") == slug:
                return s
    return None


def mark_station(
    yard_id: str,
    station_id: str = "",
    slug: str = "",
    callsign: str = "",
) -> dict:
    yard = get_yard(yard_id)
    if not yard:
        raise ValueError("yard not found")
    station = find_station(yard, station_id=station_id, slug=slug)
    if not station:
        raise ValueError("peg not found — pound a stake first")
    return add_mark(
        yard_id,
        station["lat"],
        station["lng"],
        label=station.get("name") or "Peg",
        callsign=callsign,
        method="peg",
        station_id=station.get("id") or "",
    )


def stats(yard_id: str) -> dict:
    yard = get_yard(yard_id)
    if not yard:
        return {}
    n = len(yard.get("marks") or [])
    gallons = round(n * GALLONS_PER_MARK, 1)
    liters = round(gallons * 3.785, 1)
    return {
        "marks": n,
        "gallons_saved": gallons,
        "liters_saved": liters,
        "flushes_avoided": n,
        "raccoon_confusion": round(n * 0.7, 1),
        "joy_units": n,
    }
