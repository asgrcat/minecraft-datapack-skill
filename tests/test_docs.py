from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def public_markdown_files() -> list[Path]:
    files = list(DOCS.rglob("*.md"))
    files.extend((ROOT / "templates").rglob("*.md"))
    files.extend(
        (ROOT / name)
        for name in ("README.md", "README.en.md", "CHANGELOG.md")
    )
    return sorted(files)


class DocumentationTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
