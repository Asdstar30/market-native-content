from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import helpers

build = helpers.load_script("build_context")

BASE = ["--library", str(helpers.EXAMPLE_LIB), "--locale", "en-us", "--channel", "web", "--page", "product", "--audience", "patient"]


class BuildContextTests(unittest.TestCase):
    def build_pack(self, extra: list[str]) -> tuple[dict, str, str]:
        with tempfile.TemporaryDirectory() as tmp:
            code, stdout, stderr = helpers.run(build, BASE + extra + ["--out-dir", tmp])
            self.assertEqual(code, 0, stderr)
            json_files = list(Path(tmp).glob("cp-*.json"))
            md_files = list(Path(tmp).glob("cp-*.md"))
            self.assertEqual(len(json_files), 1)
            self.assertEqual(len(md_files), 1)
            pack = json.loads(json_files[0].read_text(encoding="utf-8"))
            markdown = md_files[0].read_text(encoding="utf-8")
        return pack, markdown, stdout

    def test_filters_claims_by_channel_product_and_expiry(self) -> None:
        pack, markdown, _ = self.build_pack(["--product-id", "clear-aligners"])
        ids = {c["claim_id"] for c in pack["claims"]}
        self.assertEqual(ids, {"claim-same-day-scan-001", "claim-written-plan-002", "claim-first-visit-45min-003"})
        self.assertIn("expired", pack["claims_excluded"])
        self.assertIn("not eligible for channel", pack["claims_excluded"])
        self.assertIn("claim-written-plan-002", markdown)
        self.assertNotIn("claim-implant-warranty-004", markdown)

    def test_terms_are_split_by_status_and_type(self) -> None:
        pack, markdown, _ = self.build_pack(["--product-id", "clear-aligners"])
        required = {t["term"] for t in pack["required_terms"]}
        self.assertIn("clear aligners", required)
        self.assertIn("panoramic X-ray", required)
        self.assertNotIn("dental implants", required)
        self.assertEqual(pack["blocked_terms"], ["porcelain veneers"])
        self.assertIn("aligner trays", pack["forbidden_terms"])
        self.assertIn("hollywood smile", pack["forbidden_terms"])
        self.assertIn("seamless", pack["forbidden_terms"])
        self.assertIn("Blocked technical/regulatory terms", markdown)

    def test_pack_is_compact_and_reports_pattern(self) -> None:
        pack, markdown, stdout = self.build_pack([])
        self.assertLess(len(markdown), 9000, "pack should stay around two pages")
        self.assertEqual(pack["competitors"]["count"], 5)
        self.assertIn("No prices", markdown)
        self.assertIn("approx tokens", stdout)
        self.assertTrue(pack["pack_id"].startswith("cp-"))
        self.assertIn("en-us-web-product", pack["pack_id"])

    def test_unknown_locale_fails_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            args = [a if a != "en-us" else "en-gb" for a in BASE] + ["--out-dir", tmp]
            code, _, stderr = helpers.run(build, args)
        self.assertEqual(code, 1)
        self.assertIn("en-gb", stderr)
        self.assertIn("known: en-us", stderr)

    def test_bare_language_rejected(self) -> None:
        args = [a if a != "en-us" else "en" for a in BASE]
        code, _, stderr = helpers.run(build, args)
        self.assertEqual(code, 2)
        self.assertIn("language-market", stderr)


if __name__ == "__main__":
    unittest.main()
