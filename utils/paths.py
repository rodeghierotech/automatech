"""Utilitários para manipulação segura de caminhos e nomes de arquivo."""
from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

INVALID_WINDOWS_CHARS = r'<>:"/\\|?*'
RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


def sanitize_filename(name: str, fallback: str = "arquivo", max_length: int = 150) -> str:
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

    path = Path(cleaned)
    suffix = path.suffix
    if suffix and len(suffix) < max_length:
        stem_limit = max_length - len(suffix)
        return f"{path.stem[:stem_limit].rstrip(' .')}{suffix}"
    return cleaned[:max_length].rstrip(" .")


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


def _user_state_base() -> Path:
    if sys.platform.startswith("win"):
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))


def user_data_dir() -> Path:
    """Retorna uma pasta gravável para configurações e logs do usuário."""
    base = _user_state_base()
    candidates = (base / "Automatech", Path(tempfile.gettempdir()) / "Automatech")
    for directory in candidates:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            return directory
        except OSError:
            continue
    raise OSError("Não foi possível criar a pasta de dados da aplicação.")


def logs_dir() -> Path:
    d = user_data_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_file_path() -> Path:
    return user_data_dir() / "config.json"


def routines_file_path() -> Path:
    return user_data_dir() / "routines.json"


def history_file_path() -> Path:
    return user_data_dir() / "history.json"


def legacy_config_file_path() -> Path:
    """Local usado por versões anteriores, apenas para migração."""
    return _user_state_base() / "Automatiza" / "config.json"


def open_in_explorer(path: Path) -> bool:
    """Abre uma pasta no explorador de arquivos do sistema (Windows/macOS/Linux)."""
    path = Path(path)
    try:
        if sys.platform.startswith("win"):
            os.startfile(str(path))
        elif sys.platform == "darwin":
            import subprocess

            subprocess.run(["open", str(path)], check=False)
        else:
            import subprocess

            subprocess.run(["xdg-open", str(path)], check=False)
    except OSError:
        return False
    return True
