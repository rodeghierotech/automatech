"""Módulo: Limpar planilha.

Aplica limpeza básica de dados (linhas/colunas vazias, duplicados, espaços
extras, cabeçalhos). Nunca sobrescreve o arquivo original.
"""
from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from core.module_base import AutomationModule, ModuleInfo
from core.task_runner import run_in_background
from services.activity_service import record_execution
from services.excel_service import clean_spreadsheet, spreadsheet_preview
from ui.components.buttons import PrimaryButton, SecondaryButton
from ui.components.status_badge import StatusBadge
from ui.components.workflow_actions import ask_and_save_routine, confirm_execution
from ui.icons import load_icon
from ui.theme import COLORS, CORNER_RADIUS, FONT_FAMILY, FONT_SIZES, PADDING
from utils.errors import AppError
from utils.paths import open_in_explorer, unique_path


class CleanSpreadsheetModule(AutomationModule):
    info = ModuleInfo(
        key="clean_spreadsheet",
        name="Limpar planilha",
        description="Remova duplicados, linhas vazias e espaços extras.",
        category="Planilhas",
        icon="brush-cleaning",
    )

    def build_ui(self, parent, app) -> "ctk.CTkFrame":
        return CleanSpreadsheetScreen(parent, app)


class CleanSpreadsheetScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.selected_file: str | None = None
        self._processing = False

        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            self,
            text="Limpar planilha",
            image=load_icon("brush-cleaning", 24),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZES["title"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        header.grid(row=0, column=0, sticky="w", padx=PADDING, pady=(PADDING, 4))

        subtitle = ctk.CTkLabel(
            self,
            text="Escolha a planilha e as opções de limpeza. Um novo arquivo será gerado.",
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
        )
        self.file_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 16))

        options_frame = ctk.CTkFrame(panel, fg_color="transparent")
        options_frame.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 8))

        self.opt_empty_rows = ctk.BooleanVar(value=True)
        self.opt_duplicates = ctk.BooleanVar(value=True)
        self.opt_whitespace = ctk.BooleanVar(value=True)
        self.opt_empty_cols = ctk.BooleanVar(value=True)
        self.opt_headers = ctk.BooleanVar(value=True)
        self.opt_ignore_case = ctk.BooleanVar(value=False)

        checks = [
            ("Remover linhas completamente vazias", self.opt_empty_rows),
            ("Remover linhas duplicadas", self.opt_duplicates),
            ("Ignorar maiúsculas/minúsculas ao remover duplicados", self.opt_ignore_case),
            ("Remover espaços extras em textos", self.opt_whitespace),
            ("Remover colunas completamente vazias", self.opt_empty_cols),
            ("Padronizar cabeçalhos", self.opt_headers),
        ]
        for i, (label, var) in enumerate(checks):
            ctk.CTkCheckBox(options_frame, text=label, variable=var).grid(
                row=i, column=0, sticky="w", pady=4
            )

        ctk.CTkLabel(
            panel, text="Prévia dos dados",
            font=(FONT_FAMILY, 13, "bold"), text_color=COLORS["text_primary"], anchor="w",
        ).grid(row=3, column=0, sticky="w", padx=20, pady=(4, 6))
        self.preview_label = ctk.CTkLabel(
            panel, text="Selecione uma planilha para visualizar uma amostra.",
            font=("Consolas", 11), text_color=COLORS["text_secondary"],
            anchor="w", justify="left", wraplength=760,
        )
        self.preview_label.grid(row=4, column=0, sticky="w", padx=20, pady=(0, 20))

        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.grid(row=3, column=0, sticky="ew", padx=PADDING, pady=20)

        self.run_btn = PrimaryButton(
            action_row, text="Limpar planilha", command=self._run, width=180
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

        self.summary_label = ctk.CTkLabel(
            self,
            text="",
            font=(FONT_FAMILY, 12),
            text_color=COLORS["text_secondary"],
            anchor="w",
            justify="left",
            wraplength=620,
        )
        self.summary_label.grid(row=5, column=0, sticky="w", padx=PADDING, pady=(8, 0))

    def _select_file(self) -> None:
        file = filedialog.askopenfilename(
            title="Selecione a planilha", filetypes=[("Planilhas Excel", "*.xlsx")]
        )
        if file:
            self.selected_file = file
            self.file_label.configure(text=Path(file).name)
            try:
                self.preview_label.configure(text=spreadsheet_preview(file))
                self.status_badge.set_state("pronto")
            except AppError as exc:
                self.preview_label.configure(text="Prévia indisponível.")
                self.status_badge.set_state("erro", exc.user_message)

    def _run(self) -> None:
        if self._processing:
            return
        if not self.selected_file:
            self.status_badge.set_state("erro", "Selecione uma planilha primeiro.")
            return

        source = Path(self.selected_file)
        output_path = unique_path(source.parent, f"{source.stem}_limpo.xlsx")
        selected_file = self.selected_file
        options = self._cleaning_options()

        enabled = sum(1 for value in options.values() if value)
        details = (
            f"Arquivo: {selected_file}\n"
            f"Destino: {output_path}\n"
            f"Opções de limpeza ativas: {enabled}\n\n"
            f"Amostra:\n{self.preview_label.cget('text')}"
        )
        if not confirm_execution(self, "Limpar planilha", details):
            return

        self._processing = True
        self.open_folder_btn.pack_forget()
        self.run_btn.configure(state="disabled")
        self.status_badge.set_state("processando")
        self.summary_label.configure(text="")

        def task():
            return clean_spreadsheet(
                selected_file,
                output_path,
                **options,
            )

        def on_success(summary: dict[str, int]) -> None:
            self._processing = False
            self.run_btn.configure(state="normal")
            self._last_output_dir = output_path.parent
            self.open_folder_btn.pack(side="left", padx=(16, 0))
            self.status_badge.set_state("concluido", f"Arquivo gerado: '{output_path.name}'.")
            self.summary_label.configure(
                text=(
                    f"Linhas: {summary['linhas_originais']} → {summary['linhas_finais']}   |   "
                    f"Colunas: {summary['colunas_originais']} → {summary['colunas_finais']}   |   "
                    f"Duplicados removidos: {summary['duplicados_removidos']}"
                )
            )
            record_execution(
                CleanSpreadsheetModule.info.key, CleanSpreadsheetModule.info.name,
                "success",
                f"{summary['linhas_finais']} linhas e {summary['colunas_finais']} colunas gravadas em {output_path.name}.",
                output_path,
            )
            if self.app.settings.open_folder_after_finish:
                open_in_explorer(output_path.parent)

        def on_error(message: str) -> None:
            self._processing = False
            self.run_btn.configure(state="normal")
            self.status_badge.set_state("erro", message)
            record_execution(
                CleanSpreadsheetModule.info.key, CleanSpreadsheetModule.info.name,
                "error", message,
            )

        run_in_background(self, CleanSpreadsheetModule.info.key, task, on_success, on_error)

    def _open_last_output(self) -> None:
        if hasattr(self, "_last_output_dir"):
            open_in_explorer(self._last_output_dir)

    def _cleaning_options(self) -> dict[str, bool]:
        return {
            "remove_empty_rows": self.opt_empty_rows.get(),
            "remove_duplicates": self.opt_duplicates.get(),
            "trim_whitespace": self.opt_whitespace.get(),
            "remove_empty_columns": self.opt_empty_cols.get(),
            "standardize_headers": self.opt_headers.get(),
            "ignore_case_on_duplicates": self.opt_ignore_case.get(),
        }

    def _save_routine(self) -> None:
        if not self.selected_file:
            self.status_badge.set_state("erro", "Selecione uma planilha antes de salvar.")
            return
        try:
            name = ask_and_save_routine(
                self, CleanSpreadsheetModule.info.key, CleanSpreadsheetModule.info.name,
                {"selected_file": self.selected_file, "options": self._cleaning_options()},
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
        variables = {
            "remove_empty_rows": self.opt_empty_rows,
            "remove_duplicates": self.opt_duplicates,
            "trim_whitespace": self.opt_whitespace,
            "remove_empty_columns": self.opt_empty_cols,
            "standardize_headers": self.opt_headers,
            "ignore_case_on_duplicates": self.opt_ignore_case,
        }
        options = parameters.get("options", {})
        for key, variable in variables.items():
            if key in options:
                variable.set(bool(options[key]))
        try:
            self.preview_label.configure(text=spreadsheet_preview(file))
        except AppError as exc:
            self.status_badge.set_state("erro", exc.user_message)
            return
        self.status_badge.set_state("pronto", "Rotina carregada. Revise a prévia.")
