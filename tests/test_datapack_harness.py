from __future__ import annotations

import importlib.util
import hashlib
import json
import queue
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
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

    def test_resolve_separates_active_rules_from_history(self) -> None:
        profiles = HARNESS.load_profiles()
        payload = HARNESS.resolved_profile_payload("1.20.5", profiles)
        active = "\n".join(payload["active_ai_rules"])
        history = "\n".join(
            rule
            for entry in payload["rule_history"]
            for rule in entry["rules"]
        )
        self.assertIn("旧 `{tag}` item suffixを出力しない", active)
        self.assertNotIn("1.14 以降の `/data modify`", active)
        self.assertIn("1.14 以降の `/data modify`", history)
        self.assertNotIn("ai_rules", payload)

    def test_known_boundaries_are_documented(self) -> None:
        commands = (ROOT / "docs" / "commands.md").read_text(encoding="utf-8")
        formats = (ROOT / "docs" / "json-formats.md").read_text(encoding="utf-8")
        self.assertIn("1.13〜1.20.6 では `data/<namespace>/functions/", commands)
        self.assertIn("`@n` | 最寄り entity。1.21 以降", commands)
        self.assertIn("| trial_spawner | 1.21.2 |", formats)


class PackValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profiles = HARNESS.load_profiles()

    def make_pack(self, root: Path, metadata: Any) -> None:
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

    def test_pack_metadata_top_level_must_be_an_object(self) -> None:
        invalid_values = ([], 0, "metadata", None)
        for value in invalid_values:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temporary:
                pack = Path(temporary)
                self.make_pack(pack, value)
                result = HARNESS.validate_pack(
                    "1.20.6",
                    pack,
                    None,
                    self.profiles,
                )
                self.assertIn(
                    "pack.mcmeta: top level must be an object",
                    result.errors,
                )

        with tempfile.TemporaryDirectory() as temporary:
            pack = Path(temporary)
            (pack / "pack.mcmeta").write_text("", encoding="utf-8")
            result = HARNESS.validate_pack(
                "1.20.6",
                pack,
                None,
                self.profiles,
            )
            self.assertTrue(
                any("invalid UTF-8/JSON" in error for error in result.errors)
            )

    def test_line_continuation_requires_1_20_2(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pack = Path(temporary)
            self.make_pack(
                pack,
                {"pack": {"pack_format": 15, "description": "test"}},
            )
            function = pack / "data" / "example" / "functions" / "load.mcfunction"
            function.parent.mkdir(parents=True)
            function.write_text("say first \\\nsecond\n", encoding="utf-8")
            result = HARNESS.validate_pack(
                "1.20.1",
                pack,
                None,
                self.profiles,
            )
            self.assertTrue(
                any(
                    "line continuation requires 1.20.2" in error
                    for error in result.errors
                )
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


class ReportTests(unittest.TestCase):
    def test_reports_use_temporary_working_directory(self) -> None:
        profiles = HARNESS.load_profiles()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            jar = root / "server.jar"
            jar.write_bytes(b"jar")
            output = root / "generated"
            captured: dict[str, Any] = {}

            def fake_run(command: list[str], **kwargs: Any) -> mock.Mock:
                captured["command"] = command
                captured["cwd"] = Path(kwargs["cwd"])
                captured["cwd_existed"] = captured["cwd"].is_dir()
                captured["check"] = kwargs["check"]
                return mock.Mock(returncode=0)

            with (
                mock.patch.object(
                    HARNESS,
                    "fetch_release",
                    return_value=(jar, {}),
                ),
                mock.patch.object(
                    HARNESS.subprocess,
                    "run",
                    side_effect=fake_run,
                ),
            ):
                HARNESS.run_reports(
                    "26.2",
                    "java",
                    root / "cache",
                    output,
                    profiles,
                )

            self.assertTrue(captured["cwd_existed"])
            self.assertFalse(captured["cwd"].exists())
            self.assertFalse(captured["check"])
            output_index = captured["command"].index("--output") + 1
            self.assertEqual(str(output.resolve()), captured["command"][output_index])
            self.assertEqual(str(jar.resolve()), captured["command"][3])


class ServerLogTests(unittest.TestCase):
    def test_common_load_failures_are_detected(self) -> None:
        messages = (
            "Couldn't load function example:test",
            "Failed to parse data file example:test from example:test.json",
            "Unknown function example:test",
        )
        for message in messages:
            with self.subTest(message=message):
                self.assertTrue(HARNESS.server_log_errors(message))

    def test_positive_server_markers_are_recognized(self) -> None:
        enabled = (
            "There are 2 data pack(s) enabled: "
            "[vanilla (built-in)], [file/pack-under-test (world)]"
        )
        self.assertTrue(HARNESS.enabled_list_completed(enabled))
        self.assertTrue(HARNESS.tested_pack_is_enabled(enabled))
        self.assertFalse(
            HARNESS.tested_pack_is_enabled(
                "There are 1 data pack(s) enabled: [vanilla (built-in)]"
            )
        )
        self.assertTrue(HARNESS.reload_started("Reloading!\n"))
        self.assertTrue(HARNESS.reload_completed("Loaded 1250 advancements\n"))

    def test_server_test_checks_enabled_pack_before_and_after_reload(self) -> None:
        class FakeProcess:
            def __init__(self) -> None:
                self.returncode: int | None = None
                self.lines: queue.Queue[str | None] = queue.Queue()
                self.lines.put('[Server thread/INFO]: Done (1.0s)! For help, type "help"\n')
                self.commands: list[str] = []
                self.stdout = self
                self.stdin = self

            def __iter__(self) -> Any:
                while True:
                    line = self.lines.get()
                    if line is None:
                        return
                    yield line

            def write(self, text: str) -> int:
                for command in text.splitlines():
                    self.commands.append(command)
                    if command == "datapack list enabled":
                        self.lines.put(
                            "There are 2 data pack(s) enabled: "
                            "[vanilla (built-in)], "
                            "[file/pack-under-test (world)]\n"
                        )
                    elif command == "reload":
                        self.lines.put("Reloading!\n")
                        self.lines.put("[Server thread/INFO]: PACK_TEST_LOAD_OK\n")
                        self.lines.put("Loaded 1250 advancements\n")
                    elif command == "stop":
                        self.returncode = 0
                        self.lines.put("Stopping server\n")
                        self.lines.put(None)
                return len(text)

            def flush(self) -> None:
                return None

            def poll(self) -> int | None:
                return self.returncode

            def wait(self, timeout: int | None = None) -> int:
                if self.returncode is None:
                    raise AssertionError(f"process did not stop within {timeout}")
                return self.returncode

            def terminate(self) -> None:
                self.returncode = -15
                self.lines.put(None)

            def kill(self) -> None:
                self.returncode = -9
                self.lines.put(None)

        process = FakeProcess()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pack = root / "pack"
            pack.mkdir()
            jar = root / "server.jar"
            jar.write_bytes(b"jar")
            with (
                mock.patch.object(
                    HARNESS,
                    "fetch_release",
                    return_value=(jar, {}),
                ),
                mock.patch.object(
                    HARNESS.subprocess,
                    "Popen",
                    return_value=process,
                ),
            ):
                status, log = HARNESS.server_test(
                    "1.20.5",
                    pack,
                    "java",
                    root / "cache",
                    2,
                    True,
                    ["PACK_TEST_LOAD_OK"],
                )

        self.assertEqual(0, status)
        self.assertIn("PACK_TEST_LOAD_OK", log)
        self.assertEqual(
            [
                "datapack list enabled",
                "reload",
                "datapack list enabled",
                "stop",
            ],
            process.commands,
        )


if __name__ == "__main__":
    unittest.main()
