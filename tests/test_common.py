from __future__ import annotations

import unittest

import helpers

mnc = helpers.load_script("mnc_common")


class FrontMatterTests(unittest.TestCase):
    def test_parses_scalars_and_lists(self) -> None:
        text = "---\nasset_id: x\nrevision: 2\nclaim_refs:\n  - a\n  - b\ntags: [p, q]\nempty:\n---\n## h1\nHello\n"
        meta, body = mnc.parse_front_matter(text)
        self.assertEqual(meta["asset_id"], "x")
        self.assertEqual(meta["revision"], 2)
        self.assertEqual(meta["claim_refs"], ["a", "b"])
        self.assertEqual(meta["tags"], ["p", "q"])
        self.assertIsNone(meta["empty"])
        self.assertEqual(mnc.parse_fields(body)["h1"], "Hello")

    def test_no_front_matter(self) -> None:
        meta, body = mnc.parse_front_matter("plain text")
        self.assertEqual(meta, {})
        self.assertEqual(body, "plain text")

    def test_round_trip(self) -> None:
        data = {"a": "x", "b": ["1", "2"], "c": None, "d": True}
        again = mnc.parse_simple_yaml(mnc.dump_simple_yaml(data))
        self.assertEqual(again["a"], "x")
        self.assertEqual(again["b"], [1, 2])
        self.assertIsNone(again["c"])
        self.assertTrue(again["d"])


class TermMatchingTests(unittest.TestCase):
    def test_arabic_prefix_and_variants(self) -> None:
        text = mnc.normalize_text("والتقويم الشفاف مناسب، وبأعلى معايير الجودة")
        self.assertTrue(mnc.contains_term(text, "تقويم شفاف"))
        self.assertTrue(mnc.contains_term(text, "أعلى معايير الجودة"))
        self.assertTrue(mnc.contains_term(text, "اعلي معايير الجوده"))

    def test_latin_word_boundary(self) -> None:
        text = mnc.normalize_text("We deliver in three weeks. Delivery is tracked.")
        self.assertTrue(mnc.contains_term(text, "deliver"))
        self.assertFalse(mnc.contains_term(text, "liver"))
        self.assertTrue(mnc.contains_term(text, "Three Weeks"))

    def test_cjk_substring(self) -> None:
        text = mnc.normalize_text("我们提供电缆解决方案")
        self.assertTrue(mnc.contains_term(text, "解决方案"))
        self.assertFalse(mnc.contains_term(text, "光缆"))

    def test_locale_id(self) -> None:
        self.assertTrue(mnc.is_locale_id("en-us"))
        self.assertTrue(mnc.is_locale_id("zh-cn"))
        self.assertFalse(mnc.is_locale_id("en"))
        self.assertFalse(mnc.is_locale_id("EN-US"))


if __name__ == "__main__":
    unittest.main()
