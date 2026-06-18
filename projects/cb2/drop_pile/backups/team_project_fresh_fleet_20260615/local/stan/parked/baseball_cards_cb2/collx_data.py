"""CollX CSV import, catalog storage, and price lookup — no heuristic fallback."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
COLLX_DIR = BASE_DIR / "data" / "collx"
CATALOG_FILE = COLLX_DIR / "catalog.json"
META_FILE = COLLX_DIR / "meta.json"
COLLECTION_FILE = BASE_DIR / "data" / "collection.json"

DRIVE_ROOT = Path("/mnt/shared/GoogleDrive/MyDrive")
COLLX_INBOX = DRIVE_ROOT / "collx_inbox"
COLLX_CURRENT = COLLX_INBOX / "current"
COLLX_ARCHIVE = COLLX_INBOX / "archive"
CANONICAL_NAME = "collx_export.csv"
CANONICAL_PATH = COLLX_CURRENT / CANONICAL_NAME
DOWNLOADS = Path("/mnt/shared/MyFiles/Downloads")

DRIVE_CANDIDATES = [
    CANONICAL_PATH,
    COLLX_INBOX / "collx_export.csv",
    DRIVE_ROOT / "collx_export.csv",
    DRIVE_ROOT / "CollX Export.csv",
    DRIVE_ROOT / "collx_collection.csv",
    DRIVE_ROOT / "collection_export.csv",
    DRIVE_ROOT / "My Collection.csv",
    DRIVE_ROOT / "lester" / "collx_export.csv",
]

SCAN_ROOTS = [
    COLLX_INBOX,
    DRIVE_ROOT,
    DRIVE_ROOT / "lester",
    DOWNLOADS,
    Path.home() / "Downloads",
]

PLAYER_KEYS = ("player", "athlete", "player name", "name", "card name")
YEAR_KEYS = ("year", "card year")
SET_KEYS = ("set", "card set", "set name", "product")
NUMBER_KEYS = ("card #", "card number", "number", "#", "card no")
CONDITION_KEYS = ("condition", "card condition")
GRADE_KEYS = ("grade", "grader grade", "psa grade")
MARKET_PRICE_KEYS = (
    "market_value",
    "market value",
    "estimated value",
    "est. value",
    "est value",
    "average price",
    "avg price",
    "collx value",
)
ASKING_PRICE_KEYS = ("asking_price", "asking price", "your price", "listing price")
PURCHASE_PRICE_KEYS = ("purchase_price", "purchase price")
SOLD_PRICE_KEYS = ("sold_for_price", "sold for price")
# Fallback only when market column missing
LEGACY_PRICE_KEYS = ("price", "value")
BRAND_KEYS = ("brand", "manufacturer")
CATEGORY_KEYS = ("category", "sport")
ADDED_KEYS = ("added", "date added", "created")
QUANTITY_KEYS = ("quantity", "qty")
LOCATION_KEYS = ("location", "bin", "box")
IMAGE_FRONT_KEYS = ("front_image", "front image", "image url", "card image url", "image", "photo url", "thumbnail")
IMAGE_BACK_KEYS = ("back_image", "back image")
COLLX_ID_KEYS = ("collx_id", "collx id", "id")
FLAGS_KEYS = ("flags", "flag")
TEAM_KEYS = ("team", "franchise")
ROOKIE_KEYS = ("rookie", "is rookie", "rc")
AUTO_KEYS = ("autograph", "auto", "is autograph", "signed")
NOTES_KEYS = ("notes", "note", "description")


def _now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def _norm_header(h: str) -> str:
    return re.sub(r"\s+", " ", (h or "").strip().lower())


def _pick(row: dict[str, str], keys: tuple[str, ...]) -> str:
    for k in keys:
        if k in row and row[k]:
            return row[k].strip()
    return ""


def _pick_image(row: dict[str, str]) -> tuple[str, str]:
    front = _pick(row, IMAGE_FRONT_KEYS)
    back = _pick(row, IMAGE_BACK_KEYS)
    return front, back


def _pick_price(row: dict[str, str], keys: tuple[str, ...]) -> tuple[str, float | None]:
    raw = _pick(row, keys)
    return raw, _parse_price(raw)


def _pick_market_price(row: dict[str, str]) -> tuple[str, float | None]:
    raw, val = _pick_price(row, MARKET_PRICE_KEYS)
    if val is not None:
        return raw, val
    return _pick_price(row, LEGACY_PRICE_KEYS)


def thumb_api_path(collx_id: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", str(collx_id))[:64]
    return f"/api/collx/thumb/{safe}"


def _parse_price(raw: str) -> float | None:
    if not raw:
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", raw.replace(",", ""))
    if not cleaned:
        return None
    try:
        val = float(cleaned)
        return val if val >= 0 else None
    except ValueError:
        return None


def _parse_bool(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "y", "rc", "rookie"}


def _norm_token(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _card_key(player: str, year: int | str, card_set: str, card_number: str) -> str:
    y = str(year).strip()
    return "|".join(
        [
            _norm_token(player),
            y,
            _norm_token(card_set),
            _norm_token(card_number),
        ]
    )


def _ensure_dirs() -> None:
    COLLX_DIR.mkdir(parents=True, exist_ok=True)
    COLLECTION_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def _save_json(path: Path, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_meta() -> dict[str, Any]:
    _ensure_dirs()
    meta = _load_json(META_FILE, {})
    if not isinstance(meta, dict):
        meta = {}
    return meta


def load_catalog() -> list[dict[str, Any]]:
    _ensure_dirs()
    data = _load_json(CATALOG_FILE, [])
    return data if isinstance(data, list) else []


def catalog_index(catalog: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    idx: dict[str, dict[str, Any]] = {}
    for row in catalog:
        key = row.get("match_key") or _card_key(
            row.get("player", ""),
            row.get("year", ""),
            row.get("set", ""),
            row.get("card_number", ""),
        )
        idx[key] = row
    return idx


def ensure_inbox() -> Path:
    return ensure_inbox_layout()


def _archive_stamp() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d_%H%M%S")


def ensure_inbox_layout() -> Path:
    """Single-file inbox: collx_inbox/current/collx_export.csv only."""
    _ensure_dirs()
    try:
        COLLX_INBOX.mkdir(parents=True, exist_ok=True)
        COLLX_CURRENT.mkdir(parents=True, exist_ok=True)
        COLLX_ARCHIVE.mkdir(parents=True, exist_ok=True)
        instructions = COLLX_CURRENT / "SAVE_COLLX_HERE.txt"
        if not instructions.is_file():
            instructions.write_text(
                "Save your CollX CSV export HERE as exactly:\n\n"
                "  collx_export.csv\n\n"
                "Only one file in this folder — phone/Drive picker shows one option.\n"
                "Or drop CSV in collx_inbox/ (parent) — auto-import moves it here.\n"
                "Old exports go to collx_inbox/archive/\n",
                encoding="utf-8",
            )
    except OSError:
        pass
    return COLLX_INBOX


def _archive_csv(path: Path) -> Path | None:
    if not path.is_file() or path.suffix.lower() != ".csv":
        return None
    try:
        dest_dir = COLLX_ARCHIVE / _archive_stamp()
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / path.name
        if path.resolve() == dest.resolve():
            return dest
        shutil.move(str(path), str(dest))
        return dest
    except OSError:
        return None


def _pending_csv_paths() -> list[Path]:
    """CSV drops waiting to become the single canonical file."""
    paths: list[Path] = []
    if COLLX_INBOX.is_dir():
        for p in COLLX_INBOX.iterdir():
            if p.is_file() and p.suffix.lower() == ".csv":
                paths.append(p)
    if COLLX_CURRENT.is_dir():
        for p in COLLX_CURRENT.iterdir():
            if p.is_file() and p.suffix.lower() == ".csv" and p.name != CANONICAL_NAME:
                paths.append(p)
    for root in (DOWNLOADS, Path.home() / "Downloads"):
        if root.is_dir():
            for p in root.glob("*.csv"):
                name = p.name.lower()
                if p.is_file() and ("collx" in name or "download_user" in name):
                    paths.append(p)
    return paths


def consolidate_new_exports() -> dict[str, Any]:
    """Move newest drop into current/collx_export.csv; archive the rest."""
    ensure_inbox_layout()
    pending = _pending_csv_paths()
    canonical_exists = CANONICAL_PATH.is_file()

    if not pending and canonical_exists:
        return {
            "status": "ok",
            "new": False,
            "canonical": str(CANONICAL_PATH),
            "message": "Canonical export already in place",
        }
    if not pending:
        return {"status": "skipped", "new": False, "message": "No CollX CSV waiting"}

    def _pending_rows(p: Path) -> int:
        prev = preview_collx_csv(p)
        return int(prev.get("rows", 0)) if not prev.get("error") else 0

    newest = max(pending, key=lambda p: (_pending_rows(p), p.stat().st_mtime))
    try:
        text = newest.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {"status": "error", "message": f"Could not read {newest}: {exc}"}

    archived: list[str] = []
    for p in list(COLLX_INBOX.glob("*.csv")) + list(COLLX_CURRENT.glob("*.csv")):
        dest = _archive_csv(p)
        if dest:
            archived.append(str(dest))

    COLLX_CURRENT.mkdir(parents=True, exist_ok=True)
    CANONICAL_PATH.write_text(text, encoding="utf-8")
    return {
        "status": "ok",
        "new": True,
        "from": str(newest),
        "canonical": str(CANONICAL_PATH),
        "archived": archived,
        "size_bytes": CANONICAL_PATH.stat().st_size,
    }


def _file_fingerprint(path: Path) -> str:
    try:
        data = path.read_bytes()
        return hashlib.sha256(data).hexdigest()[:20]
    except OSError:
        return ""


def _inbox_root_csvs() -> list[Path]:
    if not COLLX_INBOX.is_dir():
        return []
    return [p for p in COLLX_INBOX.iterdir() if p.is_file() and p.suffix.lower() == ".csv"]


def load_collx_expected() -> dict[str, Any]:
    """Optional targets from collx_inbox/COLLX_EXPECTED.txt (items + total)."""
    expected: dict[str, Any] = {}
    path = COLLX_INBOX / "COLLX_EXPECTED.txt"
    if not path.is_file():
        return expected
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, _, val = line.partition(":")
                key = key.strip().lower()
                val = val.strip().replace("$", "").replace(",", "")
                if key in ("items", "cards", "count"):
                    expected["items"] = int(float(val))
                elif key in ("total", "value", "total_mid"):
                    expected["total"] = float(val)
    except (OSError, ValueError):
        pass
    return expected


def preview_csv_text(text: str) -> dict[str, Any]:
    """Row count and CollX total from raw CSV text (no writes)."""
    catalog, meta = parse_csv_text(text, source="preview")
    if meta.get("error"):
        return {"rows": 0, "skipped": 0, "total_mid": 0, "error": meta["error"]}
    total_mid = round(sum(float(c.get("price") or 0) for c in catalog), 2)
    return {
        "rows": len(catalog),
        "skipped": meta.get("skipped_rows", 0),
        "total_mid": total_mid,
    }


def preview_collx_csv(path: Path) -> dict[str, Any]:
    """Row count and CollX total without writing catalog."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        prev = preview_csv_text(text)
        prev["path"] = str(path)
        prev["size_bytes"] = path.stat().st_size
        return prev
    except OSError as exc:
        return {"path": str(path), "error": str(exc)}


def _iter_collx_csv_files() -> list[Path]:
    """All CollX-like CSV paths — inbox (incl. archive), candidates, scan roots."""
    seen: set[str] = set()
    out: list[Path] = []

    def add(path: Path) -> None:
        if not path.is_file():
            return
        key = str(path.resolve())
        if key in seen:
            return
        headers = _peek_csv_headers(path)
        if _score_collx_headers(headers) < 4:
            return
        seen.add(key)
        out.append(path)

    for fixed in DRIVE_CANDIDATES:
        add(fixed)
    if COLLX_INBOX.is_dir():
        for p in COLLX_INBOX.rglob("*.csv"):
            add(p)
    for root in SCAN_ROOTS:
        if not root.is_dir() or root == COLLX_INBOX:
            continue
        depth = 0 if root in (COLLX_CURRENT, DOWNLOADS, Path.home() / "Downloads") else 3
        try:
            for dirpath, dirnames, filenames in os.walk(root):
                if COLLX_ARCHIVE.name in dirnames:
                    dirnames.remove(COLLX_ARCHIVE.name)
                rel = Path(dirpath).relative_to(root)
                if len(rel.parts) > depth:
                    dirnames.clear()
                    continue
                for name in filenames:
                    if name.lower().endswith(".csv"):
                        add(Path(dirpath) / name)
        except OSError:
            continue
    return out


def largest_collx_csv_on_drive() -> dict[str, Any] | None:
    """Best CollX CSV on mounted Drive by row count (scans archive too)."""
    best: dict[str, Any] | None = None
    for path in _iter_collx_csv_files():
        preview = preview_collx_csv(path)
        if preview.get("error"):
            continue
        try:
            preview["modified"] = datetime.fromtimestamp(
                path.stat().st_mtime, tz=timezone.utc
            ).astimezone().isoformat()
        except OSError:
            pass
        if not best or preview.get("rows", 0) > best.get("rows", 0):
            best = dict(preview)
    return best


def promote_largest_export_to_canonical() -> dict[str, Any]:
    """If a larger CollX CSV exists on Drive than canonical, copy it to current/."""
    ensure_inbox_layout()
    largest = largest_collx_csv_on_drive()
    if not largest:
        return {"status": "skipped", "message": "No CollX CSV on Drive"}

    canon_rows = 0
    if CANONICAL_PATH.is_file():
        canon_rows = preview_collx_csv(CANONICAL_PATH).get("rows", 0)

    if largest.get("rows", 0) <= canon_rows and CANONICAL_PATH.is_file():
        return {
            "status": "ok",
            "new": False,
            "message": f"Drive largest is {largest.get('rows')} rows — same as canonical",
            "largest": largest,
        }

    src = Path(largest["path"])
    try:
        text = src.read_text(encoding="utf-8", errors="replace")
        CANONICAL_PATH.parent.mkdir(parents=True, exist_ok=True)
        CANONICAL_PATH.write_text(text, encoding="utf-8")
        return {
            "status": "ok",
            "new": True,
            "from": str(src),
            "canonical": str(CANONICAL_PATH),
            "rows": largest.get("rows"),
            "total_mid": largest.get("total_mid"),
        }
    except OSError as exc:
        return {"status": "error", "message": str(exc)}


def tidy_inbox_after_import(imported_rows: int | None = None) -> dict[str, Any]:
    """Archive inbox drops after import — skip if import looks incomplete (audit safety)."""
    ensure_inbox_layout()
    expected = load_collx_expected()
    exp_items = expected.get("items")
    if exp_items and imported_rows is not None and imported_rows < int(exp_items) - 15:
        return {
            "status": "skipped",
            "message": (
                f"Only {imported_rows} rows imported vs ~{exp_items} expected — "
                "keeping inbox files for puppy/email audit (not dropping)."
            ),
            "imported_rows": imported_rows,
            "expected_items": exp_items,
        }
    archived: list[str] = []
    for p in COLLX_INBOX.glob("*.csv"):
        dest = _archive_csv(p)
        if dest:
            archived.append(str(dest))
    if COLLX_CURRENT.is_dir():
        for p in COLLX_CURRENT.iterdir():
            if p.is_file() and p.suffix.lower() == ".csv" and p.name != CANONICAL_NAME:
                dest = _archive_csv(p)
                if dest:
                    archived.append(str(dest))
    return {"status": "ok", "archived": archived}


def audit_drive_csvs(limit: int = 20) -> list[dict[str, Any]]:
    """Every CollX CSV on Drive with row counts — for garbage-in audit."""
    rows: list[dict[str, Any]] = []
    for path in _iter_collx_csv_files():
        prev = preview_collx_csv(path)
        if prev.get("error"):
            continue
        try:
            prev["modified"] = datetime.fromtimestamp(
                path.stat().st_mtime, tz=timezone.utc
            ).astimezone().isoformat()
        except OSError:
            pass
        rows.append(prev)
    rows.sort(key=lambda x: (-(x.get("rows") or 0), -(x.get("size_bytes") or 0)))
    return rows[:limit]


def audit_pipeline() -> dict[str, Any]:
    """Full source audit: Drive + catalog vs CollX expected (GIGO check)."""
    expected = load_collx_expected()
    catalog = load_catalog()
    drive_csvs = audit_drive_csvs()
    largest = largest_collx_csv_on_drive()
    canon = preview_collx_csv(CANONICAL_PATH) if CANONICAL_PATH.is_file() else None
    collection = _load_json(COLLECTION_FILE, [])
    total_mid = round(
        sum(
            (c.get("valuation") or {}).get("estimate_mid") or 0
            for c in collection
            if isinstance(c, dict)
        ),
        2,
    )

    try:
        from collx_gmail import audit_collx_emails

        email_audit = audit_collx_emails()
    except ImportError:
        email_audit = {"status": "skipped", "message": "collx_gmail not available"}

    exp_items = expected.get("items")
    exp_total = expected.get("total")
    cat_rows = len(catalog)
    best_rows = 0
    best_source = "none"
    if drive_csvs:
        best_rows = drive_csvs[0].get("rows", 0)
        best_source = drive_csvs[0].get("path", "drive")
    email_best = (email_audit or {}).get("best_attachment")
    if email_best and (email_best.get("rows") or 0) > best_rows:
        best_rows = email_best.get("rows", 0)
        best_source = f"gmail:{email_best.get('filename', 'attachment')}"

    verdict = "unknown"
    detail = "Set items/total in collx_inbox/COLLX_EXPECTED.txt to compare."
    if exp_items:
        if cat_rows >= exp_items - 15 and best_rows >= exp_items - 15:
            verdict = "ok"
            detail = f"Catalog ({cat_rows}) and best source ({best_rows}) match CollX app (~{exp_items})."
        elif best_rows < exp_items - 15:
            verdict = "garbage_in"
            detail = (
                f"Best CSV found is only {best_rows} rows ({best_source}). "
                f"CollX app shows ~{exp_items}. Incomplete export — app cannot invent missing cards."
            )
        elif cat_rows < exp_items - 15 and best_rows >= cat_rows:
            verdict = "import_blocked_or_stale"
            detail = (
                f"Source has {best_rows} rows but catalog has {cat_rows}. "
                "Tap Sync now or upload CSV — or fingerprint blocked re-import."
            )
        else:
            verdict = "partial"
            detail = f"Catalog {cat_rows} vs expected ~{exp_items}. Check puppy email audit."

    return {
        "verdict": verdict,
        "verdict_detail": detail,
        "gigo_note": "Garbage IN → garbage OUT. We do not drop files until import count meets expected.",
        "expected": expected,
        "catalog_count": cat_rows,
        "collection_count": len(collection) if isinstance(collection, list) else 0,
        "collection_total_mid": total_mid,
        "canonical": canon,
        "drive_largest": largest,
        "drive_csvs": drive_csvs,
        "best_source_rows": best_rows,
        "best_source": best_source,
        "email_audit": email_audit,
    }


def _inbox_activity_mtime() -> float:
    mt = 0.0
    if COLLX_INBOX.is_dir():
        try:
            mt = max(mt, COLLX_INBOX.stat().st_mtime)
        except OSError:
            pass
    for p in _inbox_root_csvs():
        try:
            mt = max(mt, p.stat().st_mtime)
        except OSError:
            pass
    if CANONICAL_PATH.is_file():
        try:
            mt = max(mt, CANONICAL_PATH.stat().st_mtime)
        except OSError:
            pass
    return mt


def _should_import_canonical() -> tuple[bool, str]:
    """Detect new export via inbox drops, content hash, or mtime."""
    if _inbox_root_csvs():
        return True, "CSV waiting in collx_inbox/ (drag-drop detected)"
    largest = largest_collx_csv_on_drive()
    catalog_len = len(load_catalog())
    if largest and largest.get("rows", 0) > catalog_len:
        return True, (
            f"Drive CSV has {largest.get('rows')} rows but catalog has {catalog_len} — importing"
        )
    if not CANONICAL_PATH.is_file():
        return False, "No collx_export.csv in current/"
    meta = load_meta()
    fp = _file_fingerprint(CANONICAL_PATH)
    if fp and fp != meta.get("last_import_fingerprint"):
        return True, "Export file changed (new content)"
    last_at = meta.get("last_import_at")
    if not last_at:
        return True, "Never imported yet"
    try:
        imported = datetime.fromisoformat(last_at)
        if imported.tzinfo is None:
            imported = imported.replace(tzinfo=timezone.utc)
        canon_mtime = datetime.fromtimestamp(
            CANONICAL_PATH.stat().st_mtime, tz=timezone.utc
        ).astimezone()
        if canon_mtime > imported.astimezone():
            return True, "Export file newer than last import"
    except (OSError, ValueError):
        return True, "Could not compare timestamps"
    return False, "Same export already imported"


def fetch_and_import_collx(use_gmail: bool = True) -> dict[str, Any]:
    """Auto path: optional Gmail → consolidate → import if new."""
    result: dict[str, Any] = {"gmail": None, "consolidate": None, "import": None}
    if use_gmail:
        try:
            from collx_gmail import pull_collx_csv_from_gmail

            result["gmail"] = pull_collx_csv_from_gmail()
        except ImportError:
            result["gmail"] = {"status": "skipped", "message": "collx_gmail not available"}
        except Exception as exc:
            result["gmail"] = {"status": "error", "message": str(exc)}
    else:
        result["gmail"] = {"status": "skipped", "message": "Gmail not requested"}

    meta = load_meta()
    meta["last_poll_at"] = _now()
    inbox_mt = _inbox_activity_mtime()
    inbox_changed = inbox_mt > float(meta.get("last_inbox_mtime", 0))
    meta["last_inbox_mtime"] = inbox_mt
    _save_json(META_FILE, meta)

    result["consolidate"] = consolidate_new_exports()
    consolidate_new = bool(result["consolidate"].get("new"))
    result["promote"] = promote_largest_export_to_canonical()
    promote_new = bool(result["promote"].get("new"))
    gmail_ok = (result.get("gmail") or {}).get("status") == "ok"
    should_import, import_reason = _should_import_canonical()
    if promote_new:
        should_import = True
        import_reason = f"Larger export on Drive ({result['promote'].get('rows')} rows)"
    if inbox_changed and _inbox_root_csvs():
        should_import = True
        import_reason = "New file detected in collx_inbox/"

    if CANONICAL_PATH.is_file() and (consolidate_new or promote_new or gmail_ok or should_import or inbox_changed):
        try:
            text = CANONICAL_PATH.read_text(encoding="utf-8", errors="replace")
            imp = import_csv_text(text, source=str(CANONICAL_PATH), mode="replace")
            imp["import_reason"] = import_reason
            result["import"] = imp
            if imp.get("status") == "success":
                imp["tidy"] = tidy_inbox_after_import(imp.get("imported"))
                meta = load_meta()
                meta["last_canonical_mtime"] = CANONICAL_PATH.stat().st_mtime
                meta["last_import_fingerprint"] = _file_fingerprint(CANONICAL_PATH)
                meta["last_poll_at"] = _now()
                _save_json(META_FILE, meta)
        except OSError as exc:
            result["import"] = {"status": "error", "message": str(exc)}
    else:
        result["import"] = {
            "status": "skipped",
            "message": import_reason if CANONICAL_PATH.is_file() else "No CollX CSV on Drive yet",
        }

    result["status"] = (
        "success"
        if result.get("import", {}).get("status") == "success"
        else result.get("import", {}).get("status", "skipped")
    )
    meta = load_meta()
    imp = result.get("import") or {}
    meta["last_fetch_status"] = result["status"]
    meta["last_fetch_summary"] = (
        f"imported {imp.get('imported', 0)}"
        if imp.get("status") == "success"
        else imp.get("message", result["status"])
    )
    meta["last_poll_at"] = _now()
    _save_json(META_FILE, meta)
    try:
        audit = audit_pipeline()
        result["audit"] = {
            "verdict": audit.get("verdict"),
            "verdict_detail": audit.get("verdict_detail"),
            "best_source_rows": audit.get("best_source_rows"),
            "catalog_count": audit.get("catalog_count"),
            "expected": audit.get("expected"),
        }
    except Exception as exc:
        result["audit"] = {"error": str(exc)}

    try:
        from dev_log import log_fetch_result, log

        log_fetch_result(result, trigger="fetch_and_import")
        if result.get("audit"):
            log("collx_audit_summary", **result["audit"])
    except ImportError:
        pass
    return result


def diagnostic_snapshot() -> dict[str, Any]:
    """Compact state for developer debug log (missing cards, Drive paths)."""
    catalog = load_catalog()
    meta = load_meta()
    collection = _load_json(COLLECTION_FILE, [])
    if not isinstance(collection, list):
        collection = []
    total_mid = round(
        sum((c.get("valuation") or {}).get("estimate_mid") or 0 for c in collection if isinstance(c, dict)),
        2,
    )
    expected = load_collx_expected()
    largest = largest_collx_csv_on_drive()
    inbox_pending = [str(p) for p in _inbox_root_csvs()]
    canon_preview = preview_collx_csv(CANONICAL_PATH) if CANONICAL_PATH.is_file() else None
    discovered = discover_collx_csv_paths(limit=8)
    missing_items = None
    if expected.get("items") and len(catalog) < expected["items"]:
        missing_items = expected["items"] - len(catalog)
    return {
        "catalog_count": len(catalog),
        "collection_count": len(collection),
        "collection_total_mid": total_mid,
        "expected_items": expected.get("items"),
        "expected_total": expected.get("total"),
        "missing_items_vs_expected": missing_items,
        "canonical_path": str(CANONICAL_PATH),
        "canonical_exists": CANONICAL_PATH.is_file(),
        "canonical_preview": canon_preview,
        "drive_largest_csv": largest,
        "inbox_root_csvs": inbox_pending,
        "inbox_root_count": len(inbox_pending),
        "last_import_at": meta.get("last_import_at"),
        "last_import_rows": meta.get("last_import_rows"),
        "last_fetch_summary": meta.get("last_fetch_summary"),
        "csv_candidates_top": discovered,
    }


def status() -> dict[str, Any]:
    catalog = load_catalog()
    meta = load_meta()
    priced = sum(1 for c in catalog if c.get("price") is not None)
    discovered = discover_collx_csv_paths(limit=3)
    inbox = ensure_inbox_layout()
    inbox_root_csv = len(_inbox_root_csvs())
    pending = [str(p) for p in _inbox_root_csvs()]
    largest = largest_collx_csv_on_drive()
    expected = load_collx_expected()
    collection = _load_json(COLLECTION_FILE, [])
    total_mid = round(
        sum(
            (c.get("valuation") or {}).get("estimate_mid") or 0
            for c in collection
            if isinstance(c, dict)
        ),
        2,
    )
    mismatch = ""
    if expected.get("items") and len(catalog) < expected["items"]:
        mismatch = (
            f"CollX app shows ~{expected['items']} items but Drive import has {len(catalog)}. "
            "Full CSV not on Drive yet — drag new export to collx_inbox/."
        )
    elif expected.get("total") and total_mid and abs(total_mid - expected["total"]) > 50:
        mismatch = (
            f"CollX total ~${expected['total']:.0f} but app shows ${total_mid:.2f}. "
            "Need fresher/larger export on Drive."
        )
    elif largest and len(catalog) < largest.get("rows", 0):
        mismatch = (
            f"Drive has a {largest.get('rows')}-row CSV (${largest.get('total_mid')}) "
            f"but only {len(catalog)} imported — tap Check for new export."
        )

    canon_preview = preview_collx_csv(CANONICAL_PATH) if CANONICAL_PATH.is_file() else None
    if canon_preview and CANONICAL_PATH.is_file():
        try:
            canon_preview["modified"] = datetime.fromtimestamp(
                CANONICAL_PATH.stat().st_mtime, tz=timezone.utc
            ).astimezone().isoformat()
        except OSError:
            pass

    return {
        "catalog_count": len(catalog),
        "collection_count": len(collection) if isinstance(collection, list) else 0,
        "collection_total_mid": total_mid,
        "priced_count": priced,
        "expected_items": expected.get("items"),
        "expected_total": expected.get("total"),
        "drive_largest_csv": largest,
        "canonical_preview": canon_preview,
        "mismatch_warning": mismatch,
        "sync_state": (
            "stale_export"
            if expected.get("items") and len(catalog) < expected["items"]
            else "ok"
        ),
        "last_import_at": meta.get("last_import_at"),
        "last_import_source": meta.get("last_import_source"),
        "last_import_rows": meta.get("last_import_rows", 0),
        "drive_scan_paths": [str(p) for p in DRIVE_CANDIDATES[:4]],
        "inbox_path": str(inbox),
        "current_path": str(COLLX_CURRENT),
        "canonical_path": str(CANONICAL_PATH),
        "canonical_exists": CANONICAL_PATH.is_file(),
        "inbox_exists": inbox.is_dir(),
        "inbox_root_csv_count": inbox_root_csv,
        "pending_inbox_files": pending,
        "last_poll_at": meta.get("last_poll_at"),
        "last_import_fingerprint": meta.get("last_import_fingerprint"),
        "import_slot_hint": f"Drop CSV in collx_inbox/ OR save as {CANONICAL_PATH}",
        "csv_found_on_disk": len(discovered),
        "csv_candidates": discovered,
        "auto_fetch": True,
        "poll_interval_sec": 30,
        "last_fetch_status": meta.get("last_fetch_status"),
        "last_fetch_summary": meta.get("last_fetch_summary"),
        "data_mode": "collx",
    }


def valuation_from_price(
    price: float | None,
    source_id: str | None = None,
    match_key: str | None = None,
) -> dict[str, Any]:
    if price is None:
        return {
            "estimate_low": None,
            "estimate_mid": None,
            "estimate_high": None,
            "grade_hint": None,
            "era": None,
            "method": "collx",
            "priced": False,
            "collx_id": source_id,
            "match_key": match_key,
        }
    mid = round(float(price), 2)
    return {
        "estimate_low": round(mid * 0.9, 2),
        "estimate_mid": mid,
        "estimate_high": round(mid * 1.1, 2),
        "grade_hint": "CollX market",
        "era": None,
        "method": "collx",
        "priced": True,
        "collx_id": source_id,
        "match_key": match_key,
    }


def find_match(
    player: str,
    year: int,
    card_set: str,
    card_number: str = "",
    catalog: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    catalog = catalog or load_catalog()
    if not catalog:
        return None
    idx = catalog_index(catalog)
    key = _card_key(player, year, card_set, card_number)
    if key in idx:
        return idx[key]
    # Fuzzy: same player+year+set without number
    loose = _card_key(player, year, card_set, "")
    if loose in idx:
        return idx[loose]
    player_n = _norm_token(player)
    year_s = str(year)
    set_n = _norm_token(card_set)
    for row in catalog:
        if (
            _norm_token(row.get("player", "")) == player_n
            and str(row.get("year", "")).strip() == year_s
            and _norm_token(row.get("set", "")) == set_n
        ):
            return row
    return None


def parse_csv_text(text: str, source: str = "upload") -> tuple[list[dict[str, Any]], dict[str, Any]]:
    _ensure_dirs()
    if not text.strip():
        return [], {"error": "Empty CSV"}

    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    if not reader.fieldnames:
        return [], {"error": "CSV has no header row"}

    header_map = {_norm_header(h): h for h in reader.fieldnames if h}

    def row_get(raw_row: dict[str, Any], keys: tuple[str, ...]) -> str:
        for k in keys:
            orig = header_map.get(k)
            if orig and raw_row.get(orig):
                return str(raw_row[orig]).strip()
        return ""

    catalog: list[dict[str, Any]] = []
    skipped = 0
    for raw in reader:
        norm_row = {_norm_header(k): (v or "").strip() for k, v in raw.items() if k}
        player = _pick(norm_row, PLAYER_KEYS)
        year_raw = _pick(norm_row, YEAR_KEYS)
        card_set = _pick(norm_row, SET_KEYS) or "Unknown"
        card_number = _pick(norm_row, NUMBER_KEYS)
        if not player and not year_raw:
            skipped += 1
            continue
        try:
            year = int(re.sub(r"[^0-9]", "", year_raw)[:4] or "0")
        except ValueError:
            year = 0
        if year < 1880:
            skipped += 1
            continue

        price_raw, price = _pick_market_price(norm_row)
        asking_raw, asking = _pick_price(norm_row, ASKING_PRICE_KEYS)
        purchase_raw, purchase = _pick_price(norm_row, PURCHASE_PRICE_KEYS)
        sold_raw, sold = _pick_price(norm_row, SOLD_PRICE_KEYS)
        front_image, back_image = _pick_image(norm_row)
        image_url = front_image or back_image
        csv_id = _pick(norm_row, COLLX_ID_KEYS)
        collx_id = csv_id or str(uuid.uuid4())[:12]
        flags_raw = _pick(norm_row, FLAGS_KEYS)
        flags = flags_raw.lower()
        rookie = _parse_bool(_pick(norm_row, ROOKIE_KEYS)) or "rookie" in flags or flags == "rc" or "rc" in flags
        autograph = _parse_bool(_pick(norm_row, AUTO_KEYS)) or "auto" in flags or "au" in flags
        record = {
            "collx_id": collx_id,
            "player": player,
            "year": year,
            "set": card_set,
            "card_number": card_number,
            "condition": _pick(norm_row, CONDITION_KEYS) or "Unknown",
            "grade": _pick(norm_row, GRADE_KEYS),
            "team": _pick(norm_row, TEAM_KEYS),
            "brand": _pick(norm_row, BRAND_KEYS),
            "category": _pick(norm_row, CATEGORY_KEYS),
            "added": _pick(norm_row, ADDED_KEYS),
            "quantity": _pick(norm_row, QUANTITY_KEYS) or "1",
            "location": _pick(norm_row, LOCATION_KEYS),
            "flags": flags_raw,
            "notes": _pick(norm_row, NOTES_KEYS),
            "rookie": rookie,
            "autograph": autograph,
            "image_url": image_url,
            "back_image_url": back_image,
            "price": price,
            "price_raw": price_raw,
            "asking_price": asking,
            "asking_price_raw": asking_raw,
            "purchase_price": purchase,
            "purchase_price_raw": purchase_raw,
            "sold_price": sold,
            "sold_price_raw": sold_raw,
            "match_key": _card_key(player, year, card_set, card_number),
            "imported_at": _now(),
            "source": source,
        }
        catalog.append(record)

    meta = {
        "last_import_at": _now(),
        "last_import_source": source,
        "last_import_rows": len(catalog),
        "skipped_rows": skipped,
    }
    return catalog, meta


def _dev_log_import(event: str, payload: dict[str, Any]) -> None:
    try:
        from dev_log import log

        log(event, **payload, snapshot=diagnostic_snapshot())
    except ImportError:
        pass


def import_csv_text(text: str, source: str = "upload", mode: str = "replace") -> dict[str, Any]:
    catalog, meta = parse_csv_text(text, source=source)
    if meta.get("error"):
        err = {"status": "error", "message": meta["error"]}
        _dev_log_import("import_csv", {**err, "source": source, "mode": mode})
        return err

    if not catalog:
        err = {
            "status": "error",
            "message": "No valid card rows found in CSV. Export from CollX Pro (Player, Year, Set, Price columns).",
        }
        _dev_log_import("import_csv", {**err, "source": source, "mode": mode})
        return err

    _save_json(CATALOG_FILE, catalog)
    existing_meta = load_meta()
    existing_meta.update(meta)
    existing_meta["mode"] = mode
    _save_json(META_FILE, existing_meta)

    collection_cards = catalog_to_collection(catalog)
    if mode == "replace":
        _save_json(COLLECTION_FILE, collection_cards)
    else:
        current = _load_json(COLLECTION_FILE, [])
        if not isinstance(current, list):
            current = []
        current_keys = {c.get("match_key") or _card_key(c.get("player", ""), c.get("year", ""), c.get("set", ""), c.get("card_number", "")) for c in current}
        for card in collection_cards:
            key = card.get("match_key")
            if key not in current_keys:
                current.insert(0, card)
                current_keys.add(key)
        _save_json(COLLECTION_FILE, current)

    expected = load_collx_expected()
    imported_n = len(catalog)
    result = {
        "status": "success",
        "imported": imported_n,
        "skipped": meta.get("skipped_rows", 0),
        "collection_count": len(_load_json(COLLECTION_FILE, [])),
        "source": source,
        "mode": mode,
        "expected_items": expected.get("items"),
        "expected_total": expected.get("total"),
        "tidy": tidy_inbox_after_import(imported_n),
    }
    if expected.get("items") and imported_n < expected["items"] - 15:
        result["warning"] = (
            f"Imported {imported_n} cards but CollX app expects ~{expected['items']} — "
            "source CSV may be incomplete (garbage in)."
        )
    _dev_log_import("import_csv", result)
    try:
        import sys
        if str(Path.home() / ".stan") not in sys.path:
            sys.path.insert(0, str(Path.home() / ".stan"))
        import brian_os

        brian_os.refresh_brian_status(
            waiting_note=f"Imported {len(catalog)} cards from CollX"
        )
    except Exception:
        pass
    return result


def catalog_to_collection(catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for row in catalog:
        price = row.get("price")
        valuation = valuation_from_price(price, row.get("collx_id"), row.get("match_key"))
        image_url = row.get("image_url") or ""
        thumb = thumb_api_path(row.get("collx_id", "")) if image_url else None
        cards.append(
            {
                "id": str(uuid.uuid4())[:8],
                "collx_id": row.get("collx_id"),
                "match_key": row.get("match_key"),
                "player": row.get("player", ""),
                "year": row.get("year"),
                "set": row.get("set", ""),
                "card_number": row.get("card_number", ""),
                "condition": row.get("condition", "Unknown"),
                "grade": row.get("grade", ""),
                "team": row.get("team", ""),
                "brand": row.get("brand", ""),
                "category": row.get("category", ""),
                "flags": row.get("flags", ""),
                "added": row.get("added", ""),
                "quantity": row.get("quantity", "1"),
                "location": row.get("location", ""),
                "rookie": bool(row.get("rookie")),
                "autograph": bool(row.get("autograph")),
                "notes": row.get("notes", ""),
                "image": thumb,
                "image_url": image_url,
                "valuation": valuation,
                "collx_prices": {
                    "market": row.get("price"),
                    "asking": row.get("asking_price"),
                    "purchase": row.get("purchase_price"),
                    "sold": row.get("sold_price"),
                },
                "created_at": _now(),
                "source": "collx_import",
            }
        )
    return cards


def search_catalog(query: str, limit: int = 25) -> list[dict[str, Any]]:
    q = (query or "").strip().lower()
    catalog = load_catalog()
    if not q:
        return catalog[:limit]
    tokens = [t for t in re.split(r"\s+", q) if t]
    results: list[dict[str, Any]] = []
    for row in catalog:
        blob = " ".join(
            str(row.get(k, ""))
            for k in ("player", "set", "year", "card_number", "team", "notes")
        ).lower()
        if all(t in blob for t in tokens):
            results.append(row)
        if len(results) >= limit:
            break
    return results


def estimate_from_collx(
    player: str,
    year: int,
    card_set: str,
    condition: str,
    rookie: bool = False,
    autograph: bool = False,
    card_number: str = "",
) -> dict[str, Any]:
    catalog = load_catalog()
    if not catalog:
        return {
            **valuation_from_price(None),
            "message": "Import CollX CSV first — no catalog loaded.",
        }
    match = find_match(player, year, card_set, card_number, catalog)
    if not match:
        return {
            **valuation_from_price(None),
            "message": "No CollX match for this card in your imported data.",
        }
    val = valuation_from_price(match.get("price"), match.get("collx_id"), match.get("match_key"))
    val["matched_player"] = match.get("player")
    val["matched_set"] = match.get("set")
    return val


def _peek_csv_headers(path: Path) -> list[str]:
    try:
        sample = path.read_text(encoding="utf-8", errors="replace")[:4096]
        if not sample.strip():
            return []
        try:
            dialect = csv.Sniffer().sniff(sample[:2048], delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(io.StringIO(sample), dialect=dialect)
        row = next(reader, None)
        return [_norm_header(h) for h in row or [] if h]
    except OSError:
        return []


def _score_collx_headers(headers: list[str]) -> int:
    if not headers:
        return 0
    score = 0
    header_set = set(headers)
    if any(k in header_set for k in PLAYER_KEYS):
        score += 3
    if any(k in header_set for k in YEAR_KEYS):
        score += 2
    if any(k in header_set for k in SET_KEYS):
        score += 2
    price_keys = MARKET_PRICE_KEYS + ASKING_PRICE_KEYS + PURCHASE_PRICE_KEYS + SOLD_PRICE_KEYS + LEGACY_PRICE_KEYS
    if any(k in header_set for k in price_keys):
        score += 3
    if any(k in header_set for k in IMAGE_FRONT_KEYS):
        score += 2
    if any(k in header_set for k in NUMBER_KEYS):
        score += 1
    blob = " ".join(headers)
    if "collx" in blob:
        score += 2
    return score


def discover_collx_csv_paths(limit: int = 20) -> list[dict[str, Any]]:
    """Find any CSV on Drive/Downloads that looks like a CollX export."""
    found: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(path: Path, priority: int = 0) -> None:
        key = str(path.resolve())
        if key in seen or not path.is_file():
            return
        seen.add(key)
        headers = _peek_csv_headers(path)
        score = _score_collx_headers(headers) + priority
        if score < 4:
            return
        try:
            st = path.stat()
        except OSError:
            return
        found.append(
            {
                "path": str(path),
                "score": score,
                "size_bytes": st.st_size,
                "modified": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).astimezone().isoformat(),
                "headers": headers[:12],
            }
        )

    for fixed in DRIVE_CANDIDATES:
        add(fixed, priority=5)

    if CANONICAL_PATH.is_file():
        add(CANONICAL_PATH, priority=10)

    for root in SCAN_ROOTS:
        if not root.is_dir():
            continue
        if root == COLLX_ARCHIVE:
            continue
        depth = 0 if root in (COLLX_INBOX, COLLX_CURRENT) else 3
        try:
            for dirpath, dirnames, filenames in os.walk(root):
                if COLLX_ARCHIVE.name in dirnames:
                    dirnames.remove(COLLX_ARCHIVE.name)
                rel = Path(dirpath).relative_to(root)
                if len(rel.parts) > depth:
                    dirnames.clear()
                    continue
                for name in filenames:
                    if not name.lower().endswith(".csv"):
                        continue
                    add(Path(dirpath) / name)
        except OSError:
            continue

    found.sort(key=lambda x: (-x["score"], -Path(x["path"]).stat().st_mtime))
    return found[:limit]


def auto_import_from_drive() -> dict[str, Any]:
    """Consolidate inbox → single canonical file → import if new."""
    return fetch_and_import_collx(use_gmail=False)


def reset_collection(keep_catalog: bool = True) -> dict[str, Any]:
    _save_json(COLLECTION_FILE, [])
    if not keep_catalog:
        _save_json(CATALOG_FILE, [])
        _save_json(META_FILE, {})
    return {"status": "success", "collection_count": 0, "catalog_kept": keep_catalog}


def reimport_last_source() -> dict[str, Any]:
    meta = load_meta()
    source = meta.get("last_import_source")
    if not source or not Path(source).is_file():
        for candidate in DRIVE_CANDIDATES:
            if candidate.is_file():
                source = str(candidate)
                break
    if not source:
        return {"status": "error", "message": "No prior CollX CSV path found."}
    text = Path(source).read_text(encoding="utf-8", errors="replace")
    return import_csv_text(text, source=source, mode="replace")


def find_catalog_image(collx_id: str) -> str | None:
    for row in load_catalog():
        if str(row.get("collx_id")) == str(collx_id):
            url = row.get("image_url") or row.get("back_image_url")
            return url if url else None
    return None


def purge_test_cards() -> dict[str, Any]:
    cards = _load_json(COLLECTION_FILE, [])
    if not isinstance(cards, list):
        cards = []
    test_pat = re.compile(r"test|sounds good|phase1|example|demo", re.I)
    kept = [c for c in cards if not test_pat.search(c.get("player", ""))]
    removed = len(cards) - len(kept)
    _save_json(COLLECTION_FILE, kept)
    return {"status": "success", "removed": removed, "remaining": len(kept)}
