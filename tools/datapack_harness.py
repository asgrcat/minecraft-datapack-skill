#!/usr/bin/env python3
"""Minecraft Java Edition data pack profile and validation harness.

The standard library is sufficient. Network access is used only by ``fetch`` and
commands that call it. Minecraft itself remains the authority for Brigadier and
codec validation; this tool deliberately reports when a check is only static.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VERSIONS_DIR = REPOSITORY_ROOT / "docs" / "versions"
PROFILE_SCHEMA_PATH = VERSIONS_DIR / "profile.schema.json"
VERSION_MANIFEST_URL = (
    "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
)
RESOURCE_LOCATION_SCAN = re.compile(r"(?<![#A-Za-z0-9_.-])([a-z0-9_.-]+:[a-z0-9/._-]+)")
PATH_PART = re.compile(r"^[a-z0-9/._-]+$")
FUNCTION_REFERENCE = re.compile(
    r"(?:^|\s)(?:function|schedule\s+function)\s+"
    r"(#?[a-z0-9_.-]+:[a-z0-9/._-]+)"
)
ERROR_LOG_PATTERNS = (
    "couldn't load",
    "couldn't parse",
    "failed to load",
    "failed to parse",
    "unknown function",
    "error loading",
    "error parsing",
    "exception loading",
    "not a json",
    "syntax error",
    "errors in currently selected datapacks",
    "failed to validate datapack",
    "failed to execute reload",
    "failed to reload",
)
ENABLED_PACK_ID = "file/pack-under-test"
ENABLED_LIST_PATTERN = re.compile(
    r"\bdata pack(?:\(s\)|s)? enabled:",
    re.IGNORECASE,
)
RELOAD_STARTED_PATTERN = re.compile(r"\bReloading!\s*$", re.IGNORECASE | re.MULTILINE)
RELOAD_COMPLETED_PATTERN = re.compile(
    r"\bLoaded\s+\d+\s+advancements\b",
    re.IGNORECASE,
)
MAX_MINOR_VERSION = 0x7FFFFFFF


class HarnessError(RuntimeError):
    """Expected command-line failure."""


class ServerTestError(HarnessError):
    """Server-test failure with the collected disposable-server log."""

    def __init__(self, message: str, log: str) -> None:
        super().__init__(message)
        self.log = append_harness_error(log, message)


def append_harness_error(log: str, message: str) -> str:
    separator = "" if not log or log.endswith("\n") else "\n"
    return f"{log}{separator}[HARNESS] ERROR: {message}\n"


def load_profile_schema() -> dict[str, Any]:
    try:
        return json.loads(PROFILE_SCHEMA_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise HarnessError(f"missing schema: {PROFILE_SCHEMA_PATH}") from error
    except json.JSONDecodeError as error:
        raise HarnessError(f"{PROFILE_SCHEMA_PATH}: invalid JSON: {error}") from error


PROFILE_SCHEMA = load_profile_schema()
PROFILE_REQUIRED = set(PROFILE_SCHEMA["required"])
PROFILE_ALLOWED = set(PROFILE_SCHEMA["properties"])
COMPATIBILITY_CLASSES = set(
    PROFILE_SCHEMA["properties"]["compatibility"]["enum"]
)
COMPATIBILITY_TAGS = set(
    PROFILE_SCHEMA["properties"]["compatibility_tags"]["items"]["enum"]
)


def parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if value == "null":
        return None
    if value.startswith('"') or value.startswith("["):
        try:
            return json.loads(value)
        except json.JSONDecodeError as error:
            raise HarnessError(f"invalid front matter value {value!r}: {error}") from error
    return value


def read_profile(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise HarnessError(f"{path}: front matter must start with ---")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise HarnessError(f"{path}: front matter is not closed") from error

    profile: dict[str, Any] = {}
    for number, line in enumerate(lines[1:end], start=2):
        if not line.strip():
            continue
        if ":" not in line:
            raise HarnessError(f"{path}:{number}: expected key: value")
        key, raw = line.split(":", 1)
        key = key.strip()
        if key in profile:
            raise HarnessError(f"{path}:{number}: duplicate field {key}")
        profile[key] = parse_scalar(raw)
    profile["_path"] = path
    return profile


def extract_ai_rules(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    rules: list[str] = []
    active = False
    for line in lines:
        if line == "## AI 生成規則":
            active = True
            continue
        if active and line.startswith("## "):
            break
        if active and line.startswith("- "):
            rules.append(line[2:].strip())
        elif active and line.strip() and not line.startswith("#"):
            rules.append(line.strip())
    return rules


def profile_files() -> list[Path]:
    return sorted(
        path
        for path in VERSIONS_DIR.glob("*.md")
        if path.name != "README.md"
    )


def load_profiles() -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for path in profile_files():
        profile = read_profile(path)
        version_value = profile.get("version")
        version = (
            version_value
            if isinstance(version_value, str)
            else f"<invalid:{path.name}>"
        )
        if version in profiles:
            raise HarnessError(f"duplicate profile version: {version}")
        profiles[version] = profile
    return profiles


def validate_profile(
    profile: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
) -> list[str]:
    path = Path(profile["_path"])
    errors: list[str] = []
    public = set(profile) - {"_path"}
    missing = PROFILE_REQUIRED - public
    unknown = public - PROFILE_ALLOWED
    if missing:
        errors.append(f"{path}: missing fields: {', '.join(sorted(missing))}")
    if unknown:
        errors.append(f"{path}: unknown fields: {', '.join(sorted(unknown))}")

    version = profile.get("version")
    version_pattern = PROFILE_SCHEMA["properties"]["version"]["pattern"]
    if not isinstance(version, str) or not re.fullmatch(version_pattern, version):
        errors.append(f"{path}: invalid version")
    elif path.stem != version:
        errors.append(f"{path}: filename and version differ")
    if profile.get("edition") != "java":
        errors.append(f"{path}: edition must be java")
    directory_schema = profile.get("directory_schema")
    if not isinstance(directory_schema, str) or directory_schema not in {
        "plural",
        "singular",
    }:
        errors.append(f"{path}: invalid directory_schema")
    compatibility = profile.get("compatibility")
    if (
        not isinstance(compatibility, str)
        or compatibility not in COMPATIBILITY_CLASSES
    ):
        errors.append(f"{path}: invalid compatibility class")

    tags = profile.get("compatibility_tags", [])
    if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
        errors.append(f"{path}: compatibility_tags must be a string array")
    else:
        invalid_tags = set(tags) - COMPATIBILITY_TAGS
        if invalid_tags:
            errors.append(
                f"{path}: invalid compatibility_tags: "
                f"{', '.join(sorted(invalid_tags))}"
            )
        if len(tags) != len(set(tags)):
            errors.append(f"{path}: compatibility_tags contains duplicates")

    release_date = profile.get("release_date")
    try:
        if not isinstance(release_date, str):
            raise ValueError
        datetime.date.fromisoformat(release_date)
    except ValueError:
        errors.append(f"{path}: release_date must be YYYY-MM-DD")
    pack_format = profile.get("data_pack_format")
    if not isinstance(pack_format, str) or not re.fullmatch(
        r"\d+(?:\.\d+)?", pack_format
    ):
        errors.append(f"{path}: invalid data_pack_format")

    parent = profile.get("inherits")
    if parent is not None and not isinstance(parent, str):
        errors.append(f"{path}: inherits must be a version string or null")
    elif parent is not None and parent not in profiles:
        errors.append(f"{path}: inherits missing profile {parent}")
    if not extract_ai_rules(path):
        errors.append(f"{path}: AI 生成規則 must contain at least one rule")
    return errors


def resolve_chain(
    version: str,
    profiles: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    if version not in profiles:
        raise HarnessError(f"unsupported formal release profile: {version}")
    chain: list[dict[str, Any]] = []
    seen: set[str] = set()
    current: str | None = version
    while current is not None:
        if current in seen:
            raise HarnessError(f"inheritance cycle at {current}")
        seen.add(current)
        profile = profiles[current]
        chain.append(profile)
        current = profile["inherits"]
    chain.reverse()
    return chain


def ordered_versions(profiles: dict[str, dict[str, Any]]) -> list[str]:
    if not profiles:
        return []
    leaves = set(profiles)
    for profile in profiles.values():
        parent = profile.get("inherits")
        if parent is not None:
            leaves.discard(parent)
    if len(leaves) != 1:
        raise HarnessError(f"profiles must form one linear chain; leaves={sorted(leaves)}")
    leaf = next(iter(leaves))
    return [profile["version"] for profile in resolve_chain(leaf, profiles)]


def validate_all_profiles(profiles: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for profile in profiles.values():
        errors.extend(validate_profile(profile, profiles))
    try:
        order = ordered_versions(profiles)
        if len(order) != len(profiles):
            errors.append("not every profile is reachable from the latest release")
    except HarnessError as error:
        errors.append(str(error))
    return errors


def public_profile(profile: dict[str, Any]) -> dict[str, Any]:
    result = {key: value for key, value in profile.items() if key != "_path"}
    result.setdefault("compatibility_tags", [])
    return result


def resolved_profile_payload(
    version: str,
    profiles: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    chain = resolve_chain(version, profiles)
    target = chain[-1]
    return {
        "profile": public_profile(target),
        "inheritance_chain": [profile["version"] for profile in chain],
        "active_ai_rules": extract_ai_rules(Path(target["_path"])),
        "rule_history": [
            {
                "version": profile["version"],
                "rules": extract_ai_rules(Path(profile["_path"])),
            }
            for profile in chain[:-1]
        ],
        "capability_authority": {
            "commands": "generated/reports/commands.json",
            "registries": "generated/reports/registries.json",
            "vanilla_data": "generated/data/minecraft",
        },
        "required_java_major": required_java_major(version, profiles),
    }


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "mc-datapack-docs-harness/1"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def sha1_file(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "mc-datapack-docs-harness/1"},
    )
    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            with temporary.open("wb") as output:
                shutil.copyfileobj(response, output)
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def fetch_release(version: str, cache_dir: Path) -> tuple[Path, dict[str, Any]]:
    manifest = fetch_json(VERSION_MANIFEST_URL)
    matches = [
        item
        for item in manifest.get("versions", [])
        if item.get("id") == version and item.get("type") == "release"
    ]
    if len(matches) != 1:
        raise HarnessError(
            f"official manifest has {len(matches)} exact release matches for {version}"
        )
    metadata = fetch_json(matches[0]["url"])
    server = metadata.get("downloads", {}).get("server")
    if not server:
        raise HarnessError(f"{version}: official metadata has no server download")

    release_dir = cache_dir / version
    jar_path = release_dir / "server.jar"
    metadata_path = release_dir / "version.json"
    if not jar_path.exists() or sha1_file(jar_path) != server["sha1"]:
        download_file(server["url"], jar_path)
    actual = sha1_file(jar_path)
    if actual != server["sha1"]:
        raise HarnessError(
            f"{version}: SHA-1 mismatch: expected {server['sha1']}, got {actual}"
        )
    release_dir.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return jar_path, metadata


def required_java_major(version: str, profiles: dict[str, dict[str, Any]]) -> int:
    order = ordered_versions(profiles)
    index = order.index(version)
    if index >= order.index("26.1"):
        return 25
    if index >= order.index("1.20.5"):
        return 21
    if index >= order.index("1.18"):
        return 17
    if index >= order.index("1.17"):
        return 16
    return 8


def run_reports(
    version: str,
    java: str,
    cache_dir: Path,
    output: Path,
    profiles: dict[str, dict[str, Any]],
) -> None:
    jar_path, _ = fetch_release(version, cache_dir)
    jar_path = jar_path.resolve()
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    order = ordered_versions(profiles)
    if order.index(version) <= order.index("1.17.1"):
        command = [
            java,
            "-cp",
            str(jar_path),
            "net.minecraft.data.Main",
            "--reports",
            "--server",
            "--output",
            str(output),
        ]
    else:
        command = [
            java,
            "-DbundlerMainClass=net.minecraft.data.Main",
            "-jar",
            str(jar_path),
            "--reports",
            "--server",
            "--output",
            str(output),
        ]
    print(
        f"running data generator with Java {required_java_major(version, profiles)} "
        f"target: {' '.join(command)}",
        file=sys.stderr,
    )
    with tempfile.TemporaryDirectory(
        prefix="mc-datapack-reports-"
    ) as working_directory:
        completed = subprocess.run(
            command,
            cwd=working_directory,
            check=False,
        )
    if completed.returncode:
        raise HarnessError(f"data generator exited with {completed.returncode}")


def format_tuple(raw: str) -> tuple[int, int]:
    major, dot, minor = raw.partition(".")
    return int(major), int(minor) if dot else 0


def metadata_format_tuple(
    value: Any,
    *,
    integer_is_major_maximum: bool = False,
) -> tuple[int, int] | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value, MAX_MINOR_VERSION if integer_is_major_maximum else 0
    if (
        isinstance(value, list)
        and len(value) in {1, 2}
        and all(isinstance(part, int) and not isinstance(part, bool) for part in value)
    ):
        if len(value) == 2:
            return value[0], value[1]
        return (
            value[0],
            MAX_MINOR_VERSION if integer_is_major_maximum else 0,
        )
    return None


def contains_target_format(pack: dict[str, Any], target: tuple[int, int]) -> bool:
    minimum = metadata_format_tuple(pack.get("min_format"))
    maximum = metadata_format_tuple(
        pack.get("max_format"),
        integer_is_major_maximum=True,
    )
    if minimum is not None and maximum is not None:
        return minimum <= target <= maximum

    supported = pack.get("supported_formats")
    if isinstance(supported, int) and not isinstance(supported, bool):
        return target == (supported, 0)
    if isinstance(supported, list) and len(supported) == 2:
        low = metadata_format_tuple(supported[0])
        high = metadata_format_tuple(supported[1])
        return low is not None and high is not None and low <= target <= high
    if isinstance(supported, dict):
        low = metadata_format_tuple(supported.get("min_inclusive"))
        high = metadata_format_tuple(supported.get("max_inclusive"))
        return low is not None and high is not None and low <= target <= high

    legacy = metadata_format_tuple(pack.get("pack_format"))
    return legacy == target


def generated_root(reports: Path) -> Path:
    if (reports / "reports").is_dir() or (reports / "data").is_dir():
        return reports
    if (reports / "generated").is_dir():
        return reports / "generated"
    return reports


def load_command_roots(reports: Path | None) -> set[str] | None:
    if reports is None:
        return None
    root = generated_root(reports)
    commands_path = root / "reports" / "commands.json"
    if not commands_path.is_file():
        raise HarnessError(f"commands report not found: {commands_path}")
    commands = json.loads(commands_path.read_text(encoding="utf-8"))
    return set(commands.get("children", {}))


def load_registry_ids(reports: Path | None) -> set[str]:
    if reports is None:
        return set()
    root = generated_root(reports)
    registries_path = root / "reports" / "registries.json"
    if not registries_path.is_file():
        raise HarnessError(f"registries report not found: {registries_path}")
    registries = json.loads(registries_path.read_text(encoding="utf-8"))
    values: set[str] = set()
    for registry in registries.values():
        entries = registry.get("entries", {}) if isinstance(registry, dict) else {}
        values.update(entries)
    return values


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def resource_id_for_file(path: Path, pack_root: Path, schema: str) -> str | None:
    relative = path.relative_to(pack_root)
    parts = relative.parts
    if len(parts) < 4 or parts[0] != "data":
        return None
    namespace = parts[1]
    kind = parts[2]
    expected = "function" if schema == "singular" else "functions"
    if kind != expected or path.suffix != ".mcfunction":
        return None
    resource_path = Path(*parts[3:]).with_suffix("").as_posix()
    return f"{namespace}:{resource_path}"


def logical_function_lines(text: str) -> Iterable[tuple[int, str]]:
    buffer = ""
    start = 0
    for number, physical in enumerate(text.splitlines(), start=1):
        stripped_right = physical.rstrip()
        if not buffer:
            start = number
        if (
            stripped_right.endswith("\\")
            and not stripped_right.lstrip().startswith("#")
        ):
            buffer += stripped_right[:-1].strip() + " "
            continue
        logical = (buffer + physical.strip()).strip()
        buffer = ""
        if logical:
            yield start, logical
    if buffer:
        yield start, buffer.rstrip()


def validate_pack(
    version: str,
    pack_root: Path,
    reports: Path | None,
    profiles: dict[str, dict[str, Any]],
) -> ValidationResult:
    result = ValidationResult()
    profile = profiles[version]
    schema = profile["directory_schema"]
    pack_root = pack_root.resolve()
    if not pack_root.is_dir():
        result.error(f"pack path is not a directory: {pack_root}")
        return result

    metadata_path = pack_root / "pack.mcmeta"
    metadata: Any = None
    metadata_parsed = False
    if not metadata_path.is_file():
        result.error("pack.mcmeta is missing")
    else:
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata_parsed = True
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            result.error(f"pack.mcmeta: invalid UTF-8/JSON: {error}")
    if metadata_parsed and not isinstance(metadata, dict):
        result.error("pack.mcmeta: top level must be an object")
    elif metadata_parsed:
        pack = metadata.get("pack")
        if not isinstance(pack, dict):
            result.error("pack.mcmeta: pack must be an object")
        else:
            target_format = format_tuple(str(profile["data_pack_format"]))
            order = ordered_versions(profiles)
            uses_minor_schema = order.index(version) >= order.index("1.21.9")
            if uses_minor_schema and (
                metadata_format_tuple(pack.get("min_format")) is None
                or metadata_format_tuple(
                    pack.get("max_format"),
                    integer_is_major_maximum=True,
                )
                is None
            ):
                result.error(
                    "pack.mcmeta: 1.21.9 or later target requires valid "
                    "min_format and max_format"
                )
            elif not uses_minor_schema and metadata_format_tuple(
                pack.get("pack_format")
            ) is None:
                result.error(
                    "pack.mcmeta: pre-1.21.9 target requires numeric pack_format"
                )
            elif not contains_target_format(pack, target_format):
                result.error(
                    "pack.mcmeta: declared formats do not contain target "
                    f"{profile['data_pack_format']}"
                )

    for json_path in sorted(pack_root.rglob("*.json")):
        try:
            json.loads(json_path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            result.error(f"{json_path.relative_to(pack_root)}: invalid JSON: {error}")

    for path in sorted(pack_root.rglob("*")):
        relative = path.relative_to(pack_root)
        if path.is_file() and any(
            not PATH_PART.fullmatch(part)
            for part in relative.parts
            if part not in {"pack.mcmeta", "pack.png"}
        ):
            result.error(f"{relative}: path contains invalid characters")
        if len(relative.parts) >= 2 and relative.parts[0] == "data":
            namespace = relative.parts[1]
            if not re.fullmatch(r"[a-z0-9_.-]+", namespace):
                result.error(f"{relative}: invalid namespace {namespace!r}")

    plural_types = {
        "advancements",
        "functions",
        "item_modifiers",
        "loot_tables",
        "predicates",
        "recipes",
        "structures",
    }
    singular_types = {
        "advancement",
        "function",
        "item_modifier",
        "loot_table",
        "predicate",
        "recipe",
        "structure",
    }
    forbidden_types = singular_types if schema == "plural" else plural_types
    expected_function_dir = "functions" if schema == "plural" else "function"
    tag_directory_pairs = {
        "block": "blocks",
        "entity_type": "entity_types",
        "fluid": "fluids",
        "function": "functions",
        "game_event": "game_events",
        "item": "items",
    }
    wrong_tag_dirs = (
        set(tag_directory_pairs)
        if schema == "plural"
        else set(tag_directory_pairs.values())
    )
    for namespace_dir in (pack_root / "data").glob("*") if (pack_root / "data").is_dir() else []:
        if not namespace_dir.is_dir():
            continue
        for forbidden in sorted(forbidden_types):
            if (namespace_dir / forbidden).exists():
                result.error(
                    f"{(namespace_dir / forbidden).relative_to(pack_root)}: "
                    f"wrong {schema} directory schema"
                )
        for wrong_tag_dir in sorted(wrong_tag_dirs):
            wrong_tag = namespace_dir / "tags" / wrong_tag_dir
            if wrong_tag.exists():
                result.error(
                    f"{wrong_tag.relative_to(pack_root)}: "
                    f"wrong {schema} tag directory schema"
                )

    command_roots = load_command_roots(reports)
    registry_ids = load_registry_ids(reports)
    functions: set[str] = set()
    function_files = sorted(pack_root.rglob("*.mcfunction"))
    for path in function_files:
        resource = resource_id_for_file(path, pack_root, schema)
        if resource:
            functions.add(resource)
        else:
            result.error(
                f"{path.relative_to(pack_root)}: expected data/<namespace>/"
                f"{expected_function_dir}/<path>.mcfunction"
            )

    order = ordered_versions(profiles)
    supports_macro = order.index(version) >= order.index("1.20.2")
    supports_line_continuation = supports_macro
    for path in function_files:
        relative = path.relative_to(pack_root)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:
            result.error(f"{relative}: invalid UTF-8: {error}")
            continue
        if text.startswith("\ufeff"):
            result.error(f"{relative}: UTF-8 BOM is not allowed")
            continue
        if not supports_line_continuation:
            for number, physical in enumerate(text.splitlines(), start=1):
                stripped = physical.rstrip()
                if (
                    stripped.endswith("\\")
                    and not stripped.lstrip().startswith("#")
                ):
                    result.error(
                        f"{relative}:{number}: line continuation requires "
                        "1.20.2 or later"
                    )
        for number, line in logical_function_lines(text):
            if line.startswith("#"):
                continue
            if line.startswith("/"):
                result.error(f"{relative}:{number}: function command starts with /")
                continue
            if line.startswith("$") and not supports_macro:
                result.error(f"{relative}:{number}: macro requires 1.20.2 or later")
                continue
            parse_line = line[1:].lstrip() if line.startswith("$") else line
            root = parse_line.split(maxsplit=1)[0] if parse_line else ""
            if command_roots is not None and "$(" not in root and root not in command_roots:
                result.error(
                    f"{relative}:{number}: command root {root!r} absent from commands.json"
                )
            for match in FUNCTION_REFERENCE.finditer(parse_line):
                reference = match.group(1)
                if reference.startswith("#"):
                    continue
                namespace = reference.split(":", 1)[0]
                if namespace != "minecraft" and reference not in functions:
                    result.error(
                        f"{relative}:{number}: missing local function {reference}"
                    )

    local_resources: set[str] = set(functions)
    data_root = pack_root / "data"
    if data_root.is_dir():
        for path in data_root.rglob("*"):
            if not path.is_file() or path.suffix not in {".json", ".nbt"}:
                continue
            relative = path.relative_to(data_root)
            if len(relative.parts) >= 3:
                local_resources.add(
                    f"{relative.parts[0]}:"
                    f"{Path(*relative.parts[2:]).with_suffix('').as_posix()}"
                )
    if registry_ids:
        unknown: set[str] = set()
        for json_path in sorted(pack_root.rglob("*.json")):
            try:
                text = json_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for identifier in RESOURCE_LOCATION_SCAN.findall(text):
                if (
                    identifier.startswith("minecraft:")
                    and identifier not in registry_ids
                    and identifier not in local_resources
                ):
                    unknown.add(identifier)
        for identifier in sorted(unknown):
            result.warn(
                f"{identifier}: not found in registry report; it may be a "
                "serializer or vanilla data resource and requires codec/reload validation"
            )

    if reports is None:
        result.warn(
            "commands.json and registries.json were not supplied; command roots and "
            "registry IDs were not checked"
        )
    result.warn(
        "static validation cannot prove Brigadier argument parsing, Minecraft codecs, "
        "loot context, or runtime behavior; run server-test"
    )
    return result


def copy_pack(pack: Path, destination: Path) -> None:
    if not pack.is_dir():
        raise HarnessError("server-test currently requires an unpacked pack directory")
    shutil.copytree(pack, destination)


def server_log_errors(log: str) -> list[str]:
    lower = log.lower()
    return [pattern for pattern in ERROR_LOG_PATTERNS if pattern in lower]


def enabled_list_completed(log: str) -> bool:
    return ENABLED_LIST_PATTERN.search(log) is not None


def tested_pack_is_enabled(log: str) -> bool:
    return enabled_list_completed(log) and ENABLED_PACK_ID in log


def reload_started(log: str) -> bool:
    return RELOAD_STARTED_PATTERN.search(log) is not None


def reload_completed(log: str) -> bool:
    return RELOAD_COMPLETED_PATTERN.search(log) is not None


def server_test(
    version: str,
    pack: Path,
    java: str,
    cache_dir: Path,
    timeout: int,
    accept_eula: bool,
    expected_logs: Iterable[str] = (),
) -> tuple[int, str]:
    if not accept_eula:
        raise HarnessError("server-test requires explicit --accept-eula")
    jar_path, _ = fetch_release(version, cache_dir)
    with tempfile.TemporaryDirectory(prefix="mc-datapack-harness-") as temporary:
        server_dir = Path(temporary)
        (server_dir / "eula.txt").write_text("eula=true\n", encoding="utf-8")
        (server_dir / "server.properties").write_text(
            "\n".join(
                (
                    "level-name=world",
                    "online-mode=false",
                    "spawn-protection=0",
                    "function-permission-level=2",
                    "enable-command-block=true",
                    "",
                )
            ),
            encoding="utf-8",
        )
        destination = server_dir / "world" / "datapacks" / "pack-under-test"
        destination.parent.mkdir(parents=True, exist_ok=True)
        copy_pack(pack.resolve(), destination)

        process = subprocess.Popen(
            [java, "-jar", str(jar_path), "--nogui"],
            cwd=server_dir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        output: list[str] = []
        started = threading.Event()
        output_changed = threading.Condition()

        def read_output() -> None:
            assert process.stdout is not None
            for line in process.stdout:
                with output_changed:
                    output.append(line)
                    output_changed.notify_all()
                if re.search(r'Done \([0-9.]+s\)!', line):
                    started.set()
            with output_changed:
                output_changed.notify_all()

        def send_command(command: str) -> int:
            assert process.stdin is not None
            with output_changed:
                start_index = len(output)
            process.stdin.write(command + "\n")
            process.stdin.flush()
            return start_index

        def wait_for_output(
            start_index: int,
            predicate: Any,
            description: str,
        ) -> str:
            deadline = time.monotonic() + timeout
            with output_changed:
                while True:
                    segment = "".join(output[start_index:])
                    if predicate(segment):
                        return segment
                    errors = server_log_errors(segment)
                    if errors:
                        raise HarnessError(
                            f"server log reported error(s) before {description}: "
                            + ", ".join(errors)
                        )
                    if process.poll() is not None:
                        raise HarnessError(
                            f"server exited before {description}"
                        )
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise HarnessError(
                            f"server did not report {description} within {timeout}s"
                        )
                    output_changed.wait(remaining)

        reader = threading.Thread(target=read_output, daemon=True)
        reader.start()
        interaction_error: Exception | None = None
        try:
            if not started.wait(timeout):
                raise HarnessError(f"server did not finish startup within {timeout}s")

            enabled_start = send_command("datapack list enabled")
            enabled_log = wait_for_output(
                enabled_start,
                enabled_list_completed,
                "the enabled data pack list",
            )
            if not tested_pack_is_enabled(enabled_log):
                raise HarnessError(
                    f"{ENABLED_PACK_ID} is absent from the enabled data pack list"
                )

            reload_start = send_command("reload")
            wait_for_output(
                reload_start,
                reload_started,
                "reload start",
            )
            reload_log = wait_for_output(
                reload_start,
                reload_completed,
                "reload completion",
            )
            expected_logs = tuple(expected_logs)
            if expected_logs:
                reload_log = wait_for_output(
                    reload_start,
                    lambda log: reload_completed(log)
                    and all(marker in log for marker in expected_logs),
                    "reload completion and expected log marker(s)",
                )

            recheck_start = send_command("datapack list enabled")
            recheck_log = wait_for_output(
                recheck_start,
                enabled_list_completed,
                "the post-reload enabled data pack list",
            )
            if not tested_pack_is_enabled(recheck_log):
                raise HarnessError(
                    f"{ENABLED_PACK_ID} is not enabled after reload"
                )

            send_command("stop")
            process.wait(timeout=timeout)
        except (HarnessError, OSError, subprocess.SubprocessError) as error:
            interaction_error = error
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
            reader.join(timeout=2)

        log = "".join(output)
        if interaction_error is not None:
            raise ServerTestError(str(interaction_error), log) from interaction_error
        failures = server_log_errors(log)
        if process.returncode != 0:
            failures.append(f"server exit {process.returncode}")
        if failures:
            log = append_harness_error(
                log,
                "server log/process failure(s): " + ", ".join(failures),
            )
            return 1, log
        return 0, log


def print_validation(result: ValidationResult) -> int:
    for message in result.errors:
        print(f"ERROR: {message}")
    for message in result.warnings:
        print(f"WARN: {message}")
    if result.errors:
        print(f"validation failed: {len(result.errors)} error(s)")
        return 1
    print(f"validation passed with {len(result.warnings)} warning(s)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("profiles", help="validate all version profiles")

    resolve = subparsers.add_parser("resolve", help="resolve one formal release profile")
    resolve.add_argument("version")

    fetch = subparsers.add_parser("fetch", help="download and SHA-1 verify server JAR")
    fetch.add_argument("version")
    fetch.add_argument("--cache-dir", type=Path, default=Path(".cache/minecraft"))

    reports = subparsers.add_parser("reports", help="run the official data generator")
    reports.add_argument("version")
    reports.add_argument("--cache-dir", type=Path, default=Path(".cache/minecraft"))
    reports.add_argument("--output", type=Path, required=True)
    reports.add_argument("--java", default="java")

    validate = subparsers.add_parser("validate-pack", help="run static pack checks")
    validate.add_argument("version")
    validate.add_argument("pack", type=Path)
    validate.add_argument("--reports", type=Path)

    server = subparsers.add_parser(
        "server-test",
        help="start the exact server, issue reload, and inspect logs",
    )
    server.add_argument("version")
    server.add_argument("pack", type=Path)
    server.add_argument("--cache-dir", type=Path, default=Path(".cache/minecraft"))
    server.add_argument("--java", default="java")
    server.add_argument("--timeout", type=int, default=120)
    server.add_argument("--accept-eula", action="store_true")
    server.add_argument(
        "--expect-log",
        action="append",
        default=[],
        help="require this literal marker in the reload log; repeatable",
    )
    server.add_argument("--log", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        profiles = load_profiles()
        profile_errors = validate_all_profiles(profiles)
        if profile_errors:
            for error in profile_errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1

        if args.command == "profiles":
            order = ordered_versions(profiles)
            print(f"validated {len(order)} profiles: {order[0]} .. {order[-1]}")
            return 0
        if args.version not in profiles:
            raise HarnessError(f"unsupported formal release profile: {args.version}")

        if args.command == "resolve":
            payload = resolved_profile_payload(args.version, profiles)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        if args.command == "fetch":
            jar, metadata = fetch_release(args.version, args.cache_dir)
            print(
                json.dumps(
                    {
                        "version": args.version,
                        "server_jar": str(jar),
                        "sha1": metadata["downloads"]["server"]["sha1"],
                    },
                    indent=2,
                )
            )
            return 0
        if args.command == "reports":
            run_reports(
                args.version,
                args.java,
                args.cache_dir,
                args.output,
                profiles,
            )
            return 0
        if args.command == "validate-pack":
            return print_validation(
                validate_pack(
                    args.version,
                    args.pack,
                    args.reports,
                    profiles,
                )
            )
        if args.command == "server-test":
            try:
                status, log = server_test(
                    args.version,
                    args.pack,
                    args.java,
                    args.cache_dir,
                    args.timeout,
                    args.accept_eula,
                    args.expect_log,
                )
            except ServerTestError as error:
                print(f"ERROR: {error}", file=sys.stderr)
                status, log = 1, error.log
            if args.log:
                args.log.parent.mkdir(parents=True, exist_ok=True)
                args.log.write_text(log, encoding="utf-8")
            else:
                print(log)
            return status
        raise HarnessError(f"unhandled command: {args.command}")
    except (HarnessError, OSError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
