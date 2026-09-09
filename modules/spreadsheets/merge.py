"""Módulo: Unir planilhas.

Permite selecionar várias planilhas Excel e gerar uma única planilha
contendo todos os registros, validando compatibilidade de colunas.
"""
from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from core.module_base import AutomationModule, ModuleInfo
from core.task_runner import run_in_background
from services.activity_service import record_execution
from services.excel_service import merge_spreadsheets, spreadsheet_preview
from ui.components.buttons import PrimaryButton, SecondaryButton
from ui.components.status_badge import StatusBadge
from ui.components.workflow_actions import ask_and_save_routine, confirm_execution
from ui.icons import load_icon
from ui.theme import COLORS, CORNER_RADIUS, FONT_FAMILY, FONT_SIZES, PADDING
from utils.errors import AppError, ValidationError
from utils.paths import open_in_explorer, unique_path
from utils.validators import require_files_selected


class MergeSpreadsheetsModule(AutomationModule):
    info = ModuleInfo(
        key="merge_spreadsheets",
        name="Unir planilhas",
        description="Combine várias planilhas Excel em um único arquivo.",
        category="Planilhas",
        icon="combine",
    )

    def build_ui(self, parent, app) -> "ctk.CTkFrame":
        return MergeSpreadsheetsScreen(parent, app)


class MergeSpreadsheetsScreen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.selected_files: list[str] = []
        self.output_dir: str = app.settings.default_output_dir
        self._processing = False

        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            self,
            text="Unir planilhas",
            image=load_icon("combine", 24),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZES["title"], "bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        header.grid(row=0, column=0, sticky="w", padx=PADDING, pady=(PADDING, 4))

        subtitle = ctk.CTkLabel(
            self,
            text="Selecione as planilhas que deseja combinar em um único arquivo.",
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
            text="Selecionar planilhas",
            image=load_icon("file-spreadsheet", 18),
            compound="left",
            command=self._select_files,
        )
        select_btn.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 8))

        self.files_label = ctk.CTkLabel(
            panel,
            text="Nenhum arquivo selecionado.",
            font=(FONT_FAMILY, 12),
            text_color=COLORS["text_secondary"],
            anchor="w",
            wraplength=620,
        )
        self.files_label.grid(row=1, column=0, sticky="w", padx=20)

        dest_btn = SecondaryButton(
            panel,
            text="Escolher onde salvar",
            image=load_icon("folder-open", 18),
            compound="left",
            command=self._select_output,
        )
        dest_btn.grid(row=2, column=0, sticky="w", padx=20, pady=(16, 8))

        self.output_label = ctk.CTkLabel(
            panel,
            text="Nenhum destino selecionado.",
            font=(FONT_FAMILY, 12),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        self.output_label.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            panel, text="Prévia do primeiro arquivo",
            font=(FONT_FAMILY, 13, "bold"), text_color=COLORS["text_primary"], anchor="w",
        ).grid(row=4, column=0, sticky="w", padx=20, pady=(0, 6))
        self.preview_label = ctk.CTkLabel(
            panel, text="Selecione as planilhas para visualizar uma amostra.",
            font=("Consolas", 11), text_color=COLORS["text_secondary"],
            anchor="w", justify="left", wraplength=760,
        )
        self.preview_label.grid(row=5, column=0, sticky="w", padx=20, pady=(0, 20))

        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.grid(row=3, column=0, sticky="ew", padx=PADDING, pady=20)

        self.run_btn = PrimaryButton(
            action_row, text="Unir planilhas", command=self._run, width=180
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

    def _select_files(self) -> None:
        files = filedialog.askopenfilenames(
            title="Selecione as planilhas",
            filetypes=[("Planilhas Excel", "*.xlsx")],
        )
        if files:
            self.selected_files = list(files)
            self.files_label.configure(
                text=f"{len(self.selected_files)} arquivo(s) selecionado(s)."
            )
            try:
                self.preview_label.configure(text=spreadsheet_preview(self.selected_files[0]))
                self.status_badge.set_state("pronto")
            except AppError as exc:
                self.preview_label.configure(text="Prévia indisponível.")
                self.status_badge.set_state("erro", exc.user_message)

    def _select_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Salvar planilha unificada como",
            defaultextension=".xlsx",
            initialdir=self.output_dir,
            initialfile="planilha_unificada.xlsx",
            filetypes=[("Planilha Excel", "*.xlsx")],
        )
        if path:
            self.output_dir = str(Path(path).parent)
            self._output_path = path
            self.output_label.configure(text=Path(path).name)

    def _run(self) -> None:
        if self._processing:
            return
        try:
            require_files_selected(
                self.selected_files,
                "Selecione ao menos duas planilhas.",
                minimum=2,
            )
            if not hasattr(self, "_output_path"):
                self.status_badge.set_state("erro", "Escolha onde salvar o arquivo primeiro.")
                return
        except ValidationError as exc:
            self.status_badge.set_state("erro", exc.user_message)
            return

        details = (
            f"Arquivos: {len(self.selected_files)}\n"
            f"Destino: {self._output_path}\n\n"
            f"Amostra:\n{self.preview_label.cget('text')}"
        )
        if not confirm_execution(self, "Unir planilhas", details):
            return

        self._processing = True
        self.open_folder_btn.pack_forget()
        self.run_btn.configure(state="disabled")
        self.status_badge.set_state("processando")
        self.progress.pack(side="left", padx=16)
        self.progress.configure(mode="indeterminate")
        self.progress.start()

        output_path = unique_path(
            Path(self._output_path).parent, Path(self._output_path).name
        )
        selected_files = list(self.selected_files)

        def task():
            return merge_spreadsheets(selected_files, output_path)

        def on_success(total_rows: int) -> None:
            self._processing = False
            self.progress.stop()
            self.progress.pack_forget()
            self._last_output_dir = output_path.parent
            self.open_folder_btn.pack(side="left", padx=(16, 0))
            self.run_btn.configure(state="normal")
            self.status_badge.set_state(
                "concluido", f"Concluído! {total_rows} linhas gravadas em '{output_path.name}'."
            )
            record_execution(
                MergeSpreadsheetsModule.info.key, MergeSpreadsheetsModule.info.name,
                "success", f"{total_rows} linhas reunidas em {output_path.name}.", output_path,
            )
            if self.app.settings.open_folder_after_finish:
                open_in_explorer(output_path.parent)

        def on_error(message: str) -> None:
            self._processing = False
            self.progress.stop()
            self.progress.pack_forget()
            self.run_btn.configure(state="normal")
            self.status_badge.set_state("erro", message)
            record_execution(
                MergeSpreadsheetsModule.info.key, MergeSpreadsheetsModule.info.name,
                "error", message,
            )

        run_in_background(self, MergeSpreadsheetsModule.info.key, task, on_success, on_error)

    def _open_last_output(self) -> None:
        if hasattr(self, "_last_output_dir"):
            open_in_explorer(self._last_output_dir)

    def _save_routine(self) -> None:
        if len(self.selected_files) < 2 or not hasattr(self, "_output_path"):
            self.status_badge.set_state(
                "erro", "Selecione as planilhas e o destino antes de salvar a rotina."
            )
            return
        try:
            name = ask_and_save_routine(
                self, MergeSpreadsheetsModule.info.key, MergeSpreadsheetsModule.info.name,
                {"selected_files": self.selected_files, "output_path": self._output_path},
            )
        except OSError:
            self.status_badge.set_state("erro", "Não foi possível salvar a rotina.")
            return
        if name:
            self.status_badge.set_state("concluido", f"Rotina “{name}” salva.")

    def apply_preset(self, parameters: dict) -> None:
        self.selected_files = [
            str(path) for path in parameters.get("selected_files", []) if Path(path).is_file()
        ]
        output = parameters.get("output_path")
        if output:
            self._output_path = str(output)
            self.output_dir = str(Path(output).parent)
            self.output_label.configure(text=Path(output).name)
        if self.selected_files:
            self.files_label.configure(text=f"{len(self.selected_files)} arquivo(s) selecionado(s).")
            try:
                self.preview_label.configure(text=spreadsheet_preview(self.selected_files[0]))
            except AppError:
                self.preview_label.configure(text="Prévia indisponível.")
        if len(self.selected_files) < 2:
            self.status_badge.set_state(
                "erro", "Alguns arquivos desta rotina não estão mais disponíveis."
            )
        else:
            self.status_badge.set_state("pronto", "Rotina carregada. Revise a prévia.")
