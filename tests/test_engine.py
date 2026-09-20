from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from engine.check import evaluate, main as check_main
from engine.facts import build_context
from engine.model import load_repo


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "japan-summer-2026"


class ScaffoldRepoTests(unittest.TestCase):
    def test_scaffold_passes_hard_checks(self) -> None:
        self.assertEqual(check_main(["--root", str(ROOT)]), 0)

    def test_engine_has_no_travel_words(self) -> None:
        banned = ("trip", "booking", "itinerary", "traveler", "kimono", "sleep")
        for path in (ROOT / "engine").glob("*.py"):
            text = path.read_text(encoding="utf-8").lower()
            for word in banned:
                self.assertNotIn(word, text, f"{path.name} contains {word!r}")


class ExampleRepoTests(unittest.TestCase):
    def test_example_emits_early_start_and_weather_facts(self) -> None:
        context = build_context(load_repo(EXAMPLE, ROOT / "domains"))
        kinds = {(item.get("type"), item.get("path")) for item in context["facts"]}
        self.assertIn(("clock_before", "itinerary/fushimi-early.yaml"), kinds)
        self.assertIn(("boolean_true", "itinerary/kyoto-kimono.yaml"), kinds)

    def test_example_passes_hard_checks(self) -> None:
        self.assertEqual(
            check_main(["--root", str(EXAMPLE), "--domain-root", str(ROOT / "domains")]),
            0,
        )


class CleanRepoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for name in (
            "engine",
            "domains",
            "itinerary",
            "bookings",
            "dependencies",
            "evidence",
            "actuals",
            ".github",
        ):
            src = ROOT / name
            if src.exists():
                shutil.copytree(src, self.root / name)
        for name in ("repo.yaml", "requirements.txt", ".gitignore"):
            shutil.copy2(ROOT / name, self.root / name)

        shutil.copy2(ROOT / "trip.yaml", self.root / "trip.yaml")
        shutil.copy2(ROOT / "budget.yaml", self.root / "budget.yaml")
        for path in (self.root / "itinerary").glob("*.yaml"):
            path.unlink()
        for path in (self.root / "bookings").glob("*.yaml"):
            path.unlink()
        for path in (self.root / "dependencies").glob("*.yaml"):
            path.unlink()

        (self.root / "trip.yaml").write_text(
            """schema_version: 1
id: demo-trip
title: Demo trip
status: planning
timezone: UTC
dates:
  start: "2027-01-01"
  end: "2027-01-03"
traveler_ids: [traveler-a]
route:
  - {base: city, nights: 2}
hard_constraints:
  minimum_sleep_hours: 6
  rolling_sleep_window_nights: 3
  rolling_sleep_average_min_hours: 7
  early_morning_before: "08:00"
  consecutive_early_mornings_max: 1
  meal_gap_hours_max: 6
  minimum_transfer_margin_minutes: 20
  maximum_walking_km: null
  maximum_independent_anchors_per_day: 2
  weather_sensitive_spend_max: 150
  weather_fallback_utility_min: 0.5
must_haves:
  - id: one-night
    implemented_by: [city-stay]
assumptions:
  normal_departure_local: "09:30"
""",
            encoding="utf-8",
        )
        (self.root / "budget.yaml").write_text(
            """schema_version: 1
currency: USD
total: 1000
reserve: null
hard_cap: null
categories: []
""",
            encoding="utf-8",
        )
        (self.root / "itinerary" / "city-stay.yaml").write_text(
            """schema_version: 1
id: city-stay
title: City hotel
kind: lodging
status: committed
day: "2027-01-01"
start: "2027-01-01T15:00:00+00:00"
end: "2027-01-03T11:00:00+00:00"
timezone: UTC
location:
  name: City
exclusive: true
sleep_hours: 8
booking_ids: [city-hotel]
""",
            encoding="utf-8",
        )
        (self.root / "bookings" / "city-hotel.yaml").write_text(
            """schema_version: 1
id: city-hotel
type: lodging
provider: Hotel
status: confirmed
start: "2027-01-01T15:00:00+00:00"
end: "2027-01-03T11:00:00+00:00"
location:
  name: City
exclusive: true
cost:
  amount: 400
  currency: USD
  commitment: committed
refundable: null
cancellation_deadline: null
external_ref: null
""",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_valid_trip_passes(self) -> None:
        self.assertEqual(check_main(["--root", str(self.root)]), 0)

    def test_forbidden_key_passport_fails(self) -> None:
        path = self.root / "bookings" / "city-hotel.yaml"
        text = path.read_text(encoding="utf-8")
        path.write_text(text + "passport_number: X1234567\n", encoding="utf-8")
        codes = {item.code for item in evaluate(load_repo(self.root))}
        self.assertIn("secrets", codes)

    def test_email_value_fails_secret_patterns(self) -> None:
        path = self.root / "itinerary" / "city-stay.yaml"
        text = path.read_text(encoding="utf-8")
        path.write_text(text + "notes: contact traveler@example.com before check-in\n", encoding="utf-8")
        codes = {item.code for item in evaluate(load_repo(self.root))}
        self.assertIn("secret-patterns", codes)


if __name__ == "__main__":
    unittest.main()
