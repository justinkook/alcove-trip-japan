"""Shared command arguments."""

from __future__ import annotations

import argparse
from pathlib import Path


def parser(description: str) -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=description)
    command.add_argument("--root", type=Path, default=Path.cwd())
    command.add_argument("--domain-root", type=Path, default=None)
    return command
