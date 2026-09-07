"""Registro central de módulos disponíveis na aplicação.

Para adicionar um novo módulo à Central de Automações, basta:
1. Criar a classe do módulo (ver core/module_base.py).
2. Importá-la e adicioná-la à lista MODULES abaixo.

Nenhum outro arquivo da aplicação precisa ser alterado.
"""
from __future__ import annotations

from core.module_base import AutomationModule
from modules.files.organizer import FileOrganizerModule
from modules.spreadsheets.clean import CleanSpreadsheetModule
from modules.spreadsheets.merge import MergeSpreadsheetsModule
from modules.spreadsheets.split import SplitSpreadsheetModule

MODULES: list[AutomationModule] = [
    MergeSpreadsheetsModule(),
    SplitSpreadsheetModule(),
    CleanSpreadsheetModule(),
    FileOrganizerModule(),
]


def get_module(key: str) -> AutomationModule | None:
    for module in MODULES:
        if module.info.key == key:
            return module
    return None
