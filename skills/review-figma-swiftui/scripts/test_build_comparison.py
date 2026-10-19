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
        self.output = self.root / "output/ui-review/index.html"
        self.image = self.root / "actual-source.png"
        Image.new("RGBA", (24, 48), (20, 80, 140, 180)).save(self.image)
        self.base = {
            "title": "UI Report", "scope": "Settings 与 History",
            "columns": [{"id": "design", "label": "Figma", "viewport": [320, 640]}, {"id": "phone", "label": "用户指定设备", "viewport": [320, 640]}],
            "rows": [{"key": "settings-first", "title": "设置", "group": "Settings", "state": "empty", "status": "unreviewed", "cells": {"design": {"path": self.image.name, "source": "figma"}, "phone": {"path": self.image.name, "source": "preview", "note": "仅用于生成器单元检查"}}}],
        }

    def run_cli(self, data, *options):
        self.manifest.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return subprocess.run([sys.executable, str(SCRIPT), str(self.manifest), "--project-root", str(self.root), *options], capture_output=True, text=True)

    def registry(self):
        return json.loads(self.output.with_name("manifest.json").read_text())

    def snapshot(self):
        return {str(p.relative_to(self.output.parent)): sha256(p.read_bytes()).hexdigest() for p in self.output.parent.rglob("*") if p.is_file()}

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

    def test_modules_accumulate_and_survive_deleted_source_images(self):
        self.assertEqual(self.run_cli(self.base).returncode, 0)
        settings = self.registry()["rows"][0]
        self.image.unlink()
        other = self.root / "history.png"
        Image.new("RGB", (20, 30), "green").save(other)
        data = deepcopy(self.base)
        data["rows"][0].update(key="history-first", title="历史", group="History")
        for cell in data["rows"][0]["cells"].values():
            cell["path"] = other.name
        self.assertEqual(self.run_cli(data).returncode, 0)
        registry = self.registry()
        self.assertEqual([r["group"] for r in registry["rows"]], ["Settings", "History"])
        self.assertEqual(registry["rows"][0], settings)
        for row in registry["rows"]:
            for cell in row["cells"].values():
                self.assertTrue((self.output.parent / cell["path"]).is_file())
                self.assertFalse(Path(cell["path"]).is_absolute())

    def test_refresh_keeps_other_modules_and_previous_states(self):
        data = deepcopy(self.base)
        other = deepcopy(data["rows"][0])
        other.update(key="history-first", title="历史", group="History")
        data["rows"].append(other)
        self.assertEqual(self.run_cli(data).returncode, 0)
        history = deepcopy(self.registry()["rows"][1])
        update = deepcopy(self.base)
        update["rows"][0]["note"] = "本轮修改"
        new = deepcopy(update["rows"][0])
        new.update(key="settings-bottom", state="bottom")
        update["rows"].append(new)
        self.assertEqual(self.run_cli(update).returncode, 0)
        rows = self.registry()["rows"]
        self.assertEqual([r["key"] for r in rows], ["settings-first", "settings-bottom", "history-first"])
        self.assertEqual(rows[-1], history)
        self.assertEqual(rows[0]["note"], "本轮修改")
        partial = deepcopy(self.base)
        partial["rows"][0] = new
        self.assertEqual(self.run_cli(partial).returncode, 0)
        self.assertEqual(len(self.registry()["rows"]), 3)

    def test_cross_module_key_and_column_conflicts_preserve_registry(self):
        self.assertEqual(self.run_cli(self.base).returncode, 0)
        before = self.snapshot()
        data = deepcopy(self.base)
        data["rows"][0]["group"] = "Another Module"
        self.assertEqual(self.run_cli(data).returncode, 2)
        self.assertEqual(before, self.snapshot())
        data = deepcopy(self.base)
        data["columns"][1]["label"] = "Different Device"
        self.assertEqual(self.run_cli(data).returncode, 2)
        self.assertEqual(before, self.snapshot())

    def test_added_device_is_an_explicit_gap_for_previous_modules(self):
        data = deepcopy(self.base)
        data["rows"][0]["status"] = "verified"
        self.assertEqual(self.run_cli(data).returncode, 0)
        incoming = deepcopy(self.base)
        incoming["columns"].append({"id": "tablet", "label": "平板", "viewport": [768, 1024]})
        incoming["rows"][0].update(key="history-first", group="History")
        incoming["rows"][0]["cells"]["tablet"] = {"path": self.image.name, "source": "runtime"}
        self.assertEqual(self.run_cli(incoming).returncode, 0)
        old = self.registry()["rows"][0]
        self.assertEqual(old["group"], "Settings")
        self.assertEqual(old["status"], "unreviewed")
        self.assertIn("missing", old["cells"]["tablet"])
        self.assertEqual(len(old["cells"]), 3)

    def test_refresh_does_not_reuse_stale_device_evidence(self):
        data = deepcopy(self.base)
        data["columns"].append({"id": "tablet", "label": "平板", "viewport": [768, 1024]})
        data["rows"][0]["cells"]["tablet"] = {"path": self.image.name, "source": "runtime"}
        self.assertEqual(self.run_cli(data).returncode, 0)
        update = deepcopy(self.base)
        update["rows"][0]["status"] = "verified"
        self.assertEqual(self.run_cli(update).returncode, 0)
        row = self.registry()["rows"][0]
        self.assertIn("missing", row["cells"]["tablet"])
        self.assertEqual(row["status"], "unreviewed")

    def test_registry_rebuild_is_portable_and_repeatable(self):
        self.base["boundaries"] = ["隔离图片"]
        self.assertEqual(self.run_cli(self.base).returncode, 0)
        before = self.snapshot()
        self.image.unlink()
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.output.with_name("manifest.json")), "--project-root", str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_concurrent_module_updates_do_not_lose_rows(self):
        first = self.root / "settings.json"
        first.write_text(json.dumps(self.base))
        other = deepcopy(self.base)
        other["rows"][0].update(key="history-first", group="History")
        second = self.root / "history.json"
        second.write_text(json.dumps(other))
        processes = [subprocess.Popen([sys.executable, str(SCRIPT), str(path), "--project-root", str(self.root)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for path in (first, second)]
        for process in processes:
            _, error = process.communicate(timeout=20)
            self.assertEqual(process.returncode, 0, error)
        self.assertEqual({row["group"] for row in self.registry()["rows"]}, {"Settings", "History"})


if __name__ == "__main__":
    unittest.main()
