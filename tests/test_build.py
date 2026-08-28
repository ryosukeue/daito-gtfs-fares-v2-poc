from __future__ import annotations

import csv
import hashlib
import tempfile
import unittest
from pathlib import Path

from src.build_fares_v2 import build
from src.common import DEFAULT_ZIP
from src.demo import FareEngine
from src.validate import validate


class BuildTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.processed = self.root / "processed"
        self.output = self.root / "feed.zip"
        self.stats = build(DEFAULT_ZIP, self.processed, self.output)
        self.engine = FareEngine(self.processed)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_expected_counts(self) -> None:
        self.assertEqual(self.stats["areas"], 144)
        self.assertEqual(self.stats["fare_products"], 63)
        self.assertEqual(self.stats["fare_leg_rules"], 1879)
        self.assertEqual(self.stats["fare_transfer_rules"], 8)

    def test_community_adult_and_senior(self) -> None:
        adult = self.engine.leg("R1", "S11_1", "S7_1", "adult", "cash")
        senior = self.engine.leg("R1", "S11_1", "S7_1", "senior_65_plus", "cash")
        self.assertEqual(adult["amount"], 270)
        self.assertEqual(senior["amount"], 140)

    def test_special_section_has_no_child_discount(self) -> None:
        child = self.engine.leg("R2", "S11_1", "S10_1", "child", "child_icoca")
        self.assertEqual(child["amount"], 120)

    def test_south_and_taxi_discounts(self) -> None:
        south = self.engine.leg("R9", "S54_1", "S55_1", "disabled_child_south_taxi", "cash")
        taxi = self.engine.leg("R3", "S12_1", "S25_1", "senior_65_plus", "cash")
        self.assertEqual(south["amount"], 80)
        self.assertEqual(taxi["amount"], 200)

    def test_transfer_is_limited_and_computed(self) -> None:
        journey = self.engine.journey([
            {"route_id": "R13", "origin": "S74_1", "destination": "S54_1"},
            {"route_id": "R11", "origin": "S54_2", "destination": "S10_1"},
        ], "adult", "cash")
        self.assertEqual(journey["transfer_adjustment"], -120)
        self.assertEqual(journey["total"], 240)
        unrelated = self.engine.journey([
            {"route_id": "R1", "origin": "S11_1", "destination": "S7_1"},
            {"route_id": "R1", "origin": "S7_1", "destination": "S6_1"},
        ], "adult", "cash")
        self.assertEqual(unrelated["transfer_adjustment"], 0)

    def test_no_senior_ic_variant(self) -> None:
        with self.assertRaises(LookupError):
            self.engine.leg("R1", "S11_1", "S7_1", "senior_65_plus", "transit_ic")

    def test_custom_validator_passes(self) -> None:
        report = validate(self.output)
        self.assertEqual(report["summary"]["errors"], 0, report["notices"])

    def test_build_is_byte_reproducible(self) -> None:
        second = self.root / "second.zip"
        build(DEFAULT_ZIP, self.root / "processed2", second)
        digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        self.assertEqual(digest(self.output), digest(second))


if __name__ == "__main__":
    unittest.main()
