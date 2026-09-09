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
from services.activity_service import record_execution
from services.excel_service import get_headers, split_spreadsheet, spreadsheet_preview
from ui.components.buttons import PrimaryButton, SecondaryButton
from ui.components.status_badge import StatusBadge
from ui.components.workflow_actions import ask_and_save_routine, confirm_execution
from ui.icons import load_icon
from ui.theme import COLORS, CORNER_RADIUS, FONT_FAMILY, FONT_SIZES, PADDING
from utils.errors import AppError
from utils.paths import open_in_explorer


class SplitSpreadsheetModule(AutomationModule):
    info = ModuleInfo(
        key="split_spreadsheet",
        name="Separar planilha",
        description="Divida uma planilha em vários arquivos por coluna.",
        category="Planilhas",
        icon="split",
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
            text="Separar planilha",
            image=load_icon("split", 24),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZES["title"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        header.grid(row=0, column=0, sticky="w", padx=PADDING, pady=(PADDING, 4))

        subtitle = ctk.CTkLabel(
            self,
            text="Selecione uma planilha e a coluna usada para dividi-la em vários arquivos.",
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
            text="Selecionar planilha",
            image=load_icon("file-spreadsheet", 18),
            compound="left",
            command=self._select_file,
        )
        select_btn.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 8))

        self.file_label = ctk.CTkLabel(
            panel,
            text="Nenhum arquivo selecionado.",
            font=(FONT_FAMILY, 12),
            text_color=COLORS["text_secondary"],
            anchor="w",
            wraplength=620,
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

        dest_btn = SecondaryButton(
            panel,
            text="Escolher pasta de destino",
            image=load_icon("folder-open", 18),
            compound="left",
            command=self._select_output,
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

        ctk.CTkLabel(
            panel, text="Prévia dos dados",
            font=(FONT_FAMILY, 13, "bold"), text_color=COLORS["text_primary"], anchor="w",
        ).grid(row=6, column=0, sticky="w", padx=20, pady=(0, 6))
        self.preview_label = ctk.CTkLabel(
            panel, text="Selecione uma planilha para visualizar uma amostra.",
            font=("Consolas", 11), text_color=COLORS["text_secondary"],
            anchor="w", justify="left", wraplength=760,
        )
        self.preview_label.grid(row=7, column=0, sticky="w", padx=20, pady=(0, 20))

        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.grid(row=3, column=0, sticky="ew", padx=PADDING, pady=20)

        self.run_btn = PrimaryButton(
            action_row, text="Gerar arquivos", command=self._run, width=180
        )
        self.run_btn.pack(side="left")

        SecondaryButton(
            action_row, text="Salvar rotina", command=self._save_routine, width=130
        ).pack(side="left", padx=(10, 0))

        self.progress = ctk.CTkProgressBar(action_row, width=200)
        self.progress.set(0)
        self.progress.pack(side="left", padx=16)
        self.progress.pack_forget()

        self.open_folder_btn = SecondaryButton(
            action_row,
            text="Abrir pasta",
            image=load_icon("folder-open", 18),
            compound="left",
            command=self._open_last_output,
        )

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
            preview = spreadsheet_preview(file)
        except AppError as exc:
            self.status_badge.set_state("erro", exc.user_message)
            return

        self.column_menu.configure(values=headers, state="normal")
        if headers:
            self.column_menu.set(headers[0])
        self.preview_label.configure(text=preview)
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
        details = (
            f"Arquivo: {self.selected_file}\n"
            f"Separar pela coluna: {column}\n"
            f"Destino: {self.output_dir}\n\n"
            f"Amostra:\n{self.preview_label.cget('text')}"
        )
        if not confirm_execution(self, "Separar planilha", details):
            return
        self._processing = True
        self.open_folder_btn.pack_forget()
        self.run_btn.configure(state="disabled")
        self.status_badge.set_state("processando")
        self.progress.pack(side="left", padx=16)
        self.progress.configure(mode="indeterminate")
        self.progress.start()

        selected_file = self.selected_file
        output_dir = self.output_dir

        def task():
            return split_spreadsheet(selected_file, column, output_dir)

        def on_success(count: int) -> None:
            self._processing = False
            self.progress.stop()
            self.progress.pack_forget()
            self._last_output_dir = Path(output_dir)
            self.open_folder_btn.pack(side="left", padx=(16, 0))
            self.run_btn.configure(state="normal")
            self.status_badge.set_state("concluido", f"{count} arquivo(s) gerado(s).")
            record_execution(
                SplitSpreadsheetModule.info.key, SplitSpreadsheetModule.info.name,
                "success", f"{count} arquivo(s) gerado(s) pela coluna {column}.", output_dir,
            )
            if self.app.settings.open_folder_after_finish:
                open_in_explorer(Path(self.output_dir))

        def on_error(message: str) -> None:
            self._processing = False
            self.progress.stop()
            self.progress.pack_forget()
            self.run_btn.configure(state="normal")
            self.status_badge.set_state("erro", message)
            record_execution(
                SplitSpreadsheetModule.info.key, SplitSpreadsheetModule.info.name,
                "error", message,
            )

        run_in_background(self, SplitSpreadsheetModule.info.key, task, on_success, on_error)

    def _open_last_output(self) -> None:
        if hasattr(self, "_last_output_dir"):
            open_in_explorer(self._last_output_dir)

    def _save_routine(self) -> None:
        if not self.selected_file or not self.output_dir or self.column_menu.get() == "-":
            self.status_badge.set_state(
                "erro", "Selecione o arquivo, a coluna e o destino antes de salvar."
            )
            return
        try:
            name = ask_and_save_routine(
                self, SplitSpreadsheetModule.info.key, SplitSpreadsheetModule.info.name,
                {"selected_file": self.selected_file, "column": self.column_menu.get(),
                 "output_dir": self.output_dir},
            )
        except OSError:
            self.status_badge.set_state("erro", "Não foi possível salvar a rotina.")
            return
        if name:
            self.status_badge.set_state("concluido", f"Rotina “{name}” salva.")

    def apply_preset(self, parameters: dict) -> None:
        file = parameters.get("selected_file")
        if not file or not Path(file).is_file():
            self.status_badge.set_state("erro", "O arquivo desta rotina não está mais disponível.")
            return
        self.selected_file = str(file)
        self.file_label.configure(text=Path(file).name)
        self.output_dir = str(parameters.get("output_dir", "")) or None
        if self.output_dir:
            self.output_label.configure(text=self.output_dir)
        try:
            headers = get_headers(file)
            self.column_menu.configure(values=headers, state="normal")
            column = str(parameters.get("column", headers[0]))
            self.column_menu.set(column if column in headers else headers[0])
            self.preview_label.configure(text=spreadsheet_preview(file))
        except AppError as exc:
            self.status_badge.set_state("erro", exc.user_message)
            return
        self.status_badge.set_state("pronto", "Rotina carregada. Revise a prévia.")
