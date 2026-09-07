"""Módulo: Organizador de arquivos.

Organiza automaticamente os arquivos de uma pasta em subpastas por
categoria (Imagens, PDF, Planilhas, etc). Nunca apaga arquivos.
"""
from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from core.module_base import AutomationModule, ModuleInfo
from core.task_runner import run_in_background
from services.file_service import organize_folder, preview_organization
from ui.components.status_badge import StatusBadge
from ui.theme import COLORS, CORNER_RADIUS, FONT_FAMILY, PADDING
from utils.errors import AppError
from utils.paths import open_in_explorer


class FileOrganizerModule(AutomationModule):
    info = ModuleInfo(
        key="file_organizer",
        name="Organizador de arquivos",
        description="Organize uma pasta automaticamente por tipo de arquivo.",
        category="Arquivos",
        icon="🗂️",
    )

    def build_ui(self, parent, app) -> "ctk.CTkFrame":
        return FileOrganizerScreen(parent, app)


class FileOrganizerScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.selected_folder: str | None = None
        self._processing = False

        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            self,
            text="🗂️  Organizador de arquivos",
            font=(FONT_FAMILY, 22, "bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        header.grid(row=0, column=0, sticky="w", padx=PADDING, pady=(PADDING, 4))

        subtitle = ctk.CTkLabel(
            self,
            text="Escolha uma pasta para organizar os arquivos automaticamente por tipo.",
            font=(FONT_FAMILY, 13),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=PADDING, pady=(0, 20))

        panel = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=CORNER_RADIUS)
        panel.grid(row=2, column=0, sticky="ew", padx=PADDING)
        panel.grid_columnconfigure(0, weight=1)

        select_btn = ctk.CTkButton(panel, text="Selecionar pasta", command=self._select_folder)
        select_btn.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 8))

        self.folder_label = ctk.CTkLabel(
            panel,
            text="Nenhuma pasta selecionada.",
            font=(FONT_FAMILY, 12),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        self.folder_label.grid(row=1, column=0, sticky="w", padx=20)

        self.preview_label = ctk.CTkLabel(
            panel,
            text="",
            font=(FONT_FAMILY, 12),
            text_color=COLORS["text_primary"],
            anchor="w",
            justify="left",
        )
        self.preview_label.grid(row=2, column=0, sticky="w", padx=20, pady=(12, 20))

        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.grid(row=3, column=0, sticky="ew", padx=PADDING, pady=20)

        self.run_btn = ctk.CTkButton(
            action_row, text="Organizar arquivos", command=self._run, width=180, state="disabled"
        )
        self.run_btn.pack(side="left")

        self.status_badge = StatusBadge(self)
        self.status_badge.grid(row=4, column=0, sticky="w", padx=PADDING)

    def _select_folder(self) -> None:
        folder = filedialog.askdirectory(title="Selecione a pasta a organizar")
        if not folder:
            return

        self.selected_folder = folder
        self.folder_label.configure(text=folder)

        try:
            counts = preview_organization(folder)
        except AppError as exc:
            self.status_badge.set_state("erro", exc.user_message)
            self.run_btn.configure(state="disabled")
            return

        total = sum(counts.values())
        if total == 0:
            self.preview_label.configure(text="Nenhum arquivo encontrado nesta pasta.")
            self.run_btn.configure(state="disabled")
            self.status_badge.set_state("aguardando")
            return

        details = "  |  ".join(f"{cat}: {n}" for cat, n in sorted(counts.items()))
        self.preview_label.configure(
            text=f"{total} arquivo(s) serão organizados.\n{details}"
        )
        self.run_btn.configure(state="normal")
        self.status_badge.set_state("pronto")

    def _run(self) -> None:
        if self._processing or not self.selected_folder:
            return

        self._processing = True
        self.run_btn.configure(state="disabled")
        self.status_badge.set_state("processando")

        def task():
            return organize_folder(self.selected_folder)

        def on_success(moved: dict[str, int]) -> None:
            self._processing = False
            self.run_btn.configure(state="normal")
            total = sum(moved.values())
            self.status_badge.set_state("concluido", f"{total} arquivo(s) organizado(s).")
            details = "  |  ".join(f"{cat}: {n}" for cat, n in sorted(moved.items()))
            self.preview_label.configure(text=details)
            if self.app.settings.open_folder_after_finish:
                open_in_explorer(Path(self.selected_folder))

        def on_error(message: str) -> None:
            self._processing = False
            self.run_btn.configure(state="normal")
            self.status_badge.set_state("erro", message)

        run_in_background(self, FileOrganizerModule.info.key, task, on_success, on_error)
