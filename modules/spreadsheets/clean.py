"""Módulo: Limpar planilha com diagnóstico antes da execução."""
from __future__ import annotations

from pathlib import Path
from tkinter import TclError, filedialog

import customtkinter as ctk

from core.module_base import AutomationModule, ModuleInfo
from core.task_runner import run_in_background
from services.activity_service import record_execution
from services.excel_service import analyze_spreadsheet, clean_spreadsheet_detailed
from services.spreadsheet_cleaning import CleaningOptions, CleaningResult
from services.spreadsheet_profile_service import CleaningPreview
from ui.components.buttons import PrimaryButton, SecondaryButton
from ui.components.data_profile_panel import DataProfilePanel
from ui.components.status_badge import StatusBadge
from ui.components.workflow_actions import ask_and_save_routine, confirm_execution
from ui.icons import load_icon
from ui.theme import COLORS, CORNER_RADIUS, FONT_FAMILY, FONT_SIZES, PADDING
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
        self._analysis_revision = 0
        self._analysis_after_id: str | None = None
        self._analysis_ready = False
        self._current_preview: CleaningPreview | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        content = ctk.CTkScrollableFrame(self, fg_color="transparent")
        content.grid(row=0, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            content,
            text="Limpar planilha",
            image=load_icon("brush-cleaning", 24),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZES["title"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=PADDING, pady=(PADDING, 4))
        ctk.CTkLabel(
            content,
            text="Analise os dados, revise as opções e gere uma nova planilha com relatório.",
            font=(FONT_FAMILY, FONT_SIZES["subtitle"]),
            text_color=COLORS["text_secondary"],
            anchor="w",
            wraplength=720,
        ).grid(row=1, column=0, sticky="w", padx=PADDING, pady=(0, 20))

        panel = ctk.CTkFrame(
            content, fg_color=COLORS["bg_card"], corner_radius=CORNER_RADIUS
        )
        panel.grid(row=2, column=0, sticky="ew", padx=PADDING)
        panel.grid_columnconfigure(0, weight=1)
        SecondaryButton(
            panel,
            text="Selecionar planilha",
            image=load_icon("file-spreadsheet", 18),
            compound="left",
            command=self._select_file,
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(20, 8))
        self.file_label = ctk.CTkLabel(
            panel,
            text="Nenhum arquivo selecionado.",
            font=(FONT_FAMILY, 12),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        self.file_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 16))

        options_frame = ctk.CTkFrame(panel, fg_color="transparent")
        options_frame.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 14))
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
        for row, (label, variable) in enumerate(checks):
            ctk.CTkCheckBox(
                options_frame,
                text=label,
                variable=variable,
                command=self._schedule_analysis,
            ).grid(row=row, column=0, sticky="w", pady=4)

        self.profile_panel = DataProfilePanel(panel)
        self.profile_panel.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))

        action_row = ctk.CTkFrame(content, fg_color="transparent")
        action_row.grid(row=3, column=0, sticky="ew", padx=PADDING, pady=20)
        self.run_btn = PrimaryButton(
            action_row,
            text="Limpar planilha",
            command=self._run,
            width=180,
            state="disabled",
        )
        self.run_btn.pack(side="left")
        SecondaryButton(
            action_row,
            text="Salvar rotina",
            command=self._save_routine,
            width=130,
        ).pack(side="left", padx=(10, 0))
        self.open_folder_btn = SecondaryButton(
            action_row,
            text="Abrir pasta",
            image=load_icon("folder-open", 18),
            compound="left",
            command=self._open_last_output,
        )

        self.status_badge = StatusBadge(content)
        self.status_badge.grid(row=4, column=0, sticky="w", padx=PADDING)
        self.summary_label = ctk.CTkLabel(
            content,
            text="",
            font=(FONT_FAMILY, 12),
            text_color=COLORS["text_secondary"],
            anchor="w",
            justify="left",
            wraplength=720,
        )
        self.summary_label.grid(
            row=5, column=0, sticky="w", padx=PADDING, pady=(8, PADDING)
        )

    def _select_file(self) -> None:
        file = filedialog.askopenfilename(
            title="Selecione a planilha", filetypes=[("Planilhas Excel", "*.xlsx")]
        )
        if not file:
            return
        self.selected_file = file
        self.file_label.configure(text=Path(file).name)
        self._schedule_analysis()

    def _schedule_analysis(self) -> None:
        if not self.selected_file or self._processing:
            return
        self._analysis_revision += 1
        revision = self._analysis_revision
        self._analysis_ready = False
        self._current_preview = None
        self.run_btn.configure(state="disabled")
        self.profile_panel.show_loading()
        self.status_badge.set_state("processando", "Analisando planilha…")
        if self._analysis_after_id is not None:
            try:
                self.after_cancel(self._analysis_after_id)
            except TclError:
                pass
        self._analysis_after_id = self.after(
            250, lambda: self._start_analysis(revision)
        )

    def _start_analysis(self, revision: int) -> None:
        self._analysis_after_id = None
        if revision != self._analysis_revision or not self.selected_file:
            return
        selected_file = self.selected_file
        options = self._cleaning_options()

        def task() -> CleaningPreview:
            return analyze_spreadsheet(selected_file, options)

        def on_success(preview: CleaningPreview) -> None:
            if revision != self._analysis_revision:
                return
            self._current_preview = preview
            self._analysis_ready = True
            self.profile_panel.render(preview)
            self.run_btn.configure(state="normal")
            self.status_badge.set_state(
                "pronto", "Raio-X atualizado. Revise a estimativa."
            )

        def on_error(message: str) -> None:
            if revision != self._analysis_revision:
                return
            self._analysis_ready = False
            self._current_preview = None
            self.profile_panel.show_error(message)
            self.run_btn.configure(state="disabled")
            self.status_badge.set_state("erro", message)

        run_in_background(
            self,
            f"{CleanSpreadsheetModule.info.key}_analysis",
            task,
            on_success,
            on_error,
        )

    def _run(self) -> None:
        if self._processing:
            return
        if not self.selected_file:
            self.status_badge.set_state("erro", "Selecione uma planilha primeiro.")
            return
        if not self._analysis_ready or self._current_preview is None:
            self.status_badge.set_state("erro", "Aguarde a conclusão do Raio-X.")
            return

        source = Path(self.selected_file)
        output_path = unique_path(source.parent, f"{source.stem}_limpo.xlsx")
        selected_file = self.selected_file
        options = self._cleaning_options()
        profile = self._current_preview.original
        estimate = self._current_preview.estimated_metrics
        details = (
            f"Arquivo: {selected_file}\n"
            f"Destino: {output_path}\n\n"
            f"Antes: {profile.rows} linhas × {profile.columns} colunas\n"
            f"Estimativa: {estimate.final_rows} linhas × {estimate.final_columns} colunas\n"
            f"Duplicados a remover: {estimate.duplicates_removed}\n"
            f"Textos a ajustar: {estimate.trimmed_text_cells}"
        )
        if not confirm_execution(self, "Limpar planilha", details):
            return

        self._processing = True
        self.open_folder_btn.pack_forget()
        self.run_btn.configure(state="disabled")
        self.status_badge.set_state("processando")
        self.summary_label.configure(text="")

        def task() -> CleaningResult:
            return clean_spreadsheet_detailed(selected_file, output_path, options)

        def on_success(result: CleaningResult) -> None:
            self._processing = False
            self.run_btn.configure(
                state="normal" if self._analysis_ready else "disabled"
            )
            self._last_output_dir = result.output_path.parent
            self.open_folder_btn.pack(side="left", padx=(16, 0))
            message = f"Arquivo gerado: '{result.output_path.name}'."
            if result.report_warning:
                message = f"{message} {result.report_warning}"
            self.status_badge.set_state("concluido", message)
            metrics = result.metrics
            summary = (
                f"Linhas: {metrics.original_rows} → {metrics.final_rows}   |   "
                f"Colunas: {metrics.original_columns} → {metrics.final_columns}   |   "
                f"Duplicados removidos: {metrics.duplicates_removed}"
            )
            if result.report_warning:
                summary = f"{summary}\n{result.report_warning}"
            self.summary_label.configure(text=summary)
            record_execution(
                CleanSpreadsheetModule.info.key,
                CleanSpreadsheetModule.info.name,
                "success",
                f"{metrics.final_rows} linhas e {metrics.final_columns} colunas gravadas em {result.output_path.name}.",
                result.output_path,
                result.report_path,
            )
            if self.app.settings.open_folder_after_finish:
                open_in_explorer(result.output_path.parent)

        def on_error(message: str) -> None:
            self._processing = False
            self.run_btn.configure(
                state="normal" if self._analysis_ready else "disabled"
            )
            self.status_badge.set_state("erro", message)
            record_execution(
                CleanSpreadsheetModule.info.key,
                CleanSpreadsheetModule.info.name,
                "error",
                message,
            )

        run_in_background(
            self,
            CleanSpreadsheetModule.info.key,
            task,
            on_success,
            on_error,
        )

    def _open_last_output(self) -> None:
        if hasattr(self, "_last_output_dir"):
            open_in_explorer(self._last_output_dir)

    def _cleaning_options(self) -> CleaningOptions:
        return CleaningOptions(
            remove_empty_rows=self.opt_empty_rows.get(),
            remove_duplicates=self.opt_duplicates.get(),
            trim_whitespace=self.opt_whitespace.get(),
            remove_empty_columns=self.opt_empty_cols.get(),
            standardize_headers=self.opt_headers.get(),
            ignore_case_on_duplicates=self.opt_ignore_case.get(),
        )

    def _save_routine(self) -> None:
        if not self.selected_file:
            self.status_badge.set_state(
                "erro", "Selecione uma planilha antes de salvar."
            )
            return
        try:
            name = ask_and_save_routine(
                self,
                CleanSpreadsheetModule.info.key,
                CleanSpreadsheetModule.info.name,
                {
                    "selected_file": self.selected_file,
                    "options": self._cleaning_options().as_dict(),
                },
            )
        except OSError:
            self.status_badge.set_state("erro", "Não foi possível salvar a rotina.")
            return
        if name:
            self.status_badge.set_state("concluido", f"Rotina “{name}” salva.")

    def apply_preset(self, parameters: dict) -> None:
        file = parameters.get("selected_file")
        if not file or not Path(file).is_file():
            self.status_badge.set_state(
                "erro", "O arquivo desta rotina não está mais disponível."
            )
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
        self._schedule_analysis()
