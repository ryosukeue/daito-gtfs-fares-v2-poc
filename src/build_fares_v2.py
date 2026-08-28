from __future__ import annotations

import argparse
import csv
import io
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path

try:
    from .common import DEFAULT_DIST, DEFAULT_PROCESSED, DEFAULT_ZIP, read_csv_bytes, write_csv_path
except ImportError:  # Direct execution
    from common import DEFAULT_DIST, DEFAULT_PROCESSED, DEFAULT_ZIP, read_csv_bytes, write_csv_path


COMMUNITY_ROUTES = {"R1", "R2", "R5", "R6", "R10", "R11", "R12", "R13", "R15"}
SOUTH_ROUTES = {"R9", "R14"}
TAXI_ROUTES = {"R3", "R4", "R7", "R8", "R16", "R17"}
NETWORK_FOR_ROUTE = {
    **{route: "daito_community" for route in COMMUNITY_ROUTES},
    **{route: "daito_south" for route in SOUTH_ROUTES},
    **{route: "daito_taxi" for route in TAXI_ROUTES},
}

PRODUCT_FOR_V1 = {
    ("daito_community", "Fare120yen_00"): "community_120",
    ("daito_community", "Fare240yen_00"): "community_240",
    ("daito_community", "Fare270yen_00"): "community_270",
    ("daito_south", "Fare300yen_00"): "south_300",
    ("daito_taxi", "Fare300yen_00"): "taxi_300",
    ("daito_taxi", "Fare330yen_00"): "taxi_330",
    ("daito_taxi", "Fare350yen_00"): "taxi_350",
    ("daito_taxi", "Fare390yen_00"): "taxi_390",
}

ELIGIBILITY_URL = "https://www.city.daito.lg.jp/site/kokyokotsu/67602.html"


def _row(product: str, name: str, category: str, media: str, amount: int) -> dict[str, str]:
    return {
        "fare_product_id": product,
        "fare_product_name": name,
        "rider_category_id": category,
        "fare_media_id": media,
        "amount": str(amount),
        "currency": "JPY",
    }


def build_fare_products() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for media in ("cash", "transit_ic", "child_icoca", "ic_excluding_pitapa"):
        rows.append(_row("community_120", "コミュニティバス特定区間", "", media, 120))

    community_tiers = {240: (120, 60), 270: (140, 70)}
    for adult, (discount, disabled_child) in community_tiers.items():
        product = f"community_{adult}"
        name = f"コミュニティバス{adult}円区間"
        rows += [
            _row(product, name, "adult", "cash", adult),
            _row(product, name, "adult", "transit_ic", adult),
            _row(product, name, "child", "cash", discount),
            _row(product, name, "child", "child_icoca", discount),
            _row(product, name, "senior_65_plus", "cash", discount),
            _row(product, name, "disability_community", "cash", discount),
            _row(product, name, "disability_community", "ic_excluding_pitapa", discount),
            _row(product, name, "disabled_child_community", "cash", disabled_child),
            _row(product, name, "disabled_child_community", "ic_excluding_pitapa", disabled_child),
        ]

    rows += [
        _row("south_300", "南部地域コミュニティバス", "adult", "cash", 300),
        _row("south_300", "南部地域コミュニティバス", "child", "cash", 150),
        _row("south_300", "南部地域コミュニティバス", "senior_65_plus", "cash", 150),
        _row("south_300", "南部地域コミュニティバス", "disability_south_taxi", "cash", 150),
        _row("south_300", "南部地域コミュニティバス", "disabled_child_south_taxi", "cash", 80),
    ]
    taxi_tiers = {300: (150, 80), 330: (170, 90), 350: (180, 90), 390: (200, 100)}
    for adult, (discount, disabled_child) in taxi_tiers.items():
        product = f"taxi_{adult}"
        name = f"東部地域乗合タクシー{adult}円区間"
        rows += [
            _row(product, name, "adult", "cash", adult),
            _row(product, name, "child", "cash", discount),
            _row(product, name, "senior_65_plus", "cash", discount),
            _row(product, name, "disability_south_taxi", "cash", discount),
            _row(product, name, "disabled_child_south_taxi", "cash", disabled_child),
        ]

    # fare_transfer_type=0 computes A + AB. AB is therefore the amount still
    # payable for the second leg after applying the published discount. This
    # avoids negative products and is accepted by older consumers/validators.
    rows.append(_row("transfer_pay_120_full", "120円区間同士の乗継時追加支払額", "", "transfer_ticket", 0))
    payable_by_target = {
        120: {"adult": 0, "child": 60, "senior_65_plus": 60, "disability_community": 60, "disabled_child_community": 90},
        240: {"adult": 120, "child": 60, "senior_65_plus": 60, "disability_community": 60, "disabled_child_community": 30},
        270: {"adult": 150, "child": 80, "senior_65_plus": 80, "disability_community": 80, "disabled_child_community": 40},
    }
    for target, category_amounts in payable_by_target.items():
        product = f"transfer_pay_{target}_standard"
        for category, amount in category_amounts.items():
            rows.append(_row(product, f"{target}円区間への乗継時追加支払額", category, "transfer_ticket", amount))
    return rows


def rider_categories() -> list[dict[str, str]]:
    return [
        {"rider_category_id": "adult", "rider_category_name": "大人", "is_default_fare_category": "1", "eligibility_url": ELIGIBILITY_URL},
        {"rider_category_id": "child", "rider_category_name": "小児", "is_default_fare_category": "0", "eligibility_url": ELIGIBILITY_URL},
        {"rider_category_id": "senior_65_plus", "rider_category_name": "65歳以上", "is_default_fare_category": "0", "eligibility_url": ELIGIBILITY_URL},
        {"rider_category_id": "disability_community", "rider_category_name": "コミュニティバス障害者等割引対象", "is_default_fare_category": "0", "eligibility_url": ELIGIBILITY_URL},
        {"rider_category_id": "disability_south_taxi", "rider_category_name": "南部・東部障害者等割引対象", "is_default_fare_category": "0", "eligibility_url": ELIGIBILITY_URL},
        {"rider_category_id": "disabled_child_community", "rider_category_name": "コミュニティバス障害者等割引対象の小児", "is_default_fare_category": "0", "eligibility_url": ELIGIBILITY_URL},
        {"rider_category_id": "disabled_child_south_taxi", "rider_category_name": "南部・東部障害者等割引対象の小児", "is_default_fare_category": "0", "eligibility_url": ELIGIBILITY_URL},
    ]


def fare_media() -> list[dict[str, str]]:
    return [
        {"fare_media_id": "cash", "fare_media_name": "現金", "fare_media_type": "0"},
        {"fare_media_id": "transit_ic", "fare_media_name": "交通系ICカード（ICOCA・PiTaPa等）", "fare_media_type": "2"},
        {"fare_media_id": "child_icoca", "fare_media_name": "子どもICOCA", "fare_media_type": "2"},
        {"fare_media_id": "ic_excluding_pitapa", "fare_media_name": "PiTaPa以外の交通系ICカード（手帳提示）", "fare_media_type": "2"},
        {"fare_media_id": "transfer_ticket", "fare_media_name": "車内発行の紙の乗継券", "fare_media_type": "1"},
    ]


def _transfer_group(route: str, origin: str, destination: str, product: str) -> str:
    tier = product.removeprefix("community_")
    if route == "R5" and destination == "S11_1":
        return f"west_to_station_{tier}"
    if route == "R2" and origin == "S11_1" and destination == "S10_1":
        return "station_to_cityhall_west_120"
    if route == "R2" and origin == "S10_1" and destination == "S11_1":
        return "cityhall_to_station_west_120"
    if route == "R6" and origin == "S11_1":
        return f"station_to_west_{tier}"
    if route in {"R13", "R15"} and destination in {"S54_1", "S54_2"}:
        return f"south_to_station_{tier}"
    if route == "R11" and origin == "S54_2" and destination == "S10_1":
        return "station_to_cityhall_south_120"
    if route == "R10" and origin == "S10_1" and destination == "S54_2":
        return "cityhall_to_station_south_120"
    if route in {"R12", "R15"} and origin == "S54_1":
        return f"station_to_south_{tier}"
    return ""


def _build_transfer_rules(group_ids: set[str]) -> list[dict[str, str]]:
    pairs: list[tuple[str, str]] = []
    for tier in ("120", "240", "270"):
        pairs += [
            (f"west_to_station_{tier}", "station_to_cityhall_west_120"),
            ("cityhall_to_station_west_120", f"station_to_west_{tier}"),
            (f"south_to_station_{tier}", "station_to_cityhall_south_120"),
            ("cityhall_to_station_south_120", f"station_to_south_{tier}"),
        ]
    rows = []
    for from_group, to_group in pairs:
        if from_group not in group_ids or to_group not in group_ids:
            continue
        to_tier = to_group.rsplit("_", 1)[-1]
        product = "transfer_pay_120_full" if from_group.endswith("_120") and to_tier == "120" else f"transfer_pay_{to_tier}_standard"
        rows.append({
            "from_leg_group_id": from_group,
            "to_leg_group_id": to_group,
            "transfer_count": "",
            "duration_limit": "",
            "duration_limit_type": "",
            "fare_transfer_type": "0",
            "fare_product_id": product,
        })
    return rows


def build(input_zip: Path, processed: Path, output_zip: Path) -> dict[str, int]:
    if processed.exists():
        shutil.rmtree(processed)
    processed.mkdir(parents=True)
    with zipfile.ZipFile(input_zip) as archive:
        source: dict[str, tuple[list[dict[str, str]], list[str]]] = {}
        for name in sorted(n for n in archive.namelist() if n.endswith(".txt")):
            rows, fields, _ = read_csv_bytes(archive.read(name), name)
            source[name] = (rows, fields)
            write_csv_path(processed / name, fields, rows)

    # Add recommended metadata that can be determined without changing service.
    fare_attributes, fare_attribute_fields = source["fare_attributes.txt"]
    if "agency_id" not in fare_attribute_fields:
        fare_attribute_fields.append("agency_id")
    for fare in fare_attributes:
        fare["agency_id"] = "6000020272183"
    write_csv_path(processed / "fare_attributes.txt", fare_attribute_fields, fare_attributes)

    feed_info, feed_info_fields = source["feed_info.txt"]
    for field in ("feed_version", "feed_contact_url"):
        if field not in feed_info_fields:
            feed_info_fields.append(field)
    for feed in feed_info:
        feed["feed_version"] = "2026-fares-v2-poc-1"
        feed["feed_contact_url"] = "https://www.city.daito.lg.jp/site/kokyokotsu/68741.html"
    write_csv_path(processed / "feed_info.txt", feed_info_fields, feed_info)

    # The official source has decimal separators accidentally split into CSV
    # columns for these three records. Rejoining the visible numeric fragments
    # restores 34.704536 / 135.6238244 without inventing coordinates.
    source_stops = source["stops.txt"][0]
    for stop in source_stops:
        if stop["stop_id"] in {"S53", "S53_1", "S53_2"}:
            stop["stop_lat"] = "34.704536"
            stop["stop_lon"] = "135.6238244"
            stop["zone_id"] = stop["stop_id"]
            stop["location_type"] = "1" if stop["stop_id"] == "S53" else "0"
            stop["parent_station"] = "" if stop["stop_id"] == "S53" else "S53"
    write_csv_path(processed / "stops.txt", source["stops.txt"][1], source_stops)

    # R4 in the source references parent stations in stop_times. GTFS requires
    # a platform (location_type=0). The opposite-direction `_2` platform is
    # used where published; otherwise the station's sole platform is used.
    children: defaultdict[str, list[str]] = defaultdict(list)
    location_type = {stop["stop_id"]: stop["location_type"] for stop in source_stops}
    for stop in source_stops:
        if stop["parent_station"]:
            children[stop["parent_station"]].append(stop["stop_id"])
    trip_route = {trip["trip_id"]: trip["route_id"] for trip in source["trips.txt"][0]}
    source_stop_times = source["stop_times.txt"][0]
    for stop_time in source_stop_times:
        stop_id = stop_time["stop_id"]
        if trip_route[stop_time["trip_id"]] == "R4" and location_type.get(stop_id) == "1":
            candidates = children[stop_id]
            if not candidates:
                raise ValueError(f"R4 station {stop_id} has no platform")
            stop_time["stop_id"] = next((item for item in candidates if item.endswith("_2")), candidates[0])
    write_csv_path(processed / "stop_times.txt", source["stop_times.txt"][1], source_stop_times)

    routes, route_fields = source["routes.txt"]
    unknown_routes = {row["route_id"] for row in routes} - set(NETWORK_FOR_ROUTE)
    if unknown_routes:
        raise ValueError(f"unclassified routes: {sorted(unknown_routes)}")
    if "network_id" not in route_fields:
        route_fields.append("network_id")
    for route in routes:
        route["network_id"] = NETWORK_FOR_ROUTE[route["route_id"]]
    write_csv_path(processed / "routes.txt", route_fields, routes)

    stops = {row["stop_id"]: row for row in source["stops.txt"][0]}
    fare_rules = source["fare_rules.txt"][0]
    referenced_stops = sorted({row["origin_id"] for row in fare_rules} | {row["destination_id"] for row in fare_rules})
    areas = [{"area_id": f"area_{stop_id}", "area_name": stops[stop_id]["stop_name"]} for stop_id in referenced_stops]
    stop_areas = [{"area_id": f"area_{stop_id}", "stop_id": stop_id} for stop_id in referenced_stops]

    candidate_rules: dict[tuple[str, str, str, str], dict[str, str]] = {}
    group_conflicts: defaultdict[tuple[str, str, str, str], set[str]] = defaultdict(set)
    for rule in fare_rules:
        network = NETWORK_FOR_ROUTE[rule["route_id"]]
        key = (network, rule["origin_id"], rule["destination_id"], rule["fare_id"])
        product = PRODUCT_FOR_V1.get((network, rule["fare_id"]))
        if not product:
            raise ValueError(f"no Fares v2 product mapping for {network}/{rule['fare_id']}")
        group = _transfer_group(rule["route_id"], rule["origin_id"], rule["destination_id"], product)
        if group:
            group_conflicts[key].add(group)
        candidate_rules.setdefault(key, {
            "leg_group_id": group,
            "network_id": network,
            "from_area_id": f"area_{rule['origin_id']}",
            "to_area_id": f"area_{rule['destination_id']}",
            "fare_product_id": product,
            "rule_priority": "1",
        })
        if group and candidate_rules[key]["leg_group_id"] not in ("", group):
            raise ValueError(f"conflicting transfer groups for {key}")
        if group:
            candidate_rules[key]["leg_group_id"] = group
    if any(len(groups) > 1 for groups in group_conflicts.values()):
        raise ValueError("a fare leg rule would belong to multiple transfer groups")
    leg_rules = sorted(candidate_rules.values(), key=lambda row: (row["network_id"], row["from_area_id"], row["to_area_id"], row["fare_product_id"]))
    groups = {row["leg_group_id"] for row in leg_rules if row["leg_group_id"]}
    transfer_rules = _build_transfer_rules(groups)

    write_csv_path(processed / "areas.txt", ["area_id", "area_name"], areas)
    write_csv_path(processed / "stop_areas.txt", ["area_id", "stop_id"], stop_areas)
    write_csv_path(processed / "rider_categories.txt", ["rider_category_id", "rider_category_name", "is_default_fare_category", "eligibility_url"], rider_categories())
    write_csv_path(processed / "fare_media.txt", ["fare_media_id", "fare_media_name", "fare_media_type"], fare_media())
    products = build_fare_products()
    write_csv_path(processed / "fare_products.txt", ["fare_product_id", "fare_product_name", "rider_category_id", "fare_media_id", "amount", "currency"], products)
    write_csv_path(processed / "fare_leg_rules.txt", ["leg_group_id", "network_id", "from_area_id", "to_area_id", "fare_product_id", "rule_priority"], leg_rules)
    write_csv_path(processed / "fare_transfer_rules.txt", ["from_leg_group_id", "to_leg_group_id", "transfer_count", "duration_limit", "duration_limit_type", "fare_transfer_type", "fare_product_id"], transfer_rules)

    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(processed.glob("*.txt"), key=lambda p: p.name):
            info = zipfile.ZipInfo(path.name, date_time=(2026, 4, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    return {
        "areas": len(areas),
        "fare_products": len(products),
        "fare_leg_rules": len(leg_rules),
        "fare_transfer_rules": len(transfer_rules),
        "output_files": len(list(processed.glob("*.txt"))),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and integrate GTFS Fares v2")
    parser.add_argument("--input", type=Path, default=DEFAULT_ZIP)
    parser.add_argument("--processed", type=Path, default=DEFAULT_PROCESSED)
    parser.add_argument("--output", type=Path, default=DEFAULT_DIST)
    args = parser.parse_args()
    result = build(args.input, args.processed, args.output)
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
