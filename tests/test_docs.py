from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
VERSION_TABLE_LINK = re.compile(
    r"^\[([^\]]+)\]\(\.\./versions/([^/)]+)\.md\)$"
)
MAIN_JSON_PARAMETER_HEADER = (
    "| 正式リリース | item | dimension/worldgen | enchantment | variant |"
)
EVENT_JSON_PARAMETER_HEADER = (
    "| 正式リリース | predicate | advancement | loot table | recipe "
    "| item modifier |"
)


def public_markdown_files() -> list[Path]:
    files = list(DOCS.rglob("*.md"))
    files.extend((ROOT / "templates").rglob("*.md"))
    files.extend(
        (ROOT / name)
        for name in ("README.md", "README.en.md", "CHANGELOG.md")
    )
    return sorted(files)


class DocumentationTests(unittest.TestCase):
    def parse_version_table(
        self,
        markdown: str,
        header: str,
        expected_columns: int,
    ) -> list[str]:
        lines = markdown.splitlines()
        self.assertEqual(
            1,
            lines.count(header),
            f"expected exactly one table header: {header}",
        )
        header_line = lines.index(header)
        table_lines = lines[header_line:]
        versions: list[str] = []

        for offset, line in enumerate(table_lines, start=header_line + 1):
            if not line.startswith("|"):
                break
            self.assertTrue(
                line.endswith("|"),
                f"JSON parameter table line {offset} has no closing pipe",
            )
            cells = [cell.strip() for cell in line[1:-1].split("|")]
            self.assertEqual(
                expected_columns,
                len(cells),
                f"JSON parameter table line {offset} has {len(cells)} columns",
            )
            if offset == header_line + 2:
                self.assertTrue(
                    all(re.fullmatch(r"-+", cell) for cell in cells),
                    f"JSON parameter table line {offset} is not a separator",
                )
                continue
            if offset == header_line + 1:
                continue

            match = VERSION_TABLE_LINK.fullmatch(cells[0])
            self.assertIsNotNone(
                match,
                f"JSON parameter table line {offset} has an invalid version link",
            )
            assert match is not None
            self.assertEqual(
                match.group(1),
                match.group(2),
                f"JSON parameter table line {offset} version/link mismatch",
            )
            versions.append(match.group(1))

        self.assertTrue(versions, f"table has no release rows: {header}")
        return versions

    def assert_versions_are_unique(
        self,
        versions: list[str],
        table_name: str,
    ) -> None:
        duplicates = sorted(
            version for version in set(versions) if versions.count(version) > 1
        )
        self.assertEqual(
            [],
            duplicates,
            f"{table_name} has duplicate versions",
        )

    def test_agent_guides_match(self) -> None:
        self.assertEqual(
            (ROOT / "AGENTS.md").read_text(encoding="utf-8"),
            (ROOT / "CLAUDE.md").read_text(encoding="utf-8"),
        )

    def test_local_markdown_links_exist(self) -> None:
        missing: list[str] = []
        for markdown in public_markdown_files():
            text = markdown.read_text(encoding="utf-8")
            for target in MARKDOWN_LINK.findall(text):
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                path_text = target.split("#", 1)[0]
                if not path_text:
                    continue
                target_path = (markdown.parent / path_text).resolve()
                if not target_path.exists():
                    missing.append(
                        f"{markdown.relative_to(ROOT)} -> {target}"
                    )
        self.assertEqual([], missing)

    def test_json_code_fences_parse(self) -> None:
        failures: list[str] = []
        for markdown in public_markdown_files():
            active = False
            start = 0
            block: list[str] = []
            for number, line in enumerate(
                markdown.read_text(encoding="utf-8").splitlines(),
                start=1,
            ):
                if not active and line == "```json":
                    active = True
                    start = number + 1
                    block = []
                    continue
                if active and line == "```":
                    try:
                        json.loads("\n".join(block))
                    except json.JSONDecodeError as error:
                        failures.append(
                            f"{markdown.relative_to(ROOT)}:{start}: {error}"
                        )
                    active = False
                    continue
                if active:
                    block.append(line)
            if active:
                failures.append(
                    f"{markdown.relative_to(ROOT)}:{start}: unclosed JSON fence"
                )
        self.assertEqual([], failures)

    def test_each_document_has_one_top_level_heading(self) -> None:
        failures: list[str] = []
        for markdown in DOCS.rglob("*.md"):
            active_fence = False
            headings = 0
            for line in markdown.read_text(encoding="utf-8").splitlines():
                if line.startswith("```"):
                    active_fence = not active_fence
                    continue
                if not active_fence and line.startswith("# "):
                    headings += 1
            if headings != 1:
                failures.append(
                    f"{markdown.relative_to(ROOT)}: H1 count is {headings}"
                )
        self.assertEqual([], failures)

    def test_version_terminology_is_consistent(self) -> None:
        failures = [
            str(markdown.relative_to(ROOT))
            for markdown in public_markdown_files()
            if "版" in markdown.read_text(encoding="utf-8")
        ]
        self.assertEqual([], failures)

    def test_main_json_parameter_table_covers_every_release_profile(self) -> None:
        index = (
            DOCS / "json-parameters" / "README.md"
        ).read_text(encoding="utf-8")
        versions = self.parse_version_table(
            index,
            MAIN_JSON_PARAMETER_HEADER,
            expected_columns=5,
        )
        self.assert_versions_are_unique(versions, "main JSON parameter table")

        release_profiles = {
            profile.stem
            for profile in (DOCS / "versions").glob("*.md")
            if profile.name != "README.md"
        }
        self.assertEqual(50, len(release_profiles))
        self.assertEqual(release_profiles, set(versions))

    def test_event_json_parameter_table_has_valid_unique_rows(self) -> None:
        index = (
            DOCS / "json-parameters" / "README.md"
        ).read_text(encoding="utf-8")
        versions = self.parse_version_table(
            index,
            EVENT_JSON_PARAMETER_HEADER,
            expected_columns=6,
        )
        self.assert_versions_are_unique(versions, "event JSON parameter table")


if __name__ == "__main__":
    unittest.main()
