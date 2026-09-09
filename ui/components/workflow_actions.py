"""Ações compartilhadas pelas telas de automação."""
from __future__ import annotations

from tkinter import messagebox
from typing import Any

import customtkinter as ctk

from services.activity_service import save_routine


def confirm_execution(parent: Any, title: str, details: str) -> bool:
    """Exibe a prévia final e só libera a execução após confirmação."""
    return messagebox.askokcancel(
        "Confirmar execução",
        f"{title}\n\n{details}\n\nDeseja iniciar esta automação?",
        parent=parent.winfo_toplevel(),
        icon="question",
    )


def ask_and_save_routine(
    parent: Any,
    module_key: str,
    module_name: str,
    parameters: dict[str, Any],
) -> str | None:
    dialog = ctk.CTkInputDialog(
        master=parent.winfo_toplevel(),
        text="Dê um nome para reutilizar esta configuração:",
        title="Salvar rotina",
    )
    name = dialog.get_input()
    if not name or not name.strip():
        return None
    save_routine(name, module_key, module_name, parameters)
    return name.strip()
