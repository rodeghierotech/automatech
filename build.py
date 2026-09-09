"""Gera o executável Windows (Automatech.exe) usando PyInstaller.

Uso:
    python build.py

O executável final aparece em dist/Automatech/Automatech.exe
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

APP_NAME = "Automatech"
ROOT = Path(__file__).resolve().parent


def main() -> None:
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",  # não abre console
        "--name",
        APP_NAME,
        "--collect-all",
        "customtkinter",
        "--add-data",
        f"{ROOT / 'assets'}{';' if sys.platform.startswith('win') else ':'}assets",
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
