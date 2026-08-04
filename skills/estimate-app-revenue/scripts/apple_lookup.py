#!/usr/bin/env python3
"""通过 Apple iTunes Search API 查询 App 与开发者作品组合。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_URL = "https://itunes.apple.com/lookup"
APP_FIELDS = (
    "trackId",
    "trackName",
    "artistId",
    "artistName",
    "sellerName",
    "sellerUrl",
    "bundleId",
    "kind",
    "primaryGenreName",
    "genres",
    "price",
    "formattedPrice",
    "currency",
    "version",
    "currentVersionReleaseDate",
    "releaseDate",
    "minimumOsVersion",
    "contentAdvisoryRating",
    "averageUserRating",
    "userRatingCount",
    "trackViewUrl",
)


def fetch_lookup(identifier: int, country: str, entity: str | None = None) -> dict[str, Any]:
    params = {"id": identifier, "country": country, "limit": 200}
    if entity:
        params["entity"] = entity
    request = Request(
        f"{API_URL}?{urlencode(params)}",
        headers={"User-Agent": "estimate-app-revenue/1.0"},
    )
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def compact_app(raw: dict[str, Any]) -> dict[str, Any]:
    return {key: raw[key] for key in APP_FIELDS if raw.get(key) is not None}


def is_app(raw: dict[str, Any]) -> bool:
    return raw.get("kind") in {"software", "mac-software"} and raw.get("trackId") is not None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="查询 Apple App Store App 及同开发者作品组合，并输出 JSON。"
    )
    parser.add_argument("app_id", type=int, help="App Store App ID 或开发者 ID")
    parser.add_argument("--country", default="us", help="两位 storefront 国家代码，默认 us")
    parser.add_argument("--output", help="输出文件；省略时写入 stdout")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    country = args.country.lower()
    if len(country) != 2 or not country.isalpha():
        print("error: --country 必须是两位字母国家代码", file=sys.stderr)
        return 2

    try:
        direct = fetch_lookup(args.app_id, country)
        direct_results = direct.get("results", [])
        primary = next((item for item in direct_results if is_app(item)), None)

        if primary:
            input_type = "app"
            artist_id = int(primary["artistId"])
            portfolio_response = fetch_lookup(artist_id, country, "software")
        else:
            input_type = "developer"
            artist_id = args.app_id
            portfolio_response = fetch_lookup(artist_id, country, "software")

        portfolio_results = portfolio_response.get("results", [])
        artist = next(
            (item for item in portfolio_results if item.get("wrapperType") == "artist"),
            None,
        )
        apps_by_id = {
            int(item["trackId"]): compact_app(item)
            for item in portfolio_results
            if is_app(item)
        }
        if primary:
            apps_by_id.setdefault(int(primary["trackId"]), compact_app(primary))
        if not apps_by_id and not artist:
            print(
                f"error: storefront={country} 未找到 ID {args.app_id} 对应的 App 或开发者",
                file=sys.stderr,
            )
            return 1

        apps = sorted(apps_by_id.values(), key=lambda item: (item.get("kind", ""), item.get("trackName", "")))
        platform_counts: dict[str, int] = {}
        for app in apps:
            kind = str(app.get("kind", "unknown"))
            platform_counts[kind] = platform_counts.get(kind, 0) + 1

        developer_name = (artist or {}).get("artistName")
        if not developer_name and primary:
            developer_name = primary.get("artistName")

        result = {
            "queriedAt": datetime.now(timezone.utc).isoformat(),
            "source": API_URL,
            "storefront": country,
            "input": {"id": args.app_id, "type": input_type},
            "targetApp": compact_app(primary) if primary else None,
            "developer": {
                "artistId": artist_id,
                "artistName": developer_name,
                "artistViewUrl": (artist or {}).get("artistViewUrl"),
            },
            "portfolio": {
                "appCount": len(apps),
                "platformCounts": platform_counts,
                "apps": apps,
            },
            "limitations": [
                "Apple Lookup 仅提供 storefront 元数据，不提供下载量、内购收入或利润。",
                "下架、地区不可用或 API 未返回的产品可能不在作品列表中。",
            ],
        }
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            with open(args.output, "w", encoding="utf-8") as output:
                output.write(rendered)
        else:
            sys.stdout.write(rendered)
        return 0
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        print(f"error: Apple Lookup 请求失败: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
