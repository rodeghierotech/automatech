"""Card visual usado na tela inicial para representar um módulo de automação."""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from core.module_base import ModuleInfo
from ui.theme import COLORS, CORNER_RADIUS, FONT_FAMILY


class ModuleCard(ctk.CTkFrame):
    def __init__(self, parent, info: ModuleInfo, on_open: Callable[[str], None], **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=CORNER_RADIUS,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs,
        )
        self.info = info
        self.on_open = on_open

        self.grid_columnconfigure(0, weight=1)

        icon_label = ctk.CTkLabel(
            self, text=info.icon, font=(FONT_FAMILY, 32), text_color=COLORS["text_primary"]
        )
        icon_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 8))

        name_label = ctk.CTkLabel(
            self,
            text=info.name,
            font=(FONT_FAMILY, 16, "bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        name_label.grid(row=1, column=0, sticky="w", padx=20)

        desc_label = ctk.CTkLabel(
            self,
            text=info.description,
            font=(FONT_FAMILY, 12),
            text_color=COLORS["text_secondary"],
            anchor="w",
            justify="left",
            wraplength=220,
        )
        desc_label.grid(row=2, column=0, sticky="w", padx=20, pady=(4, 16))

        open_btn = ctk.CTkButton(
            self,
            text="Abrir",
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            corner_radius=CORNER_RADIUS,
            command=lambda: self.on_open(info.key),
        )
        open_btn.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
