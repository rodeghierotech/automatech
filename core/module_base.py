"""Classe base que todo módulo de automação deve implementar.

Para criar um novo módulo:
1. Criar uma subclasse de AutomationModule.
2. Implementar build_ui() retornando um CTkFrame com a interface do módulo.
3. Registrar a classe em core/module_registry.py.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleInfo:
    key: str            # identificador único, ex: "merge_spreadsheets"
    name: str            # nome exibido, ex: "Unir planilhas"
    description: str     # descrição curta para o card
    category: str        # ex: "Planilhas", "Arquivos"
    icon: str = "file-spreadsheet"


class AutomationModule(ABC):
    """Contrato que toda automação deve seguir."""

    info: ModuleInfo

    @abstractmethod
    def build_ui(self, parent, app) -> "ctk.CTkFrame":  # noqa: F821
        """Constrói e retorna o frame de interface deste módulo.

        `app` é a instância principal da aplicação (App), útil para
        acessar configurações globais (ex: pasta padrão de saída).
        """
        raise NotImplementedError
