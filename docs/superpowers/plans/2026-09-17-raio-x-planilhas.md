# Raio-X de Planilhas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar diagnóstico local, comparação antes/depois e relatório HTML ao fluxo “Limpar planilha”, preservando arquivos originais e explicando cada transformação.

**Architecture:** A transformação será extraída para um motor puro compartilhado pela prévia e pela execução. Um serviço de perfil produzirá dataclasses com métricas agregadas; o serviço de Excel continuará responsável por leitura e escrita, e um gerador separado criará o relatório HTML. A tela executará análises em segundo plano e ignorará resultados obsoletos por número de revisão.

**Tech Stack:** Python 3.11+, pandas 3.0.5, openpyxl 3.1.5, CustomTkinter 5.2.2, `unittest`, biblioteca padrão `html`/`datetime`, PyInstaller 6.22.2.

**Spec:** `docs/superpowers/specs/2026-09-17-raio-x-planilhas-design.md`

## Global Constraints

- Processar somente arquivos `.xlsx` e manter todo o conteúdo no computador do usuário.
- Nunca sobrescrever o arquivo de origem, a saída ou um relatório existente.
- Não incluir valores de células ou linhas completas no relatório; somente nomes de colunas e métricas agregadas.
- Manter mensagens amigáveis na interface e detalhes técnicos apenas no log.
- Não adicionar dependência para PDF; o relatório será HTML autônomo em UTF-8.
- Preservar compatibilidade com entradas antigas de `history.json` sem `report_path`.
- Executar operações pesadas por `core.task_runner.run_in_background`; workers não podem tocar em widgets.
- Manter `clean_spreadsheet()` compatível com os testes e consumidores atuais.

---

## File Map

- Create `services/spreadsheet_cleaning.py`: opções, métricas, resultado e motor puro de limpeza.
- Create `services/spreadsheet_profile_service.py`: perfil agregado e simulação sobre `DataFrame`.
- Create `services/report_service.py`: geração segura do relatório HTML.
- Create `ui/components/data_profile_panel.py`: apresentação compacta do Raio-X.
- Create `tests/test_ui_smoke.py`: regressão da abertura de “Limpar planilha”.
- Create `tests/test_spreadsheet_cleaning.py`: comportamento do motor compartilhado.
- Create `tests/test_spreadsheet_profile.py`: métricas e simulação.
- Create `tests/test_report_service.py`: conteúdo, escape e nomes sem conflito.
- Create `tests/test_activity_service.py`: histórico antigo e `report_path` novo.
- Modify `services/excel_service.py`: delegar transformação e expor análise/execução detalhada.
- Modify `services/activity_service.py`: persistir caminho opcional do relatório.
- Modify `modules/spreadsheets/clean.py`: análise assíncrona, painel e execução detalhada.
- Modify `ui/screens/history_screen.py`: abrir relatório existente.
- Modify `README.md`: documentar Raio-X, relatório e inicialização pelo ambiente virtual.
- Modify `config/settings.py`: elevar a versão para `0.3.0` após validação.

---

### Task 1: Lock down clean-screen navigation and the correct runtime

**Files:**
- Create: `tests/test_ui_smoke.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: `ui.app.App.navigate(destination: str) -> None`
- Produces: a smoke test proving `clean_spreadsheet` builds `CleanSpreadsheetScreen`

- [ ] **Step 1: Record the existing diagnostic evidence**

Run:

```powershell
Get-Content "$env:LOCALAPPDATA\Automatech\logs\app.log" -Tail 120
& .\venv\Scripts\python.exe -c "from core.module_registry import get_module; m=get_module('clean_spreadsheet'); print(type(m).__name__, m.info.key)"
& .\venv\Scripts\python.exe -c "from ui.app import App; app=App(); app.withdraw(); app.navigate('clean_spreadsheet'); app.update_idletasks(); print(type(app._current_screen).__name__); app.destroy()"
```

Expected: the historical log may show `ModuleNotFoundError: customtkinter` from a different Python, while both commands using `venv` print `CleanSpreadsheetModule clean_spreadsheet` and `CleanSpreadsheetScreen`.

- [ ] **Step 2: Write the navigation smoke test**

```python
import unittest

from modules.spreadsheets.clean import CleanSpreadsheetScreen
from ui.app import App


class NavigationSmokeTests(unittest.TestCase):
    def test_clean_spreadsheet_screen_opens(self) -> None:
        app = App()
        app.withdraw()
        try:
            app.navigate("clean_spreadsheet")
            app.update_idletasks()
            self.assertIsInstance(app._current_screen, CleanSpreadsheetScreen)
        finally:
            app.destroy()
```

- [ ] **Step 3: Run the smoke test**

Run: `& .\venv\Scripts\python.exe -m unittest tests.test_ui_smoke -v`

Expected: PASS. If it fails, use the emitted traceback to make the smallest correction in the failing import, asset path, or constructor, then rerun this exact test. Do not change the screen based only on the historical missing-dependency log.

- [ ] **Step 4: Add runtime troubleshooting to README**

Add this command after environment setup:

```powershell
.\venv\Scripts\python.exe main.py
```

Document that `ModuleNotFoundError: customtkinter` means the app was started outside the project virtual environment.

- [ ] **Step 5: Commit the runtime guard**

```powershell
git add tests/test_ui_smoke.py README.md
git commit -m "test: protect clean screen navigation"
```

---

### Task 2: Extract one pure cleaning engine

**Files:**
- Create: `services/spreadsheet_cleaning.py`
- Create: `tests/test_spreadsheet_cleaning.py`
- Modify: `services/excel_service.py:225-280`
- Modify: `tests/test_services.py:52-66`

**Interfaces:**
- Produces: `CleaningOptions`, `CleaningMetrics`, `CleaningResult`, `apply_cleaning(df, options)`
- Preserves: `clean_spreadsheet(file_path, output_path, **flags) -> dict[str, int]`

- [ ] **Step 1: Write failing tests for the shared engine**

```python
import unittest

import pandas as pd

from services.spreadsheet_cleaning import CleaningOptions, apply_cleaning


class SpreadsheetCleaningTests(unittest.TestCase):
    def test_apply_cleaning_returns_exact_metrics(self) -> None:
        frame = pd.DataFrame(
            {" Nome ": [" Ana ", "Ana", None, "Bia"], "Vazia": [None, None, None, None]}
        )

        cleaned, metrics = apply_cleaning(frame, CleaningOptions())

        self.assertEqual(list(cleaned.columns), ["Nome"])
        self.assertEqual(len(cleaned), 2)
        self.assertEqual(metrics.original_rows, 4)
        self.assertEqual(metrics.final_rows, 2)
        self.assertEqual(metrics.original_columns, 2)
        self.assertEqual(metrics.final_columns, 1)
        self.assertEqual(metrics.duplicates_removed, 1)
        self.assertEqual(metrics.empty_rows_removed, 1)
        self.assertEqual(metrics.empty_columns_removed, 1)
        self.assertEqual(metrics.trimmed_text_cells, 1)
        self.assertEqual(metrics.headers_changed, 1)

    def test_disabled_options_preserve_dataframe(self) -> None:
        frame = pd.DataFrame({" Nome ": [" Ana ", " Ana "]})
        options = CleaningOptions(
            remove_empty_rows=False,
            remove_duplicates=False,
            trim_whitespace=False,
            remove_empty_columns=False,
            standardize_headers=False,
            ignore_case_on_duplicates=False,
        )

        cleaned, metrics = apply_cleaning(frame, options)

        pd.testing.assert_frame_equal(cleaned, frame)
        self.assertEqual(metrics.duplicates_removed, 0)
        self.assertEqual(metrics.trimmed_text_cells, 0)
        self.assertEqual(metrics.headers_changed, 0)
```

- [ ] **Step 2: Run the tests to verify the module is missing**

Run: `& .\venv\Scripts\python.exe -m unittest tests.test_spreadsheet_cleaning -v`

Expected: FAIL with `ModuleNotFoundError: services.spreadsheet_cleaning`.

- [ ] **Step 3: Implement the dataclasses and pure engine**

Import `asdict` and `dataclass` from `dataclasses`, then create these public contracts:

```python
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
```

Implement `apply_cleaning(df: pd.DataFrame, options: CleaningOptions) -> tuple[pd.DataFrame, CleaningMetrics]` by moving the existing transformations from `clean_spreadsheet`. Count each transformation before replacing the working frame. Work on `df.copy()` so callers keep their original frame.

- [ ] **Step 4: Delegate the existing API to the engine**

Keep the current keyword parameters on `clean_spreadsheet()`, build `CleaningOptions` from them, call `apply_cleaning`, write through `_write_spreadsheet`, and return `metrics.as_legacy_summary()`.

- [ ] **Step 5: Run engine and regression tests**

Run:

```powershell
& .\venv\Scripts\python.exe -m unittest tests.test_spreadsheet_cleaning tests.test_services -v
```

Expected: all tests PASS, including the existing legacy summary assertions.

- [ ] **Step 6: Commit the shared engine**

```powershell
git add services/spreadsheet_cleaning.py services/excel_service.py tests/test_spreadsheet_cleaning.py tests/test_services.py
git commit -m "refactor: share spreadsheet cleaning engine"
```

---

### Task 3: Build the Raio-X profile and cleaning simulation

**Files:**
- Create: `services/spreadsheet_profile_service.py`
- Create: `tests/test_spreadsheet_profile.py`
- Modify: `services/excel_service.py`

**Interfaces:**
- Consumes: `CleaningOptions`, `CleaningMetrics`, `apply_cleaning`
- Produces: `ColumnProfile`, `SpreadsheetProfile`, `CleaningPreview`, `profile_dataframe()`, `analyze_spreadsheet()`

- [ ] **Step 1: Write failing profile tests**

```python
import unittest

import pandas as pd

from services.spreadsheet_cleaning import CleaningOptions
from services.spreadsheet_profile_service import profile_dataframe, simulate_cleaning


class SpreadsheetProfileTests(unittest.TestCase):
    def test_profile_reports_aggregates_without_cell_samples(self) -> None:
        frame = pd.DataFrame({"Nome": [" Ana ", None, "Bia"], "Valor": [1, 1, None]})

        profile = profile_dataframe(frame, source_path="clientes.xlsx")

        self.assertEqual(profile.rows, 3)
        self.assertEqual(profile.columns, 2)
        self.assertEqual(profile.empty_cells, 2)
        self.assertEqual(profile.duplicate_rows, 0)
        self.assertEqual(profile.trimmed_text_cells, 1)
        self.assertEqual(profile.column_profiles[0].name, "Nome")
        self.assertEqual(profile.column_profiles[0].empty_cells, 1)
        self.assertEqual(profile.column_profiles[0].distinct_values, 2)
        self.assertFalse(hasattr(profile.column_profiles[0], "sample_values"))

    def test_simulation_uses_shared_cleaning_rules(self) -> None:
        frame = pd.DataFrame({"Nome": [" Ana ", "Ana", None]})

        preview = simulate_cleaning(frame, "clientes.xlsx", CleaningOptions())

        self.assertEqual(preview.original.rows, 3)
        self.assertEqual(preview.estimated_metrics.final_rows, 1)
        self.assertEqual(preview.estimated_metrics.duplicates_removed, 1)
```

- [ ] **Step 2: Verify the tests fail before implementation**

Run: `& .\venv\Scripts\python.exe -m unittest tests.test_spreadsheet_profile -v`

Expected: FAIL with the missing profile module.

- [ ] **Step 3: Implement profile dataclasses and pure functions**

Use these public structures:

```python
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
```

Normalize inferred types to the Portuguese labels `Texto`, `Número`, `Data`, `Booleano`, `Misto` and `Vazio`. Count blank or duplicated normalized headers in `header_issues`. Do not store cell values.

- [ ] **Step 4: Add the file-level adapter**

In `services/excel_service.py`, add:

```python
def analyze_spreadsheet(
    file_path: str | Path,
    options: CleaningOptions,
) -> CleaningPreview:
    frame = read_spreadsheet(file_path)
    return simulate_cleaning(frame, str(Path(file_path)), options)
```

- [ ] **Step 5: Run profile and service tests**

Run:

```powershell
& .\venv\Scripts\python.exe -m unittest tests.test_spreadsheet_profile tests.test_spreadsheet_cleaning tests.test_services -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit the profiling service**

```powershell
git add services/spreadsheet_profile_service.py services/excel_service.py tests/test_spreadsheet_profile.py
git commit -m "feat: add local spreadsheet raio-x"
```

---

### Task 4: Generate a safe standalone HTML report

**Files:**
- Create: `services/report_service.py`
- Create: `tests/test_report_service.py`

**Interfaces:**
- Consumes: `CleaningPreview`, `CleaningMetrics`, source and output paths, applied `CleaningOptions`
- Produces: `write_cleaning_report(preview, final_metrics, options, source_path, output_path, requested_path) -> Path`

- [ ] **Step 1: Write failing report tests**

```python
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from services.report_service import write_cleaning_report
from services.spreadsheet_cleaning import CleaningOptions, apply_cleaning
from services.spreadsheet_profile_service import simulate_cleaning


class ReportServiceTests(unittest.TestCase):
    def test_report_escapes_names_and_uses_unique_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            folder = Path(temporary_directory)
            requested = folder / "resultado_relatorio.html"
            requested.write_text("existente", encoding="utf-8")
            options = CleaningOptions()
            frame = pd.DataFrame({"Cliente <VIP>": [" Ana ", "Ana"]})
            preview = simulate_cleaning(frame, "entrada & origem.xlsx", options)
            _, metrics = apply_cleaning(frame, options)

            generated = write_cleaning_report(
                preview=preview,
                final_metrics=metrics,
                options=options,
                source_path=Path("entrada & origem.xlsx"),
                output_path=folder / "resultado.xlsx",
                requested_path=requested,
            )

            content = generated.read_text(encoding="utf-8")
            self.assertEqual(generated.name, "resultado_relatorio (1).html")
            self.assertIn("Cliente &lt;VIP&gt;", content)
            self.assertIn("entrada &amp; origem.xlsx", content)
            self.assertNotIn("Cliente <VIP>", content)
```

- [ ] **Step 2: Verify the report module is missing**

Run: `& .\venv\Scripts\python.exe -m unittest tests.test_report_service -v`

Expected: FAIL with `ModuleNotFoundError: services.report_service`.

- [ ] **Step 3: Implement the report writer**

Implement:

```python
def write_cleaning_report(
    preview: CleaningPreview,
    final_metrics: CleaningMetrics,
    options: CleaningOptions,
    source_path: Path,
    output_path: Path,
    requested_path: Path,
) -> Path:
    destination = unique_path(requested_path.parent, requested_path.name)
    html_document = _render_cleaning_report(
        preview, final_metrics, options, source_path, output_path
    )
    destination.write_text(html_document, encoding="utf-8")
    return destination
```

Escape every interpolated filename and column name with `html.escape`. Include embedded CSS, `<meta charset="utf-8">`, generation timestamp, option labels, summary metrics and the column table. Do not render data values.

- [ ] **Step 4: Run report tests**

Run: `& .\venv\Scripts\python.exe -m unittest tests.test_report_service -v`

Expected: PASS.

- [ ] **Step 5: Commit the report generator**

```powershell
git add services/report_service.py tests/test_report_service.py
git commit -m "feat: generate cleaning reports"
```

---

### Task 5: Execute detailed cleaning and persist report artifacts

**Files:**
- Modify: `services/excel_service.py`
- Modify: `services/activity_service.py:60-82`
- Modify: `ui/screens/history_screen.py`
- Create: `tests/test_activity_service.py`
- Modify: `tests/test_services.py`

**Interfaces:**
- Consumes: profile, cleaning engine and report writer
- Produces: `clean_spreadsheet_detailed(file_path: str | Path, output_path: str | Path, options: CleaningOptions) -> CleaningResult`
- Extends: `record_execution(module_key, module_name, status, summary, output_path=None, report_path=None) -> None`

- [ ] **Step 1: Write failing detailed-execution and history tests**

Add to `tests/test_services.py`:

```python
def test_detailed_cleaning_generates_spreadsheet_and_report(self) -> None:
    source = self._spreadsheet("clientes.xlsx", {"Nome": [" Ana ", "Ana"]})
    output = self.folder / "clientes_limpo.xlsx"

    result = clean_spreadsheet_detailed(source, output, CleaningOptions())

    self.assertTrue(result.output_path.exists())
    self.assertIsNotNone(result.report_path)
    self.assertTrue(result.report_path.exists())
    self.assertEqual(result.metrics.duplicates_removed, 1)
```

Create `tests/test_activity_service.py`:

```python
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.activity_service import list_history, record_execution


class ActivityServiceTests(unittest.TestCase):
    def test_history_accepts_old_entries_and_persists_report_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            history_path = Path(temporary_directory) / "history.json"
            history_path.write_text(
                '[{"id":"old","status":"success"}]', encoding="utf-8"
            )
            with patch(
                "services.activity_service.history_file_path",
                return_value=history_path,
            ):
                record_execution(
                    "clean_spreadsheet",
                    "Limpar planilha",
                    "success",
                    "Concluída",
                    "saida.xlsx",
                    "saida_relatorio.html",
                )
                history = list_history()

        self.assertEqual(history[0]["report_path"], "saida_relatorio.html")
        self.assertNotIn("report_path", history[1])
```

- [ ] **Step 2: Verify the new contracts fail**

Run:

```powershell
& .\venv\Scripts\python.exe -m unittest tests.test_services.SpreadsheetServiceTests.test_detailed_cleaning_generates_spreadsheet_and_report tests.test_activity_service -v
```

Expected: FAIL because `clean_spreadsheet_detailed` and `report_path` do not exist.

- [ ] **Step 3: Implement detailed cleaning**

Implement this exact signature:

```python
def clean_spreadsheet_detailed(
    file_path: str | Path,
    output_path: str | Path,
    options: CleaningOptions,
) -> CleaningResult:
```

The function must read once, create the preview, apply the shared engine, write the `.xlsx`, derive `<output_stem>_relatorio.html`, and then attempt the HTML report. Return:

```python
CleaningResult(
    metrics=metrics,
    output_path=destination,
    report_path=report_path,
    report_warning=report_warning,
)
```

Catch `OSError` only around report creation. Set `report_path=None` and `report_warning="A planilha foi criada, mas não foi possível gerar o relatório."`; do not delete the spreadsheet. Keep `clean_spreadsheet()` as the compatibility wrapper returning `result.metrics.as_legacy_summary()` without generating a report.

- [ ] **Step 4: Extend history and its UI**

Add the optional `report_path` argument to `record_execution` and persist it only when provided. In `HistoryScreen`, replace the single grid-positioned button with an `actions` frame in column 1 spanning the three card rows. Pack “Abrir pasta” and, when `Path(report_path).is_file()`, “Abrir relatório” in that frame. The report button calls the existing `open_in_explorer(Path(report_path))`; on Windows it delegates files and folders to `os.startfile`.

- [ ] **Step 5: Run service and history tests**

Run:

```powershell
& .\venv\Scripts\python.exe -m unittest tests.test_services tests.test_activity_service tests.test_report_service -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit execution artifacts**

```powershell
git add services/excel_service.py services/activity_service.py ui/screens/history_screen.py tests/test_services.py tests/test_activity_service.py
git commit -m "feat: track cleaning report artifacts"
```

---

### Task 6: Integrate the Raio-X into the cleaning screen

**Files:**
- Create: `ui/components/data_profile_panel.py`
- Modify: `modules/spreadsheets/clean.py`
- Modify: `tests/test_ui_smoke.py`

**Interfaces:**
- Consumes: `analyze_spreadsheet()`, `clean_spreadsheet_detailed()`, `CleaningPreview`
- Produces: `DataProfilePanel.render(preview: CleaningPreview) -> None`

- [ ] **Step 1: Add a failing UI state test**

Extend `tests/test_ui_smoke.py`:

```python
def test_clean_screen_starts_without_ready_analysis(self) -> None:
    app = App()
    app.withdraw()
    try:
        app.navigate("clean_spreadsheet")
        screen = app._current_screen
        self.assertFalse(screen._analysis_ready)
        self.assertEqual(screen.run_btn.cget("state"), "disabled")
        self.assertIsNotNone(screen.profile_panel)
    finally:
        app.destroy()
```

- [ ] **Step 2: Verify the UI contract fails**

Run: `& .\venv\Scripts\python.exe -m unittest tests.test_ui_smoke -v`

Expected: FAIL because the analysis state and panel are not present.

- [ ] **Step 3: Build the reusable profile panel**

`DataProfilePanel` must expose `show_empty()`, `show_loading()`, `show_error(message)` and `render(preview)`. Use existing `COLORS`, `FONT_FAMILY`, `FONT_SIZES` and `CORNER_RADIUS`. Render summary labels and a `CTkScrollableFrame` for columns; do not render cell values.

```python
class DataProfilePanel(ctk.CTkFrame):
    def _clear_columns(self) -> None:
        for child in self.columns_frame.winfo_children():
            child.destroy()

    def show_empty(self) -> None:
        self.summary_label.configure(text="Selecione uma planilha para gerar o Raio-X.")
        self._clear_columns()

    def show_loading(self) -> None:
        self.summary_label.configure(text="Analisando planilha…")
        self._clear_columns()

    def show_error(self, message: str) -> None:
        self.summary_label.configure(text=message, text_color=COLORS["error"])
        self._clear_columns()

    def render(self, preview: CleaningPreview) -> None:
        profile = preview.original
        metrics = preview.estimated_metrics
        self.summary_label.configure(
            text=(
                f"{profile.rows} linhas • {profile.columns} colunas • "
                f"{profile.empty_cells} células vazias • "
                f"estimativa: {metrics.final_rows} × {metrics.final_columns}"
            ),
            text_color=COLORS["text_primary"],
        )
        self._clear_columns()
        for row, column in enumerate(profile.column_profiles):
            ctk.CTkLabel(
                self.columns_frame,
                text=(
                    f"{column.name}  |  {column.inferred_type}  |  "
                    f"vazios: {column.empty_cells}  |  distintos: {column.distinct_values}"
                ),
                anchor="w",
                text_color=COLORS["text_secondary"],
            ).grid(row=row, column=0, sticky="ew", padx=8, pady=3)
```

The implementation replaces the contents of its internal summary and column frames in each method. `render()` formats only `preview.original`, `preview.estimated_metrics` and the fields of each `ColumnProfile`.

- [ ] **Step 4: Add versioned background analysis**

In `CleanSpreadsheetScreen`, initialize:

```python
self._analysis_revision = 0
self._analysis_after_id: str | None = None
self._analysis_ready = False
self._current_preview: CleaningPreview | None = None
```

Each file or option change calls `_schedule_analysis()`, which increments the revision, disables `run_btn`, cancels the previous `.after()` callback when present, and schedules `_start_analysis(revision)` after 250 ms. The background task captures the file path and `CleaningOptions`. Success and error callbacks must first compare the captured revision with `self._analysis_revision`; stale results return without updating widgets.

Change `_cleaning_options()` to return `CleaningOptions`. Each checkbox receives `command=self._schedule_analysis`; routine persistence uses `self._cleaning_options().as_dict()` so the existing JSON schema remains boolean fields.

- [ ] **Step 5: Use exact preview and detailed execution**

Replace the textual sample in the confirmation with the profile summary and estimated final dimensions. Run `clean_spreadsheet_detailed`. On success:

```python
record_execution(
    CleanSpreadsheetModule.info.key,
    CleanSpreadsheetModule.info.name,
    "success",
    summary_text,
    result.output_path,
    result.report_path,
)
```

Display `result.report_warning` as a nonfatal warning when present. Save routines with the existing boolean option fields, and invoke `_schedule_analysis()` after `apply_preset()` restores them.

- [ ] **Step 6: Make the screen vertically scrollable**

Place the existing header, options, `DataProfilePanel`, actions and status inside one `CTkScrollableFrame`, preserving the current minimum window size `920x620`. Keep action labels in Portuguese and the existing dark theme.

- [ ] **Step 7: Run UI and service tests**

Run:

```powershell
& .\venv\Scripts\python.exe -m unittest tests.test_ui_smoke tests.test_spreadsheet_profile tests.test_spreadsheet_cleaning tests.test_services tests.test_activity_service tests.test_report_service -v
```

Expected: all tests PASS.

- [ ] **Step 8: Commit the UI integration**

```powershell
git add ui/components/data_profile_panel.py modules/spreadsheets/clean.py tests/test_ui_smoke.py
git commit -m "feat: show spreadsheet raio-x before cleaning"
```

---

### Task 7: Validate the complete Windows flow and release metadata

**Files:**
- Modify: `README.md`
- Modify: `config/settings.py:11`

**Interfaces:**
- Consumes: all previous tasks
- Produces: documented and packaged Automatech `0.3.0`

- [ ] **Step 1: Run the complete automated suite**

Run: `& .\venv\Scripts\python.exe -m unittest discover -s tests -v`

Expected: every test PASS with no traceback or hung UI process.

- [ ] **Step 2: Perform the Windows application check**

Run: `& .\venv\Scripts\python.exe main.py`

Use a fixture containing duplicates, blank rows, one empty column, padded text and a header containing `&`. Verify:

1. “Limpar planilha” opens.
2. The window remains responsive while “Analisando planilha…” is visible.
3. Changing an option refreshes the estimate.
4. Confirmation shows estimated before/after metrics.
5. Execution creates a new `.xlsx` and `_relatorio.html` without changing the source.
6. The HTML opens and contains only aggregate metrics.
7. Histórico opens both the output folder and report.
8. The screen works at `920x620`.

- [ ] **Step 3: Update documentation and version**

Set `APP_VERSION = "0.3.0"`. Add README bullets for “Raio-X dos Dados”, comparison before/after and local HTML report. Mark no roadmap item complete unless its full behavior is delivered; “Rotinas com várias etapas encadeadas” remains pending.

- [ ] **Step 4: Build the Windows bundle**

Run: `& .\venv\Scripts\python.exe build.py`

Expected: `dist\Automatech\Automatech.exe` is created without missing-import errors.

- [ ] **Step 5: Smoke-test the newly built executable**

Run: `& .\dist\Automatech\Automatech.exe`

Repeat steps 1, 2, 5 and 7 from the Windows application check using the newly built executable. Confirm that the report opens from the packaged application.

- [ ] **Step 6: Inspect the final diff**

Run:

```powershell
git status --short
git diff --check
git diff --stat 604aecd..HEAD
```

Expected: only planned source, test, documentation and build-metadata files are changed; `git diff --check` prints nothing.

- [ ] **Step 7: Commit release metadata**

```powershell
git add README.md config/settings.py
git commit -m "docs: release Automatech 0.3.0"
```

---

## Completion Evidence

Before declaring the milestone complete, retain these results in the final handoff:

- output of `python -m unittest discover -s tests -v`;
- screenshot or direct visual observation of the Raio-X at normal and minimum window sizes;
- generated `.xlsx` and HTML report names from the manual fixture;
- output of `build.py` and startup result of the newly built executable;
- final commit list and concise note about the historical wrong-Python diagnosis.
