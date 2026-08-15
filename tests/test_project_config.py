from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "minecraft-datapack"
SPEC = importlib.util.spec_from_file_location(
    "datapack_harness_project_tests",
    SKILL / "tools" / "datapack_harness.py",
)
assert SPEC is not None and SPEC.loader is not None
HARNESS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = HARNESS
SPEC.loader.exec_module(HARNESS)


def template_config() -> dict[str, Any]:
    return json.loads(
        (SKILL / "templates" / "datapack-project.json").read_text(
            encoding="utf-8"
        )
    )


def installed_or_archive_commit() -> str:
    return HARNESS.installed_git_commit() or ("a" * 40)


class ProjectConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profiles = HARNESS.load_profiles()

    def write_project(
        self,
        root: Path,
        config: dict[str, Any],
    ) -> Path:
        path = root / "datapack-project.json"
        path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def test_distributed_schema_and_template_are_valid_json(self) -> None:
        schema = json.loads(
            (SKILL / "schemas" / "datapack-project.schema.json").read_text(
                encoding="utf-8"
            )
        )
        config = template_config()
        self.assertEqual(1, schema["properties"]["schema_version"]["const"])
        self.assertEqual(
            {
                "schema_version",
                "target_version",
                "namespace",
                "pack_root",
                "validation_level",
            },
            set(schema["required"]),
        )
        self.assertNotIn("harness", config)
        self.assertEqual(
            {"generated", "static", "server", "functional"},
            set(HARNESS.VALIDATION_LEVELS),
        )

    def test_consumer_workflow_is_static_and_installation_agnostic(self) -> None:
        workflow = (
            SKILL / "templates" / "github" / "workflows" / "datapack-harness.yml"
        ).read_text(encoding="utf-8")
        self.assertEqual(1, workflow.count("datapack_harness.py"))
        self.assertIn("validate-project", workflow)
        self.assertNotIn("submodules:", workflow)

    def test_minimal_template_passes_and_applies_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.write_project(Path(temporary), template_config())
            config, result = HARNESS.validate_project_config(
                project,
                self.profiles,
            )
        self.assertIsNotNone(config)
        self.assertEqual([], result.errors)
        self.assertEqual([], result.warnings)
        self.assertEqual("java", config["edition"])
        self.assertEqual(
            {"min": "1.20.5", "max": "1.20.5"},
            config["supported_versions"],
        )
        self.assertFalse(config["experimental_features"])
        self.assertEqual("vanilla", config["server_type"])
        self.assertEqual(".cache/minecraft", config["cache_dir"])
        self.assertEqual(
            "build/minecraft/1.20.5/generated",
            config["report_dir"],
        )

    def test_optional_provenance_passes_without_warnings(self) -> None:
        config = template_config()
        config["harness"] = {
            "version": HARNESS.HARNESS_VERSION,
            "source": "https://github.com/asgrcat/mc-datapack-harness",
            "commit": installed_or_archive_commit(),
        }
        with tempfile.TemporaryDirectory() as temporary:
            project = self.write_project(Path(temporary), config)
            loaded, result = HARNESS.validate_project_config(
                project,
                self.profiles,
            )
        self.assertIsNotNone(loaded)
        self.assertEqual(config["harness"], loaded["harness"])
        self.assertEqual([], result.errors)
        self.assertEqual([], result.warnings)

    def test_skill_does_not_assume_parent_repository_metadata(self) -> None:
        self.assertIsNone(HARNESS.installed_git_commit())

    def test_invalid_project_fields_fail_closed(self) -> None:
        cases = {
            "target_version": "1.20.5-rc1",
            "namespace": "Uppercase",
            "pack_root": "../outside",
            "validation_level": "automatic-server",
            "edition": "bedrock",
            "experimental_features": "false",
            "server_type": "paper",
            "cache_dir": "../cache",
            "report_dir": "/tmp/reports",
        }
        for field, value in cases.items():
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                config = template_config()
                config[field] = value
                project = self.write_project(Path(temporary), config)
                _, result = HARNESS.validate_project_config(
                    project,
                    self.profiles,
                )
                self.assertTrue(result.errors)

    def test_unknown_and_invalid_optional_fields_fail_closed(self) -> None:
        cases = (
            {"unexpected": True},
            {"harness": {"unexpected": True}},
            {"harness": None},
            {"$schema": None},
        )
        for additions in cases:
            with self.subTest(additions=additions), tempfile.TemporaryDirectory() as temporary:
                config = template_config()
                config.update(additions)
                project = self.write_project(Path(temporary), config)
                _, result = HARNESS.validate_project_config(
                    project,
                    self.profiles,
                )
                self.assertTrue(result.errors)

    def test_target_must_be_inside_supported_range(self) -> None:
        config = template_config()
        config["supported_versions"] = {
            "min": "1.21",
            "max": "1.21.1",
        }
        with tempfile.TemporaryDirectory() as temporary:
            project = self.write_project(Path(temporary), config)
            _, result = HARNESS.validate_project_config(
                project,
                self.profiles,
            )
        self.assertTrue(
            any("outside supported_versions" in error for error in result.errors)
        )

    def test_snapshot_target_requires_explicit_experimental_opt_in(self) -> None:
        config = template_config()
        config["target_version"] = "26.3-snapshot-6"
        config["supported_versions"] = {
            "min": "26.3-snapshot-6",
            "max": "26.3-snapshot-6",
        }
        with tempfile.TemporaryDirectory() as temporary:
            project = self.write_project(Path(temporary), config)
            _, result = HARNESS.validate_project_config(
                project,
                self.profiles,
            )
            self.assertTrue(
                any(
                    "requires experimental_features: true" in error
                    for error in result.errors
                )
            )

            config["experimental_features"] = True
            project = self.write_project(Path(temporary), config)
            loaded, result = HARNESS.validate_project_config(
                project,
                self.profiles,
            )
        self.assertIsNotNone(loaded)
        self.assertEqual([], result.errors)

    def test_project_check_works_from_nested_harness_layout(self) -> None:
        config = template_config()
        with tempfile.TemporaryDirectory() as temporary:
            project = self.write_project(Path(temporary), config)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = HARNESS.main(
                    ["project-check", "--project", str(project)]
                )
        self.assertEqual(0, status)
        payload = json.loads(output.getvalue())
        self.assertEqual("1.20.5", payload["target_version"])
        self.assertEqual("static", payload["validation_level"])

    def test_cli_runs_after_distribution_is_nested(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            consumer = Path(temporary) / "consumer"
            harness_root = consumer / "tools" / "mc-datapack-harness"
            shutil.copytree(SKILL, harness_root)

            completed = subprocess.run(
                [
                    sys.executable,
                    str(harness_root / "tools" / "datapack_harness.py"),
                    "profiles",
                ],
                cwd=consumer,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("validated 58 profiles", completed.stdout)

    def test_validate_project_uses_configured_pack_root(self) -> None:
        config = template_config()
        config["validation_level"] = "server"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = self.write_project(root, config)
            pack = root / "datapack"
            pack.mkdir()
            (pack / "pack.mcmeta").write_text(
                json.dumps(
                    {
                        "pack": {
                            "pack_format": 41,
                            "description": "consumer test",
                        }
                    }
                ),
                encoding="utf-8",
            )
            function = (
                pack
                / "data"
                / "example"
                / "functions"
                / "load.mcfunction"
            )
            function.parent.mkdir(parents=True)
            function.write_text("say loaded\n", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = HARNESS.main(
                    ["validate-project", "--project", str(project)]
                )

        self.assertEqual(0, status)
        text = output.getvalue()
        self.assertIn("completed validation level: static", text)
        self.assertIn("requested validation level: server", text)
        self.assertIn("remaining validation: server", text)


if __name__ == "__main__":
    unittest.main()
