"""Módulo: Separar planilha.

Divide uma planilha em vários arquivos, um por valor único de uma coluna
escolhida pelo usuário (ex: separar por Vendedor).
"""
from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from core.module_base import AutomationModule, ModuleInfo
from core.task_runner import run_in_background
from services.excel_service import get_headers, split_spreadsheet
from ui.components.status_badge import StatusBadge
from ui.theme import COLORS, CORNER_RADIUS, FONT_FAMILY, PADDING
from utils.errors import AppError
from utils.paths import open_in_explorer


class SplitSpreadsheetModule(AutomationModule):
    info = ModuleInfo(
        key="split_spreadsheet",
        name="Separar planilha",
        description="Divida uma planilha em vários arquivos por coluna.",
        category="Planilhas",
        icon="✂️",
    )

    def build_ui(self, parent, app) -> "ctk.CTkFrame":
        return SplitSpreadsheetScreen(parent, app)


class SplitSpreadsheetScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.selected_file: str | None = None
        self.output_dir: str | None = None
        self._processing = False

        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            self,
            text="✂️  Separar planilha",
            font=(FONT_FAMILY, 22, "bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        header.grid(row=0, column=0, sticky="w", padx=PADDING, pady=(PADDING, 4))

        subtitle = ctk.CTkLabel(
            self,
            text="Selecione uma planilha e a coluna usada para dividi-la em vários arquivos.",
            font=(FONT_FAMILY, 13),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=PADDING, pady=(0, 20))

        panel = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=CORNER_RADIUS)
        panel.grid(row=2, column=0, sticky="ew", padx=PADDING)
        panel.grid_columnconfigure(0, weight=1)

        select_btn = ctk.CTkButton(panel, text="Selecionar planilha", command=self._select_file)
        select_btn.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 8))

        self.file_label = ctk.CTkLabel(
            panel,
            text="Nenhum arquivo selecionado.",
            font=(FONT_FAMILY, 12),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        self.file_label.grid(row=1, column=0, sticky="w", padx=20)

        ctk.CTkLabel(
            panel,
            text="Coluna para separar:",
            font=(FONT_FAMILY, 13),
            text_color=COLORS["text_primary"],
            anchor="w",
        ).grid(row=2, column=0, sticky="w", padx=20, pady=(16, 4))

        self.column_menu = ctk.CTkOptionMenu(panel, values=["-"], state="disabled")
        self.column_menu.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 16))

        dest_btn = ctk.CTkButton(
            panel, text="Escolher pasta de destino", command=self._select_output
        )
        dest_btn.grid(row=4, column=0, sticky="w", padx=20, pady=(0, 8))

        self.output_label = ctk.CTkLabel(
            panel,
            text="Nenhuma pasta selecionada.",
            font=(FONT_FAMILY, 12),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        self.output_label.grid(row=5, column=0, sticky="w", padx=20, pady=(0, 20))

        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.grid(row=3, column=0, sticky="ew", padx=PADDING, pady=20)

        self.run_btn = ctk.CTkButton(action_row, text="Separar", command=self._run, width=180)
        self.run_btn.pack(side="left")

        self.progress = ctk.CTkProgressBar(action_row, width=200)
        self.progress.set(0)
        self.progress.pack(side="left", padx=16)
        self.progress.pack_forget()

        self.status_badge = StatusBadge(self)
        self.status_badge.grid(row=4, column=0, sticky="w", padx=PADDING)

    def _select_file(self) -> None:
        file = filedialog.askopenfilename(
            title="Selecione a planilha", filetypes=[("Planilhas Excel", "*.xlsx")]
        )
        if not file:
            return

        self.selected_file = file
        self.file_label.configure(text=Path(file).name)

        try:
            headers = get_headers(file)
        except AppError as exc:
            self.status_badge.set_state("erro", exc.user_message)
            return

        self.column_menu.configure(values=headers, state="normal")
        if headers:
            self.column_menu.set(headers[0])
        self.status_badge.set_state("pronto")

    def _select_output(self) -> None:
        folder = filedialog.askdirectory(title="Selecione a pasta de destino")
        if folder:
            self.output_dir = folder
            self.output_label.configure(text=folder)

    def _run(self) -> None:
        if self._processing:
            return
        if not self.selected_file:
            self.status_badge.set_state("erro", "Selecione uma planilha primeiro.")
            return
        if not self.output_dir:
            self.status_badge.set_state("erro", "Selecione a pasta de destino.")
            return

        column = self.column_menu.get()
        self._processing = True
        self.run_btn.configure(state="disabled")
        self.status_badge.set_state("processando")
        self.progress.pack(side="left", padx=16)
        self.progress.set(0)

        def task():
            def on_progress(current, total):
                self.after(0, lambda: self.progress.set(current / max(total, 1)))

            return split_spreadsheet(self.selected_file, column, self.output_dir, on_progress)

        def on_success(count: int) -> None:
            self._processing = False
            self.run_btn.configure(state="normal")
            self.status_badge.set_state("concluido", f"{count} arquivo(s) gerado(s).")
            if self.app.settings.open_folder_after_finish:
                open_in_explorer(Path(self.output_dir))

        def on_error(message: str) -> None:
            self._processing = False
            self.run_btn.configure(state="normal")
            self.status_badge.set_state("erro", message)

        run_in_background(self, SplitSpreadsheetModule.info.key, task, on_success, on_error)
