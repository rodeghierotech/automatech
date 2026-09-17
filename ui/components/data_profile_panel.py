"""Painel reutilizável para apresentar o Raio-X de uma planilha."""
from __future__ import annotations

import customtkinter as ctk

from services.spreadsheet_profile_service import CleaningPreview
from ui.theme import COLORS, CORNER_RADIUS, FONT_FAMILY, FONT_SIZES


class DataProfilePanel(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_card_hover"], corner_radius=CORNER_RADIUS, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self, text="Raio-X dos Dados",
            font=(FONT_FAMILY, FONT_SIZES["heading"], "bold"),
            text_color=COLORS["text_primary"], anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        self.summary_label = ctk.CTkLabel(
            self, text="", font=(FONT_FAMILY, FONT_SIZES["body"]),
            text_color=COLORS["text_secondary"], anchor="w", justify="left",
            wraplength=760,
        )
        self.summary_label.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))
        self.columns_frame = ctk.CTkScrollableFrame(self, height=132, fg_color="transparent")
        self.columns_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 10))
        self.columns_frame.grid_columnconfigure(0, weight=1)
        self.show_empty()

    def _clear_columns(self) -> None:
        for child in self.columns_frame.winfo_children():
            child.destroy()

    def show_empty(self) -> None:
        self.summary_label.configure(text="Selecione uma planilha para gerar o Raio-X.", text_color=COLORS["text_secondary"])
        self._clear_columns()

    def show_loading(self) -> None:
        self.summary_label.configure(text="Analisando planilha…", text_color=COLORS["accent"])
        self._clear_columns()

    def show_error(self, message: str) -> None:
        self.summary_label.configure(text=message, text_color=COLORS["error"])
        self._clear_columns()

    def render(self, preview: CleaningPreview) -> None:
        profile = preview.original
        metrics = preview.estimated_metrics
        self.summary_label.configure(
            text=(
                f"{profile.rows} linhas • {profile.columns} colunas • "
                f"{profile.empty_cells} células vazias • {profile.duplicate_rows} duplicado(s)\n"
                f"Estimativa após a limpeza: {metrics.final_rows} linhas × {metrics.final_columns} colunas"
            ),
            text_color=COLORS["text_primary"],
        )
        self._clear_columns()
        for row, column in enumerate(profile.column_profiles):
            ctk.CTkLabel(
                self.columns_frame,
                text=(
                    f"{column.name}  |  {column.inferred_type}  |  vazios: {column.empty_cells}  |  "
                    f"distintos: {column.distinct_values}  |  espaços: {column.trimmed_text_cells}"
                ),
                font=("Consolas", 11), anchor="w", text_color=COLORS["text_secondary"],
            ).grid(row=row, column=0, sticky="ew", padx=8, pady=3)
