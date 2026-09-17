from __future__ import annotations

import unittest
import tempfile
import time
from pathlib import Path

import pandas as pd

from modules.spreadsheets.clean import CleanSpreadsheetScreen
from ui.app import App


class NavigationSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = App()
        cls.app.withdraw()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.app.destroy()

    def setUp(self) -> None:
        self.app.navigate("clean_spreadsheet")
        self.app.update_idletasks()

    def test_clean_spreadsheet_screen_opens(self) -> None:
        self.assertIsInstance(self.app._current_screen, CleanSpreadsheetScreen)

    def test_clean_screen_starts_without_ready_analysis(self) -> None:
        screen = self.app._current_screen
        self.assertFalse(screen._analysis_ready)
        self.assertEqual(screen.run_btn.cget("state"), "disabled")
        self.assertIsNotNone(screen.profile_panel)

    def test_saved_routine_triggers_background_analysis(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "clientes.xlsx"
            pd.DataFrame({"Nome": [" Ana ", "Ana"]}).to_excel(
                source, index=False, engine="openpyxl"
            )
            screen = self.app._current_screen

            screen.apply_preset(
                {"selected_file": str(source), "options": {"remove_duplicates": True}}
            )
            deadline = time.monotonic() + 5
            while not screen._analysis_ready and time.monotonic() < deadline:
                self.app.update()
                time.sleep(0.05)

            self.assertTrue(screen._analysis_ready)
            self.assertEqual(screen.run_btn.cget("state"), "normal")
            self.assertEqual(
                screen._current_preview.estimated_metrics.duplicates_removed, 1
            )


if __name__ == "__main__":
    unittest.main()
