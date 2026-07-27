from __future__ import annotations

import contextlib
import importlib.util
import hashlib
import io
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
        parameter_history = payload["json_parameter_history"]
        self.assertEqual("1.13", parameter_history[0]["version"])
        self.assertEqual("1.20.5", parameter_history[-1]["version"])
        self.assertEqual(
            len(payload["inheritance_chain"]),
            len(parameter_history),
        )
        self.assertIn(
            "dimension/worldgen",
            parameter_history[-1]["changes"],
        )

    def test_known_boundaries_are_documented(self) -> None:
        commands = (ROOT / "docs" / "commands.md").read_text(encoding="utf-8")
        formats = (ROOT / "docs" / "json-formats.md").read_text(encoding="utf-8")
        self.assertIn("1.13〜1.20.6 では `data/<namespace>/functions/", commands)
        self.assertIn("`@n` | 最寄り entity。1.21 以降", commands)
        self.assertIn("| trial_spawner | 1.21.2 |", formats)

    def test_json_parameter_changes_require_labeled_family_bullets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "profile.md"
            path.write_text(
                "\n".join(
                    (
                        "# Test",
                        "",
                        "## JSONパラメータ差分",
                        "",
                        "- item: item change",
                        "- **dimension/worldgen**: worldgen change",
                        "- enchantment: enchantment change",
                        "- **variant**: variant change",
                        "- predicate: predicate change",
                        "- advancement: advancement change",
                        "- loot_table: loot change",
                        "- recipe: recipe change",
                        "- item_modifier: modifier change",
                        "",
                        "## AI 生成規則",
                        "",
                        "- rule",
                    )
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                {
                    "item": "item change",
                    "dimension/worldgen": "worldgen change",
                    "enchantment": "enchantment change",
                    "variant": "variant change",
                    "predicate": "predicate change",
                    "advancement": "advancement change",
                    "loot_table": "loot change",
                    "recipe": "recipe change",
                    "item_modifier": "modifier change",
                },
                dict(HARNESS.extract_json_parameter_changes(path)),
            )


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

    def test_function_encoding_errors_do_not_abort_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pack = Path(temporary)
            self.make_pack(
                pack,
                {"pack": {"pack_format": 41, "description": "test"}},
            )
            functions = pack / "data" / "example" / "functions"
            functions.mkdir(parents=True)
            (functions / "invalid.mcfunction").write_bytes(b"say ok\n\xff\n")
            (functions / "other.mcfunction").write_text(
                "function example:missing\n",
                encoding="utf-8",
            )
            result = HARNESS.validate_pack(
                "1.20.6",
                pack,
                None,
                self.profiles,
            )
            self.assertTrue(
                any("invalid.mcfunction: invalid UTF-8" in error for error in result.errors)
            )
            self.assertTrue(
                any("missing local function example:missing" in error for error in result.errors)
            )

    def test_empty_function_is_valid_but_utf8_bom_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pack = Path(temporary)
            self.make_pack(
                pack,
                {"pack": {"pack_format": 41, "description": "test"}},
            )
            functions = pack / "data" / "example" / "functions"
            functions.mkdir(parents=True)
            (functions / "empty.mcfunction").write_bytes(b"")
            (functions / "bom.mcfunction").write_bytes(
                b"\xef\xbb\xbfsay loaded\n"
            )
            result = HARNESS.validate_pack(
                "1.20.6",
                pack,
                None,
                self.profiles,
            )
            self.assertEqual(
                1,
                sum("UTF-8 BOM is not allowed" in error for error in result.errors),
            )
            self.assertFalse(
                any("empty.mcfunction" in error for error in result.errors)
            )

    def test_invalid_utf8_json_with_reports_is_a_validation_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pack = root / "pack"
            pack.mkdir()
            self.make_pack(
                pack,
                {"pack": {"pack_format": 41, "description": "test"}},
            )
            invalid = pack / "data" / "example" / "predicates" / "invalid.json"
            invalid.parent.mkdir(parents=True)
            invalid.write_bytes(b'{"condition":"minecraft:random_chance",\xff}')

            reports = root / "generated" / "reports"
            reports.mkdir(parents=True)
            (reports / "commands.json").write_text(
                '{"children":{}}',
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
                any(
                    "invalid.json: invalid JSON" in error
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
            provenance = json.loads(
                (output / HARNESS.REPORT_PROVENANCE_FILE).read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual("26.2", provenance["version"])
            self.assertEqual(HARNESS.sha1_file(jar), provenance["server_sha1"])


class JsonCatalogTests(unittest.TestCase):
    def test_catalog_separates_registry_ids_from_observed_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            generated = Path(temporary) / "generated"
            reports = generated / "reports"
            data = generated / "data" / "minecraft"
            reports.mkdir(parents=True)
            (data / "dimension").mkdir(parents=True)
            (data / "dimension_type").mkdir(parents=True)
            (data / "enchantment").mkdir()
            (data / "cat_variant").mkdir()
            (data / "worldgen" / "configured_feature").mkdir(parents=True)
            (generated / HARNESS.REPORT_PROVENANCE_FILE).write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "version": "test",
                        "server_sha1": "fixture",
                    }
                ),
                encoding="utf-8",
            )
            (reports / "registries.json").write_text(
                json.dumps(
                    {
                        "minecraft:data_component_type": {
                            "entries": {
                                "minecraft:custom_name": {},
                                "minecraft:max_stack_size": {},
                            }
                        },
                        "minecraft:enchantment_value_effect_type": {
                            "entries": {"minecraft:add": {}}
                        },
                        "minecraft:loot_condition_type": {
                            "entries": {"minecraft:random_chance": {}}
                        },
                        "minecraft:loot_function_type": {
                            "entries": {"minecraft:set_count": {}}
                        },
                        "minecraft:recipe_serializer": {
                            "entries": {"minecraft:crafting_shaped": {}}
                        },
                        "minecraft:trigger_type": {
                            "entries": {"minecraft:tick": {}}
                        },
                        "minecraft:frog_variant": {
                            "entries": {"minecraft:temperate": {}}
                        },
                        "minecraft:worldgen/feature": {
                            "entries": {"minecraft:ore": {}}
                        },
                        "minecraft:worldgen/structure_processor": {
                            "entries": {"minecraft:block_ignore": {}}
                        },
                    }
                ),
                encoding="utf-8",
            )
            (reports / "datapack.json").write_text(
                json.dumps(
                    {
                        "registries": {
                            "minecraft:cat_variant": {
                                "elements": True,
                                "tags": True,
                            },
                            "minecraft:dimension_type": {
                                "elements": True,
                                "tags": False,
                            },
                        }
                    }
                ),
                encoding="utf-8",
            )
            (reports / "items.json").write_text(
                json.dumps(
                    {
                        "minecraft:stick": {
                            "components": [
                                {
                                    "type": "minecraft:max_stack_size",
                                    "value": 64,
                                }
                            ]
                        },
                        "minecraft:stone": {
                            "components": [
                                {
                                    "type": "minecraft:max_stack_size",
                                    "value": 64,
                                }
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )
            (data / "dimension" / "overworld.json").write_text(
                json.dumps(
                    {
                        "type": "minecraft:overworld",
                        "generator": {"type": "minecraft:noise"},
                    }
                ),
                encoding="utf-8",
            )
            (data / "dimension_type" / "overworld.json").write_text(
                json.dumps(
                    {
                        "ambient_light": 0.0,
                        "monster_spawn_light_level": {
                            "min_inclusive": 0,
                            "max_inclusive": 7,
                        },
                    }
                ),
                encoding="utf-8",
            )
            (data / "enchantment" / "test.json").write_text(
                json.dumps({"max_level": 2, "effects": {}}),
                encoding="utf-8",
            )
            (data / "cat_variant" / "test.json").write_text(
                json.dumps({"asset_id": "example:test"}),
                encoding="utf-8",
            )
            (data / "worldgen" / "configured_feature" / "test.json").write_text(
                json.dumps({"type": "minecraft:ore", "config": {}}),
                encoding="utf-8",
            )
            (data / "advancement").mkdir()
            (data / "advancement" / "test.json").write_text(
                json.dumps(
                    {
                        "criteria": {
                            "tick": {"trigger": "minecraft:tick"}
                        }
                    }
                ),
                encoding="utf-8",
            )
            (data / "loot_table").mkdir()
            (data / "loot_table" / "test.json").write_text(
                json.dumps({"type": "minecraft:generic", "pools": []}),
                encoding="utf-8",
            )
            (data / "recipe").mkdir()
            (data / "recipe" / "test.json").write_text(
                json.dumps(
                    {
                        "type": "minecraft:crafting_shaped",
                        "pattern": ["#"],
                        "key": {"#": "minecraft:stick"},
                        "result": {"id": "minecraft:stick"},
                    }
                ),
                encoding="utf-8",
            )

            catalog = HARNESS.build_json_catalog("test", generated)

            self.assertEqual(
                ["minecraft:custom_name", "minecraft:max_stack_size"],
                catalog["registry_ids"]["item_component_types"],
            )
            self.assertEqual(
                ["minecraft:ore"],
                catalog["worldgen_dispatchers"]["minecraft:worldgen/feature"],
            )
            self.assertEqual(
                ["minecraft:block_ignore"],
                catalog["worldgen_dispatchers"][
                    "minecraft:worldgen/structure_processor"
                ],
            )
            self.assertEqual(
                ["minecraft:random_chance"],
                catalog["registry_ids"]["loot_condition_types"],
            )
            self.assertEqual(
                ["minecraft:tick"],
                catalog["registry_ids"]["advancement_trigger_types"],
            )
            self.assertEqual(
                ["minecraft:cat_variant", "minecraft:frog_variant"],
                catalog["variant_registries"],
            )
            self.assertEqual(
                ["minecraft:cat_variant"],
                catalog["data_driven_variant_registries"],
            )
            dimension_fields = catalog["observed_shapes"]["dimension"]["fields"]
            self.assertEqual(["string"], dimension_fields["$.type"])
            self.assertEqual(["object"], dimension_fields["$.generator"])
            dimension_fields = catalog["observed_shapes"]["dimension_type"]["fields"]
            self.assertEqual(["number"], dimension_fields["$.ambient_light"])
            self.assertEqual(
                ["integer"],
                dimension_fields[
                    "$.monster_spawn_light_level.max_inclusive"
                ],
            )
            self.assertIn(
                "not a complete codec schema",
                catalog["coverage"]["observed_shapes"],
            )
            item_defaults = catalog["observed_shapes"]["item_defaults"]
            self.assertEqual(2, item_defaults["record_count"])
            self.assertEqual(
                ["integer"],
                item_defaults["fields"]["$.components[].value"],
            )
            self.assertEqual(
                ["string"],
                catalog["observed_shapes"]["advancement"]["fields"][
                    "$.criteria.tick.trigger"
                ],
            )
            self.assertEqual(
                ["array"],
                catalog["observed_shapes"]["loot_table"]["fields"]["$.pools"],
            )
            self.assertEqual(
                ["array"],
                catalog["observed_shapes"]["recipe"]["fields"]["$.pattern"],
            )
            self.assertFalse(
                any("minecraft:stick" in path for path in item_defaults["fields"])
            )

            with self.assertRaisesRegex(
                HARNESS.HarnessError,
                "does not match requested version",
            ):
                HARNESS.build_json_catalog("other", generated)

    def test_catalog_distinguishes_empty_and_unpublished_registries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            generated = Path(temporary) / "generated"
            reports = generated / "reports"
            data = generated / "data" / "minecraft"
            reports.mkdir(parents=True)
            data.mkdir(parents=True)
            (generated / HARNESS.REPORT_PROVENANCE_FILE).write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "version": "test",
                        "server_sha1": "fixture",
                    }
                ),
                encoding="utf-8",
            )
            (reports / "registries.json").write_text(
                json.dumps(
                    {
                        "minecraft:loot_pool_entry_type": {
                            "entries": {}
                        }
                    }
                ),
                encoding="utf-8",
            )

            catalog = HARNESS.build_json_catalog("test", generated)

            self.assertEqual([], catalog["registry_ids"]["loot_entry_types"])
            self.assertEqual([], catalog["registry_ids"]["recipe_types"])
            self.assertEqual(
                {"minecraft:loot_pool_entry_type": "present"},
                catalog["registry_sources"]["loot_entry_types"],
            )
            self.assertEqual(
                {"minecraft:recipe_type": "unknown"},
                catalog["registry_sources"]["recipe_types"],
            )

    def test_catalog_reads_split_item_component_reports(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            generated = Path(temporary) / "generated"
            reports = generated / "reports"
            data = generated / "data" / "minecraft"
            item_reports = reports / "minecraft" / "components" / "item"
            item_reports.mkdir(parents=True)
            data.mkdir(parents=True)
            (generated / HARNESS.REPORT_PROVENANCE_FILE).write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "version": "26.2",
                        "server_sha1": "fixture",
                    }
                ),
                encoding="utf-8",
            )
            (reports / "registries.json").write_text("{}", encoding="utf-8")
            (item_reports / "stick.json").write_text(
                json.dumps(
                    {
                        "minecraft:max_stack_size": 64,
                        "minecraft:item_name": {
                            "translate": "item.minecraft.stick"
                        },
                    }
                ),
                encoding="utf-8",
            )
            (item_reports / "stone.json").write_text(
                json.dumps({"minecraft:max_stack_size": 64}),
                encoding="utf-8",
            )

            catalog = HARNESS.build_json_catalog("26.2", generated)
            item_defaults = catalog["observed_shapes"]["item_defaults"]
            self.assertEqual(2, item_defaults["file_count"])
            self.assertEqual(2, item_defaults["record_count"])
            self.assertEqual(
                "reports/<namespace>/components/item/<path>.json",
                item_defaults["layout"],
            )
            self.assertEqual(
                ["integer"],
                item_defaults["fields"]["$.minecraft:max_stack_size"],
            )

    def test_catalog_reads_legacy_worldgen_report_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            generated = Path(temporary) / "generated"
            reports = generated / "reports"
            data = generated / "data" / "minecraft"
            legacy = reports / "worldgen" / "minecraft"
            transitional = reports / "minecraft"
            (legacy / "dimension").mkdir(parents=True)
            (legacy / "dimension_type").mkdir(parents=True)
            (legacy / "worldgen" / "configured_structure_feature").mkdir(
                parents=True
            )
            (transitional / "dimension").mkdir(parents=True)
            data.mkdir(parents=True)
            (generated / HARNESS.REPORT_PROVENANCE_FILE).write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "version": "1.18.2",
                        "server_sha1": "fixture",
                    }
                ),
                encoding="utf-8",
            )
            (reports / "registries.json").write_text("{}", encoding="utf-8")
            (legacy / "dimension" / "overworld.json").write_text(
                json.dumps(
                    {
                        "type": "minecraft:overworld",
                        "generator": {"type": "minecraft:noise"},
                    }
                ),
                encoding="utf-8",
            )
            (transitional / "dimension" / "the_end.json").write_text(
                json.dumps(
                    {
                        "type": "minecraft:the_end",
                        "generator": {"type": "minecraft:noise"},
                    }
                ),
                encoding="utf-8",
            )
            (legacy / "dimension_type" / "overworld.json").write_text(
                json.dumps({"ambient_light": 0.0}),
                encoding="utf-8",
            )
            (
                legacy
                / "worldgen"
                / "configured_structure_feature"
                / "village.json"
            ).write_text(
                json.dumps({"type": "minecraft:jigsaw"}),
                encoding="utf-8",
            )

            catalog = HARNESS.build_json_catalog("1.18.2", generated)
            self.assertEqual(
                2,
                catalog["observed_shapes"]["dimension"]["file_count"],
            )
            self.assertEqual(
                ["string"],
                catalog["observed_shapes"]["dimension"]["fields"]["$.type"],
            )
            self.assertEqual(
                ["number"],
                catalog["observed_shapes"]["dimension_type"]["fields"][
                    "$.ambient_light"
                ],
            )
            self.assertEqual(
                ["string"],
                catalog["observed_shapes"]["worldgen"]["fields"]["$.type"],
            )


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
        boundary_cases = {
            "1.13": (
                "There are 2 data packs enabled: "
                "[vanilla], [file/pack-under-test]"
            ),
            "1.17": (
                "There are 2 data packs enabled: "
                "[vanilla], [file/pack-under-test]"
            ),
            "1.18": (
                "There are 2 data pack(s) enabled: "
                "[vanilla (built-in)], [file/pack-under-test (world)]"
            ),
            "1.20.5": (
                "There are 2 data pack(s) enabled: "
                "[vanilla (built-in)], [file/pack-under-test (world)]"
            ),
            "1.21.9": (
                "There are 2 data pack(s) enabled: "
                "[vanilla (built-in)], [file/pack-under-test (world)]"
            ),
            "26.2": (
                "There are 2 data pack(s) enabled: "
                "[vanilla (built-in)], [file/pack-under-test (world)]"
            ),
        }
        for version, enabled in boundary_cases.items():
            with self.subTest(version=version):
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
            def __init__(
                self,
                *,
                pack_enabled: bool = True,
                reload_lines: tuple[str, ...] | None = None,
            ) -> None:
                self.returncode: int | None = None
                self.lines: queue.Queue[str | None] = queue.Queue()
                self.lines.put('[Server thread/INFO]: Done (1.0s)! For help, type "help"\n')
                self.commands: list[str] = []
                self.pack_enabled = pack_enabled
                self.reload_lines = reload_lines or (
                    "Reloading!\n",
                    "[Server thread/INFO]: PACK_TEST_LOAD_OK\n",
                    "Loaded 1250 advancements\n",
                )
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
                        if self.pack_enabled:
                            self.lines.put(
                                "There are 2 data pack(s) enabled: "
                                "[vanilla (built-in)], "
                                "[file/pack-under-test (world)]\n"
                            )
                        else:
                            self.lines.put(
                                "There are 1 data pack(s) enabled: "
                                "[vanilla (built-in)]\n"
                            )
                    elif command == "reload":
                        for line in self.reload_lines:
                            self.lines.put(line)
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

        failed_process = FakeProcess(pack_enabled=False)
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
                    return_value=failed_process,
                ),
            ):
                with self.assertRaises(HARNESS.ServerTestError) as raised:
                    HARNESS.server_test(
                        "1.20.5",
                        pack,
                        "java",
                        root / "cache",
                        2,
                        True,
                    )

        self.assertIn("Done (1.0s)", raised.exception.log)
        self.assertIn(
            "file/pack-under-test is absent",
            raised.exception.log,
        )

        failure_cases = (
            (
                FakeProcess(reload_lines=("Reloading!\n",)),
                0.05,
                "reload completion",
            ),
            (
                FakeProcess(
                    reload_lines=(
                        "Reloading!\n",
                        "Couldn't load function example:test\n",
                    )
                ),
                2,
                "couldn't load",
            ),
        )
        for failed_process, timeout, expected in failure_cases:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as temporary:
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
                        return_value=failed_process,
                    ),
                ):
                    with self.assertRaises(HARNESS.ServerTestError) as raised:
                        HARNESS.server_test(
                            "1.20.5",
                            pack,
                            "java",
                            root / "cache",
                            timeout,
                            True,
                        )
                self.assertIn(expected, raised.exception.log.lower())

    def test_main_saves_server_log_when_server_test_raises(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            log_path = Path(temporary) / "nested" / "server.log"
            error = HARNESS.ServerTestError(
                "reload completion timed out",
                "Reloading!\npartial server output\n",
            )
            with mock.patch.object(
                HARNESS,
                "server_test",
                side_effect=error,
            ), contextlib.redirect_stderr(io.StringIO()):
                status = HARNESS.main(
                    [
                        "server-test",
                        "1.20.5",
                        "unused-pack",
                        "--accept-eula",
                        "--log",
                        str(log_path),
                    ]
                )

            self.assertEqual(1, status)
            self.assertEqual(error.log, log_path.read_text(encoding="utf-8"))
            self.assertIn("partial server output", error.log)
            self.assertIn("reload completion timed out", error.log)


if __name__ == "__main__":
    unittest.main()
