"""Configurações persistidas localmente em config.json."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from utils.paths import config_file_path, legacy_config_file_path

APP_NAME = "Automatech"
APP_VERSION = "0.2.0"


@dataclass
class Settings:
    theme: str = "dark"  # "dark" ou "light"
    default_output_dir: str = str(Path.home() / "Documents")
    open_folder_after_finish: bool = True

    @classmethod
    def load(cls) -> "Settings":
        path = config_file_path()
        source_path = path if path.exists() else legacy_config_file_path()
        if not source_path.exists():
            settings = cls()
            try:
                settings.save()
            except OSError:
                pass
            return settings
        try:
            data = json.loads(source_path.read_text(encoding="utf-8"))
            defaults = asdict(cls())
            settings = cls(**{key: data.get(key, value) for key, value in defaults.items()})
            if settings.theme not in {"dark", "light", "system"}:
                settings.theme = "dark"
            if source_path != path:
                try:
                    settings.save()
                except OSError:
                    pass
            return settings
        except (json.JSONDecodeError, OSError, TypeError, AttributeError):
            return cls()

    def save(self) -> None:
        path = config_file_path()
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(asdict(self), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        temporary.replace(path)
