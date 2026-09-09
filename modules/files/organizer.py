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
from services.activity_service import record_execution
from services.file_service import organize_folder, preview_organization
from ui.components.buttons import PrimaryButton, SecondaryButton
from ui.components.status_badge import StatusBadge
from ui.components.workflow_actions import ask_and_save_routine, confirm_execution
from ui.icons import load_icon
from ui.theme import COLORS, CORNER_RADIUS, FONT_FAMILY, FONT_SIZES, PADDING
from utils.errors import AppError
from utils.paths import open_in_explorer


class FileOrganizerModule(AutomationModule):
    info = ModuleInfo(
        key="file_organizer",
        name="Organizador de arquivos",
        description="Organize uma pasta automaticamente por tipo de arquivo.",
        category="Arquivos",
        icon="folder-cog",
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
            text="Organizador de arquivos",
            image=load_icon("folder-cog", 24),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZES["title"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        header.grid(row=0, column=0, sticky="w", padx=PADDING, pady=(PADDING, 4))

        subtitle = ctk.CTkLabel(
            self,
            text="Escolha uma pasta para organizar os arquivos automaticamente por tipo.",
            font=(FONT_FAMILY, FONT_SIZES["subtitle"]),
            text_color=COLORS["text_secondary"],
            anchor="w",
            wraplength=620,
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=PADDING, pady=(0, 20))

        panel = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=CORNER_RADIUS)
        panel.grid(row=2, column=0, sticky="ew", padx=PADDING)
        panel.grid_columnconfigure(0, weight=1)

        select_btn = SecondaryButton(
            panel,
            text="Selecionar pasta",
            image=load_icon("folder-open", 18),
            compound="left",
            command=self._select_folder,
        )
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
            wraplength=620,
        )
        self.preview_label.grid(row=2, column=0, sticky="w", padx=20, pady=(12, 20))

        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.grid(row=3, column=0, sticky="ew", padx=PADDING, pady=20)

        self.run_btn = PrimaryButton(
            action_row, text="Organizar arquivos", command=self._run, width=180, state="disabled"
        )
        self.run_btn.pack(side="left")

        SecondaryButton(
            action_row, text="Salvar rotina", command=self._save_routine, width=130
        ).pack(side="left", padx=(10, 0))

        self.open_folder_btn = SecondaryButton(
            action_row,
            text="Abrir pasta",
            image=load_icon("folder-open", 18),
            compound="left",
            command=self._open_last_output,
        )

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

        if not confirm_execution(
            self,
            "Organizar arquivos",
            f"Pasta: {self.selected_folder}\n\n{self.preview_label.cget('text')}",
        ):
            return

        self._processing = True
        self.open_folder_btn.pack_forget()
        self.run_btn.configure(state="disabled")
        self.status_badge.set_state("processando")
        selected_folder = self.selected_folder

        def task():
            return organize_folder(selected_folder)

        def on_success(moved: dict[str, int]) -> None:
            self._processing = False
            self.run_btn.configure(state="normal")
            self._last_output_dir = Path(selected_folder)
            self.open_folder_btn.pack(side="left", padx=(16, 0))
            total = sum(moved.values())
            self.status_badge.set_state("concluido", f"{total} arquivo(s) organizado(s).")
            details = "  |  ".join(f"{cat}: {n}" for cat, n in sorted(moved.items()))
            self.preview_label.configure(text=details)
            record_execution(
                FileOrganizerModule.info.key, FileOrganizerModule.info.name,
                "success", f"{total} arquivo(s) organizado(s).", selected_folder,
            )
            if self.app.settings.open_folder_after_finish:
                open_in_explorer(Path(selected_folder))

        def on_error(message: str) -> None:
            self._processing = False
            self.run_btn.configure(state="normal")
            self.status_badge.set_state("erro", message)
            record_execution(
                FileOrganizerModule.info.key, FileOrganizerModule.info.name,
                "error", message,
            )

        run_in_background(self, FileOrganizerModule.info.key, task, on_success, on_error)

    def _open_last_output(self) -> None:
        if hasattr(self, "_last_output_dir"):
            open_in_explorer(self._last_output_dir)

    def _save_routine(self) -> None:
        if not self.selected_folder:
            self.status_badge.set_state("erro", "Selecione uma pasta antes de salvar.")
            return
        try:
            name = ask_and_save_routine(
                self, FileOrganizerModule.info.key, FileOrganizerModule.info.name,
                {"selected_folder": self.selected_folder},
            )
        except OSError:
            self.status_badge.set_state("erro", "Não foi possível salvar a rotina.")
            return
        if name:
            self.status_badge.set_state("concluido", f"Rotina “{name}” salva.")

    def apply_preset(self, parameters: dict) -> None:
        folder = parameters.get("selected_folder")
        if not folder or not Path(folder).is_dir():
            self.status_badge.set_state("erro", "A pasta desta rotina não está mais disponível.")
            return
        self.selected_folder = str(folder)
        self.folder_label.configure(text=self.selected_folder)
        try:
            counts = preview_organization(self.selected_folder)
        except AppError as exc:
            self.status_badge.set_state("erro", exc.user_message)
            return
        total = sum(counts.values())
        details = "  |  ".join(f"{cat}: {n}" for cat, n in sorted(counts.items()))
        self.preview_label.configure(
            text=f"{total} arquivo(s) serão organizados.\n{details}"
        )
        self.run_btn.configure(state="normal" if total else "disabled")
        self.status_badge.set_state("pronto", "Rotina carregada. Revise a prévia.")
