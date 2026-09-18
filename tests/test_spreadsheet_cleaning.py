from __future__ import annotations

import unittest

import pandas as pd

from services.spreadsheet_cleaning import CleaningOptions, apply_cleaning


class SpreadsheetCleaningTests(unittest.TestCase):
    def test_apply_cleaning_returns_exact_metrics(self) -> None:
        frame = pd.DataFrame(
            {
                " Nome ": [" Ana ", "Ana", None, "Bia"],
                "Vazia": [None, None, None, None],
            }
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

    def test_ignore_case_removes_text_duplicates(self) -> None:
        frame = pd.DataFrame({"Nome": ["Ana", "ANA", "Bia"]})
        options = CleaningOptions(ignore_case_on_duplicates=True)

        cleaned, metrics = apply_cleaning(frame, options)

        self.assertEqual(cleaned["Nome"].tolist(), ["Ana", "Bia"])
        self.assertEqual(metrics.duplicates_removed, 1)


if __name__ == "__main__":
    unittest.main()
