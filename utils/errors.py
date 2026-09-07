"""Exceções customizadas usadas em toda a aplicação.

Toda exceção lançada aqui carrega uma `user_message` amigável,
que é o texto exibido na interface. O detalhe técnico completo
vai apenas para o log.
"""
from __future__ import annotations


class AppError(Exception):
    """Erro genérico da aplicação com mensagem amigável ao usuário."""

    def __init__(self, user_message: str, technical_detail: str = ""):
        super().__init__(technical_detail or user_message)
        self.user_message = user_message
        self.technical_detail = technical_detail or user_message


class FileAccessError(AppError):
    """Arquivo não pode ser lido/escrito (aberto, sem permissão, não existe)."""


class InvalidSpreadsheetError(AppError):
    """Planilha vazia, corrompida ou em formato inesperado."""


class IncompatibleColumnsError(AppError):
    """Planilhas com colunas incompatíveis para uma operação de união."""


class ValidationError(AppError):
    """Entrada do usuário inválida (seleção obrigatória ausente, etc.)."""
