from __future__ import annotations

import logging
from pathlib import Path


def setup_logging(home: Path) -> None:
    """Configure a small file logger for CLI runs."""

    log_dir = home / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_dir / "agent.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )
