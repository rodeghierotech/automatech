"""Lógica de manipulação de planilhas Excel, isolada da interface gráfica.

Todas as funções aqui são "puras" no sentido de que não conhecem CustomTkinter,
não atualizam widgets e apenas trabalham com dados e arquivos. Isso facilita
testes e reutilização por qualquer módulo futuro.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import pandas as pd

from services.spreadsheet_cleaning import CleaningOptions, apply_cleaning
from services.spreadsheet_profile_service import CleaningPreview, simulate_cleaning
from utils.errors import (
    FileAccessError,
    IncompatibleColumnsError,
    InvalidSpreadsheetError,
    ValidationError,
)
from utils.paths import sanitize_filename, unique_path
from utils.validators import validate_spreadsheet_path

ProgressCallback = Callable[[int, int], None]  # (atual, total)


def _write_spreadsheet(df: pd.DataFrame, output_path: str | Path) -> None:
    """Grava uma planilha nova e remove arquivos parciais em caso de falha."""
    destination = Path(output_path)
    if destination.exists():
        raise ValidationError(
            f"Já existe um arquivo chamado '{destination.name}'. Escolha outro nome."
        )
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(destination, index=False, engine="openpyxl")
    except (PermissionError, OSError) as exc:
        if destination.exists():
            try:
                destination.unlink()
            except OSError:
                pass
        raise FileAccessError(
            f"Não foi possível salvar '{destination.name}'. Verifique se o arquivo está "
            "aberto e se a pasta permite gravação.",
            technical_detail=str(exc),
        ) from exc


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
    headers = [str(column) for column in df.columns]
    if not headers:
        raise InvalidSpreadsheetError(f"A planilha '{p.name}' não possui colunas.")
    return headers


def spreadsheet_preview(path: str | Path, max_rows: int = 3, max_columns: int = 5) -> str:
    """Retorna uma amostra compacta e segura para exibição antes da execução."""
    p = validate_spreadsheet_path(path)
    try:
        df = pd.read_excel(p, engine="openpyxl", nrows=max_rows)
    except Exception as exc:  # noqa: BLE001
        raise InvalidSpreadsheetError(
            f"Não foi possível gerar a prévia de '{p.name}'.",
            technical_detail=str(exc),
        ) from exc
    if not len(df.columns):
        raise InvalidSpreadsheetError(f"A planilha '{p.name}' não possui colunas.")

    visible = df.iloc[:, :max_columns].fillna("")
    headers = [str(column)[:18] for column in visible.columns]
    lines = ["  |  ".join(headers)]
    for values in visible.itertuples(index=False, name=None):
        lines.append("  |  ".join(str(value).replace("\n", " ")[:18] for value in values))
    if len(df.columns) > max_columns:
        lines[0] += f"  |  +{len(df.columns) - max_columns} coluna(s)"
    return "\n".join(lines)


def analyze_spreadsheet(
    file_path: str | Path,
    options: CleaningOptions,
) -> CleaningPreview:
    """Gera o Raio-X e a estimativa de limpeza de uma planilha."""
    frame = read_spreadsheet(file_path)
    return simulate_cleaning(frame, str(Path(file_path)), options)


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
        raise ValidationError("Selecione ao menos duas planilhas para unir.")

    output_path = Path(output_path)
    resolved_sources = {Path(path).resolve() for path in file_paths}
    if output_path.resolve() in resolved_sources:
        raise ValidationError("Escolha um nome diferente dos arquivos originais.")

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

    _write_spreadsheet(merged, output_path)

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
    if total == 0:
        raise InvalidSpreadsheetError(
            f"A coluna '{column}' não possui valores para gerar arquivos."
        )
    generated = 0

    for idx, value in enumerate(unique_values, start=1):
        subset = df[df[column] == value]
        filename = f"{sanitize_filename(str(value), fallback='sem_valor', max_length=140)}.xlsx"
        dest = unique_path(output_dir, filename)
        _write_spreadsheet(subset, dest)
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
    if Path(output_path).resolve() == Path(file_path).resolve():
        raise ValidationError("O arquivo de saída precisa ser diferente do original.")
    options = CleaningOptions(
        remove_empty_rows=remove_empty_rows,
        remove_duplicates=remove_duplicates,
        trim_whitespace=trim_whitespace,
        remove_empty_columns=remove_empty_columns,
        standardize_headers=standardize_headers,
        ignore_case_on_duplicates=ignore_case_on_duplicates,
    )
    cleaned, metrics = apply_cleaning(df, options)
    _write_spreadsheet(cleaned, output_path)
    return metrics.as_legacy_summary()
