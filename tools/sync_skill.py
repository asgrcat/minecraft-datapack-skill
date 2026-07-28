#!/usr/bin/env python3
"""Synchronize the installable Agent Skill with repository source files."""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "minecraft-datapack"
DIRECTORIES = ("docs", "schemas", "templates")
FILES = (
    "LICENSE",
    "VERSION",
    "tools/datapack_harness.py",
)


def copy_distribution(destination: Path) -> None:
    for relative in DIRECTORIES:
        shutil.copytree(ROOT / relative, destination / relative)
    for relative in FILES:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


def differing_files() -> list[str]:
    differences: list[str] = []
    for relative in DIRECTORIES:
        comparison = filecmp.dircmp(ROOT / relative, SKILL_ROOT / relative)

        def collect(current: filecmp.dircmp[str], prefix: Path) -> None:
            differences.extend(
                str(prefix / name)
                for name in (
                    current.left_only
                    + current.right_only
                    + current.diff_files
                    + current.funny_files
                )
            )
            for name, child in current.subdirs.items():
                collect(child, prefix / name)

        collect(comparison, Path(relative))
    for relative in FILES:
        source = ROOT / relative
        bundled = SKILL_ROOT / relative
        if not bundled.is_file() or not filecmp.cmp(source, bundled, shallow=False):
            differences.append(relative)
    return sorted(set(differences))


def synchronize() -> None:
    SKILL_ROOT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="minecraft-datapack-skill-",
        dir=SKILL_ROOT.parent,
    ) as temporary:
        staged = Path(temporary)
        copy_distribution(staged)
        for relative in (*DIRECTORIES, *FILES):
            target = SKILL_ROOT / relative
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
            source = staged / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="report differences without changing the skill",
    )
    arguments = parser.parse_args()
    if arguments.check:
        differences = differing_files()
        if differences:
            for difference in differences:
                print(difference)
            return 1
        print("skill distribution is synchronized")
        return 0
    synchronize()
    print(f"synchronized {SKILL_ROOT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
