"""Tela de configurações do sistema (tema, pasta padrão, comportamento)."""
from __future__ import annotations

from tkinter import filedialog

import customtkinter as ctk

from ui.components.buttons import SecondaryButton
from ui.components.status_badge import StatusBadge
from ui.icons import load_icon
from ui.theme import COLORS, CORNER_RADIUS, FONT_FAMILY, FONT_SIZES, PADDING


class SettingsScreen(ctk.CTkFrame):
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.app = app
        self.settings = app.settings
        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            self,
            text="Configurações",
            image=load_icon("settings", 24),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZES["title"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        title.grid(row=0, column=0, sticky="w", padx=PADDING, pady=(PADDING, 20))

        panel = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=CORNER_RADIUS)
        panel.grid(row=1, column=0, sticky="ew", padx=PADDING, pady=(0, PADDING))
        panel.grid_columnconfigure(0, weight=1)

        # Tema
        ctk.CTkLabel(
            panel, text="Tema", font=(FONT_FAMILY, 14, "bold"), text_color=COLORS["text_primary"]
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 4))

        self.theme_var = ctk.StringVar(
            value="Claro" if self.settings.theme == "light" else "Escuro"
        )
        theme_menu = ctk.CTkSegmentedButton(
            panel,
            values=["Escuro", "Claro"],
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
        output_entry = ctk.CTkEntry(
            panel,
            textvariable=self.output_dir_var,
            height=40,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
        )
        output_entry.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 16))

        browse_btn = SecondaryButton(
            panel,
            text="Selecionar pasta",
            image=load_icon("folder-open", 18),
            compound="left",
            width=150,
            command=self._browse_output_dir,
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

        self.status_badge = StatusBadge(self)
        self.status_badge.grid(row=2, column=0, sticky="w", padx=PADDING)

    def _save_settings(self) -> bool:
        try:
            self.settings.save()
        except OSError:
            self.status_badge.set_state(
                "erro", "Não foi possível salvar as configurações neste computador."
            )
            return False
        self.status_badge.set_state("concluido", "Configurações salvas.")
        return True

    def _on_theme_change(self, value: str) -> None:
        self.settings.theme = "light" if value == "Claro" else "dark"
        self._save_settings()
        ctk.set_appearance_mode(self.settings.theme)

    def _browse_output_dir(self) -> None:
        folder = filedialog.askdirectory(title="Selecione a pasta padrão de saída")
        if folder:
            self.output_dir_var.set(folder)
            self.settings.default_output_dir = folder
            self._save_settings()

    def _on_open_after_change(self) -> None:
        self.settings.open_folder_after_finish = self.open_after_var.get()
        self._save_settings()
