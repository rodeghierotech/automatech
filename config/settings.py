"""Configurações persistidas localmente em config.json."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from utils.paths import config_file_path

APP_NAME = "Automatiza"
APP_VERSION = "0.1.0"


@dataclass
class Settings:
    theme: str = "dark"  # "dark" ou "light"
    default_output_dir: str = str(Path.home() / "Documents")
    open_folder_after_finish: bool = True

    @classmethod
    def load(cls) -> "Settings":
        path = config_file_path()
        if not path.exists():
            settings = cls()
            settings.save()
            return settings
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return cls(**{**asdict(cls()), **data})
        except (json.JSONDecodeError, OSError, TypeError):
            return cls()

    def save(self) -> None:
        path = config_file_path()
        path.write_text(
            json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8"
        )
