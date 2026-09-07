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
from services.excel_service import merge_spreadsheets
from ui.components.status_badge import StatusBadge
from ui.theme import COLORS, CORNER_RADIUS, FONT_FAMILY, PADDING
from utils.paths import open_in_explorer, unique_path
from utils.validators import require_files_selected


class MergeSpreadsheetsModule(AutomationModule):
    info = ModuleInfo(
        key="merge_spreadsheets",
        name="Unir planilhas",
        description="Combine várias planilhas Excel em um único arquivo.",
        category="Planilhas",
        icon="🧩",
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
            text="🧩  Unir planilhas",
            font=(FONT_FAMILY, 22, "bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        header.grid(row=0, column=0, sticky="w", padx=PADDING, pady=(PADDING, 4))

        subtitle = ctk.CTkLabel(
            self,
            text="Selecione as planilhas que deseja combinar em um único arquivo.",
            font=(FONT_FAMILY, 13),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=PADDING, pady=(0, 20))

        panel = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=CORNER_RADIUS)
        panel.grid(row=2, column=0, sticky="ew", padx=PADDING)
        panel.grid_columnconfigure(0, weight=1)

        select_btn = ctk.CTkButton(
            panel, text="Selecionar planilhas", command=self._select_files
        )
        select_btn.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 8))

        self.files_label = ctk.CTkLabel(
            panel,
            text="Nenhum arquivo selecionado.",
            font=(FONT_FAMILY, 12),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        self.files_label.grid(row=1, column=0, sticky="w", padx=20)

        dest_btn = ctk.CTkButton(
            panel, text="Escolher onde salvar", command=self._select_output
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

        action_row = ctk.CTkFrame(self, fg_color="transparent")
        action_row.grid(row=3, column=0, sticky="ew", padx=PADDING, pady=20)

        self.run_btn = ctk.CTkButton(
            action_row, text="Unir planilhas", command=self._run, width=180
        )
        self.run_btn.pack(side="left")

        self.progress = ctk.CTkProgressBar(action_row, width=200)
        self.progress.set(0)
        self.progress.pack(side="left", padx=16)
        self.progress.pack_forget()

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
            self.status_badge.set_state("pronto")

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
            require_files_selected(self.selected_files, "Selecione ao menos duas planilhas.")
            if not hasattr(self, "_output_path"):
                self.status_badge.set_state("erro", "Escolha onde salvar o arquivo primeiro.")
                return
        except Exception as exc:  # ValidationError
            self.status_badge.set_state("erro", getattr(exc, "user_message", str(exc)))
            return

        self._processing = True
        self.run_btn.configure(state="disabled")
        self.status_badge.set_state("processando")
        self.progress.pack(side="left", padx=16)
        self.progress.set(0)

        output_path = unique_path(
            Path(self._output_path).parent, Path(self._output_path).name
        )

        def task():
            def on_progress(current, total):
                self.after(0, lambda: self.progress.set(current / total))

            return merge_spreadsheets(self.selected_files, output_path, on_progress)

        def on_success(total_rows: int) -> None:
            self._processing = False
            self.run_btn.configure(state="normal")
            self.status_badge.set_state(
                "concluido", f"Concluído! {total_rows} linhas gravadas em '{output_path.name}'."
            )
            if self.app.settings.open_folder_after_finish:
                open_in_explorer(output_path.parent)

        def on_error(message: str) -> None:
            self._processing = False
            self.run_btn.configure(state="normal")
            self.status_badge.set_state("erro", message)

        run_in_background(self, self.info_key(), task, on_success, on_error)

    def info_key(self) -> str:
        return MergeSpreadsheetsModule.info.key
