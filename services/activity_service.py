"""Persistência local de rotinas salvas e do histórico de execuções."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from utils.paths import history_file_path, routines_file_path


def _read_list(path: Path) -> list[dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def _write_list(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    temporary.replace(path)


def list_routines() -> list[dict[str, Any]]:
    return _read_list(routines_file_path())


def save_routine(
    name: str, module_key: str, module_name: str, parameters: dict[str, Any]
) -> dict[str, Any]:
    routine = {
        "id": uuid4().hex,
        "name": name.strip(),
        "module_key": module_key,
        "module_name": module_name,
        "parameters": parameters,
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    routines = list_routines()
    routines.insert(0, routine)
    _write_list(routines_file_path(), routines)
    return routine


def delete_routine(routine_id: str) -> None:
    routines = [item for item in list_routines() if item.get("id") != routine_id]
    _write_list(routines_file_path(), routines)


def list_history(limit: int = 100) -> list[dict[str, Any]]:
    return _read_list(history_file_path())[:limit]


def record_execution(
    module_key: str,
    module_name: str,
    status: str,
    summary: str,
    output_path: str | Path | None = None,
) -> None:
    try:
        entry = {
            "id": uuid4().hex,
            "module_key": module_key,
            "module_name": module_name,
            "status": status,
            "summary": summary,
            "output_path": str(output_path) if output_path else "",
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        path = history_file_path()
        history = _read_list(path)
        history.insert(0, entry)
        _write_list(path, history[:500])
    except OSError:
        # O histórico é complementar e não pode transformar uma execução
        # concluída em erro para o usuário.
        pass
