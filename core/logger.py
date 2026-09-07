"""Configuração central de logging.

Toda exceção interna é registrada em logs/app.log com stack trace completo.
O usuário nunca vê esse conteúdo diretamente.
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from utils.paths import logs_dir

_LOGGER_NAME = "automatiza"
_configured = False


def get_logger() -> logging.Logger:
    global _configured
    logger = logging.getLogger(_LOGGER_NAME)

    if not _configured:
        logger.setLevel(logging.DEBUG)
        log_path = logs_dir() / "app.log"

        handler = RotatingFileHandler(
            log_path, maxBytes=2_000_000, backupCount=3, encoding="utf-8"
        )
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        _configured = True

    return logger


def log_error(module: str, error: Exception) -> None:
    logger = get_logger()
    logger.error("Módulo=%s | Erro=%s", module, error, exc_info=True)
