#!/usr/bin/env python3
"""校验本地 UI 证据清单，生成可搬动的静态对比报告。需要 Pillow。"""

import argparse
from hashlib import sha256
from html import escape
from io import BytesIO
import json
import math
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

from PIL import Image


STATUSES = {
    "unreviewed": "待复查",
    "issue": "发现问题",
    "fixed": "已修复待复验",
    "verified": "视觉已复验",
    "blocked": "受阻",
}
SOURCES = {"figma": "Figma", "runtime": "原生运行", "preview": "Preview", "baseline": "历史基线"}
EXTENSIONS = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value, label):
    require(isinstance(value, str) and bool(value.strip()), f"{label} 需要非空字符串")
    return value.strip()


def identifier(value, label):
    value = text(value, label)
    require(re.fullmatch(r"[A-Za-z0-9_.-]+", value), f"{label} 仅使用字母、数字、点、下划线或连字符")
    return value


def viewport(value, label):
    require(isinstance(value, list) and len(value) == 2, f"{label} 需要 [width, height]")
    require(all(type(v) in (int, float) and math.isfinite(v) and v > 0 for v in value), f"{label} 尺寸必须为正数")
    return value


def load_manifest(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(data, dict), "清单顶层需要对象")
    for field in ("title", "scope"):
        data[field] = text(data.get(field), field)
    boundaries = data.setdefault("boundaries", [])
    require(isinstance(boundaries, list), "boundaries 需要字符串数组")
    for note in boundaries:
        text(note, "boundary")
    columns = data.get("columns")
    require(isinstance(columns, list) and len(columns) >= 2, "columns 至少包含参考及一个设备列")
    ids = set()
    for col in columns:
        require(isinstance(col, dict), "column 需要对象")
        col_id = identifier(col.get("id"), "column.id")
        col["id"] = col_id
        require(col_id not in ids, f"重复 column.id: {col_id}")
        ids.add(col_id)
        col["label"] = text(col.get("label"), "column.label")
        viewport(col.get("viewport"), "column.viewport")
    rows = data.get("rows")
    require(isinstance(rows, list) and bool(rows), "rows 需要非空数组")
    keys, files, blobs = set(), {}, {}
    for row in rows:
        require(isinstance(row, dict), "row 需要对象")
        key = identifier(row.get("key"), "row.key")
        row["key"] = key
        require(key not in keys, f"重复 row.key: {key}")
        keys.add(key)
        for field in ("title", "group", "state"):
            row[field] = text(row.get(field), f"{key}.{field}")
        require(row.get("status") in STATUSES, f"{key}.status 无效")
        for field in ("route", "note", "figma_url"):
            if field in row:
                text(row[field], f"{key}.{field}")
        if row.get("figma_url"):
            url = urlsplit(row["figma_url"])
            require(url.scheme in ("http", "https") and bool(url.netloc), f"{key}.figma_url 需要 http(s) 链接")
        cells = row.get("cells")
        require(isinstance(cells, dict) and set(cells) == ids, f"{key}.cells 必须明确覆盖所有已声明列")
        for col in columns:
            cell = cells[col["id"]]
            label = f"{key}/{col['id']}"
            require(isinstance(cell, dict), f"{label} 需要对象")
            require(("path" in cell) != ("missing" in cell), f"{label} 需要 path 或 missing，不能并存")
            if "missing" in cell:
                text(cell["missing"], label + ".missing")
                require(row["status"] != "verified", f"{key} 仍有证据缺口，不能标 verified")
                continue
            require(cell.get("source") in SOURCES, f"{label}.source 无效")
            for field in ("revision", "os", "captured_at", "note"):
                if field in cell:
                    text(cell[field], f"{label}.{field}")
            viewport(cell.get("viewport", col["viewport"]), label + ".viewport")
            filename = text(cell["path"], label + ".path")
            require("://" not in filename, f"{label}.path 只支持本地文件")
            source = Path(filename).expanduser()
            if not source.is_absolute():
                source = path.parent / source
            source = source.resolve()
            if source not in files:
                content = source.read_bytes()
                with Image.open(BytesIO(content)) as im:
                    im.verify()
                with Image.open(BytesIO(content)) as im:
                    im.load()
                    require(im.format in EXTENSIONS, f"{source} 仅支持 PNG/JPEG/WebP")
                    name = sha256(content).hexdigest() + "." + EXTENSIONS[im.format]
                    files[source] = {"name": name, "width": im.width, "height": im.height}
                    blobs[name] = content
            cell["image"] = files[source]
    return data, blobs


def cell_html(row, col):
    cell = row["cells"][col["id"]]
    if "missing" in cell:
        return '<figure><div class="missing">' + escape(cell["missing"]) + '</div><figcaption>' + escape(col["label"]) + '</figcaption></figure>'
    im = cell["image"]
    width, height = cell.get("viewport", col["viewport"])
    alt = f"{row['title']} · {row['state']} · {col['label']}"
    details = [col["label"], SOURCES[cell["source"]], f"{im['width']}×{im['height']} px", f"{width:g}×{height:g} pt"]
    for field in ("os", "captured_at"):
        if cell.get(field):
            details.append(cell[field])
    details.append("版本：" + cell.get("revision", "未记录"))
    if cell.get("note"):
        details.append(cell["note"])
    return (
        f'<figure><div class="image-scroll" style="--logical-width:{width:g}px;--view-height:{height:g}px">'
        f'<button class="image-button" type="button" aria-label="放大 {escape(alt, quote=True)}">'
        f'<img src="media/{im["name"]}" width="{im["width"]}" height="{im["height"]}" '
        f'alt="{escape(alt, quote=True)}" decoding="async"></button></div>'
        '<figcaption>' + '<br>'.join(escape(item) for item in details) + '</figcaption></figure>'
    )


def render(data, blobs):
    rows = []
    for index, row in enumerate(data["rows"], 1):
        key = row["key"]
        link = f'<a href="{escape(row["figma_url"], quote=True)}" target="_blank" rel="noreferrer">Figma ↗</a>' if row.get("figma_url") else ""
        search = " ".join(row.get(field, "") for field in ("key", "title", "group", "route", "state", "note"))
        rows.append(
            f'<section class="page" id="row-{key}" data-group="{escape(row["group"], quote=True)}" '
            f'data-status="{row["status"]}" data-search="{escape(search, quote=True)}">'
            f'<div class="row-title"><h2><a class="anchor" href="#row-{key}">{index:02d} · {escape(row["title"])}</a></h2>'
            f'<span class="status {row["status"]}">{STATUSES[row["status"]]}</span>{link}</div>'
            f'<p class="meta">{escape(row["group"])} · {escape(row["state"])} · <code>{key}</code>'
            + (" · " + escape(row["route"]) if row.get("route") else "") + '</p>'
            f'<p class="note">{escape(row.get("note", ""))}</p><div class="columns">'
            + "".join(cell_html(row, col) for col in data["columns"]) + '</div></section>'
        )
    groups = dict.fromkeys(row["group"] for row in data["rows"])
    missing = sum("missing" in cell for row in data["rows"] for cell in row["cells"].values())
    present = len(data["rows"]) * len(data["columns"]) - missing
    replacements = {
        "TITLE": escape(data["title"]), "SCOPE": escape(data["scope"]),
        "COLUMN_COUNT": str(len(data["columns"])),
        "COUNTS": f'{len(data["rows"])} 个状态 · {present} 个图像证据 · {len(blobs)} 张不同图片 · {missing} 个缺口',
        "BOUNDARIES": "".join('<li>' + escape(note) + '</li>' for note in data["boundaries"]) or '<li>未记录其他验证边界；请按实际证据复查，图片齐全不代表通过。</li>',
        "COLUMNS": "".join(f'<div><strong>{escape(col["label"])}</strong><small>{col["viewport"][0]:g}×{col["viewport"][1]:g} pt</small></div>' for col in data["columns"]),
        "GROUPS": "".join(f'<option>{escape(group)}</option>' for group in groups),
        "STATUSES": "".join(f'<option value="{key}">{label}</option>' for key, label in STATUSES.items()),
        "JUMPS": "".join(f'<option value="row-{row["key"]}">{escape(row["group"] + " · " + row["title"] + " · " + row["state"])}</option>' for row in data["rows"]),
        "ROWS": "\n".join(rows),
    }
    template = (Path(__file__).resolve().parents[1] / "assets/comparison.html").read_text(encoding="utf-8")
    return re.sub(r"@@([A-Z_]+)@@", lambda match: replacements[match[1]], template), present, missing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path, help="输出 HTML；默认清单同目录下 index.html")
    parser.add_argument("--check", action="store_true", help="只读校验清单与图像")
    args = parser.parse_args()
    try:
        manifest = args.manifest.resolve()
        data, blobs = load_manifest(manifest)
        page, present, missing = render(data, blobs)
        if args.check:
            print(f"Validated: {len(data['rows'])} states, {present} image cells, {missing} missing cells")
            return 0
        output = (args.output or manifest.parent / "index.html").resolve()
        require(output.suffix.lower() == ".html" and output != manifest, "输出需要独立的 .html 文件")
        media = output.parent / "media"
        media.mkdir(parents=True, exist_ok=True)
        for name, content in blobs.items():
            target = media / name
            if not target.exists() or target.read_bytes() != content:
                target.write_bytes(content)
        output.write_text(page, encoding="utf-8")
        print(f"Generated: {output} ({len(data['rows'])} states, {present} image cells, {missing} missing cells)")
        return 0
    except (OSError, ValueError, TypeError, KeyError, Image.DecompressionBombError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
