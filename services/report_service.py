"""Geração do relatório HTML local das limpezas de planilha."""
from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

from services.spreadsheet_cleaning import CleaningMetrics, CleaningOptions
from services.spreadsheet_profile_service import CleaningPreview
from utils.paths import unique_path


OPTION_LABELS: tuple[tuple[str, str], ...] = (
    ("remove_empty_rows", "Remover linhas completamente vazias"),
    ("remove_duplicates", "Remover linhas duplicadas"),
    ("ignore_case_on_duplicates", "Ignorar maiúsculas/minúsculas em duplicados"),
    ("trim_whitespace", "Remover espaços externos em textos"),
    ("remove_empty_columns", "Remover colunas completamente vazias"),
    ("standardize_headers", "Padronizar cabeçalhos"),
)


def _metric_card(label: str, value: int | str) -> str:
    return (
        '<div class="metric">'
        f'<span class="metric-value">{escape(str(value))}</span>'
        f'<span class="metric-label">{escape(label)}</span>'
        "</div>"
    )


def _render_cleaning_report(
    preview: CleaningPreview,
    final_metrics: CleaningMetrics,
    options: CleaningOptions,
    source_path: Path,
    output_path: Path,
) -> str:
    profile = preview.original
    generated_at = datetime.now().astimezone().strftime("%d/%m/%Y às %H:%M:%S")
    option_items = "".join(
        f'<li class="{"enabled" if getattr(options, key) else "disabled"}">'
        f'{"Aplicada" if getattr(options, key) else "Desativada"}: {escape(label)}</li>'
        for key, label in OPTION_LABELS
    )
    column_rows = "".join(
        "<tr>"
        f"<td>{escape(column.name)}</td>"
        f"<td>{escape(column.inferred_type)}</td>"
        f"<td>{column.empty_cells}</td>"
        f"<td>{column.distinct_values}</td>"
        f"<td>{column.trimmed_text_cells}</td>"
        "</tr>"
        for column in profile.column_profiles
    )
    metrics = "".join(
        (
            _metric_card("Linhas antes", final_metrics.original_rows),
            _metric_card("Linhas depois", final_metrics.final_rows),
            _metric_card("Colunas antes", final_metrics.original_columns),
            _metric_card("Colunas depois", final_metrics.final_columns),
            _metric_card("Duplicados removidos", final_metrics.duplicates_removed),
            _metric_card("Linhas vazias removidas", final_metrics.empty_rows_removed),
            _metric_card("Colunas vazias removidas", final_metrics.empty_columns_removed),
            _metric_card("Textos ajustados", final_metrics.trimmed_text_cells),
            _metric_card("Cabeçalhos ajustados", final_metrics.headers_changed),
        )
    )

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Relatório de transformação — Automatech</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, Segoe UI, sans-serif; }}
    body {{ margin: 0; background: #0b1120; color: #e5e7eb; }}
    main {{ width: min(1080px, calc(100% - 40px)); margin: 40px auto; }}
    header, section {{ background: #111827; border: 1px solid #24324a; border-radius: 14px; padding: 24px; margin-bottom: 16px; }}
    h1, h2 {{ margin-top: 0; }} h1 {{ color: #f8fafc; }} h2 {{ color: #bfdbfe; font-size: 18px; }}
    .eyebrow {{ color: #60a5fa; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
    .files {{ display: grid; gap: 8px; color: #cbd5e1; }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }}
    .metric {{ background: #0f172a; border-radius: 10px; padding: 16px; }}
    .metric-value {{ display: block; color: #f8fafc; font-size: 24px; font-weight: 700; }}
    .metric-label {{ display: block; color: #94a3b8; font-size: 13px; margin-top: 4px; }}
    ul {{ padding-left: 20px; }} li {{ margin: 8px 0; }} .enabled {{ color: #bbf7d0; }} .disabled {{ color: #94a3b8; }}
    .table-wrap {{ overflow-x: auto; }} table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 11px 12px; border-bottom: 1px solid #24324a; text-align: left; }} th {{ color: #93c5fd; font-size: 13px; }}
    footer {{ color: #64748b; text-align: center; padding: 16px; font-size: 12px; }}
  </style>
</head>
<body>
  <main>
    <header>
      <div class="eyebrow">Automatech • Raio-X dos Dados</div>
      <h1>Relatório de transformação</h1>
      <div class="files">
        <span><strong>Origem:</strong> {escape(source_path.name)}</span>
        <span><strong>Resultado:</strong> {escape(output_path.name)}</span>
        <span><strong>Gerado em:</strong> {escape(generated_at)}</span>
      </div>
    </header>
    <section>
      <h2>Resultado da limpeza</h2>
      <div class="metrics">{metrics}</div>
    </section>
    <section>
      <h2>Opções da execução</h2>
      <ul>{option_items}</ul>
    </section>
    <section>
      <h2>Perfil original por coluna</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Coluna</th><th>Tipo</th><th>Vazios</th><th>Distintos</th><th>Espaços externos</th></tr></thead>
          <tbody>{column_rows}</tbody>
        </table>
      </div>
    </section>
    <footer>Processamento local. O relatório contém somente métricas agregadas.</footer>
  </main>
</body>
</html>
"""


def write_cleaning_report(
    preview: CleaningPreview,
    final_metrics: CleaningMetrics,
    options: CleaningOptions,
    source_path: Path,
    output_path: Path,
    requested_path: Path,
) -> Path:
    destination = unique_path(requested_path.parent, requested_path.name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    document = _render_cleaning_report(
        preview, final_metrics, options, source_path, output_path
    )
    destination.write_text(document, encoding="utf-8")
    return destination
