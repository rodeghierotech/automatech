"""Tela inicial: apresenta os módulos disponíveis como cards."""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from core.module_registry import MODULES
from ui.components.module_card import ModuleCard
from ui.theme import COLORS, FONT_FAMILY, FONT_SIZES, PADDING

CARDS_PER_ROW = 2


class HomeScreen(ctk.CTkFrame):
    def __init__(
        self,
        parent,
        on_open_module: Callable[[str], None],
        category: str | None = None,
        **kwargs,
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        title = ctk.CTkLabel(
            self,
            text=category or "Automatech",
            font=(FONT_FAMILY, FONT_SIZES["title"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        title.grid(row=0, column=0, sticky="w", padx=PADDING, pady=(PADDING, 0))

        subtitle = ctk.CTkLabel(
            self,
            text=(
                "Escolha uma automação desta categoria."
                if category
                else "Automatize tarefas repetitivas em poucos cliques."
            ),
            font=(FONT_FAMILY, FONT_SIZES["subtitle"]),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=PADDING, pady=(4, 20))

        cards_area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        cards_area.grid(row=2, column=0, sticky="nsew", padx=PADDING - 6, pady=(0, PADDING))
        for col in range(CARDS_PER_ROW):
            cards_area.grid_columnconfigure(col, weight=1, uniform="cards")

        modules = [module for module in MODULES if category is None or module.info.category == category]
        for idx, module in enumerate(modules):
            row, col = divmod(idx, CARDS_PER_ROW)
            card = ModuleCard(cards_area, module.info, on_open=on_open_module)
            card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
