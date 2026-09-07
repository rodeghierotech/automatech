"""Gera o executável Windows (Automatiza.exe) usando PyInstaller.

Uso:
    python build.py

O executável final aparece em dist/Automatiza/Automatiza.exe
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import customtkinter

APP_NAME = "Automatiza"
ROOT = Path(__file__).resolve().parent


def main() -> None:
    ctk_path = Path(customtkinter.__file__).parent

    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",  # não abre console
        "--name",
        APP_NAME,
        "--add-data",
        f"{ctk_path}{';' if sys.platform.startswith('win') else ':'}customtkinter",
        "--collect-all",
        "customtkinter",
        # Importado pelas extensões do NumPy; pode escapar da análise estática.
        "--hidden-import",
        "numpy._core._exceptions",
        str(ROOT / "main.py"),
    ]

    print("Executando:", " ".join(args))
    subprocess.run(args, check=True, cwd=ROOT)

    dist_dir = ROOT / "dist" / APP_NAME
    print(f"\nBuild concluído. Executável em: {dist_dir / (APP_NAME + '.exe')}")


if __name__ == "__main__":
    main()
