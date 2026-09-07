"""Janela principal da aplicação: monta sidebar + área de conteúdo e navega entre telas."""
from __future__ import annotations

import customtkinter as ctk

from config.settings import APP_NAME, APP_VERSION, Settings
from core.module_registry import get_module
from ui.screens.home_screen import HomeScreen
from ui.screens.settings_screen import SettingsScreen
from ui.sidebar import Sidebar
from ui.theme import COLORS

ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.settings = Settings.load()
        ctk.set_appearance_mode(self.settings.theme)

        self.title(f"{APP_NAME} — v{APP_VERSION}")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(fg_color=COLORS["bg_dark"])

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, on_navigate=self.navigate)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self._current_screen: ctk.CTkFrame | None = None
        self.navigate("home")

    # ------------------------------------------------------------------
    def navigate(self, destination: str) -> None:
        """Troca a tela exibida na área de conteúdo.

        `destination` pode ser: 'home', 'spreadsheets', 'files', 'settings',
        ou a `key` de um módulo específico (para abrir direto via card).
        """
        self.sidebar.set_active(self._sidebar_key_for(destination))

        if destination == "home":
            self._show_screen(HomeScreen(self.content, on_open_module=self.navigate))
        elif destination == "settings":
            self._show_screen(SettingsScreen(self.content, app=self))
        elif destination in ("spreadsheets", "files"):
            # Atalhos de categoria por enquanto levam à Home (cards já filtram visualmente).
            self._show_screen(HomeScreen(self.content, on_open_module=self.navigate))
        else:
            module = get_module(destination)
            if module is None:
                self._show_screen(HomeScreen(self.content, on_open_module=self.navigate))
                return
            self._show_screen(module.build_ui(self.content, app=self))

    def _sidebar_key_for(self, destination: str) -> str:
        if destination in ("home", "spreadsheets", "files", "settings"):
            return destination
        module = get_module(destination)
        if module and module.info.category == "Planilhas":
            return "spreadsheets"
        if module and module.info.category == "Arquivos":
            return "files"
        return "home"

    def _show_screen(self, screen: ctk.CTkFrame) -> None:
        if self._current_screen is not None:
            self._current_screen.destroy()
        self._current_screen = screen
        screen.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
