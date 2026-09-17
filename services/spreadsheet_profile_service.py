"""Perfil agregado de planilhas e simulação segura de limpeza."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from services.spreadsheet_cleaning import (
    CleaningMetrics,
    CleaningOptions,
    apply_cleaning,
)


@dataclass(frozen=True)
class ColumnProfile:
    name: str
    inferred_type: str
    empty_cells: int
    distinct_values: int
    trimmed_text_cells: int


@dataclass(frozen=True)
class SpreadsheetProfile:
    source_path: str
    rows: int
    columns: int
    empty_cells: int
    duplicate_rows: int
    empty_rows: int
    empty_columns: int
    trimmed_text_cells: int
    header_issues: int
    column_profiles: tuple[ColumnProfile, ...]


@dataclass(frozen=True)
class CleaningPreview:
    original: SpreadsheetProfile
    estimated_metrics: CleaningMetrics


def _inferred_type(series: pd.Series) -> str:
    non_empty = series.dropna()
    if non_empty.empty:
        return "Vazio"
    if pd.api.types.is_bool_dtype(series.dtype):
        return "Booleano"
    if pd.api.types.is_datetime64_any_dtype(series.dtype):
        return "Data"
    if pd.api.types.is_numeric_dtype(series.dtype):
        return "Número"

    value_types = {type(value) for value in non_empty}
    if value_types and all(issubclass(value_type, str) for value_type in value_types):
        return "Texto"
    return "Misto"


def _trimmed_text_cells(series: pd.Series) -> int:
    return int(
        series.map(
            lambda value: isinstance(value, str) and value != value.strip()
        ).sum()
    )


def _header_issue_count(columns: pd.Index) -> int:
    issues = 0
    seen: set[str] = set()
    for column in columns:
        normalized = str(column).strip().casefold()
        if not normalized:
            issues += 1
        elif normalized in seen:
            issues += 1
        seen.add(normalized)
    return issues


def profile_dataframe(
    frame: pd.DataFrame,
    source_path: str,
) -> SpreadsheetProfile:
    column_profiles: list[ColumnProfile] = []
    for index, column in enumerate(frame.columns):
        series = frame.iloc[:, index]
        column_profiles.append(
            ColumnProfile(
                name=str(column),
                inferred_type=_inferred_type(series),
                empty_cells=int(series.isna().sum()),
                distinct_values=int(series.nunique(dropna=True)),
                trimmed_text_cells=_trimmed_text_cells(series),
            )
        )

    return SpreadsheetProfile(
        source_path=source_path,
        rows=len(frame),
        columns=len(frame.columns),
        empty_cells=int(frame.isna().sum().sum()),
        duplicate_rows=int(frame.duplicated().sum()),
        empty_rows=int(frame.isna().all(axis=1).sum()),
        empty_columns=int(frame.isna().all(axis=0).sum()),
        trimmed_text_cells=sum(
            column.trimmed_text_cells for column in column_profiles
        ),
        header_issues=_header_issue_count(frame.columns),
        column_profiles=tuple(column_profiles),
    )


def simulate_cleaning(
    frame: pd.DataFrame,
    source_path: str,
    options: CleaningOptions,
) -> CleaningPreview:
    original = profile_dataframe(frame, source_path)
    _, estimated_metrics = apply_cleaning(frame, options)
    return CleaningPreview(original=original, estimated_metrics=estimated_metrics)
