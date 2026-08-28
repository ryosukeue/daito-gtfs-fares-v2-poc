from __future__ import annotations

import argparse
import collections
import json
import zipfile
from pathlib import Path

try:
    from .common import DEFAULT_ZIP, read_csv_bytes, sha256, write_json
except ImportError:  # Direct execution
    from common import DEFAULT_ZIP, read_csv_bytes, sha256, write_json


CORE_FILES = [
    "agency.txt", "routes.txt", "trips.txt", "stops.txt", "stop_times.txt",
    "calendar.txt", "calendar_dates.txt", "fare_attributes.txt", "fare_rules.txt",
]


def inspect_zip(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        names = sorted(name for name in archive.namelist() if not name.endswith("/"))
        parsed: dict[str, list[dict[str, str]]] = {}
        files: dict[str, object] = {}
        for name in names:
            payload = archive.read(name)
            rows, fields, encoding = read_csv_bytes(payload, name)
            parsed[name] = rows
            files[name] = {
                "rows": len(rows),
                "fields": fields,
                "encoding": encoding,
                "has_empty_header": any(not field for field in payload.decode(encoding, errors="replace").splitlines()[0].split(",")),
            }

    routes = parsed.get("routes.txt", [])
    trips = parsed.get("trips.txt", [])
    fare_rules = parsed.get("fare_rules.txt", [])
    route_names = {row["route_id"]: row.get("route_long_name", "") for row in routes}
    trip_counts = collections.Counter(row["route_id"] for row in trips)
    fare_counts = collections.Counter(row["fare_id"] for row in fare_rules)

    route_ids = set(route_names)
    stop_ids = {row["stop_id"] for row in parsed.get("stops.txt", [])}
    trip_ids = {row["trip_id"] for row in trips}
    service_ids = {row["service_id"] for row in parsed.get("calendar.txt", [])}
    service_ids |= {row["service_id"] for row in parsed.get("calendar_dates.txt", [])}
    issues: list[dict[str, object]] = []

    checks = {
        "fare_rule_route": [row for row in fare_rules if row["route_id"] not in route_ids],
        "fare_rule_origin": [row for row in fare_rules if row["origin_id"] not in stop_ids],
        "fare_rule_destination": [row for row in fare_rules if row["destination_id"] not in stop_ids],
        "trip_route": [row for row in trips if row["route_id"] not in route_ids],
        "trip_service": [row for row in trips if row["service_id"] not in service_ids],
        "stop_time_trip": [row for row in parsed.get("stop_times.txt", []) if row["trip_id"] not in trip_ids],
        "stop_time_stop": [row for row in parsed.get("stop_times.txt", []) if row["stop_id"] not in stop_ids],
    }
    for check, bad_rows in checks.items():
        if bad_rows:
            issues.append({"severity": "ERROR", "check": check, "count": len(bad_rows)})
    for name, info in files.items():
        if info["encoding"] != "utf-8-sig":
            issues.append({"severity": "ERROR", "check": "not_utf8", "file": name, "encoding": info["encoding"]})
        if info["has_empty_header"]:
            issues.append({"severity": "WARNING", "check": "empty_header", "file": name})

    return {
        "source": str(path),
        "sha256": sha256(path),
        "files": files,
        "routes": [
            {"route_id": route_id, "route_long_name": name, "trips": trip_counts[route_id]}
            for route_id, name in route_names.items()
        ],
        "fare_rule_counts": dict(sorted(fare_counts.items())),
        "issues": issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect a Daito City GTFS ZIP")
    parser.add_argument("input", type=Path, nargs="?", default=DEFAULT_ZIP)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = inspect_zip(args.input)
    if args.output:
        write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
