from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
