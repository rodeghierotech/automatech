"""Validações comuns usadas pelos módulos de automação."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from utils.errors import FileAccessError, ValidationError

VALID_SPREADSHEET_EXTENSIONS = {".xlsx"}


def require_files_selected(
    files: Iterable[str],
    message: str = "Selecione ao menos um arquivo.",
    minimum: int = 1,
) -> None:
    if len(list(files)) < minimum:
        raise ValidationError(message)


def validate_spreadsheet_path(path: str | Path) -> Path:
    p = Path(path)
    if not p.exists():
        raise FileAccessError(
            f"O arquivo '{p.name}' não foi encontrado. Ele pode ter sido movido ou excluído."
        )
    if p.suffix.lower() not in VALID_SPREADSHEET_EXTENSIONS:
        raise ValidationError(f"'{p.name}' não é uma planilha Excel válida (.xlsx).")
    if not p.is_file():
        raise FileAccessError(f"'{p.name}' não é um arquivo válido.")
    return p
