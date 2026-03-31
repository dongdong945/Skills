#!/usr/bin/env python3
"""Create a standard MVVM + Clean directory skeleton for one business feature."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

BASE_DIRECTORIES = (
    Path("App/Presentation/Features"),
    Path("App/Domain/Entities"),
    Path("App/Domain/Repositories"),
    Path("App/Data/Repositories"),
    Path("App/Data/DataSources/Remote"),
    Path("App/Data/DataSources/Local"),
    Path("App/Data/Models"),
)

DIRECTORY_TEMPLATES = (
    Path("App/Presentation/Features/{feature}"),
    Path("App/Presentation/Features/{feature}/Views"),
    Path("App/Presentation/Features/{feature}/ViewModels"),
    Path("App/Presentation/Features/{feature}/Models"),
    Path("App/Domain/Entities/{feature}"),
    Path("App/Domain/Repositories/{feature}"),
    Path("App/Data/Repositories/{feature}"),
    Path("App/Data/DataSources/Remote/{feature}"),
    Path("App/Data/DataSources/Local/{feature}"),
    Path("App/Data/Models/{feature}"),
)


def normalize_feature_name(raw_name: str) -> str:
    parts = re.findall(r"[A-Za-z0-9]+", raw_name)
    if not parts:
        raise ValueError("feature name must contain at least one letter or digit")
    return "".join(part[:1].upper() + part[1:] for part in parts)


def build_feature_directories(feature_name: str) -> list[Path]:
    return [Path(str(template).format(feature=feature_name)) for template in DIRECTORY_TEMPLATES]


def check_base_directories(project_root: Path) -> list[Path]:
    return [base for base in BASE_DIRECTORIES if not (project_root / base).is_dir()]


def create_directories(project_root: Path, feature_name: str, dry_run: bool) -> tuple[list[Path], list[Path]]:
    created: list[Path] = []
    existing: list[Path] = []

    for relative_path in build_feature_directories(feature_name):
        absolute_path = project_root / relative_path
        if absolute_path.exists():
            existing.append(relative_path)
            continue
        if not dry_run:
            absolute_path.mkdir(parents=True, exist_ok=True)
        created.append(relative_path)

    return created, existing


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create MVVM + Clean directories for a business feature.",
    )
    parser.add_argument("feature_name", help="Business feature name, for example Subscription")
    parser.add_argument(
        "--root",
        default=".",
        help="Project root directory. Defaults to the current directory.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview directories without creating them.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(args.root).resolve()

    if not project_root.is_dir():
        print(f"[ERROR] Project root does not exist: {project_root}", file=sys.stderr)
        return 1

    try:
        feature_name = normalize_feature_name(args.feature_name)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    missing_bases = check_base_directories(project_root)
    if missing_bases:
        print("[ERROR] Missing base directories:", file=sys.stderr)
        for path in missing_bases:
            print(f"  - {path}", file=sys.stderr)
        return 1

    created, existing = create_directories(project_root, feature_name, args.dry_run)

    action = "Would create" if args.dry_run else "Created"
    print(f"Feature: {feature_name}")
    print(f"Project root: {project_root}")
    print(f"{action} {len(created)} director{'y' if len(created) == 1 else 'ies'}")
    for path in created:
        print(f"  + {path}")

    print(f"Existing {len(existing)} director{'y' if len(existing) == 1 else 'ies'}")
    for path in existing:
        print(f"  = {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
