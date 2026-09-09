"""Lógica de organização e manipulação de arquivos, isolada da interface."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from utils.errors import FileAccessError, ValidationError
from utils.paths import unique_path

ProgressCallback = Callable[[int, int], None]

EXTENSION_CATEGORIES: dict[str, list[str]] = {
    "Imagens": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff"],
    "PDF": [".pdf"],
    "Planilhas": [".xlsx", ".xls", ".csv", ".ods"],
    "Documentos": [".doc", ".docx", ".txt", ".rtf", ".odt"],
    "Vídeos": [".mp4", ".avi", ".mov", ".mkv", ".wmv"],
    "Áudio": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
    "Compactados": [".zip", ".rar", ".7z", ".tar", ".gz"],
}


def _files_in(folder: Path) -> list[Path]:
    try:
        return [item for item in folder.iterdir() if item.is_file()]
    except (PermissionError, OSError) as exc:
        raise FileAccessError(
            "Não foi possível acessar os arquivos da pasta selecionada.",
            technical_detail=str(exc),
        ) from exc


def categorize_extension(extension: str) -> str:
    extension = extension.lower()
    for category, extensions in EXTENSION_CATEGORIES.items():
        if extension in extensions:
            return category
    return "Outros"


def preview_organization(folder: str | Path) -> dict[str, int]:
    """Retorna quantos arquivos serão movidos, agrupados por categoria."""
    folder = Path(folder)
    if not folder.exists() or not folder.is_dir():
        raise ValidationError("A pasta selecionada não foi encontrada.")

    counts: dict[str, int] = {}
    for item in _files_in(folder):
        category = categorize_extension(item.suffix)
        counts[category] = counts.get(category, 0) + 1
    return counts


def organize_folder(
    folder: str | Path,
    progress_cb: ProgressCallback | None = None,
) -> dict[str, int]:
    """Organiza os arquivos de uma pasta em subpastas por categoria.

    Nunca apaga arquivos e nunca sobrescreve arquivos existentes.
    Retorna o resumo de quantos arquivos foram movidos por categoria.
    """
    folder = Path(folder)
    if not folder.exists() or not folder.is_dir():
        raise ValidationError("A pasta selecionada não foi encontrada.")

    files = _files_in(folder)
    total = len(files)
    moved: dict[str, int] = {}

    for idx, item in enumerate(files, start=1):
        category = categorize_extension(item.suffix)
        dest_dir = folder / category
        try:
            dest_dir.mkdir(exist_ok=True)
        except (PermissionError, OSError) as exc:
            raise FileAccessError(
                f"Não foi possível criar a pasta '{category}'. Verifique as permissões.",
                technical_detail=str(exc),
            ) from exc

        destination = unique_path(dest_dir, item.name)
        try:
            shutil.move(str(item), str(destination))
        except (PermissionError, OSError) as exc:
            raise FileAccessError(
                f"Não foi possível mover o arquivo '{item.name}'. "
                "Verifique se ele não está aberto em outro programa.",
                technical_detail=str(exc),
            ) from exc

        moved[category] = moved.get(category, 0) + 1
        if progress_cb:
            progress_cb(idx, total)

    return moved
