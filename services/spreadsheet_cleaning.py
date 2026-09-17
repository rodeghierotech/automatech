"""Motor puro de limpeza de planilhas e métricas das transformações."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class CleaningOptions:
    remove_empty_rows: bool = True
    remove_duplicates: bool = True
    trim_whitespace: bool = True
    remove_empty_columns: bool = True
    standardize_headers: bool = True
    ignore_case_on_duplicates: bool = False

    def as_dict(self) -> dict[str, bool]:
        return asdict(self)


@dataclass(frozen=True)
class CleaningMetrics:
    original_rows: int
    final_rows: int
    original_columns: int
    final_columns: int
    duplicates_removed: int
    empty_rows_removed: int
    empty_columns_removed: int
    trimmed_text_cells: int
    headers_changed: int

    def as_legacy_summary(self) -> dict[str, int]:
        return {
            "linhas_originais": self.original_rows,
            "linhas_finais": self.final_rows,
            "colunas_originais": self.original_columns,
            "colunas_finais": self.final_columns,
            "duplicados_removidos": self.duplicates_removed,
        }


@dataclass(frozen=True)
class CleaningResult:
    metrics: CleaningMetrics
    output_path: Path
    report_path: Path | None = None
    report_warning: str = ""


def text_columns(df: pd.DataFrame) -> list[object]:
    return [
        column
        for column in df.columns
        if df[column].dtype == object or pd.api.types.is_string_dtype(df[column].dtype)
    ]


def standardized_headers(columns: pd.Index) -> list[str]:
    result: list[str] = []
    occurrences: dict[str, int] = {}
    for column in columns:
        base = str(column).strip().title() or "Coluna"
        key = base.casefold()
        occurrences[key] = occurrences.get(key, 0) + 1
        count = occurrences[key]
        result.append(base if count == 1 else f"{base} ({count})")
    return result


def apply_cleaning(
    df: pd.DataFrame,
    options: CleaningOptions,
) -> tuple[pd.DataFrame, CleaningMetrics]:
    """Aplica as opções sem alterar o DataFrame recebido."""
    cleaned = df.copy()
    original_rows = len(cleaned)
    original_columns = len(cleaned.columns)

    headers_changed = 0
    if options.standardize_headers:
        updated_headers = standardized_headers(cleaned.columns)
        headers_changed = sum(
            str(current) != updated
            for current, updated in zip(cleaned.columns, updated_headers, strict=True)
        )
        cleaned.columns = updated_headers

    trimmed_text_cells = 0
    if options.trim_whitespace:
        for column in text_columns(cleaned):
            trimmed_text_cells += int(
                cleaned[column]
                .map(lambda value: isinstance(value, str) and value != value.strip())
                .sum()
            )
            cleaned[column] = cleaned[column].map(
                lambda value: value.strip() if isinstance(value, str) else value
            )

    empty_columns_removed = 0
    if options.remove_empty_columns:
        before_columns = len(cleaned.columns)
        cleaned = cleaned.dropna(axis=1, how="all")
        empty_columns_removed = before_columns - len(cleaned.columns)

    empty_rows_removed = 0
    if options.remove_empty_rows:
        before_rows = len(cleaned)
        cleaned = cleaned.dropna(axis=0, how="all")
        empty_rows_removed = before_rows - len(cleaned)

    duplicates_removed = 0
    if options.remove_duplicates:
        before_rows = len(cleaned)
        if options.ignore_case_on_duplicates:
            comparison_key = cleaned.copy()
            for column in text_columns(comparison_key):
                comparison_key[column] = comparison_key[column].map(
                    lambda value: value.casefold() if isinstance(value, str) else value
                )
            cleaned = cleaned[~comparison_key.duplicated()]
        else:
            cleaned = cleaned.drop_duplicates()
        duplicates_removed = before_rows - len(cleaned)

    metrics = CleaningMetrics(
        original_rows=original_rows,
        final_rows=len(cleaned),
        original_columns=original_columns,
        final_columns=len(cleaned.columns),
        duplicates_removed=duplicates_removed,
        empty_rows_removed=empty_rows_removed,
        empty_columns_removed=empty_columns_removed,
        trimmed_text_cells=trimmed_text_cells,
        headers_changed=headers_changed,
    )
    return cleaned, metrics
