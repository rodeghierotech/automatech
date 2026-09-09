"""Constantes visuais centralizadas: cores, fontes e espaçamentos.

Manter tudo aqui evita valores de cor "mágicos" espalhados pela UI e
facilita trocar o tema no futuro.
"""
from __future__ import annotations

COLORS = {
    "bg_dark": ("#f3f6fb", "#0b1120"),
    "bg_sidebar": ("#ffffff", "#0f172a"),
    "bg_card": ("#ffffff", "#151e2f"),
    "bg_card_hover": ("#e8eef8", "#1e293b"),
    "bg_input": ("#f8fafc", "#101827"),
    "accent": "#3b82f6",
    "accent_hover": "#2563eb",
    "accent_soft": ("#dbeafe", "#172e4d"),
    "text_primary": ("#0f172a", "#f8fafc"),
    "text_secondary": ("#526176", "#94a3b8"),
    "success": "#22c55e",
    "error": "#ef4444",
    "warning": "#f59e0b",
    "border": ("#dbe3ef", "#263349"),
}

FONT_FAMILY = "Segoe UI"

FONT_SIZES = {
    "title": 28,
    "subtitle": 14,
    "heading": 18,
    "body": 13,
    "caption": 12,
    "small": 11,
}

CORNER_RADIUS = 12
PADDING = 16
BUTTON_HEIGHT = 40
