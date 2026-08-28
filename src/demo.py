from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

try:
    from .common import DEFAULT_PROCESSED, PROJECT_ROOT, write_json
except ImportError:  # Direct execution
    from common import DEFAULT_PROCESSED, PROJECT_ROOT, write_json


def read_table(root: Path, name: str) -> list[dict[str, str]]:
    with (root / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


class FareEngine:
    def __init__(self, root: Path):
        self.routes = {row["route_id"]: row for row in read_table(root, "routes.txt")}
        self.stops = {row["stop_id"]: row for row in read_table(root, "stops.txt")}
        self.areas = {row["stop_id"]: row["area_id"] for row in read_table(root, "stop_areas.txt")}
        self.leg_rules = read_table(root, "fare_leg_rules.txt")
        self.products = read_table(root, "fare_products.txt")
        self.transfers = read_table(root, "fare_transfer_rules.txt")

    def leg(self, route_id: str, origin: str, destination: str, category: str, media: str) -> dict[str, object]:
        network = self.routes[route_id]["network_id"]
        matches = [row for row in self.leg_rules if row["network_id"] == network and row["from_area_id"] == self.areas[origin] and row["to_area_id"] == self.areas[destination]]
        if len(matches) != 1:
            raise LookupError(f"expected one fare leg rule, got {len(matches)} for {route_id}/{origin}/{destination}")
        rule = matches[0]
        variants = [row for row in self.products if row["fare_product_id"] == rule["fare_product_id"] and row["fare_media_id"] == media and row["rider_category_id"] in ("", category)]
        if len(variants) != 1:
            raise LookupError(f"expected one product variant, got {len(variants)} for {rule['fare_product_id']}/{category}/{media}")
        variant = variants[0]
        return {
            "route_id": route_id,
            "route_name": self.routes[route_id]["route_long_name"],
            "network_id": network,
            "from_stop_id": origin,
            "from_stop_name": self.stops[origin]["stop_name"],
            "to_stop_id": destination,
            "to_stop_name": self.stops[destination]["stop_name"],
            "from_area_id": self.areas[origin],
            "to_area_id": self.areas[destination],
            "leg_group_id": rule["leg_group_id"],
            "fare_product_id": rule["fare_product_id"],
            "fare_product_name": variant["fare_product_name"],
            "rider_category_id": category,
            "fare_media_id": media,
            "amount": int(variant["amount"]),
        }

    def journey(self, legs: list[dict[str, str]], category: str, media: str) -> dict[str, object]:
        resolved = [self.leg(**leg, category=category, media=media) for leg in legs]
        discount = 0
        transfer_product = ""
        if len(resolved) == 2:
            matches = [row for row in self.transfers if row["from_leg_group_id"] == resolved[0]["leg_group_id"] and row["to_leg_group_id"] == resolved[1]["leg_group_id"]]
            if matches:
                transfer_product = matches[0]["fare_product_id"]
                variants = [row for row in self.products if row["fare_product_id"] == transfer_product and row["rider_category_id"] in ("", category)]
                if len(variants) != 1:
                    raise LookupError(f"transfer variant not unique for {transfer_product}/{category}")
                additional_payment = int(variants[0]["amount"])
                discount = additional_payment - int(resolved[1]["amount"])
        return {"legs": resolved, "transfer_product_id": transfer_product, "transfer_adjustment": discount, "total": sum(int(leg["amount"]) for leg in resolved) + discount}


def build_examples(root: Path) -> dict[str, object]:
    engine = FareEngine(root)
    examples = [
        {
            "id": "special_section",
            "title": "住道駅前［北］ → 大東市役所庁舎前",
            "before": "Fares v1では成人120円だけを取得可能。小児も割引なしである理由や支払媒体は分からない。",
            "after": engine.journey([{"route_id": "R2", "origin": "S11_1", "destination": "S10_1"}], "child", "child_icoca"),
            "note": "特定区間は割引対象外のため、小児も120円。",
        },
        {
            "id": "community_senior",
            "title": "住道駅前［北］ → 三箇西",
            "before": "Fares v1では成人270円のみ。",
            "after": engine.journey([{"route_id": "R1", "origin": "S11_1", "destination": "S7_1"}], "senior_65_plus", "cash"),
            "note": "65歳以上は現金・乗務員への声掛けが必要。270円の半額135円を10円単位へ切り上げて140円。",
        },
        {
            "id": "south_disabled_child",
            "title": "住道駅南 → 大東中央病院前（南部地域コミュニティバス）",
            "before": "Fares v1では成人300円のみ。",
            "after": engine.journey([{"route_id": "R9", "origin": "S54_1", "destination": "S55_1"}], "disabled_child_south_taxi", "cash"),
            "note": "対象手帳を持つ小児は80円。南部は現金のみ。",
        },
        {
            "id": "cityhall_transfer",
            "title": "南新田南 → 住道駅南で乗継 → 大東市役所庁舎前",
            "before": "Fares v1では各乗車240円+120円=360円としてしか扱えず、乗継券の120円引きを計算できない。",
            "after": engine.journey([
                {"route_id": "R13", "origin": "S74_1", "destination": "S54_1"},
                {"route_id": "R11", "origin": "S54_2", "destination": "S10_1"},
            ], "adult", "cash"),
            "note": "最初のバスで紙の乗継券を受け取る運用条件がある。240+120-120=240円。",
        },
    ]
    return {
        "generated_from": "data/processed Fares v2 tables",
        "disclaimer": "GTFS仕様上の表現例。特定アプリでの表示・計算対応を保証しない。",
        "examples": examples,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build human-readable Before/After fare examples")
    parser.add_argument("--input", type=Path, default=DEFAULT_PROCESSED)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "demo" / "examples.json")
    args = parser.parse_args()
    result = build_examples(args.input)
    write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
