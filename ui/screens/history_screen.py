"""Tela com o histórico local das automações executadas."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import customtkinter as ctk

from services.activity_service import list_history
from ui.components.buttons import SecondaryButton
from ui.theme import COLORS, CORNER_RADIUS, FONT_FAMILY, FONT_SIZES, PADDING
from utils.paths import open_in_explorer


def _date_label(value: str) -> str:
    try:
        return datetime.fromisoformat(value).strftime("%d/%m/%Y às %H:%M")
    except (TypeError, ValueError):
        return "Data não disponível"


class HistoryScreen(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            self, text="Histórico",
            font=(FONT_FAMILY, FONT_SIZES["title"], "bold"),
            text_color=COLORS["text_primary"], anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=PADDING, pady=(PADDING, 4))
        ctk.CTkLabel(
            self, text="Consulte as últimas execuções e abra os resultados gerados.",
            font=(FONT_FAMILY, FONT_SIZES["subtitle"]),
            text_color=COLORS["text_secondary"], anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=PADDING, pady=(0, 20))

        area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        area.grid(row=2, column=0, sticky="nsew", padx=PADDING, pady=(0, PADDING))
        area.grid_columnconfigure(0, weight=1)
        entries = list_history()
        if not entries:
            ctk.CTkLabel(
                area, text="O histórico aparecerá aqui após a primeira execução.",
                text_color=COLORS["text_secondary"],
                font=(FONT_FAMILY, FONT_SIZES["body"]),
            ).grid(row=0, column=0, sticky="w", padx=8, pady=8)
            return

        for row, entry in enumerate(entries):
            card = ctk.CTkFrame(
                area, fg_color=COLORS["bg_card"], border_width=1,
                border_color=COLORS["border"], corner_radius=CORNER_RADIUS,
            )
            card.grid(row=row, column=0, sticky="ew", padx=4, pady=6)
            card.grid_columnconfigure(0, weight=1)
            success = entry.get("status") == "success"
            ctk.CTkLabel(
                card, text=entry.get("module_name", "Automação"),
                font=(FONT_FAMILY, FONT_SIZES["heading"], "bold"),
                text_color=COLORS["text_primary"], anchor="w",
            ).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 2))
            ctk.CTkLabel(
                card, text=entry.get("summary", "Sem detalhes."),
                font=(FONT_FAMILY, FONT_SIZES["body"]),
                text_color=COLORS["text_secondary"], anchor="w", wraplength=560,
            ).grid(row=1, column=0, sticky="w", padx=18)
            ctk.CTkLabel(
                card,
                text=f"{'Concluída' if success else 'Falhou'} • {_date_label(entry.get('created_at', ''))}",
                font=(FONT_FAMILY, FONT_SIZES["small"]),
                text_color=COLORS["success"] if success else COLORS["error"], anchor="w",
            ).grid(row=2, column=0, sticky="w", padx=18, pady=(4, 14))
            output = entry.get("output_path", "")
            if output:
                SecondaryButton(
                    card, text="Abrir pasta", width=108,
                    command=lambda value=output: open_in_explorer(
                        Path(value) if Path(value).is_dir() else Path(value).parent
                    ),
                ).grid(row=0, column=1, rowspan=3, padx=18, pady=14)
