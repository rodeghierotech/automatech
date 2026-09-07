"""Utilitários para manipulação segura de caminhos e nomes de arquivo."""
from __future__ import annotations

import re
import sys
from pathlib import Path

INVALID_WINDOWS_CHARS = r'<>:"/\\|?*'
RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_filename(name: str, fallback: str = "arquivo") -> str:
    """Remove caracteres inválidos no Windows e nomes reservados."""
    name = str(name).strip()
    if not name:
        return fallback

    cleaned = re.sub(f"[{re.escape(INVALID_WINDOWS_CHARS)}]", "_", name)
    cleaned = cleaned.strip(" .")

    if not cleaned:
        return fallback

    if cleaned.upper() in RESERVED_NAMES:
        cleaned = f"{cleaned}_"

    return cleaned[:150]  # evita caminhos absurdamente longos


def unique_path(directory: Path, filename: str) -> Path:
    """Retorna um Path que não sobrescreve nenhum arquivo existente.

    Se 'relatorio.xlsx' já existir, retorna 'relatorio (1).xlsx', etc.
    """
    directory = Path(directory)
    base = Path(filename)
    stem, suffix = base.stem, base.suffix
    candidate = directory / filename
    counter = 1
    while candidate.exists():
        candidate = directory / f"{stem} ({counter}){suffix}"
        counter += 1
    return candidate


def app_base_dir() -> Path:
    """Diretório base da aplicação, funcionando tanto em dev quanto congelado (PyInstaller)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def logs_dir() -> Path:
    d = app_base_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_file_path() -> Path:
    return app_base_dir() / "config.json"


def open_in_explorer(path: Path) -> None:
    """Abre uma pasta no explorador de arquivos do sistema (Windows/macOS/Linux)."""
    path = Path(path)
    if sys.platform.startswith("win"):
        os_startfile = getattr(sys.modules.get("os") or __import__("os"), "startfile", None)
        if os_startfile:
            os_startfile(str(path))
    elif sys.platform == "darwin":
        import subprocess

        subprocess.run(["open", str(path)], check=False)
    else:
        import subprocess

        subprocess.run(["xdg-open", str(path)], check=False)
