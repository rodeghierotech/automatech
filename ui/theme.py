"""Constantes visuais centralizadas: cores, fontes e espaçamentos.

Manter tudo aqui evita valores de cor "mágicos" espalhados pela UI e
facilita trocar o tema no futuro.
"""
from __future__ import annotations

COLORS = {
    "bg_dark": "#1a1d24",
    "bg_sidebar": "#15171d",
    "bg_card": "#242832",
    "bg_card_hover": "#2b303c",
    "accent": "#3b82f6",
    "accent_hover": "#2563eb",
    "text_primary": "#e5e7eb",
    "text_secondary": "#9ca3af",
    "success": "#22c55e",
    "error": "#ef4444",
    "warning": "#f59e0b",
    "border": "#2d3138",
}

FONT_FAMILY = "Segoe UI"

FONT_SIZES = {
    "title": 24,
    "subtitle": 14,
    "heading": 18,
    "body": 13,
    "small": 11,
}

CORNER_RADIUS = 10
PADDING = 20
