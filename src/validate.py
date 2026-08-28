from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

try:
    from .common import DEFAULT_DIST, read_csv_bytes, write_json
except ImportError:  # Direct execution
    from common import DEFAULT_DIST, read_csv_bytes, write_json


REQUIRED_FILES = {"agency.txt", "routes.txt", "trips.txt", "stops.txt", "stop_times.txt"}
FARES_V2_FILES = {
    "rider_categories.txt", "fare_media.txt", "fare_products.txt", "fare_leg_rules.txt",
    "fare_transfer_rules.txt", "areas.txt", "stop_areas.txt",
}


def validate(path: Path) -> dict[str, object]:
    notices: list[dict[str, object]] = []

    def add(severity: str, code: str, message: str, **context: object) -> None:
        notices.append({"severity": severity, "code": code, "message": message, **context})

    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if any("/" in name.rstrip("/") for name in names):
            add("ERROR", "FILES_IN_SUBDIRECTORY", "GTFS files must be at ZIP root")
        duplicate_names = [name for name, count in Counter(names).items() if count > 1]
        for name in duplicate_names:
            add("ERROR", "DUPLICATE_FILE", "Duplicate ZIP entry", file=name)
        files = {name: archive.read(name) for name in names if name.endswith(".txt")}

    for name in sorted(REQUIRED_FILES - set(files)):
        add("ERROR", "MISSING_REQUIRED_FILE", "Required GTFS file is missing", file=name)
    for name in sorted(FARES_V2_FILES - set(files)):
        add("ERROR", "MISSING_FARES_V2_FILE", "Expected PoC Fares v2 file is missing", file=name)

    tables: dict[str, list[dict[str, str]]] = {}
    fields: dict[str, list[str]] = {}
    for name, payload in files.items():
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            add("ERROR", "INVALID_UTF8", "File is not valid UTF-8", file=name, offset=exc.start)
            continue
        try:
            rows, header, _ = read_csv_bytes(payload, name)
        except (csv.Error, UnicodeDecodeError) as exc:
            add("ERROR", "INVALID_CSV", str(exc), file=name)
            continue
        tables[name], fields[name] = rows, header
        if not header or any(not field for field in header):
            add("ERROR", "EMPTY_HEADER", "CSV contains an empty header", file=name)
        for index, row in enumerate(rows, start=2):
            if None in row:
                add("ERROR", "EXTRA_COLUMN", "CSV row has an unnamed extra value", file=name, row=index)

    required_fields = {
        "agency.txt": ["agency_name", "agency_url", "agency_timezone"],
        "routes.txt": ["route_id", "route_type", "network_id"],
        "trips.txt": ["route_id", "service_id", "trip_id"],
        "stops.txt": ["stop_id", "stop_name"],
        "stop_times.txt": ["trip_id", "stop_id", "stop_sequence"],
        "rider_categories.txt": ["rider_category_id", "rider_category_name", "is_default_fare_category"],
        "fare_media.txt": ["fare_media_id", "fare_media_type"],
        "fare_products.txt": ["fare_product_id", "amount", "currency"],
        "fare_leg_rules.txt": ["network_id", "from_area_id", "to_area_id", "fare_product_id"],
        "fare_transfer_rules.txt": ["fare_transfer_type"],
        "areas.txt": ["area_id"],
        "stop_areas.txt": ["area_id", "stop_id"],
    }
    for filename, names in required_fields.items():
        if filename not in tables:
            continue
        for field in names:
            if field not in fields[filename]:
                add("ERROR", "MISSING_FIELD", "Required field missing", file=filename, field=field)
            elif any(not row.get(field, "") for row in tables[filename]):
                add("ERROR", "MISSING_VALUE", "Required field has empty values", file=filename, field=field)

    primary_keys = {
        "routes.txt": ["route_id"], "trips.txt": ["trip_id"], "stops.txt": ["stop_id"],
        "rider_categories.txt": ["rider_category_id"], "fare_media.txt": ["fare_media_id"],
        "fare_products.txt": ["fare_product_id", "rider_category_id", "fare_media_id"],
        "fare_leg_rules.txt": ["network_id", "from_area_id", "to_area_id", "from_timeframe_group_id", "to_timeframe_group_id", "fare_product_id"],
        "fare_transfer_rules.txt": ["from_leg_group_id", "to_leg_group_id", "fare_product_id", "transfer_count", "duration_limit"],
        "areas.txt": ["area_id"], "stop_areas.txt": ["area_id", "stop_id"],
    }
    for filename, keys in primary_keys.items():
        if filename not in tables:
            continue
        seen: set[tuple[str, ...]] = set()
        for index, row in enumerate(tables[filename], start=2):
            key = tuple(row.get(field, "") for field in keys)
            if key in seen:
                add("ERROR", "DUPLICATE_PRIMARY_KEY", "Duplicate primary key", file=filename, row=index, key=key)
            seen.add(key)

    ids = {
        "route": {row["route_id"] for row in tables.get("routes.txt", [])},
        "trip": {row["trip_id"] for row in tables.get("trips.txt", [])},
        "stop": {row["stop_id"] for row in tables.get("stops.txt", [])},
        "area": {row["area_id"] for row in tables.get("areas.txt", [])},
        "category": {row["rider_category_id"] for row in tables.get("rider_categories.txt", [])},
        "media": {row["fare_media_id"] for row in tables.get("fare_media.txt", [])},
        "product": {row["fare_product_id"] for row in tables.get("fare_products.txt", [])},
        "leg_group": {row.get("leg_group_id", "") for row in tables.get("fare_leg_rules.txt", []) if row.get("leg_group_id")},
    }
    foreign_checks = [
        ("trips.txt", "route_id", "route"), ("stop_times.txt", "trip_id", "trip"),
        ("stop_times.txt", "stop_id", "stop"), ("stop_areas.txt", "stop_id", "stop"),
        ("stop_areas.txt", "area_id", "area"), ("fare_products.txt", "rider_category_id", "category"),
        ("fare_products.txt", "fare_media_id", "media"), ("fare_leg_rules.txt", "from_area_id", "area"),
        ("fare_leg_rules.txt", "to_area_id", "area"), ("fare_leg_rules.txt", "fare_product_id", "product"),
        ("fare_transfer_rules.txt", "from_leg_group_id", "leg_group"),
        ("fare_transfer_rules.txt", "to_leg_group_id", "leg_group"),
        ("fare_transfer_rules.txt", "fare_product_id", "product"),
    ]
    for filename, field, target in foreign_checks:
        for index, row in enumerate(tables.get(filename, []), start=2):
            value = row.get(field, "")
            if value and value not in ids[target]:
                add("ERROR", "BAD_FOREIGN_KEY", "Foreign key not found", file=filename, row=index, field=field, value=value)

    network_ids = {row.get("network_id", "") for row in tables.get("routes.txt", [])}
    for index, row in enumerate(tables.get("fare_leg_rules.txt", []), start=2):
        if row.get("network_id") not in network_ids:
            add("ERROR", "BAD_NETWORK_REFERENCE", "Fare leg network does not occur in routes.txt", row=index)
    for index, row in enumerate(tables.get("fare_products.txt", []), start=2):
        try:
            float(row.get("amount", ""))
        except ValueError:
            add("ERROR", "INVALID_AMOUNT", "Fare product amount is not numeric", row=index)
        if row.get("currency") != "JPY":
            add("WARNING", "UNEXPECTED_CURRENCY", "Expected JPY for Daito City", row=index)

    for filename in ("calendar.txt", "calendar_dates.txt", "feed_info.txt"):
        for index, row in enumerate(tables.get(filename, []), start=2):
            for field in ("start_date", "end_date", "date", "feed_start_date", "feed_end_date"):
                value = row.get(field, "")
                if value:
                    try:
                        dt.datetime.strptime(value, "%Y%m%d")
                    except ValueError:
                        add("ERROR", "INVALID_DATE", "Date must be YYYYMMDD", file=filename, row=index, field=field, value=value)

    counts = Counter(notice["severity"] for notice in notices)
    return {
        "input": str(path),
        "summary": {"errors": counts["ERROR"], "warnings": counts["WARNING"], "notices": len(notices)},
        "tables": {name: len(rows) for name, rows in sorted(tables.items())},
        "notices": notices,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run project-specific GTFS/Fares v2 checks")
    parser.add_argument("input", type=Path, nargs="?", default=DEFAULT_DIST)
    parser.add_argument("--output", type=Path, default=Path("reports/custom_validation.json"))
    args = parser.parse_args()
    result = validate(args.input)
    write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result["summary"]["errors"] else 0)


if __name__ == "__main__":
    main()
