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
        self.images, self.rows, self.words, self.links, self.figures = [], [], [], [], []
        self.selects, self.active_select, self.active_option = {}, None, None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "img" and attrs.get("src"):
            self.images.append(attrs)
        if tag == "section":
            self.rows.append(attrs)
        if tag == "a":
            self.links.append(attrs)
        if tag == "figure":
            self.figures.append(attrs)
        if tag == "select":
            self.active_select = attrs.get("id")
            self.selects[self.active_select] = []
        if tag == "option" and self.active_select:
            self.active_option = attrs | {"text": ""}
            self.selects[self.active_select].append(self.active_option)

    def handle_endtag(self, tag):
        if tag == "select":
            self.active_select = None
        if tag == "option":
            self.active_option = None

    def handle_data(self, value):
        self.words.append(value)
        if self.active_option is not None:
            self.active_option["text"] += value


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

    def test_localized_states_keep_independent_evidence_and_links(self):
        data = deepcopy(self.base)
        data["locale_labels"] = {"en": "English", "zh_hans": "简体中文"}
        data["rows"][0]["locale"] = "EN"
        chinese = deepcopy(data["rows"][0])
        chinese.update(key="settings-first-zh-Hans", locale="zh_hans")
        chinese["cells"]["design"]["locale"] = "en"
        data["rows"].append(chinese)
        self.assertEqual(self.run_cli(data).returncode, 0)
        rows = self.registry()["rows"]
        self.assertEqual([row["locale"] for row in rows], ["en", "zh-Hans"])
        self.assertEqual(rows[1]["cells"]["design"]["locale"], "en")
        parsed = ReportParser(self.output.read_text())
        self.assertEqual([row["data-locale"] for row in parsed.rows], ["en", "zh-Hans"])
        self.assertEqual([(option.get("value"), option["text"]) for option in parsed.selects["locale"]],
                         [("", "全部语言"), ("en", "English (en)"), ("zh-Hans", "简体中文 (zh-Hans)")])
        links = [link["href"] for link in parsed.links if link.get("class") == "anchor"]
        self.assertEqual(links, ["?module=Settings&locale=en&device=phone#row-settings-first", "?module=Settings&locale=zh-Hans&device=phone#row-settings-first-zh-Hans"])
        self.assertEqual(json.loads(self.manifest.read_text()), data)

    def test_legacy_language_is_unlabeled_and_labels_survive_module_updates(self):
        self.assertEqual(self.run_cli(self.base).returncode, 0)
        legacy = self.registry()["rows"][0]
        update = deepcopy(self.base)
        update["locale_labels"] = {"pt_BR": "Português do Brasil"}
        update["rows"][0].update(key="history-pt-BR", group="History", locale="pt_br")
        self.assertEqual(self.run_cli(update).returncode, 0)
        registry = self.registry()
        self.assertEqual(registry["rows"][0], legacy)
        self.assertEqual(registry["rows"][1]["locale"], "pt-BR")
        self.assertEqual(registry["locale_labels"], {"pt-BR": "Português do Brasil"})
        parsed = ReportParser(self.output.read_text())
        self.assertEqual(parsed.rows[0]["data-locale"], "")
        self.assertIn({"value": "__unlabeled__", "text": "未标注语言"}, parsed.selects["locale"])
        self.assertEqual(self.run_cli(self.base).returncode, 0)
        self.assertEqual(self.registry()["locale_labels"], registry["locale_labels"])
        self.assertEqual(self.registry()["rows"][1], registry["rows"][1])

    def test_other_language_cannot_overwrite_existing_state(self):
        self.base["rows"][0]["locale"] = "en"
        self.assertEqual(self.run_cli(self.base).returncode, 0)
        before = self.snapshot()
        update = deepcopy(self.base)
        update["rows"][0]["locale"] = "fr"
        result = self.run_cli(update)
        self.assertEqual(result.returncode, 2)
        self.assertIn("另一语言请使用独立 key", result.stderr)
        self.assertEqual(self.snapshot(), before)
        del update["rows"][0]["locale"]
        result = self.run_cli(update)
        self.assertEqual(result.returncode, 2)
        self.assertIn("更新时保留 locale", result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_invalid_locales_do_not_change_existing_report(self):
        self.assertEqual(self.run_cli(self.base).returncode, 0)
        before = self.snapshot()
        variants = []
        for value in ["", "<script>", ["en", "fr"]]:
            invalid = deepcopy(self.base)
            invalid["rows"][0]["locale"] = value
            variants.append(invalid)
        invalid = deepcopy(self.base)
        invalid["rows"][0]["cells"]["phone"]["locale"] = "en<script>"
        variants.append(invalid)
        for labels in [["en"], {"en": ""}, {"en_US": "English", "en-us": "Duplicate"}]:
            invalid = deepcopy(self.base)
            invalid["locale_labels"] = labels
            variants.append(invalid)
        for data in variants:
            with self.subTest(data=data):
                self.assertEqual(self.run_cli(data).returncode, 2)
                self.assertEqual(self.snapshot(), before)

    def test_language_labels_are_escaped_and_rebuild_is_lossless(self):
        self.base["locale_labels"] = {"en": '<img src="injected"> & English'}
        self.base["rows"][0]["locale"] = "en"
        self.assertEqual(self.run_cli(self.base).returncode, 0)
        parsed = ReportParser(self.output.read_text())
        self.assertEqual(len(parsed.images), 2)
        self.assertIn('<img src="injected"> & English (en)', "".join(parsed.words))
        before = self.snapshot()
        self.image.unlink()
        result = subprocess.run([sys.executable, str(SCRIPT), str(self.output.with_name("manifest.json")), "--project-root", str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_device_picker_defaults_to_iphone12_and_keeps_duo_evidence(self):
        data = deepcopy(self.base)
        data["columns"].extend([
            {"id": "duo-outer", "label": "iPhone Duo · 外屏", "viewport": [466, 678]},
            {"id": "duo-inner", "label": "iPhone Duo · 内屏", "viewport": [800, 600]},
            {"id": "iphone12", "label": "iPhone 12", "viewport": [390, 844]},
        ])
        cells = data["rows"][0]["cells"]
        cells["duo-outer"] = {"path": self.image.name, "source": "runtime", "note": "测试元数据，不是设备验收"}
        cells["duo-inner"] = {"missing": "未执行内屏采样"}
        cells["iphone12"] = deepcopy(cells["phone"])
        self.assertEqual(self.run_cli(data).returncode, 0)
        parsed = ReportParser(self.output.read_text())
        devices = parsed.selects["device"]
        self.assertEqual([option["value"] for option in devices], ["phone", "iphone-duo", "iphone12"])
        self.assertEqual(next(option["text"] for option in devices if option["value"] == "iphone-duo"), "iPhone Duo")
        self.assertEqual([option["value"] for option in devices if "selected" in option], ["iphone12"])
        self.assertEqual([figure["data-column"] for figure in parsed.figures if "hidden" not in figure], ["design", "iphone12"])
        row = self.registry()["rows"][0]
        self.assertEqual(set(row["cells"]), set(cells))
        self.assertEqual(row["cells"]["duo-outer"]["note"], cells["duo-outer"]["note"])
        self.assertEqual(row["cells"]["duo-inner"], cells["duo-inner"])

    def test_duo_outer_only_shows_three_poses_without_inventing_evidence(self):
        data = deepcopy(self.base)
        data["columns"][1] = {"id": "iphone-duo-outer", "label": "iPhone Duo · 外屏", "viewport": [466, 678]}
        row = data["rows"][0]
        row["cells"]["iphone-duo-outer"] = row["cells"].pop("phone")
        row["status"] = "verified"
        self.assertEqual(self.run_cli(data).returncode, 0)
        parsed = ReportParser(self.output.read_text())
        self.assertEqual([(option["value"], option["text"]) for option in parsed.selects["device"]], [("iphone-duo", "iPhone Duo")])
        self.assertEqual([figure["data-column"] for figure in parsed.figures if "hidden" not in figure],
                         ["design", "iphone-duo-outer", "iphone-duo-half-fold", "iphone-duo-inner"])
        self.assertEqual(len(parsed.images), 2)
        self.assertIn("2 个缺口", "".join(parsed.words))
        self.assertIn("未采集 · 尺寸待测量", "".join(parsed.words))
        self.assertEqual(parsed.rows[0]["data-status"], "unreviewed")
        self.assertEqual(set(self.registry()["rows"][0]["cells"]), {"design", "iphone-duo-outer"})
        self.assertEqual(self.registry()["rows"][0]["status"], "verified")

    def test_duo_poses_retain_separate_images_in_display_order(self):
        data = deepcopy(self.base)
        for name, color in [("inner", "red"), ("outer", "green"), ("half-fold", "blue")]:
            path = self.root / f"{name}.png"
            Image.new("RGB", (30, 40), color).save(path)
            data["columns"].append({"id": f"duo-{name}", "label": f"Duo {name}", "viewport": [30, 40]})
            data["rows"][0]["cells"][f"duo-{name}"] = {"path": path.name, "source": "runtime"}
        self.assertEqual(self.run_cli(data).returncode, 0)
        parsed = ReportParser(self.output.read_text())
        poses = [figure for figure in parsed.figures if figure.get("data-device") == "iphone-duo"]
        self.assertEqual([figure["data-column"] for figure in poses], ["duo-outer", "duo-half-fold", "duo-inner"])
        self.assertEqual(len(parsed.images), 5)
        self.assertEqual(len({image["src"] for image in parsed.images}), 4)
        self.assertIn("0 个缺口", "".join(parsed.words))
        self.assertEqual(len(self.registry()["columns"]), 5)

    def test_duplicate_duo_pose_columns_fail_without_overwriting_evidence(self):
        data = deepcopy(self.base)
        for name in ["duo-outer", "iphone-duo-outer"]:
            data["columns"].append({"id": name, "label": name, "viewport": [466, 678]})
            data["rows"][0]["cells"][name] = {"path": self.image.name, "source": "runtime"}
        self.assertEqual(self.run_cli(data).returncode, 2)
        self.assertFalse(self.output.exists())

    def test_legacy_device_label_selects_iphone12_without_renaming_columns(self):
        data = deepcopy(self.base)
        data["columns"].append({"id": "reference", "label": "iPhone 12 · iOS 27", "viewport": [390, 844]})
        data["rows"][0]["cells"]["reference"] = deepcopy(data["rows"][0]["cells"]["phone"])
        self.assertEqual(self.run_cli(data).returncode, 0)
        parsed = ReportParser(self.output.read_text())
        self.assertEqual([option["value"] for option in parsed.selects["device"] if "selected" in option], ["reference"])
        self.assertEqual([column["id"] for column in self.registry()["columns"]], ["design", "phone", "reference"])

    def test_report_without_iphone12_uses_first_declared_device(self):
        data = deepcopy(self.base)
        data["columns"].append({"id": "pro", "label": "iPhone 12 Pro", "viewport": [390, 844]})
        data["rows"][0]["cells"]["pro"] = {"missing": "未采集"}
        self.assertEqual(self.run_cli(data).returncode, 0)
        parsed = ReportParser(self.output.read_text())
        self.assertEqual([option["value"] for option in parsed.selects["device"] if "selected" in option], ["phone"])
        self.assertEqual([figure["data-column"] for figure in parsed.figures if "hidden" not in figure], ["design", "phone"])
        self.assertEqual(len(self.registry()["columns"]), 3)


if __name__ == "__main__":
    unittest.main()
