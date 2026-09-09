from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from services.excel_service import (
    clean_spreadsheet,
    merge_spreadsheets,
    split_spreadsheet,
)
from services.file_service import organize_folder
from utils.errors import IncompatibleColumnsError, ValidationError
from utils.paths import sanitize_filename


class SpreadsheetServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.folder = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _spreadsheet(self, name: str, data: dict[str, list[object]]) -> Path:
        path = self.folder / name
        pd.DataFrame(data).to_excel(path, index=False, engine="openpyxl")
        return path

    def test_merge_reorders_columns_and_keeps_all_rows(self) -> None:
        first = self._spreadsheet("a.xlsx", {"Nome": ["Ana"], "Valor": [1]})
        second = self._spreadsheet("b.xlsx", {"Valor": [2], "Nome": ["Bia"]})
        output = self.folder / "unificada.xlsx"

        rows = merge_spreadsheets([str(first), str(second)], output)

        result = pd.read_excel(output, engine="openpyxl")
        self.assertEqual(rows, 2)
        self.assertEqual(list(result.columns), ["Nome", "Valor"])
        self.assertEqual(result["Nome"].tolist(), ["Ana", "Bia"])

    def test_merge_rejects_incompatible_columns(self) -> None:
        first = self._spreadsheet("a.xlsx", {"Nome": ["Ana"]})
        second = self._spreadsheet("b.xlsx", {"Cliente": ["Bia"]})

        with self.assertRaises(IncompatibleColumnsError):
            merge_spreadsheets([str(first), str(second)], self.folder / "saida.xlsx")

    def test_output_never_overwrites_existing_file(self) -> None:
        first = self._spreadsheet("a.xlsx", {"Nome": ["Ana"]})
        second = self._spreadsheet("b.xlsx", {"Nome": ["Bia"]})
        output = self.folder / "saida.xlsx"
        output.write_bytes(b"conteudo-original")

        with self.assertRaises(ValidationError):
            merge_spreadsheets([str(first), str(second)], output)

        self.assertEqual(output.read_bytes(), b"conteudo-original")

    def test_clean_preserves_missing_values_and_trims_text(self) -> None:
        source = self._spreadsheet(
            "dados.xlsx",
            {" Nome ": [" Ana ", None, " Ana "], "Valor": [1, 2, 1]},
        )
        output = self.folder / "dados_limpos.xlsx"

        summary = clean_spreadsheet(source, output)

        result = pd.read_excel(output, engine="openpyxl")
        self.assertEqual(summary["duplicados_removidos"], 1)
        self.assertEqual(result["Nome"].iloc[0], "Ana")
        self.assertTrue(pd.isna(result["Nome"].iloc[1]))

    def test_split_generates_safe_unique_names(self) -> None:
        source = self._spreadsheet(
            "dados.xlsx",
            {"Equipe": ["Norte/Sul", "Norte/Sul", "Leste"], "Valor": [1, 2, 3]},
        )
        output = self.folder / "separadas"

        count = split_spreadsheet(str(source), "Equipe", output)

        self.assertEqual(count, 2)
        self.assertTrue((output / "Norte_Sul.xlsx").exists())
        self.assertTrue((output / "Leste.xlsx").exists())


class FileServiceTests(unittest.TestCase):
    def test_organizer_preserves_conflicting_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            folder = Path(temporary_directory)
            (folder / "foto.png").write_bytes(b"nova")
            destination = folder / "Imagens"
            destination.mkdir()
            (destination / "foto.png").write_bytes(b"existente")

            moved = organize_folder(folder)

            self.assertEqual(moved, {"Imagens": 1})
            self.assertEqual((destination / "foto.png").read_bytes(), b"existente")
            self.assertEqual((destination / "foto (1).png").read_bytes(), b"nova")


class PathTests(unittest.TestCase):
    def test_sanitize_filename_preserves_extension_when_truncated(self) -> None:
        result = sanitize_filename(f"{'a' * 300}.xlsx")
        self.assertLessEqual(len(result), 150)
        self.assertTrue(result.endswith(".xlsx"))


if __name__ == "__main__":
    unittest.main()
