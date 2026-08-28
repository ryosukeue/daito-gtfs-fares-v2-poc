from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ZIP = PROJECT_ROOT / "data" / "raw" / "daito_gtfs_2026.zip"
DEFAULT_EXTRACTED = PROJECT_ROOT / "data" / "raw" / "extracted"
DEFAULT_PROCESSED = PROJECT_ROOT / "data" / "processed"
DEFAULT_DIST = PROJECT_ROOT / "dist" / "daito_gtfs_fares_v2.zip"

SOURCE_URL = "https://www.city.daito.lg.jp/uploaded/attachment/41955.zip"
SOURCE_PAGE = "https://www.city.daito.lg.jp/site/kokyokotsu/68741.html"
RESEARCH_DATE = "2026-08-28"


def decode_gtfs(data: bytes, filename: str = "") -> tuple[str, str]:
    """Decode a GTFS text file and report the encoding actually used."""
    for encoding in ("utf-8-sig", "cp932"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("utf-8/cp932", data, 0, len(data), f"cannot decode {filename}")


def read_csv_bytes(data: bytes, filename: str = "") -> tuple[list[dict[str, str]], list[str], str]:
    text, encoding = decode_gtfs(data, filename)
    reader = csv.DictReader(io.StringIO(text, newline=""))
    fields = [field for field in (reader.fieldnames or []) if field]
    rows: list[dict[str, str]] = []
    for raw in reader:
        rows.append({field: (raw.get(field) or "") for field in fields})
    return rows, fields, encoding


def read_csv_path(path: Path) -> tuple[list[dict[str, str]], list[str], str]:
    return read_csv_bytes(path.read_bytes(), path.name)


def write_csv_path(path: Path, fields: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\r\n", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

