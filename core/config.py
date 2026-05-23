"""Configuration loader for KnowledgeForge — reads config/sources.yaml."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml


def _interpolate_env(value: str) -> str:
    def replacer(match):
        return os.environ.get(match.group(1), match.group(0))
    return re.sub(r"\$\{(\w+)\}", replacer, value)


def _walk(obj: Any) -> Any:
    if isinstance(obj, str):
        return _interpolate_env(obj)
    if isinstance(obj, dict):
        return {k: _walk(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk(item) for item in obj]
    return obj


def load_sources(path: str | Path = "config/sources.yaml") -> dict:
    """Load sources.yaml. Returns raw dict with keys: rsshub, rss, youtube_channels."""
    p = Path(path)
    if not p.exists():
        return {}
    with open(p) as f:
        raw = yaml.safe_load(f) or {}
    return _walk(raw)


def load_categories(path: str | Path = "config/categories.yaml") -> dict:
    """Load categories.yaml. Returns dict mapping category name -> keywords list."""
    p = Path(path)
    if not p.exists():
        return {}
    with open(p) as f:
        raw = yaml.safe_load(f) or {}
    return _walk(raw)
