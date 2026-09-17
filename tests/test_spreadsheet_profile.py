from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from services.excel_service import analyze_spreadsheet
from services.spreadsheet_cleaning import CleaningOptions
from services.spreadsheet_profile_service import profile_dataframe, simulate_cleaning


class SpreadsheetProfileTests(unittest.TestCase):
    def test_profile_reports_aggregates_without_cell_samples(self) -> None:
        frame = pd.DataFrame(
            {"Nome": [" Ana ", None, "Bia"], "Valor": [1, 1, None]}
        )

        profile = profile_dataframe(frame, source_path="clientes.xlsx")

        self.assertEqual(profile.rows, 3)
        self.assertEqual(profile.columns, 2)
        self.assertEqual(profile.empty_cells, 2)
        self.assertEqual(profile.duplicate_rows, 0)
        self.assertEqual(profile.trimmed_text_cells, 1)
        self.assertEqual(profile.column_profiles[0].name, "Nome")
        self.assertEqual(profile.column_profiles[0].inferred_type, "Texto")
        self.assertEqual(profile.column_profiles[0].empty_cells, 1)
        self.assertEqual(profile.column_profiles[0].distinct_values, 2)
        self.assertFalse(hasattr(profile.column_profiles[0], "sample_values"))

    def test_simulation_uses_shared_cleaning_rules(self) -> None:
        frame = pd.DataFrame({"Nome": [" Ana ", "Ana", None]})

        preview = simulate_cleaning(frame, "clientes.xlsx", CleaningOptions())

        self.assertEqual(preview.original.rows, 3)
        self.assertEqual(preview.estimated_metrics.final_rows, 1)
        self.assertEqual(preview.estimated_metrics.duplicates_removed, 1)

    def test_profile_reports_header_issues_and_inferred_types(self) -> None:
        frame = pd.DataFrame(
            [[1, pd.Timestamp("2026-09-17"), True, None, "texto"],
             [2, pd.Timestamp("2026-09-18"), False, None, 3]],
            columns=["Valor", "Data", "Ativo", " ", "Valor"],
        )

        profile = profile_dataframe(frame, source_path="tipos.xlsx")

        self.assertEqual(profile.header_issues, 2)
        self.assertEqual(
            [column.inferred_type for column in profile.column_profiles],
            ["Número", "Data", "Booleano", "Vazio", "Misto"],
        )

    def test_analyze_spreadsheet_reads_xlsx(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "clientes.xlsx"
            pd.DataFrame({"Nome": ["Ana", "Ana"]}).to_excel(
                path, index=False, engine="openpyxl"
            )

            preview = analyze_spreadsheet(path, CleaningOptions())

        self.assertEqual(preview.original.rows, 2)
        self.assertEqual(preview.estimated_metrics.duplicates_removed, 1)


if __name__ == "__main__":
    unittest.main()
