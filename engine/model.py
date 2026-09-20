"""Load a domain pack and the records it declares."""

from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from engine.schema import validate


class PackError(Exception):
    pass


@dataclass(frozen=True)
class Failure:
    code: str
    path: str
    message: str


@dataclass
class Record:
    type_id: str
    path: str
    data: dict[str, Any]


@dataclass
class Document:
    id: str
    path: str
    data: dict[str, Any]


@dataclass
class Loaded:
    root: Path
    domain_id: str
    pack_dir: Path
    documents: dict[str, Document]
    records: dict[str, list[Record]]
    pack_document_ids: set[str]
    pack_record_ids: set[str]
    filename_is_id: dict[str, bool]
    failures: list[Failure]


def dig(value: Any, path: str) -> tuple[Any, bool]:
    current = value
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None, False
    return current, True


def parse_dt(value: Any) -> dt.datetime | None:
    if not isinstance(value, str):
        return None
    try:
        if "T" not in value:
            return dt.datetime.combine(dt.date.fromisoformat(value), dt.time.min)
        return dt.datetime.fromisoformat(value)
    except ValueError:
        return None


def resolve_pointer(loaded: Loaded, pointer: str) -> tuple[Any, bool]:
    parts = pointer.split(".")
    if len(parts) < 3 or parts[0] != "documents":
        raise PackError(f"bad pointer {pointer}")
    doc_id = parts[1]
    rest = ".".join(parts[2:])
    if doc_id not in loaded.pack_document_ids:
        raise PackError(f"unknown document {doc_id}")
    document = loaded.documents.get(doc_id)
    if document is None:
        return None, False
    return dig(document.data, rest)


def normalize(value: Any) -> Any:
    if isinstance(value, dt.datetime):
        return value.isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: normalize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value


def load_yaml(path: Path) -> tuple[Any, str | None]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return None, str(exc)
    if data is None:
        data = {}
    return normalize(data), None


def load_repo(root: Path, domain_root: Path | None = None) -> Loaded:
    root = root.resolve()
    domain_root = (domain_root or root / "domains").resolve()
    repo_path = root / "repo.yaml"
    repo, error = load_yaml(repo_path)
    if error or not isinstance(repo, dict) or not repo.get("domain"):
        raise PackError("repo.yaml must declare domain")
    domain_id = str(repo["domain"])
    pack_dir = domain_root / domain_id
    pack_path = pack_dir / "pack.yaml"
    if not pack_path.is_file():
        raise PackError(f"domain pack not found: {pack_path}")
    pack, error = load_yaml(pack_path)
    if error or not isinstance(pack, dict):
        raise PackError(f"unreadable pack {pack_path}")

    failures: list[Failure] = []
    documents: dict[str, Document] = {}
    pack_document_ids: set[str] = set()
    for spec in pack.get("documents") or []:
        doc_id = str(spec["id"])
        pack_document_ids.add(doc_id)
        relative = str(spec["path"])
        path = root / relative
        if not path.is_file():
            failures.append(Failure("file", relative, "missing document"))
            continue
        data, error = load_yaml(path)
        if error or not isinstance(data, dict):
            failures.append(Failure("file", relative, error or "document must be a mapping"))
            continue
        schema = json.loads((pack_dir / spec["schema"]).read_text(encoding="utf-8"))
        for pointer, message in validate(data, schema):
            failures.append(Failure("schema", relative, f"{pointer} {message}"))
        documents[doc_id] = Document(doc_id, relative, data)

    records: dict[str, list[Record]] = {}
    pack_record_ids: set[str] = set()
    filename_is_id: dict[str, bool] = {}
    for spec in pack.get("records") or []:
        type_id = str(spec["id"])
        pack_record_ids.add(type_id)
        filename_is_id[type_id] = bool(spec.get("filename_is_id"))
        schema = json.loads((pack_dir / spec["schema"]).read_text(encoding="utf-8"))
        found: list[Record] = []
        for path in sorted(root.glob(spec["glob"])):
            if path.suffix not in {".yaml", ".yml"} or path.name.startswith("."):
                continue
            relative = path.relative_to(root).as_posix()
            data, error = load_yaml(path)
            if error or not isinstance(data, dict):
                failures.append(Failure("file", relative, error or "record must be a mapping"))
                continue
            for pointer, message in validate(data, schema):
                failures.append(Failure("schema", relative, f"{pointer} {message}"))
            found.append(Record(type_id, relative, data))
        records[type_id] = found

    return Loaded(
        root=root,
        domain_id=domain_id,
        pack_dir=pack_dir,
        documents=documents,
        records=records,
        pack_document_ids=pack_document_ids,
        pack_record_ids=pack_record_ids,
        filename_is_id=filename_is_id,
        failures=failures,
    )
