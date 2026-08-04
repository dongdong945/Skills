#!/usr/bin/env python3
"""对已对齐口径的收入区间执行求和或求交，并可估算扣除后到账。"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any, Union


Number = Union[int, float]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="计算收入证据区间；输入为 JSON。")
    parser.add_argument("--input", required=True, help="JSON 文件路径，或 - 表示 stdin")
    return parser.parse_args()


def load_input(path: str) -> dict[str, Any]:
    if path == "-":
        return json.load(sys.stdin)
    with open(path, encoding="utf-8") as source:
        return json.load(source)


def validate_bound(value: Any, field: str) -> Number | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{field} 必须是有限数字或 null")
    if value < 0:
        raise ValueError(f"{field} 不能为负数")
    return value


def normalize_range(raw: dict[str, Any], index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError(f"ranges[{index}] 必须是对象")
    lower = validate_bound(raw.get("lower"), f"ranges[{index}].lower")
    upper = validate_bound(raw.get("upper"), f"ranges[{index}].upper")
    if lower is None and upper is None:
        raise ValueError(f"ranges[{index}] 至少需要一个边界")
    if lower is not None and upper is not None and lower > upper:
        raise ValueError(f"ranges[{index}] 下界不能大于上界")
    return {
        "label": raw.get("label", f"range-{index + 1}"),
        "lower": lower,
        "upper": upper,
        "lowerInclusive": bool(raw.get("lowerInclusive", True)),
        "upperInclusive": bool(raw.get("upperInclusive", True)),
    }


def sum_ranges(ranges: list[dict[str, Any]]) -> dict[str, Any]:
    lower = None if any(item["lower"] is None for item in ranges) else sum(item["lower"] for item in ranges)
    upper = None if any(item["upper"] is None for item in ranges) else sum(item["upper"] for item in ranges)
    return {
        "lower": lower,
        "upper": upper,
        "lowerInclusive": all(item["lowerInclusive"] for item in ranges) if lower is not None else False,
        "upperInclusive": all(item["upperInclusive"] for item in ranges) if upper is not None else False,
    }


def intersect_ranges(ranges: list[dict[str, Any]]) -> dict[str, Any]:
    finite_lowers = [(item["lower"], item["lowerInclusive"]) for item in ranges if item["lower"] is not None]
    finite_uppers = [(item["upper"], item["upperInclusive"]) for item in ranges if item["upper"] is not None]
    lower = max((item[0] for item in finite_lowers), default=None)
    upper = min((item[0] for item in finite_uppers), default=None)
    lower_inclusive = all(inclusive for value, inclusive in finite_lowers if value == lower)
    upper_inclusive = all(inclusive for value, inclusive in finite_uppers if value == upper)
    if lower is not None and upper is not None:
        if lower > upper or (lower == upper and not (lower_inclusive and upper_inclusive)):
            raise ValueError("输入区间没有交集；应报告来源冲突，不能求平均")
    return {
        "lower": lower,
        "upper": upper,
        "lowerInclusive": lower_inclusive if lower is not None else False,
        "upperInclusive": upper_inclusive if upper is not None else False,
    }


def calculate_proceeds(gross: dict[str, Any], deduction: dict[str, Any]) -> dict[str, Any]:
    low_rate = validate_bound(deduction.get("lower"), "deductionRate.lower")
    high_rate = validate_bound(deduction.get("upper"), "deductionRate.upper")
    if low_rate is None or high_rate is None or low_rate > high_rate or high_rate > 1:
        raise ValueError("deductionRate 需要满足 0 <= lower <= upper <= 1")
    lower = None if gross["lower"] is None else gross["lower"] * (1 - high_rate)
    upper = None if gross["upper"] is None else gross["upper"] * (1 - low_rate)
    return {
        "lower": lower,
        "upper": upper,
        "lowerInclusive": gross["lowerInclusive"],
        "upperInclusive": gross["upperInclusive"],
        "deductionRate": {"lower": low_rate, "upper": high_rate},
    }


def main() -> int:
    try:
        data = load_input(parse_args().input)
        operation = data.get("operation")
        if operation not in {"sum", "intersection"}:
            raise ValueError("operation 必须是 sum 或 intersection")
        raw_ranges = data.get("ranges")
        if not isinstance(raw_ranges, list) or not raw_ranges:
            raise ValueError("ranges 必须是非空数组")
        ranges = [normalize_range(item, index) for index, item in enumerate(raw_ranges)]
        result = sum_ranges(ranges) if operation == "sum" else intersect_ranges(ranges)
        output: dict[str, Any] = {
            "operation": operation,
            "currency": data.get("currency"),
            "period": data.get("period"),
            "metric": data.get("metric"),
            "range": result,
            "inputs": ranges,
        }
        if data.get("deductionRate") is not None:
            output["proceedsRange"] = calculate_proceeds(result, data["deductionRate"])
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
