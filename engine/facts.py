"""Emit review context. Facts are not failures."""

from __future__ import annotations

import sys
from typing import Any

import yaml

from engine.check import evaluate
from engine.cli import parser
from engine.model import Loaded, PackError, dig, load_repo, parse_dt, resolve_pointer


def _clock(value: str):
    hour, minute, *_ = value.split(":")
    import datetime as dt

    return dt.time(int(hour), int(minute))


def fact_clock_before(loaded: Loaded, spec: dict[str, Any]) -> list[dict[str, Any]]:
    bound, ok = resolve_pointer(loaded, spec["bound_from"])
    if not ok or not isinstance(bound, str) or ":" not in bound:
        return []
    bound_clock = _clock(bound)
    facts = []
    for record in loaded.records.get(spec["record"], []):
        raw, present = dig(record.data, spec["field"])
        if not present or not isinstance(raw, str) or "T" not in raw:
            continue
        parsed = parse_dt(raw)
        if parsed is None or parsed.time().replace(tzinfo=None) >= bound_clock:
            continue
        facts.append({
            "type": "clock_before",
            "rule": spec["id"],
            "path": record.path,
            "field": spec["field"],
            "value": parsed.time().replace(tzinfo=None).isoformat(timespec="minutes"),
            "bound": bound,
        })
    return facts


def fact_boolean_true(loaded: Loaded, spec: dict[str, Any]) -> list[dict[str, Any]]:
    facts = []
    for record in loaded.records.get(spec["record"], []):
        if record.data.get(spec["field"]) is True:
            facts.append({"type": "boolean_true", "rule": spec["id"], "path": record.path, "field": spec["field"]})
    return facts


def fact_number_without_bound(loaded: Loaded, spec: dict[str, Any]) -> list[dict[str, Any]]:
    bound, ok = resolve_pointer(loaded, spec["bound_from"])
    if ok and bound is not None:
        return []
    facts = []
    for record in loaded.records.get(spec["record"], []):
        value, present = dig(record.data, spec["field"])
        if present and isinstance(value, (int, float)) and not isinstance(value, bool):
            facts.append({
                "type": "number_without_bound",
                "rule": spec["id"],
                "path": record.path,
                "field": spec["field"],
                "value": value,
            })
    return facts


def fact_status_is(loaded: Loaded, spec: dict[str, Any]) -> list[dict[str, Any]]:
    facts = []
    for record in loaded.records.get(spec["record"], []):
        if record.data.get(spec["field"]) == spec["equals"]:
            facts.append({
                "type": "status_is",
                "rule": spec["id"],
                "path": record.path,
                "field": spec["field"],
                "value": spec["equals"],
            })
    return facts


def fact_project(loaded: Loaded, spec: dict[str, Any]) -> list[dict[str, Any]]:
    facts = []
    for record in loaded.records.get(spec["record"], []):
        projected = {"type": "project", "rule": spec["id"], "path": record.path}
        for field in spec.get("fields") or []:
            value, ok = dig(record.data, field)
            if ok:
                projected[field] = value
        facts.append(projected)
    return facts


FACTS = {
    "clock_before": fact_clock_before,
    "boolean_true": fact_boolean_true,
    "number_without_bound": fact_number_without_bound,
    "status_is": fact_status_is,
    "project": fact_project,
}


def _specs(pack_dir) -> list[dict[str, Any]]:
    path = pack_dir / "facts.yaml"
    if not path.is_file():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(data.get("facts") or [])


def build_context(loaded: Loaded) -> dict[str, Any]:
    failures = evaluate(loaded)
    facts: list[dict[str, Any]] = []
    for spec in _specs(loaded.pack_dir):
        kind = spec.get("type")
        fn = FACTS.get(kind)
        if fn is None:
            raise PackError(f"unknown fact type {kind}")
        facts.extend(fn(loaded, spec))
    facts.sort(key=lambda item: (str(item.get("rule")), str(item.get("path")), str(item.get("type"))))
    return {
        "schema_version": 1,
        "kind": "review-context",
        "domain": loaded.domain_id,
        "checks": {
            "passed": not failures,
            "failures": [{"code": item.code, "path": item.path, "message": item.message} for item in failures],
        },
        "facts": facts,
    }


def main(argv: list[str] | None = None) -> int:
    command = parser("Write review context. This command does not fail because a check failed.")
    command.add_argument("--check", action="store_true")
    args = command.parse_args(argv)
    try:
        context = build_context(load_repo(args.root, args.domain_root))
    except PackError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if context.get("kind") != "review-context" or "facts" not in context:
        return 2
    print(yaml.safe_dump(context, sort_keys=False, allow_unicode=True), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
