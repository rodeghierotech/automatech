"""Carregamento central dos ícones Lucide usados pela interface."""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import customtkinter as ctk
from PIL import Image


def _assets_dir() -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / "assets" / "icons"


@lru_cache(maxsize=None)
def load_icon(name: str, size: int = 20) -> ctk.CTkImage:
    path = _assets_dir() / f"{name}.png"
    image = Image.open(path).convert("RGBA")
    return ctk.CTkImage(light_image=image, dark_image=image, size=(size, size))
