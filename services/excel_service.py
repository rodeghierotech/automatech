"""Lógica de manipulação de planilhas Excel, isolada da interface gráfica.

Todas as funções aqui são "puras" no sentido de que não conhecem CustomTkinter,
não atualizam widgets e apenas trabalham com dados e arquivos. Isso facilita
testes e reutilização por qualquer módulo futuro.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import pandas as pd

from utils.errors import IncompatibleColumnsError, InvalidSpreadsheetError
from utils.paths import sanitize_filename, unique_path
from utils.validators import validate_spreadsheet_path

ProgressCallback = Callable[[int, int], None]  # (atual, total)


def read_spreadsheet(path: str | Path) -> pd.DataFrame:
    """Lê uma planilha Excel tratando erros comuns (vazia, corrompida)."""
    p = validate_spreadsheet_path(path)
    try:
        df = pd.read_excel(p, engine="openpyxl")
    except Exception as exc:  # noqa: BLE001 - qualquer falha do engine vira erro amigável
        raise InvalidSpreadsheetError(
            f"Não foi possível abrir '{p.name}'. O arquivo pode estar corrompido "
            "ou em um formato não suportado.",
            technical_detail=str(exc),
        ) from exc

    if df.empty:
        raise InvalidSpreadsheetError(f"A planilha '{p.name}' está vazia.")

    return df


def get_headers(path: str | Path) -> list[str]:
    """Retorna apenas os cabeçalhos de uma planilha, sem carregar tudo."""
    p = validate_spreadsheet_path(path)
    try:
        df = pd.read_excel(p, engine="openpyxl", nrows=0)
    except Exception as exc:  # noqa: BLE001
        raise InvalidSpreadsheetError(
            f"Não foi possível ler as colunas de '{p.name}'.",
            technical_detail=str(exc),
        ) from exc
    return list(df.columns)


# ---------------------------------------------------------------------------
# Módulo 1: Unir planilhas
# ---------------------------------------------------------------------------

def merge_spreadsheets(
    file_paths: list[str],
    output_path: str | Path,
    progress_cb: ProgressCallback | None = None,
) -> int:
    """Une várias planilhas em uma só, validando compatibilidade de colunas.

    Retorna o total de linhas gravadas no arquivo final.
    """
    if len(file_paths) < 2:
        raise InvalidSpreadsheetError("Selecione ao menos duas planilhas para unir.")

    frames: list[pd.DataFrame] = []
    reference_columns: list[str] | None = None

    total = len(file_paths)
    for idx, fp in enumerate(file_paths, start=1):
        df = read_spreadsheet(fp)
        columns = list(df.columns)

        if reference_columns is None:
            reference_columns = columns
        elif set(columns) != set(reference_columns):
            raise IncompatibleColumnsError(
                f"A planilha '{Path(fp).name}' possui colunas diferentes das demais. "
                "Todas as planilhas precisam ter as mesmas colunas."
            )
        else:
            df = df[reference_columns]  # garante mesma ordem de colunas

        frames.append(df)
        if progress_cb:
            progress_cb(idx, total)

    merged = pd.concat(frames, ignore_index=True)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_excel(output_path, index=False, engine="openpyxl")

    return len(merged)


# ---------------------------------------------------------------------------
# Módulo 2: Separar planilha
# ---------------------------------------------------------------------------

def split_spreadsheet(
    file_path: str,
    column: str,
    output_dir: str | Path,
    progress_cb: ProgressCallback | None = None,
) -> int:
    """Separa uma planilha em vários arquivos, um por valor único da coluna.

    Retorna a quantidade de arquivos gerados.
    """
    df = read_spreadsheet(file_path)

    if column not in df.columns:
        raise InvalidSpreadsheetError(
            f"A coluna '{column}' não foi encontrada na planilha."
        )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    unique_values = df[column].dropna().unique()
    total = len(unique_values)
    generated = 0

    for idx, value in enumerate(unique_values, start=1):
        subset = df[df[column] == value]
        filename = sanitize_filename(f"{value}.xlsx")
        dest = unique_path(output_dir, filename)
        subset.to_excel(dest, index=False, engine="openpyxl")
        generated += 1
        if progress_cb:
            progress_cb(idx, total)

    return generated


# ---------------------------------------------------------------------------
# Módulo 3: Limpar planilha
# ---------------------------------------------------------------------------

def clean_spreadsheet(
    file_path: str,
    output_path: str | Path,
    remove_empty_rows: bool = True,
    remove_duplicates: bool = True,
    trim_whitespace: bool = True,
    remove_empty_columns: bool = True,
    standardize_headers: bool = True,
    ignore_case_on_duplicates: bool = False,
) -> dict[str, int]:
    """Aplica limpeza básica de dados. Sempre gera um novo arquivo.

    Retorna um resumo com as quantidades alteradas.
    """
    df = read_spreadsheet(file_path)
    original_rows = len(df)
    original_cols = len(df.columns)

    if standardize_headers:
        df.columns = [str(c).strip().title() for c in df.columns]

    if trim_whitespace:
        text_cols = df.select_dtypes(include="object").columns
        for col in text_cols:
            df[col] = df[col].astype(str).str.strip().replace({"nan": None})

    if remove_empty_columns:
        df = df.dropna(axis=1, how="all")

    if remove_empty_rows:
        df = df.dropna(axis=0, how="all")

    duplicates_removed = 0
    if remove_duplicates:
        before = len(df)
        if ignore_case_on_duplicates:
            text_cols = df.select_dtypes(include="object").columns
            comparison_key = df[text_cols].apply(lambda s: s.str.lower()) if len(text_cols) else df
            dup_mask = pd.concat([comparison_key, df.drop(columns=text_cols)], axis=1).duplicated()
            df = df[~dup_mask]
        else:
            df = df.drop_duplicates()
        duplicates_removed = before - len(df)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(output_path, index=False, engine="openpyxl")

    return {
        "linhas_originais": original_rows,
        "linhas_finais": len(df),
        "colunas_originais": original_cols,
        "colunas_finais": len(df.columns),
        "duplicados_removidos": duplicates_removed,
    }
