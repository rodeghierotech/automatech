"""Sidebar fixa de navegação da aplicação."""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from config.settings import APP_NAME, APP_VERSION
from ui.icons import load_icon
from ui.theme import COLORS, FONT_FAMILY

NAV_ITEMS = [
    ("home", "Início", "house"),
    ("spreadsheets", "Planilhas", "table-2"),
    ("files", "Arquivos", "folder"),
    ("routines", "Rotinas", "workflow"),
    ("history", "Histórico", "file-spreadsheet"),
    ("settings", "Configurações", "settings"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_navigate: Callable[[str], None], **kwargs):
        super().__init__(
            parent, width=232, fg_color=COLORS["bg_sidebar"], corner_radius=0, **kwargs
        )
        self.on_navigate = on_navigate
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(len(NAV_ITEMS) + 1, weight=1)

        logo = ctk.CTkLabel(
            self,
            text=APP_NAME,
            image=load_icon("workflow", 26),
            compound="left",
            font=(FONT_FAMILY, 21, "bold"),
            text_color=COLORS["text_primary"],
        )
        logo.grid(row=0, column=0, sticky="w", padx=24, pady=(28, 24))

        self._buttons: dict[str, ctk.CTkButton] = {}
        for i, (key, label, icon) in enumerate(NAV_ITEMS, start=1):
            btn = ctk.CTkButton(
                self,
                text=label,
                image=load_icon(icon, 19),
                compound="left",
                anchor="w",
                fg_color="transparent",
                hover_color=COLORS["bg_card_hover"],
                text_color=COLORS["text_secondary"],
                font=(FONT_FAMILY, 14),
                corner_radius=10,
                height=42,
                border_spacing=12,
                command=lambda k=key: self._handle_click(k),
            )
            btn.grid(row=i, column=0, sticky="ew", padx=12, pady=3)
            self._buttons[key] = btn

        version_label = ctk.CTkLabel(
            self,
            text=f"v{APP_VERSION}",
            font=(FONT_FAMILY, 11),
            text_color=COLORS["text_secondary"],
        )
        version_label.grid(row=len(NAV_ITEMS) + 2, column=0, sticky="sw", padx=24, pady=16)

        self.set_active("home")

    def _handle_click(self, key: str) -> None:
        self.set_active(key)
        self.on_navigate(key)

    def set_active(self, key: str) -> None:
        for btn_key, btn in self._buttons.items():
            if btn_key == key:
                btn.configure(
                    fg_color=COLORS["accent_soft"],
                    text_color=COLORS["text_primary"],
                )
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_secondary"])
