"""Badge visual reutilizável para indicar o estado de uma automação."""
from __future__ import annotations

import customtkinter as ctk

from ui.theme import COLORS, FONT_FAMILY

STATUS_STYLES = {
    "aguardando": (COLORS["text_secondary"], "Aguardando seleção"),
    "pronto": (COLORS["accent"], "Pronto para executar"),
    "processando": (COLORS["warning"], "Processando..."),
    "concluido": (COLORS["success"], "Concluído"),
    "erro": (COLORS["error"], "Ocorreu um erro"),
}


class StatusBadge(ctk.CTkLabel):
    def __init__(self, parent, **kwargs):
        color, text = STATUS_STYLES["aguardando"]
        super().__init__(
            parent,
            text=f"●  {text}",
            font=(FONT_FAMILY, 12, "bold"),
            text_color=color,
            **kwargs,
        )
        self._state = "aguardando"

    def set_state(self, state: str, custom_text: str | None = None) -> None:
        color, default_text = STATUS_STYLES.get(state, STATUS_STYLES["aguardando"])
        text = custom_text or default_text
        self.configure(text=f"●  {text}", text_color=color)
        self._state = state

    @property
    def state(self) -> str:
        return self._state
