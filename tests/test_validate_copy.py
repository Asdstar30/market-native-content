from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import helpers

validate = helpers.load_script("validate_copy")

COPY = helpers.EXAMPLE_LIB / "channels" / "web" / "copy" / "en-us" / "product--clear-aligners--patient.md"
LIB_ARGS = ["--library", str(helpers.EXAMPLE_LIB)]


class ValidateTests(unittest.TestCase):
    def test_example_copy_passes(self) -> None:
        code, stdout, stderr = helpers.run(validate, ["--copy", str(COPY)] + LIB_ARGS)
        self.assertEqual(code, 0, stdout + stderr)
        self.assertIn("result: PASS", stdout)
        self.assertNotIn("number '", stdout)
        self.assertIn("approved terms used", stdout)

    def test_bad_copy_fails_with_specific_errors(self) -> None:
        text = COPY.read_text(encoding="utf-8")
        bad = (
            text.replace(
                "Clear aligners with a written plan before you pay",
                "Aligner trays for your Hollywood smile with seamless care and the latest technology in Denver",
            )
            .replace("  - claim-first-visit-45min-003", "  - claim-implant-warranty-004")
            .replace("decide at your own pace.", "decide at your own pace within 30 days.")
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.md"
            path.write_text(bad, encoding="utf-8")
            code, stdout, _ = helpers.run(validate, ["--copy", str(path)] + LIB_ARGS)
        self.assertEqual(code, 1)
        self.assertIn("result: FAIL", stdout)
        self.assertIn("forbidden term: 'aligner trays'", stdout)
        self.assertIn("forbidden term: 'hollywood smile'", stdout)
        self.assertIn("forbidden term: 'seamless'", stdout)
        self.assertIn("forbidden term: 'latest technology'", stdout)
        self.assertIn("claim-implant-warranty-004", stdout)
        self.assertRegex(stdout, r"field 'hero_title' is \d+ chars, limit 60")
        self.assertIn("number '30'", stdout)
        self.assertNotIn("number '1.'", stdout)

    def test_partial_scope_asset_does_not_warn_about_page_fields(self) -> None:
        text = COPY.read_text(encoding="utf-8").replace("content_scope: full-page", "content_scope: hero")
        head, _, _ = text.partition("## problem")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "hero.md"
            path.write_text(head, encoding="utf-8")
            code, stdout, _ = helpers.run(validate, ["--copy", str(path)] + LIB_ARGS)
        self.assertEqual(code, 0, stdout)
        self.assertNotIn("has a limit but is not in the asset", stdout)
        self.assertIn("not in this hero asset", stdout)

    def test_blocked_term_is_error(self) -> None:
        text = COPY.read_text(encoding="utf-8").replace("## specs\n", "## specs\nWe also offer porcelain veneers.\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "blocked.md"
            path.write_text(text, encoding="utf-8")
            code, stdout, _ = helpers.run(validate, ["--copy", str(path)] + LIB_ARGS)
        self.assertEqual(code, 1)
        self.assertIn("blocked term", stdout)

    def test_text_mode_against_banned_list(self) -> None:
        banned = helpers.REPO / "skills" / "market-native-core" / "references" / "banned" / "generic-en.txt"
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good.md"
            good.write_text("We ship in three weeks and publish the test report.", encoding="utf-8")
            bad = Path(tmp) / "bad.md"
            bad.write_text("Our seamless, cutting-edge solutions empower you.", encoding="utf-8")
            ok, _, _ = helpers.run(validate, ["--text", str(good), "--banned", str(banned)])
            fail, stdout, _ = helpers.run(validate, ["--text", str(bad), "--banned", str(banned)])
        self.assertEqual(ok, 0)
        self.assertEqual(fail, 1)
        self.assertIn("'seamless'", stdout)
        self.assertIn("'cutting-edge'", stdout)
        self.assertIn("'empower'", stdout)

    def test_revalidate_flags_assets_with_changed_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lib = Path(tmp) / "lib"
            shutil.copytree(helpers.EXAMPLE_LIB, lib)
            asset = lib / "channels" / "web" / "copy" / "en-us" / "product--clear-aligners--patient.md"
            asset.write_text(asset.read_text(encoding="utf-8").replace("status: draft", "status: approved"), encoding="utf-8")
            claims = lib / "core" / "claims.json"
            claims.write_text(claims.read_text(encoding="utf-8").replace('"expires": "2027-03-01"', '"expires": "2020-01-01"'), encoding="utf-8")
            code, stdout, _ = helpers.run(validate, ["--library", str(lib), "--revalidate"])
            updated = asset.read_text(encoding="utf-8")
        self.assertEqual(code, 0)
        self.assertIn("needs_revalidation", stdout)
        self.assertIn("status: needs_revalidation", updated)
        self.assertIn("claim-first-visit-45min-003", updated)
        self.assertIn("## hero_title", updated)


if __name__ == "__main__":
    unittest.main()
