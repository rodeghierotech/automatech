"""Variações padronizadas de botões da interface."""
from __future__ import annotations

import customtkinter as ctk

from ui.theme import BUTTON_HEIGHT, COLORS, CORNER_RADIUS, FONT_FAMILY


class PrimaryButton(ctk.CTkButton):
    def __init__(self, parent, **kwargs):
        defaults = {
            "height": BUTTON_HEIGHT,
            "corner_radius": CORNER_RADIUS,
            "font": (FONT_FAMILY, 13, "bold"),
            "fg_color": COLORS["accent"],
            "hover_color": COLORS["accent_hover"],
        }
        super().__init__(parent, **{**defaults, **kwargs})


class SecondaryButton(ctk.CTkButton):
    def __init__(self, parent, **kwargs):
        defaults = {
            "height": BUTTON_HEIGHT,
            "corner_radius": CORNER_RADIUS,
            "font": (FONT_FAMILY, 13),
            "fg_color": COLORS["accent_soft"],
            "hover_color": COLORS["bg_card_hover"],
            "text_color": COLORS["text_primary"],
            "border_width": 1,
            "border_color": COLORS["border"],
        }
        super().__init__(parent, **{**defaults, **kwargs})
