from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from engine.check import evaluate, main as check_main
from engine.facts import build_context
from engine.model import load_repo


ROOT = Path(__file__).resolve().parents[1]


class ScaffoldRepoTests(unittest.TestCase):
    def test_scaffold_passes_hard_checks(self) -> None:
        self.assertEqual(check_main(["--root", str(ROOT)]), 0)

    def test_engine_has_no_travel_words(self) -> None:
        banned = ("trip", "booking", "itinerary", "traveler", "kimono", "sleep")
        for path in (ROOT / "engine").glob("*.py"):
            text = path.read_text(encoding="utf-8").lower()
            for word in banned:
                self.assertNotIn(word, text, f"{path.name} contains {word!r}")


class CleanRepoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        shutil.copytree(ROOT / "domains", self.root / "domains")
        shutil.copy2(ROOT / "repo.yaml", self.root / "repo.yaml")
        # Build fixtures independently of the traveler's records and configuration.
        for name in (
            "itinerary",
            "bookings",
            "dependencies",
            "evidence",
            "actuals",
        ):
            (self.root / name).mkdir()

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

    def read_record(self, relative: str) -> dict:
        return yaml.safe_load((self.root / relative).read_text(encoding="utf-8"))

    def write_record(self, relative: str, data: dict) -> None:
        (self.root / relative).write_text(yaml.safe_dump(data), encoding="utf-8")

    def test_valid_trip_passes(self) -> None:
        self.assertEqual(check_main(["--root", str(self.root)]), 0)

    def test_unknown_trip_choices_and_empty_watch_pass(self) -> None:
        for name in ("itinerary", "bookings"):
            for path in (self.root / name).glob("*.yaml"):
                path.unlink()
        trip = self.read_record("trip.yaml")
        trip.update(
            timezone=None,
            dates={"start": None, "end": None},
            traveler_ids=[],
            route=[],
            must_haves=[],
            assumptions={"normal_departure_local": None},
            hard_constraints=dict.fromkeys(trip["hard_constraints"]),
        )
        self.write_record("trip.yaml", trip)
        self.write_record("budget.yaml", {
            "schema_version": 1, "currency": None, "total": None,
            "reserve": None, "hard_cap": None, "categories": [],
        })
        self.write_record("watch.yaml", {"schema_version": 1, "checks": []})

        context = build_context(load_repo(self.root))
        self.assertEqual(context["checks"], {"passed": True, "failures": []})
        self.assertEqual(context["facts"], [])

    def test_early_start_and_weather_are_facts_not_failures(self) -> None:
        self.write_record("itinerary/morning-walk.yaml", {
            "schema_version": 1, "id": "morning-walk", "title": "Morning walk",
            "kind": "anchor", "status": "proposed", "day": "2027-01-02",
            "start": "2027-01-02T07:00:00+00:00",
            "end": "2027-01-02T08:00:00+00:00",
            "weather_sensitive": True,
        })
        context = build_context(load_repo(self.root))
        self.assertTrue(context["checks"]["passed"])
        kinds = {(item.get("type"), item.get("path")) for item in context["facts"]}
        self.assertIn(("clock_before", "itinerary/morning-walk.yaml"), kinds)
        self.assertIn(("boolean_true", "itinerary/morning-walk.yaml"), kinds)

    def test_sleep_limit_is_enforced_only_when_set(self) -> None:
        node = self.read_record("itinerary/city-stay.yaml")
        node["sleep_hours"] = 5
        self.write_record("itinerary/city-stay.yaml", node)
        failures = evaluate(load_repo(self.root))
        self.assertEqual({item.code for item in failures}, {"sleep-floor"})

        trip = self.read_record("trip.yaml")
        trip["hard_constraints"]["minimum_sleep_hours"] = None
        self.write_record("trip.yaml", trip)
        self.assertEqual(evaluate(load_repo(self.root)), [])

    def test_unknown_currency_is_allowed_without_a_hard_cap(self) -> None:
        budget = self.read_record("budget.yaml")
        budget.update(currency=None, total=None)
        self.write_record("budget.yaml", budget)
        self.assertEqual(evaluate(load_repo(self.root)), [])

    def test_budget_cap_requires_currency_including_zero_cap(self) -> None:
        for cap in (0, 1000):
            with self.subTest(cap=cap):
                budget = self.read_record("budget.yaml")
                budget.update(currency=None, hard_cap=cap)
                self.write_record("budget.yaml", budget)
                codes = {item.code for item in evaluate(load_repo(self.root))}
                self.assertIn("budget-currency", codes)

    def test_configured_budget_cap_still_rejects_overspending(self) -> None:
        budget = self.read_record("budget.yaml")
        budget["hard_cap"] = 300
        self.write_record("budget.yaml", budget)
        codes = {item.code for item in evaluate(load_repo(self.root))}
        self.assertEqual(codes, {"committed-spend"})

    def test_invalid_currency_still_fails_schema(self) -> None:
        budget = self.read_record("budget.yaml")
        budget["currency"] = "dollars"
        self.write_record("budget.yaml", budget)
        codes = {item.code for item in evaluate(load_repo(self.root))}
        self.assertIn("schema", codes)

    def test_chronology_still_fails_without_personal_limits(self) -> None:
        trip = self.read_record("trip.yaml")
        trip["hard_constraints"] = dict.fromkeys(trip["hard_constraints"])
        trip["dates"] = {"start": "2027-01-03", "end": "2027-01-01"}
        self.write_record("trip.yaml", trip)
        codes = {item.code for item in evaluate(load_repo(self.root))}
        self.assertEqual(codes, {"trip-dates"})

    def test_required_references_still_fail_without_personal_limits(self) -> None:
        trip = self.read_record("trip.yaml")
        trip["hard_constraints"] = dict.fromkeys(trip["hard_constraints"])
        trip["must_haves"][0]["implemented_by"] = ["missing-stay"]
        self.write_record("trip.yaml", trip)
        codes = {item.code for item in evaluate(load_repo(self.root))}
        self.assertEqual(codes, {"must-have"})

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

    def test_missing_watch_yaml_is_optional(self) -> None:
        watch = self.root / "watch.yaml"
        if watch.exists():
            watch.unlink()
        failures = load_repo(self.root).failures
        self.assertFalse(any(f.path == "watch.yaml" for f in failures))

    def test_invalid_watch_schema_fails(self) -> None:
        (self.root / "watch.yaml").write_text(
            """schema_version: 1
checks:
  - id: bad
    kind: not-a-tool
""",
            encoding="utf-8",
        )
        failures = [f for f in load_repo(self.root).failures if f.path == "watch.yaml"]
        self.assertTrue(failures)
        self.assertTrue(any(f.code == "schema" for f in failures))


if __name__ == "__main__":
    unittest.main()
