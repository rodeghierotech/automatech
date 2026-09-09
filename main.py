"""Ponto de entrada da aplicação Automatech.

Execução em desenvolvimento:
    python main.py

Geração do executável:
    python build.py
"""
from __future__ import annotations

import sys
import traceback

from core.logger import get_logger


def main() -> None:
    from ui.app import App

    app = App()
    app.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 - último recurso antes de fechar sem aviso
        logger = get_logger()
        logger.critical("Falha crítica não tratada:\n%s", traceback.format_exc())
        try:
            from tkinter import messagebox

            messagebox.showerror(
                "Erro ao iniciar",
                "Não foi possível iniciar o aplicativo. Os detalhes foram salvos no log.",
            )
        except Exception:
            pass
        sys.exit(1)
