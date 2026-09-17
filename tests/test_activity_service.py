from __future__ import annotations

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


if __name__ == "__main__":
    unittest.main()
