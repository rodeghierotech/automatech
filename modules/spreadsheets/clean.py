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
from services.excel_service import clean_spreadsheet
from ui.components.status_badge import StatusBadge
from ui.theme import COLORS, CORNER_RADIUS, FONT_FAMILY, PADDING
from utils.paths import open_in_explorer, unique_path


class CleanSpreadsheetModule(AutomationModule):
    info = ModuleInfo(
        key="clean_spreadsheet",
        name="Limpar planilha",
        description="Remova duplicados, linhas vazias e espaços extras.",
        category="Planilhas",
        icon="🧹",
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
            text="🧹  Limpar planilha",
            font=(FONT_FAMILY, 22, "bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        header.grid(row=0, column=0, sticky="w", padx=PADDING, pady=(PADDING, 4))

        subtitle = ctk.CTkLabel(
            self,
            text="Escolha a planilha e as opções de limpeza. Um novo arquivo será gerado.",
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

        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.grid(row=3, column=0, sticky="ew", padx=PADDING, pady=20)

        self.run_btn = ctk.CTkButton(action_row, text="Limpar planilha", command=self._run, width=180)
        self.run_btn.pack(side="left")

        self.status_badge = StatusBadge(self)
        self.status_badge.grid(row=4, column=0, sticky="w", padx=PADDING)

        self.summary_label = ctk.CTkLabel(
            self,
            text="",
            font=(FONT_FAMILY, 12),
            text_color=COLORS["text_secondary"],
            anchor="w",
            justify="left",
        )
        self.summary_label.grid(row=5, column=0, sticky="w", padx=PADDING, pady=(8, 0))

    def _select_file(self) -> None:
        file = filedialog.askopenfilename(
            title="Selecione a planilha", filetypes=[("Planilhas Excel", "*.xlsx")]
        )
        if file:
            self.selected_file = file
            self.file_label.configure(text=Path(file).name)
            self.status_badge.set_state("pronto")

    def _run(self) -> None:
        if self._processing:
            return
        if not self.selected_file:
            self.status_badge.set_state("erro", "Selecione uma planilha primeiro.")
            return

        source = Path(self.selected_file)
        output_path = unique_path(source.parent, f"{source.stem}_limpo.xlsx")

        self._processing = True
        self.run_btn.configure(state="disabled")
        self.status_badge.set_state("processando")
        self.summary_label.configure(text="")

        def task():
            return clean_spreadsheet(
                self.selected_file,
                output_path,
                remove_empty_rows=self.opt_empty_rows.get(),
                remove_duplicates=self.opt_duplicates.get(),
                trim_whitespace=self.opt_whitespace.get(),
                remove_empty_columns=self.opt_empty_cols.get(),
                standardize_headers=self.opt_headers.get(),
                ignore_case_on_duplicates=self.opt_ignore_case.get(),
            )

        def on_success(summary: dict[str, int]) -> None:
            self._processing = False
            self.run_btn.configure(state="normal")
            self.status_badge.set_state("concluido", f"Arquivo gerado: '{output_path.name}'.")
            self.summary_label.configure(
                text=(
                    f"Linhas: {summary['linhas_originais']} → {summary['linhas_finais']}   |   "
                    f"Colunas: {summary['colunas_originais']} → {summary['colunas_finais']}   |   "
                    f"Duplicados removidos: {summary['duplicados_removidos']}"
                )
            )
            if self.app.settings.open_folder_after_finish:
                open_in_explorer(output_path.parent)

        def on_error(message: str) -> None:
            self._processing = False
            self.run_btn.configure(state="normal")
            self.status_badge.set_state("erro", message)

        run_in_background(self, CleanSpreadsheetModule.info.key, task, on_success, on_error)
