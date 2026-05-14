from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Config:
    """Runtime config for the learning agent."""

    home: Path
    model: str = "local/echo"
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    max_iterations: int = 8
    system_prompt: str = "You are Hermers, a small learning agent."

    @property
    def database_path(self) -> Path:
        return self.home / "sessions.sqlite3"


def get_hermers_home() -> Path:
    """Return the profile-safe home directory for this learning project."""

    override = os.environ.get("HERMERS_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".hermers"


def load_config() -> Config:
    """Load config.yaml if present, falling back to safe local defaults."""

    home = get_hermers_home()
    config_path = home / "config.yaml"
    raw: dict[str, Any] = {}
    if config_path.exists():
        raw = yaml.safe_load(config_path.read_text()) or {}

    return Config(
        home=home,
        model=str(raw.get("model", "local/echo")),
        base_url=str(raw.get("base_url", os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"))),
        api_key=str(raw.get("api_key", os.environ.get("OPENAI_API_KEY", ""))),
        max_iterations=int(raw.get("max_iterations", 8)),
        system_prompt=str(raw.get("system_prompt", "You are Hermers, a small learning agent.")),
    )
