"""Tela de rotinas configuradas pelo usuário."""
from __future__ import annotations

from datetime import datetime
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from services.activity_service import delete_routine, list_routines
from ui.components.buttons import PrimaryButton, SecondaryButton
from ui.theme import COLORS, CORNER_RADIUS, FONT_FAMILY, FONT_SIZES, PADDING


def _date_label(value: str) -> str:
    try:
        return datetime.fromisoformat(value).strftime("%d/%m/%Y às %H:%M")
    except (TypeError, ValueError):
        return "Data não disponível"


class RoutinesScreen(ctk.CTkFrame):
    def __init__(self, parent, on_open: Callable[[dict], None], **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.on_open = on_open
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            self, text="Rotinas salvas",
            font=(FONT_FAMILY, FONT_SIZES["title"], "bold"),
            text_color=COLORS["text_primary"], anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=PADDING, pady=(PADDING, 4))
        ctk.CTkLabel(
            self,
            text="Reabra configurações usadas com frequência sem preencher tudo novamente.",
            font=(FONT_FAMILY, FONT_SIZES["subtitle"]),
            text_color=COLORS["text_secondary"], anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=PADDING, pady=(0, 20))

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.grid(row=2, column=0, sticky="nsew", padx=PADDING, pady=(0, PADDING))
        self.list_frame.grid_columnconfigure(0, weight=1)
        self._render()

    def _render(self) -> None:
        for child in self.list_frame.winfo_children():
            child.destroy()
        routines = list_routines()
        if not routines:
            ctk.CTkLabel(
                self.list_frame,
                text="Nenhuma rotina salva ainda. Abra uma automação e use “Salvar rotina”.",
                text_color=COLORS["text_secondary"],
                font=(FONT_FAMILY, FONT_SIZES["body"]),
            ).grid(row=0, column=0, sticky="w", padx=8, pady=8)
            return

        for row, routine in enumerate(routines):
            card = ctk.CTkFrame(
                self.list_frame, fg_color=COLORS["bg_card"], border_width=1,
                border_color=COLORS["border"], corner_radius=CORNER_RADIUS,
            )
            card.grid(row=row, column=0, sticky="ew", padx=4, pady=6)
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                card, text=routine.get("name", "Rotina sem nome"),
                font=(FONT_FAMILY, FONT_SIZES["heading"], "bold"),
                text_color=COLORS["text_primary"], anchor="w",
            ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 2))
            ctk.CTkLabel(
                card,
                text=f"{routine.get('module_name', 'Automação')} • salva em {_date_label(routine.get('created_at', ''))}",
                font=(FONT_FAMILY, FONT_SIZES["caption"]),
                text_color=COLORS["text_secondary"], anchor="w",
            ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 16))
            actions = ctk.CTkFrame(card, fg_color="transparent")
            actions.grid(row=0, column=1, rowspan=2, padx=18, pady=14)
            PrimaryButton(
                actions, text="Usar rotina", width=120,
                command=lambda item=routine: self.on_open(item),
            ).pack(side="left")
            SecondaryButton(
                actions, text="Excluir", width=76,
                command=lambda item=routine: self._delete(item),
            ).pack(side="left", padx=(8, 0))

    def _delete(self, routine: dict) -> None:
        if not messagebox.askyesno(
            "Excluir rotina", f"Excluir a rotina “{routine.get('name', 'sem nome')}”?",
            parent=self.winfo_toplevel(),
        ):
            return
        try:
            delete_routine(str(routine.get("id", "")))
        except OSError:
            messagebox.showerror(
                "Excluir rotina",
                "Não foi possível excluir a rotina neste computador.",
                parent=self.winfo_toplevel(),
            )
            return
        self._render()
