from __future__ import annotations

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
            self.assertIn("Duplicados removidos", content)
            self.assertIn("Automatech", content)

    def test_report_contains_only_aggregate_profile_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            folder = Path(temporary_directory)
            options = CleaningOptions()
            secret_value = "SEGREDO-QUE-NAO-DEVE-APARECER"
            frame = pd.DataFrame({"Cliente": [secret_value]})
            preview = simulate_cleaning(frame, "entrada.xlsx", options)
            _, metrics = apply_cleaning(frame, options)

            generated = write_cleaning_report(
                preview,
                metrics,
                options,
                Path("entrada.xlsx"),
                folder / "saida.xlsx",
                folder / "saida_relatorio.html",
            )

            content = generated.read_text(encoding="utf-8")
            self.assertNotIn(secret_value, content)
            self.assertIn("Cliente", content)


if __name__ == "__main__":
    unittest.main()
