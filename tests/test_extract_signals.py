from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import helpers

extract = helpers.load_script("extract_signals")


class ExtractTests(unittest.TestCase):
    def test_utf8_rtl_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "signals.json"
            code, stdout, _ = helpers.run(extract, ["--input", str(helpers.FIXTURES / "utf8_rtl.html"), "--out", str(out)])
            self.assertEqual(code, 0, stdout)
            record = json.loads(out.read_text(encoding="utf-8"))[0]
        self.assertEqual(record["lang"], "ar")
        self.assertEqual(record["encoding"], "utf-8")
        self.assertEqual(record["h1"], "تقويم شفاف مع خطة علاج مكتوبة قبل الدفع")
        self.assertEqual(record["subtitle_candidate"], "أشعة بانوراما وفحص في الزيارة نفسها.")
        self.assertIn("احجز موعداً", record["ctas"])
        self.assertIn("اطلب عرض سعر", record["ctas"])
        self.assertIn("إرسال", record["ctas"])
        self.assertIn("الخدمات", record["nav"])
        self.assertNotIn("should not be captured", record["all_h1"])
        self.assertEqual(record["h2"], ["الخدمات", "لماذا نحن"])
        self.assertEqual(record["extraction_quality"], "high")

    def test_js_slider_hero_is_low_quality(self) -> None:
        code, stdout, _ = helpers.run(extract, ["--input", str(helpers.FIXTURES / "slider_js.html")])
        self.assertEqual(code, 0)
        record = json.loads(stdout)[0]
        self.assertEqual(record["h1"], "")
        self.assertEqual(record["extraction_quality"], "low")
        self.assertIn("hero_likely_js_or_image", record["flags"])
        self.assertIn("no_h1", record["flags"])

    def test_windows_1254_turkish_page(self) -> None:
        html = (
            '<html lang="tr"><head><meta charset="windows-1254"><title>Plastik Enjeksiyon Üreticisi</title>'
            '<meta name="description" content="Plastik enjeksiyon kalıp ve seri üretim."></head>'
            "<body><h1>Gıdaya uygun plastik enjeksiyon üreticisi</h1><h2>Ürünler</h2><h2>Sertifikalar</h2>"
            '<a class="btn" href="/teklif">Teklif Al</a></body></html>'
        )
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "tr.html"
            page.write_bytes(html.encode("windows-1254"))
            code, stdout, _ = helpers.run(extract, ["--input", str(page)])
        record = json.loads(stdout)[0]
        self.assertEqual(code, 0)
        self.assertEqual(record["encoding"], "windows-1254")
        self.assertEqual(record["h1"], "Gıdaya uygun plastik enjeksiyon üreticisi")
        self.assertIn("Teklif Al", record["ctas"])
        self.assertEqual(record["extraction_quality"], "high")

    def test_gbk_chinese_page_with_hint(self) -> None:
        html = (
            '<html lang="zh-CN"><head><title>电缆制造商</title>'
            '<meta name="description" content="控制电缆与电力电缆。"></head>'
            "<body><h1>低烟无卤控制电缆制造商</h1><h2>产品</h2><h2>资质</h2><button>获取报价</button></body></html>"
        )
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "zh.html"
            page.write_bytes(html.encode("gb18030"))
            code, stdout, _ = helpers.run(extract, ["--input", str(page), "--charset-hint", "gb18030"])
        record = json.loads(stdout)[0]
        self.assertEqual(code, 0)
        self.assertEqual(record["h1"], "低烟无卤控制电缆制造商")
        self.assertIn("获取报价", record["ctas"])

    def test_headline_split_into_elements_keeps_word_spaces(self) -> None:
        html = (
            "<html lang='en'><body>"
            "<h1><span>Plan</span><span>first.</span><br><span>Pay</span><span>later.</span></h1>"
            "<h2><span>G</span><span>r</span><span>o</span><span>w</span></h2>"
            "<h3>We <strong>ship</strong> in <em>three</em> weeks.</h3>"
            "</body></html>"
        )
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "split.html"
            page.write_text(html, encoding="utf-8")
            code, stdout, _ = helpers.run(extract, ["--input", str(page)])
        self.assertEqual(code, 0, stdout)
        record = json.loads(stdout)[0]
        self.assertEqual(record["h1"], "Plan first. Pay later.")
        self.assertEqual(record["h2"], ["Grow"])
        self.assertEqual(record["h3"], ["We ship in three weeks."])

    def test_refuses_non_public_urls(self) -> None:
        for url in ("http://localhost/", "http://127.0.0.1:8080/", "http://10.0.0.5/", "http://169.254.169.254/latest/", "ftp://example.com/", "file:///etc/passwd"):
            with self.assertRaises(ValueError, msg=url):
                extract.check_url_is_public(url)

    def test_missing_file_fails(self) -> None:
        code, _, stderr = helpers.run(extract, ["--input", "does-not-exist.html"])
        self.assertEqual(code, 1)
        self.assertIn("not found", stderr)


if __name__ == "__main__":
    unittest.main()
