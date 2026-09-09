"""Executa funções demoradas em uma thread separada, sem travar a UI.

Regra de ouro: nada que rode dentro da thread toca em widgets diretamente.
O worker envia o resultado por uma fila, consultada pela thread principal.
"""
from __future__ import annotations

import threading
from queue import Empty, Queue
from tkinter import TclError
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

    result_queue: Queue[tuple[str, Any]] = Queue(maxsize=1)

    def worker() -> None:
        try:
            result = task()
        except AppError as exc:
            log_error(module_name, exc)
            result_queue.put(("error", exc.user_message))
        except Exception as exc:  # noqa: BLE001 - captura genérica proposital
            log_error(module_name, exc)
            result_queue.put(
                (
                    "error",
                    "Ocorreu um erro inesperado ao processar. Detalhes foram salvos no log.",
                )
            )
        else:
            result_queue.put(("success", result))

    def poll_result() -> None:
        try:
            state, payload = result_queue.get_nowait()
        except Empty:
            try:
                widget.after(50, poll_result)
            except TclError:
                return
            return

        try:
            if not widget.winfo_exists():
                return
            if state == "success":
                on_success(payload)
            else:
                on_error(payload)
        except TclError:
            return

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    widget.after(50, poll_result)
