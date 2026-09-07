"""Validações comuns usadas pelos módulos de automação."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from utils.errors import FileAccessError, ValidationError

VALID_SPREADSHEET_EXTENSIONS = {".xlsx", ".xls"}


def require_files_selected(files: Iterable[str], message: str = "Selecione ao menos um arquivo.") -> None:
    if not files:
        raise ValidationError(message)


def require_folder_selected(folder: str | None, message: str = "Selecione uma pasta.") -> None:
    if not folder:
        raise ValidationError(message)


def validate_spreadsheet_path(path: str | Path) -> Path:
    p = Path(path)
    if not p.exists():
        raise FileAccessError(
            f"O arquivo '{p.name}' não foi encontrado. Ele pode ter sido movido ou excluído."
        )
    if p.suffix.lower() not in VALID_SPREADSHEET_EXTENSIONS:
        raise ValidationError(f"'{p.name}' não é uma planilha Excel válida (.xlsx).")
    return p


def is_file_locked(path: str | Path) -> bool:
    """Verifica se o arquivo está aberto/bloqueado (ex: aberto no Excel)."""
    p = Path(path)
    try:
        with open(p, "a+b"):
            return False
    except (PermissionError, OSError):
        return True
