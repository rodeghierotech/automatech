"""Executa funções demoradas em uma thread separada, sem travar a UI.

Regra de ouro: nada que rode dentro da thread deve tocar em widgets
diretamente. O retorno (sucesso ou erro) é entregue de volta à thread
principal via `widget.after(0, callback)`, que é a forma segura do
Tkinter/CustomTkinter de atualizar a interface.
"""
from __future__ import annotations

import threading
from typing import Any, Callable

from core.logger import log_error
from utils.errors import AppError


def run_in_background(
    widget: Any,
    module_name: str,
    task: Callable[[], Any],
    on_success: Callable[[Any], None],
    on_error: Callable[[str], None],
) -> None:
    """Roda `task()` em background e entrega o resultado com segurança na UI.

    - widget: qualquer widget CTk vivo (usado apenas para agendar via `.after`).
    - task: função sem argumentos que faz o trabalho pesado e retorna um valor.
    - on_success: chamado na thread principal com o valor retornado por task().
    - on_error: chamado na thread principal com uma mensagem amigável.
    """

    def worker() -> None:
        try:
            result = task()
        except AppError as exc:
            log_error(module_name, exc)
            widget.after(0, lambda: on_error(exc.user_message))
        except Exception as exc:  # noqa: BLE001 - captura genérica proposital
            log_error(module_name, exc)
            widget.after(
                0,
                lambda: on_error(
                    "Ocorreu um erro inesperado ao processar. Detalhes foram salvos no log."
                ),
            )
        else:
            widget.after(0, lambda: on_success(result))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
