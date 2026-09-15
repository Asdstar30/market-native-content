from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import helpers

init = helpers.load_script("init_library")


class InitLibraryTests(unittest.TestCase):
    def test_scaffolds_locales_and_injects_instructions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "CLAUDE.md").write_text("# Project\n", encoding="utf-8")
            code, stdout, stderr = helpers.run(init, ["--project", str(project), "--locales", "en-us,de-de", "--name", "Demo Co"])
            self.assertEqual(code, 0, stderr)
            lib = project / "market-content-library"
            self.assertTrue((lib / "core" / "claims.json").exists())
            self.assertTrue((lib / "channels" / "web" / "limits.json").exists())
            self.assertFalse((lib / "markets" / "_template").exists())
            for locale in ("en-us", "de-de"):
                glossary = json.loads((lib / "markets" / locale / "glossary.json").read_text(encoding="utf-8"))
                self.assertEqual(glossary["locale"], locale)
                banned = (lib / "markets" / locale / "banned.txt").read_text(encoding="utf-8")
                self.assertIn("Seeded from generic-", banned)
            locales = json.loads((lib / "locales.json").read_text(encoding="utf-8"))
            self.assertEqual([entry["id"] for entry in locales["locales"]], ["en-us", "de-de"])
            self.assertIn("Demo Co", (lib / "README.md").read_text(encoding="utf-8"))
            claude_md = (project / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertIn("market-native-core:start", claude_md)
            self.assertIn("market-content-library/PROJECT-INSTRUCTIONS.md", claude_md)

            # Second run must not overwrite or duplicate anything.
            (lib / "core" / "company.json").write_text('{"name": "edited"}', encoding="utf-8")
            code, stdout, _ = helpers.run(init, ["--project", str(project), "--locales", "en-us"])
            self.assertEqual(code, 0)
            self.assertIn("skip (exists)", stdout)
            self.assertEqual((lib / "core" / "company.json").read_text(encoding="utf-8"), '{"name": "edited"}')
            self.assertEqual((project / "CLAUDE.md").read_text(encoding="utf-8").count("market-native-core:start"), 1)

    def test_rejects_bare_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, _, stderr = helpers.run(init, ["--project", tmp, "--locales", "en"])
        self.assertEqual(code, 2)
        self.assertIn("language-market", stderr)


if __name__ == "__main__":
    unittest.main()
