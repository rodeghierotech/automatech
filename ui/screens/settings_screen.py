"""Tela de configurações do sistema (tema, pasta padrão, comportamento)."""
from __future__ import annotations

from tkinter import filedialog

import customtkinter as ctk

from ui.theme import COLORS, CORNER_RADIUS, FONT_FAMILY, PADDING


class SettingsScreen(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app
        self.settings = app.settings
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Configurações",
            font=(FONT_FAMILY, 24, "bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        title.grid(row=0, column=0, sticky="w", padx=PADDING, pady=(PADDING, 20))

        panel = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=CORNER_RADIUS)
        panel.grid(row=1, column=0, sticky="ew", padx=PADDING, pady=(0, PADDING))
        panel.grid_columnconfigure(1, weight=1)

        # Tema
        ctk.CTkLabel(
            panel, text="Tema", font=(FONT_FAMILY, 14, "bold"), text_color=COLORS["text_primary"]
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 4))

        self.theme_var = ctk.StringVar(value=self.settings.theme)
        theme_menu = ctk.CTkSegmentedButton(
            panel,
            values=["dark", "light"],
            variable=self.theme_var,
            command=self._on_theme_change,
        )
        theme_menu.grid(row=1, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 16))

        # Pasta padrão de saída
        ctk.CTkLabel(
            panel,
            text="Pasta padrão de saída",
            font=(FONT_FAMILY, 14, "bold"),
            text_color=COLORS["text_primary"],
        ).grid(row=2, column=0, sticky="w", padx=20, pady=(4, 4))

        self.output_dir_var = ctk.StringVar(value=self.settings.default_output_dir)
        output_entry = ctk.CTkEntry(panel, textvariable=self.output_dir_var, width=360)
        output_entry.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 16))

        browse_btn = ctk.CTkButton(
            panel, text="Selecionar pasta", width=140, command=self._browse_output_dir
        )
        browse_btn.grid(row=3, column=1, sticky="w", padx=(0, 20), pady=(0, 16))

        # Abrir pasta após finalizar
        self.open_after_var = ctk.BooleanVar(value=self.settings.open_folder_after_finish)
        open_after_check = ctk.CTkCheckBox(
            panel,
            text="Abrir pasta após finalizar uma automação",
            variable=self.open_after_var,
            command=self._on_open_after_change,
        )
        open_after_check.grid(row=4, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 20))

    def _on_theme_change(self, value: str) -> None:
        self.settings.theme = value
        self.settings.save()
        ctk.set_appearance_mode(value)

    def _browse_output_dir(self) -> None:
        folder = filedialog.askdirectory(title="Selecione a pasta padrão de saída")
        if folder:
            self.output_dir_var.set(folder)
            self.settings.default_output_dir = folder
            self.settings.save()

    def _on_open_after_change(self) -> None:
        self.settings.open_folder_after_finish = self.open_after_var.get()
        self.settings.save()
