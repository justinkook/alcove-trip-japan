"""Evaluate declarative rules. Rule ids and field names are data."""

from __future__ import annotations

import sys
from typing import Any

import yaml

from engine.cli import parser
from engine.model import Failure, Loaded, PackError, dig, load_repo, parse_dt, resolve_pointer


def _subjects(loaded: Loaded, rule: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    if "document" in rule:
        document = loaded.documents.get(rule["document"])
        if document is None:
            if rule["document"] not in loaded.pack_document_ids:
                raise PackError(f"unknown document {rule['document']}")
            return []
        return [(document.path, document.data)]
    type_id = rule["record"]
    if type_id not in loaded.pack_record_ids:
        raise PackError(f"unknown record type {type_id}")
    return [(record.path, record.data) for record in loaded.records.get(type_id, [])]


def _clause(data: dict[str, Any], clause: dict[str, Any]) -> bool:
    value, ok = dig(data, clause["field"])
    if not ok:
        return False
    if "equals" in clause:
        return value == clause["equals"]
    if "in" in clause:
        return value in clause["in"]
    if "not_in" in clause:
        return value not in clause["not_in"]
    raise PackError("a clause needs equals, in, or not_in")


def _matches(data: dict[str, Any], when: Any) -> bool:
    if when is None:
        return True
    clauses = when if isinstance(when, list) else [when]
    return all(_clause(data, clause) for clause in clauses)


def _find(loaded: Loaded, record_id: str):
    found = None
    for group in loaded.records.values():
        for record in group:
            if record.data.get("id") == record_id:
                found = record
    return found


def _message(rule: dict[str, Any], fallback: str) -> str:
    text = rule.get("message")
    return text if isinstance(text, str) and text else fallback


def eval_field_order(loaded: Loaded, rule: dict[str, Any]) -> list[Failure]:
    failures: list[Failure] = []
    for path, data in _subjects(loaded, rule):
        earlier, ok_early = dig(data, rule["earlier"])
        later, ok_late = dig(data, rule["later"])
        if not ok_early or not ok_late or earlier is None or later is None:
            continue
        left = parse_dt(earlier)
        right = parse_dt(later)
        if left is None or right is None:
            failures.append(Failure(rule["id"], path, f"{rule['earlier']} or {rule['later']} is not a datetime"))
            continue
        if right < left:
            failures.append(Failure(rule["id"], path, f"{rule['later']} is before {rule['earlier']}"))
    return failures


def eval_interval_overlap(loaded: Loaded, rule: dict[str, Any]) -> list[Failure]:
    chosen: list[tuple[str, dict[str, Any]]] = []
    for path, data in _subjects(loaded, rule):
        if data.get(rule["exclusive_field"]) is not True:
            continue
        status_field = rule.get("status_field")
        allowed = rule.get("status_in")
        if status_field and allowed is not None and data.get(status_field) not in allowed:
            continue
        start = parse_dt(data.get(rule["start"]))
        end = parse_dt(data.get(rule["end"]))
        if start is None or end is None:
            continue
        chosen.append((path, {"start": start, "end": end, "id": data.get("id")}))
    failures: list[Failure] = []
    for index, (left_path, left) in enumerate(chosen):
        for right_path, right in chosen[index + 1 :]:
            if left["start"] < right["end"] and right["start"] < left["end"]:
                failures.append(Failure(rule["id"], left_path, f"overlaps {right_path}"))
    return failures


def eval_number_compare(loaded: Loaded, rule: dict[str, Any]) -> list[Failure]:
    bound, ok = resolve_pointer(loaded, rule["bound_from"])
    if not ok or bound is None or isinstance(bound, bool):
        return []
    failures: list[Failure] = []
    op = rule["op"]
    for path, data in _subjects(loaded, rule):
        if not _matches(data, rule.get("when")):
            continue
        value, present = dig(data, rule["field"])
        if not present or value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        ok_cmp = {
            "gte": value >= bound,
            "lte": value <= bound,
            "gt": value > bound,
            "lt": value < bound,
        }.get(op)
        if ok_cmp is None:
            raise PackError(f"unknown compare op {op}")
        if not ok_cmp:
            failures.append(Failure(rule["id"], path, f"{rule['field']} {value} fails {op} {bound}"))
    return failures


def eval_refs_resolve(loaded: Loaded, rule: dict[str, Any]) -> list[Failure]:
    document = loaded.documents.get(rule["document"])
    if document is None:
        return []
    failures: list[Failure] = []
    if "each" in rule:
        items, ok = dig(document.data, rule["each"])
        if not ok or not isinstance(items, list):
            return []
        for index, item in enumerate(items):
            refs = item.get(rule["ref_field"]) if isinstance(item, dict) else None
            if not isinstance(refs, list):
                refs = []
            if rule.get("require_non_empty") and not refs:
                failures.append(Failure(rule["id"], document.path, f"{rule['each']}/{index} has no refs"))
            for ref in refs:
                if not isinstance(ref, str) or _find(loaded, ref) is None:
                    failures.append(Failure(rule["id"], document.path, f"missing ref {ref}"))
        return failures
    ids, ok = dig(document.data, rule["field"])
    target = loaded.documents.get(rule["target_document"])
    if not ok or not isinstance(ids, list) or target is None:
        return failures
    entries, ok = dig(target.data, rule["target_list"])
    known = set()
    if ok and isinstance(entries, list):
        known = {item.get(rule.get("target_id", "id")) for item in entries if isinstance(item, dict)}
    for ref in ids:
        if ref not in known:
            failures.append(Failure(rule["id"], document.path, f"missing ref {ref}"))
    return failures


def eval_bounded_sum(loaded: Loaded, rule: dict[str, Any]) -> list[Failure]:
    cap_doc = loaded.documents.get(rule["cap_document"])
    if cap_doc is None:
        return []
    cap, ok = dig(cap_doc.data, rule["cap_field"])
    if not ok or cap is None:
        return []
    unit, _ = dig(cap_doc.data, rule["unit_document_field"])
    total = 0
    seen_units: set[str] = set()
    failures: list[Failure] = []
    for path, data in _subjects(loaded, rule):
        if not _matches(data, rule.get("include_when")):
            continue
        amount, amount_ok = dig(data, rule["amount_field"])
        record_unit, unit_ok = dig(data, rule["unit_field"])
        if not amount_ok or not isinstance(amount, (int, float)) or isinstance(amount, bool):
            continue
        if unit_ok and isinstance(record_unit, str):
            seen_units.add(record_unit)
            if unit is not None and record_unit != unit:
                failures.append(Failure(rule["id"], path, f"unit {record_unit} does not match {unit}"))
        total += amount
    if len(seen_units) > 1:
        failures.append(Failure(rule["id"], cap_doc.path, "mixed units"))
    if not failures and total > cap:
        failures.append(Failure(rule["id"], cap_doc.path, f"sum {total} exceeds cap {cap}"))
    return failures


def _walk_keys(value: Any, pointer: str, banned: set[str], hits: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_pointer = f"{pointer}/{key}"
            if key.lower() in banned:
                hits.append(child_pointer)
            _walk_keys(child, child_pointer, banned, hits)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_keys(child, f"{pointer}/{index}", banned, hits)


def eval_forbidden_keys(loaded: Loaded, rule: dict[str, Any]) -> list[Failure]:
    banned = {item.lower() for item in rule["keys"]}
    failures: list[Failure] = []
    blobs: list[tuple[str, Any]] = [(doc.path, doc.data) for doc in loaded.documents.values()]
    for group in loaded.records.values():
        blobs.extend((record.path, record.data) for record in group)
    for path, data in blobs:
        hits: list[str] = []
        _walk_keys(data, path, banned, hits)
        for hit in hits:
            failures.append(Failure(rule["id"], path, f"forbidden key {hit}"))
    return failures


def eval_required_when(loaded: Loaded, rule: dict[str, Any]) -> list[Failure]:
    failures: list[Failure] = []
    for path, data in _subjects(loaded, rule):
        if not _matches(data, rule.get("when")):
            continue
        value, ok = dig(data, rule["require_field"])
        if not ok or value is None or value == "":
            failures.append(Failure(rule["id"], path, f"{rule['require_field']} is required"))
    return failures


def eval_status_gate(loaded: Loaded, rule: dict[str, Any]) -> list[Failure]:
    failures: list[Failure] = []
    targets = rule["target_status_in"]
    for path, data in _subjects(loaded, rule):
        status, ok = dig(data, rule["status_field"])
        if not ok or status not in rule["fail_when_status_in"]:
            continue
        target_id, ok = dig(data, rule["target_field"])
        if not ok or not isinstance(target_id, str):
            continue
        match = _find(loaded, target_id)
        if match is None:
            continue
        allowed = targets.get(match.type_id)
        if not allowed:
            continue
        target_status = match.data.get("status")
        if target_status in allowed:
            failures.append(Failure(rule["id"], path, f"status {status} while target status is {target_status}"))
    return failures


def eval_forbidden_value(loaded: Loaded, rule: dict[str, Any]) -> list[Failure]:
    document = loaded.documents.get(rule["document"])
    if document is None:
        return []
    value, ok = dig(document.data, rule["field"])
    if ok and value == rule["equals"]:
        return [Failure(rule["id"], document.path, _message(rule, f"{rule['field']} is {value!r}"))]
    return []


def eval_path_present(loaded: Loaded, rule: dict[str, Any]) -> list[Failure]:
    relative = str(rule["path"])
    if (loaded.root / relative).exists():
        return [Failure(rule["id"], relative, _message(rule, "path must be removed"))]
    return []


def _bound_clock(loaded: Loaded, pointer: str):
    bound, ok = resolve_pointer(loaded, pointer)
    if not ok or not isinstance(bound, str) or ":" not in bound:
        return None
    hour, minute, *_ = bound.split(":")
    import datetime as dt

    return dt.time(int(hour), int(minute))


def eval_consecutive_clock_before(loaded: Loaded, rule: dict[str, Any]) -> list[Failure]:
    bound = _bound_clock(loaded, rule["bound_from"])
    limit, ok = resolve_pointer(loaded, rule["max_from"])
    if bound is None or not ok or not isinstance(limit, int):
        return []
    early_days: list[tuple[Any, str]] = []
    for path, data in _subjects(loaded, rule):
        if not _matches(data, rule.get("when")):
            continue
        raw, present = dig(data, rule["field"])
        if not present or not isinstance(raw, str):
            continue
        parsed = parse_dt(raw)
        if parsed is None:
            continue
        clock = parsed.time().replace(tzinfo=None)
        if clock < bound:
            early_days.append((parsed.date(), path))
    early_days = sorted({day: path for day, path in early_days}.items())
    failures: list[Failure] = []
    run: list[tuple[Any, str]] = []
    for day, path in early_days:
        if run and (day - run[-1][0]).days == 1:
            run.append((day, path))
        else:
            run = [(day, path)]
        if len(run) > limit:
            failures.append(
                Failure(rule["id"], path, f"{len(run)} consecutive days before {bound.isoformat(timespec='minutes')}; max {limit}")
            )
    return failures


def eval_gap_within_group(loaded: Loaded, rule: dict[str, Any]) -> list[Failure]:
    max_hours, ok = resolve_pointer(loaded, rule["max_from"])
    if not ok or not isinstance(max_hours, (int, float)) or isinstance(max_hours, bool):
        return []
    groups: dict[Any, list[tuple[Any, str, str]]] = {}
    for path, data in _subjects(loaded, rule):
        if not _matches(data, rule.get("when")):
            continue
        group, group_ok = dig(data, rule["group_by"])
        raw, present = dig(data, rule["field"])
        if not group_ok or not present or not isinstance(raw, str):
            continue
        parsed = parse_dt(raw)
        if parsed is None:
            continue
        groups.setdefault(group, []).append((parsed, path, str(data.get("id") or path)))
    failures: list[Failure] = []
    for items in groups.values():
        items.sort(key=lambda item: item[0])
        for (left_time, _, left_id), (right_time, path, right_id) in zip(items, items[1:]):
            gap = (right_time - left_time).total_seconds() / 3600
            if gap > float(max_hours):
                failures.append(
                    Failure(rule["id"], path, f"gap {gap:.2f}h from {left_id} to {right_id}; max {max_hours:g}h")
                )
    return failures


def eval_rolling_average(loaded: Loaded, rule: dict[str, Any]) -> list[Failure]:
    window, ok_window = resolve_pointer(loaded, rule["window_from"])
    minimum, ok_min = resolve_pointer(loaded, rule["min_from"])
    if not ok_window or not ok_min or not isinstance(window, int) or window < 1:
        return []
    if not isinstance(minimum, (int, float)) or isinstance(minimum, bool):
        return []
    measured: list[tuple[Any, str, float]] = []
    for path, data in _subjects(loaded, rule):
        if not _matches(data, rule.get("when")):
            continue
        value, present = dig(data, rule["field"])
        if not (present and isinstance(value, (int, float)) and not isinstance(value, bool)):
            continue
        order_raw = data.get(rule.get("order_by", "start"))
        order = parse_dt(order_raw) if isinstance(order_raw, str) else None
        measured.append((order or path, path, float(value)))
    measured.sort(key=lambda item: item[0])
    failures: list[Failure] = []
    if len(measured) < window:
        return failures
    for start in range(len(measured) - window + 1):
        chunk = measured[start : start + window]
        avg = sum(hours for _, _, hours in chunk) / window
        if avg < float(minimum):
            failures.append(
                Failure(rule["id"], chunk[-1][1], f"{window}-item average is {avg:.2f}; minimum {minimum:g}")
            )
    return failures


def eval_count_per_group(loaded: Loaded, rule: dict[str, Any]) -> list[Failure]:
    maximum, ok = resolve_pointer(loaded, rule["max_from"])
    if not ok or not isinstance(maximum, int):
        return []
    groups: dict[Any, list[str]] = {}
    for path, data in _subjects(loaded, rule):
        if not _matches(data, rule.get("when")):
            continue
        group, group_ok = dig(data, rule["group_by"])
        if not group_ok:
            continue
        groups.setdefault(group, []).append(path)
    failures: list[Failure] = []
    for group, paths in groups.items():
        if len(paths) > maximum:
            failures.append(
                Failure(rule["id"], paths[-1], f"group {group!r} has {len(paths)} items; max {maximum}")
            )
    return failures


def eval_pair_compare(loaded: Loaded, rule: dict[str, Any]) -> list[Failure]:
    failures: list[Failure] = []
    op = rule["op"]
    for path, data in _subjects(loaded, rule):
        if not _matches(data, rule.get("when")):
            continue
        left, left_ok = dig(data, rule["left"])
        right, right_ok = dig(data, rule["right"])
        if not left_ok or not right_ok:
            continue
        if not isinstance(left, (int, float)) or isinstance(left, bool):
            continue
        if not isinstance(right, (int, float)) or isinstance(right, bool):
            continue
        ok_cmp = {
            "gte": left >= right,
            "lte": left <= right,
            "gt": left > right,
            "lt": left < right,
        }.get(op)
        if ok_cmp is None:
            raise PackError(f"unknown compare op {op}")
        if not ok_cmp:
            failures.append(Failure(rule["id"], path, f"{rule['left']} {left} fails {op} {rule['right']} {right}"))
    return failures


def eval_threshold_required(loaded: Loaded, rule: dict[str, Any]) -> list[Failure]:
    threshold, ok = resolve_pointer(loaded, rule["threshold_from"])
    if not ok or not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
        return []
    failures: list[Failure] = []
    for path, data in _subjects(loaded, rule):
        if not _matches(data, rule.get("when")):
            continue
        amount, amount_ok = dig(data, rule["amount_field"])
        if not amount_ok or not isinstance(amount, (int, float)) or isinstance(amount, bool):
            continue
        if float(amount) < float(threshold):
            continue
        value, present = dig(data, rule["require_field"])
        if not present or value is None or value == "":
            failures.append(
                Failure(rule["id"], path, f"{rule['require_field']} required when {rule['amount_field']} >= {threshold}")
            )
            continue
        min_utility, utility_ok = resolve_pointer(loaded, rule["utility_min_from"]) if rule.get("utility_min_from") else (None, False)
        if utility_ok and isinstance(min_utility, (int, float)) and not isinstance(min_utility, bool):
            utility, utility_present = dig(data, rule["utility_field"])
            if not utility_present or not isinstance(utility, (int, float)) or isinstance(utility, bool) or float(utility) < float(min_utility):
                failures.append(
                    Failure(rule["id"], path, f"{rule['utility_field']} must be >= {min_utility}")
                )
    return failures


EVALUATORS = {
    "field_order": eval_field_order,
    "interval_overlap": eval_interval_overlap,
    "number_compare": eval_number_compare,
    "refs_resolve": eval_refs_resolve,
    "bounded_sum": eval_bounded_sum,
    "forbidden_keys": eval_forbidden_keys,
    "required_when": eval_required_when,
    "status_gate": eval_status_gate,
    "forbidden_value": eval_forbidden_value,
    "path_present": eval_path_present,
    "consecutive_clock_before": eval_consecutive_clock_before,
    "gap_within_group": eval_gap_within_group,
    "rolling_average": eval_rolling_average,
    "count_per_group": eval_count_per_group,
    "pair_compare": eval_pair_compare,
    "threshold_required": eval_threshold_required,
}


def _rules(pack_dir) -> list[dict[str, Any]]:
    path = pack_dir / "rules.yaml"
    if not path.is_file():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return list(data.get("rules") or [])


def identity(loaded: Loaded) -> list[Failure]:
    failures: list[Failure] = []
    seen: dict[str, str] = {}
    for type_id, group in loaded.records.items():
        for record in group:
            record_id = record.data.get("id")
            if isinstance(record_id, str):
                previous = seen.get(record_id)
                if previous:
                    failures.append(Failure("duplicate-id", record.path, f"id {record_id} also used in {previous}"))
                else:
                    seen[record_id] = record.path
            if loaded.filename_is_id.get(type_id) and isinstance(record_id, str):
                stem = record.path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
                if stem != record_id:
                    failures.append(Failure("filename-id", record.path, f"filename must match id {record_id}"))
    return failures


def evaluate(loaded: Loaded) -> list[Failure]:
    failures = list(loaded.failures)
    for rule in _rules(loaded.pack_dir):
        kind = rule.get("type")
        fn = EVALUATORS.get(kind)
        if fn is None:
            raise PackError(f"unknown evaluator {kind}")
        failures.extend(fn(loaded, rule))
    failures.extend(identity(loaded))
    return failures


def render(failures: list[Failure]) -> str:
    lines = [f"{len(failures)} hard failure(s).", ""]
    for item in sorted(failures, key=lambda failure: (failure.code, failure.path, failure.message)):
        lines.append(f"- {item.code} `{item.path}` — {item.message}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parser("Run hard checks. Judgment is not a failure.").parse_args(argv)
    try:
        loaded = load_repo(args.root, args.domain_root)
        failures = evaluate(loaded)
    except PackError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(render(failures), end="")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
