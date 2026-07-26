from __future__ import annotations

import importlib.util
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "datapack_harness",
    ROOT / "tools" / "datapack_harness.py",
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = HARNESS
SPEC.loader.exec_module(HARNESS)


class ProfileTests(unittest.TestCase):
    def test_all_profiles_validate_and_form_one_chain(self) -> None:
        profiles = HARNESS.load_profiles()
        self.assertEqual([], HARNESS.validate_all_profiles(profiles))
        order = HARNESS.ordered_versions(profiles)
        self.assertEqual(50, len(order))
        self.assertEqual("1.13", order[0])
        self.assertEqual("26.2", order[-1])

    def test_compatibility_is_normalized(self) -> None:
        profiles = HARNESS.load_profiles()
        for profile in profiles.values():
            self.assertIn(
                profile["compatibility"],
                HARNESS.COMPATIBILITY_CLASSES,
            )

    def test_resolve_chain_reaches_origin(self) -> None:
        profiles = HARNESS.load_profiles()
        chain = HARNESS.resolve_chain("26.2", profiles)
        self.assertEqual("1.13", chain[0]["version"])
        self.assertEqual("26.2", chain[-1]["version"])
        self.assertEqual(50, len(chain))

    def test_known_boundaries_are_documented(self) -> None:
        commands = (ROOT / "docs" / "commands.md").read_text(encoding="utf-8")
        formats = (ROOT / "docs" / "json-formats.md").read_text(encoding="utf-8")
        self.assertIn("1.13〜1.20.6 では `data/<namespace>/functions/", commands)
        self.assertIn("`@n` | 最寄り entity。1.21 以降", commands)
        self.assertIn("| trial_spawner | 1.21.2 |", formats)


class PackValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profiles = HARNESS.load_profiles()

    def make_pack(self, root: Path, metadata: dict) -> None:
        (root / "pack.mcmeta").write_text(
            json.dumps(metadata),
            encoding="utf-8",
        )

    def test_plural_pack_passes_static_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pack = Path(temporary)
            self.make_pack(
                pack,
                {"pack": {"pack_format": 41, "description": "test"}},
            )
            function = pack / "data" / "example" / "functions" / "load.mcfunction"
            function.parent.mkdir(parents=True)
            function.write_text("say loaded\n", encoding="utf-8")
            result = HARNESS.validate_pack(
                "1.20.6",
                pack,
                None,
                self.profiles,
            )
            self.assertEqual([], result.errors)

    def test_plural_pack_rejects_singular_function_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pack = Path(temporary)
            self.make_pack(
                pack,
                {"pack": {"pack_format": 41, "description": "test"}},
            )
            function = pack / "data" / "example" / "function" / "load.mcfunction"
            function.parent.mkdir(parents=True)
            function.write_text("say loaded\n", encoding="utf-8")
            result = HARNESS.validate_pack(
                "1.20.6",
                pack,
                None,
                self.profiles,
            )
            self.assertTrue(
                any("wrong plural directory schema" in error for error in result.errors)
            )

    def test_singular_pack_rejects_plural_function_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pack = Path(temporary)
            self.make_pack(
                pack,
                {
                    "pack": {
                        "description": "test",
                        "min_format": [107, 1],
                        "max_format": [107, 1],
                    }
                },
            )
            function = pack / "data" / "example" / "functions" / "load.mcfunction"
            function.parent.mkdir(parents=True)
            function.write_text("say loaded\n", encoding="utf-8")
            result = HARNESS.validate_pack(
                "26.2",
                pack,
                None,
                self.profiles,
            )
            self.assertTrue(
                any("wrong singular directory schema" in error for error in result.errors)
            )

    def test_singular_pack_rejects_plural_tag_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pack = Path(temporary)
            self.make_pack(
                pack,
                {
                    "pack": {
                        "description": "test",
                        "min_format": [107, 1],
                        "max_format": [107, 1],
                    }
                },
            )
            tag = pack / "data" / "example" / "tags" / "items" / "test.json"
            tag.parent.mkdir(parents=True)
            tag.write_text('{"values":[]}', encoding="utf-8")
            result = HARNESS.validate_pack(
                "26.2",
                pack,
                None,
                self.profiles,
            )
            self.assertTrue(
                any("wrong singular tag directory schema" in error for error in result.errors)
            )

    def test_minor_target_requires_min_and_max_format(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pack = Path(temporary)
            self.make_pack(
                pack,
                {"pack": {"description": "test", "pack_format": 88}},
            )
            result = HARNESS.validate_pack(
                "1.21.9",
                pack,
                None,
                self.profiles,
            )
            self.assertTrue(
                any("requires valid min_format" in error for error in result.errors)
            )

    def test_missing_local_function_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pack = Path(temporary)
            self.make_pack(
                pack,
                {"pack": {"pack_format": 41, "description": "test"}},
            )
            function = pack / "data" / "example" / "functions" / "load.mcfunction"
            function.parent.mkdir(parents=True)
            function.write_text(
                "function example:missing\n",
                encoding="utf-8",
            )
            result = HARNESS.validate_pack(
                "1.20.6",
                pack,
                None,
                self.profiles,
            )
            self.assertIn(
                "data/example/functions/load.mcfunction:1: "
                "missing local function example:missing",
                result.errors,
            )

    def test_command_root_is_checked_against_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pack = root / "pack"
            pack.mkdir()
            self.make_pack(
                pack,
                {"pack": {"pack_format": 41, "description": "test"}},
            )
            function = pack / "data" / "example" / "functions" / "load.mcfunction"
            function.parent.mkdir(parents=True)
            function.write_text("unknown_command\n", encoding="utf-8")
            reports = root / "generated" / "reports"
            reports.mkdir(parents=True)
            (reports / "commands.json").write_text(
                json.dumps({"children": {"say": {"type": "literal"}}}),
                encoding="utf-8",
            )
            (reports / "registries.json").write_text("{}", encoding="utf-8")
            result = HARNESS.validate_pack(
                "1.20.6",
                pack,
                root / "generated",
                self.profiles,
            )
            self.assertTrue(
                any("absent from commands.json" in error for error in result.errors)
            )

    def test_minor_pack_format_range_contains_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pack = Path(temporary)
            self.make_pack(
                pack,
                {
                    "pack": {
                        "description": "test",
                        "min_format": [88, 0],
                        "max_format": [94, 1],
                    }
                },
            )
            function = pack / "data" / "example" / "function" / "load.mcfunction"
            function.parent.mkdir(parents=True)
            function.write_text("say loaded\n", encoding="utf-8")
            result = HARNESS.validate_pack(
                "1.21.11",
                pack,
                None,
                self.profiles,
            )
            self.assertFalse(
                any("declared formats" in error for error in result.errors)
            )

    def test_integer_max_format_includes_all_minor_versions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pack = Path(temporary)
            self.make_pack(
                pack,
                {
                    "pack": {
                        "description": "test",
                        "min_format": 107,
                        "max_format": 107,
                    }
                },
            )
            result = HARNESS.validate_pack(
                "26.2",
                pack,
                None,
                self.profiles,
            )
            self.assertFalse(
                any("declared formats" in error for error in result.errors)
            )

    def test_supported_formats_object_contains_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pack = Path(temporary)
            self.make_pack(
                pack,
                {
                    "pack": {
                        "description": "test",
                        "pack_format": 18,
                        "supported_formats": {
                            "min_inclusive": 18,
                            "max_inclusive": 48,
                        },
                    }
                },
            )
            result = HARNESS.validate_pack(
                "1.20.5",
                pack,
                None,
                self.profiles,
            )
            self.assertFalse(
                any("declared formats" in error for error in result.errors)
            )


class FetchTests(unittest.TestCase):
    def test_fetch_uses_exact_release_and_verifies_sha1(self) -> None:
        payload = b"server jar fixture"
        digest = hashlib.sha1(payload).hexdigest()
        manifest = {
            "versions": [
                {"id": "1.20.5", "type": "release", "url": "metadata"},
                {"id": "1.20.5-rc1", "type": "snapshot", "url": "wrong"},
            ]
        }
        metadata = {
            "id": "1.20.5",
            "downloads": {
                "server": {
                    "url": "server",
                    "sha1": digest,
                }
            },
        }
        with tempfile.TemporaryDirectory() as temporary:
            cache = Path(temporary)

            def fake_download(_url: str, destination: Path) -> None:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(payload)

            with (
                mock.patch.object(
                    HARNESS,
                    "fetch_json",
                    side_effect=[manifest, metadata],
                ),
                mock.patch.object(
                    HARNESS,
                    "download_file",
                    side_effect=fake_download,
                ),
            ):
                jar, fetched = HARNESS.fetch_release("1.20.5", cache)
            self.assertEqual(payload, jar.read_bytes())
            self.assertEqual(digest, HARNESS.sha1_file(jar))
            self.assertEqual("1.20.5", fetched["id"])


if __name__ == "__main__":
    unittest.main()
