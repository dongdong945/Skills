"""生成器的 CLI 行为检查；所有图像和报告仅写入临时目录。"""

from copy import deepcopy
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image


SCRIPT = Path(__file__).with_name("build_comparison.py")


class ReportParser(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.images, self.rows, self.words = [], [], []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "img" and attrs.get("src"):
            self.images.append(attrs)
        if tag == "section":
            self.rows.append(attrs)

    def handle_data(self, value):
        self.words.append(value)


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = self.root / "manifest.json"
        self.output = self.root / "report/index.html"
        self.image = self.root / "actual-source.png"
        Image.new("RGBA", (24, 48), (20, 80, 140, 180)).save(self.image)
        self.base = {
            "title": "UI Report", "scope": "Settings 与 History",
            "columns": [{"id": "design", "label": "Figma", "viewport": [320, 640]}, {"id": "phone", "label": "用户指定设备", "viewport": [320, 640]}],
            "rows": [{"key": "settings-first", "title": "设置", "group": "Settings", "state": "empty", "status": "unreviewed", "cells": {"design": {"path": self.image.name, "source": "figma"}, "phone": {"path": self.image.name, "source": "preview", "note": "仅用于生成器单元检查"}}}],
        }

    def run_cli(self, data, *options):
        self.manifest.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return subprocess.run([sys.executable, str(SCRIPT), str(self.manifest), "--output", str(self.output), *options], capture_output=True, text=True)

    def test_portable_lossless_output_and_order(self):
        data = deepcopy(self.base)
        other = deepcopy(data["rows"][0])
        other.update(key="history-second", title="历史", group="History", state="content")
        data["rows"].append(other)
        original = self.image.read_bytes()
        result = self.run_cli(data)
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = ReportParser(self.output.read_text())
        self.assertEqual([row["id"] for row in parsed.rows], ["row-settings-first", "row-history-second"])
        self.assertEqual([row["data-status"] for row in parsed.rows], ["unreviewed", "unreviewed"])
        self.assertEqual(len(parsed.images), 4)
        paths = {entry["src"] for entry in parsed.images}
        self.assertEqual(len(paths), 1)
        for relative in paths:
            self.assertFalse(Path(relative).is_absolute())
            self.assertEqual((self.output.parent / relative).read_bytes(), original)
        self.assertEqual(self.image.read_bytes(), original)
        self.assertEqual(json.loads(self.manifest.read_text()), data)

    def test_custom_columns_and_explicit_missing(self):
        data = deepcopy(self.base)
        data["columns"].extend([{"id": "tablet", "label": "平板横屏", "viewport": [1024, 768]}, {"id": "other", "label": "另一个设备", "viewport": [430, 932]}])
        data["rows"][0]["cells"].update(tablet={"missing": "尚未采样"}, other={"missing": "目标不可用"})
        result = self.run_cli(data)
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = ReportParser(self.output.read_text())
        self.assertEqual(len(parsed.images), 2)
        words = "".join(parsed.words)
        self.assertIn("尚未采样", words)
        self.assertIn("目标不可用", words)
        self.assertIn("平板横屏", words)
        self.assertNotIn("iPhone SE", words)

    def test_check_is_read_only_and_build_is_repeatable(self):
        result = self.run_cli(self.base, "--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.output.parent.exists())
        self.assertEqual(self.run_cli(self.base).returncode, 0)
        before = {str(p.relative_to(self.output.parent)): sha256(p.read_bytes()).hexdigest() for p in self.output.parent.rglob("*") if p.is_file()}
        self.assertEqual(self.run_cli(self.base).returncode, 0)
        after = {str(p.relative_to(self.output.parent)): sha256(p.read_bytes()).hexdigest() for p in self.output.parent.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_invalid_inputs_do_not_create_partial_report(self):
        variants = []
        missing = deepcopy(self.base)
        missing["rows"][0]["cells"]["phone"]["path"] = "not-found.png"
        variants.append(missing)
        duplicate = deepcopy(self.base)
        duplicate["rows"].append(deepcopy(duplicate["rows"][0]))
        variants.append(duplicate)
        unlisted = deepcopy(self.base)
        del unlisted["rows"][0]["cells"]["phone"]
        variants.append(unlisted)
        falsely_verified = deepcopy(self.base)
        falsely_verified["rows"][0]["status"] = "verified"
        falsely_verified["rows"][0]["cells"]["phone"] = {"missing": "无截图"}
        variants.append(falsely_verified)
        invalid_url = deepcopy(self.base)
        invalid_url["rows"][0]["figma_url"] = "javascript:alert(1)"
        variants.append(invalid_url)
        for data in variants:
            with self.subTest(data=data):
                self.assertEqual(self.run_cli(data).returncode, 2)
                self.assertFalse(self.output.parent.exists())

    def test_truncated_png_is_not_accepted_as_image_evidence(self):
        self.image.write_bytes(self.image.read_bytes()[:33])
        result = self.run_cli(self.base)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.output.parent.exists())

    def test_user_text_cannot_change_report_markup(self):
        data = deepcopy(self.base)
        content = '</script><img src="injected" onerror="alert(1)"> @@ROWS@@ & "quoted"'
        data["title"] = content
        data["rows"][0]["title"] = content
        data["rows"][0]["note"] = content
        self.assertEqual(self.run_cli(data).returncode, 0)
        parsed = ReportParser(self.output.read_text())
        self.assertEqual(len(parsed.images), 2)
        self.assertIn(content, "".join(parsed.words))
        self.assertEqual(len(parsed.rows), 1)


if __name__ == "__main__":
    unittest.main()
