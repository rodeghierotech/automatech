"""Card visual usado na tela inicial para representar um módulo de automação."""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from core.module_base import ModuleInfo
from ui.icons import load_icon
from ui.theme import BUTTON_HEIGHT, COLORS, CORNER_RADIUS, FONT_FAMILY, FONT_SIZES


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
        self.grid_rowconfigure(2, weight=1)

        icon_frame = ctk.CTkFrame(
            self,
            width=48,
            height=48,
            fg_color=COLORS["accent_soft"],
            corner_radius=12,
        )
        icon_frame.grid(row=0, column=0, sticky="w", padx=22, pady=(22, 14))
        icon_frame.grid_propagate(False)
        icon_label = ctk.CTkLabel(icon_frame, text="", image=load_icon(info.icon, 24))
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        name_label = ctk.CTkLabel(
            self,
            text=info.name,
            font=(FONT_FAMILY, FONT_SIZES["heading"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        name_label.grid(row=1, column=0, sticky="w", padx=22)

        desc_label = ctk.CTkLabel(
            self,
            text=info.description,
            font=(FONT_FAMILY, FONT_SIZES["body"]),
            text_color=COLORS["text_secondary"],
            anchor="w",
            justify="left",
            wraplength=320,
        )
        desc_label.grid(row=2, column=0, sticky="nw", padx=22, pady=(6, 20))

        open_btn = ctk.CTkButton(
            self,
            text="Abrir automação",
            image=load_icon("external-link", 17),
            compound="left",
            height=BUTTON_HEIGHT,
            fg_color=COLORS["accent_soft"],
            hover_color=COLORS["bg_card_hover"],
            text_color=COLORS["text_primary"],
            corner_radius=CORNER_RADIUS,
            command=lambda: self.on_open(info.key),
        )
        open_btn.grid(row=3, column=0, sticky="ew", padx=22, pady=(0, 22))
