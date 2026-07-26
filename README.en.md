# Minecraft Java Edition Data Pack Harness

[日本語](README.md) | [English](README.en.md)

A shared harness that resolves exact Minecraft Java Edition releases and makes AI-assisted data pack implementation and validation reproducible across game versions.

Start with the [specification index](docs/README.md) and refer to the [AI authoring contract](docs/ai-authoring.md) when generating a data pack.

## Runtime requirements

- Reading the documentation and copying templates do not require Python or Java.
- Python 3.10 or later is required only when running the bundled CLI. `profiles`, `resolve`, `project-check`, and the basic static checks use only the Python standard library.
- `fetch` and `reports` use the network only when explicitly asked to download an official Minecraft server JAR.
- The Java major version required by `reports` and `server-test` depends on the target game version.
- `server-test` does not start a server unless the user supplies `--accept-eula`.

Installation checks do not download a JAR or start Java or a Minecraft server.

## Distribution unit

Install the following paths from the same revision:

```text
README.md
README.en.md
VERSION
LICENSE
CHANGELOG.md
docs/
schemas/
templates/
tools/
tests/
```

Treat these paths as one distribution unit. Copying only part of the repository can leave the profile schema, project schema, documentation links, and tests out of sync. The maintenance-only `.github/` directory and `AGENTS.md` are not required distribution files.

## Recommended layout

```text
consumer-repository/
├── AGENTS.md
├── datapack-project.json
├── datapack/
└── tools/
    └── mc-datapack-harness/
        ├── VERSION
        ├── LICENSE
        ├── docs/
        ├── schemas/
        ├── templates/
        ├── tools/
        └── tests/
```

The examples below use `tools/mc-datapack-harness` as `<harness-root>`. If you install the harness elsewhere, such as `vendor/mc-datapack-harness`, replace the path consistently.

## Installation methods

### Git submodule

A submodule pins the harness revision in the consumer repository's gitlink. This is the recommended method when harness updates should remain separate from the consumer repository's own changes.

```bash
git submodule add https://github.com/asgrcat/mc-datapack-harness \
  tools/mc-datapack-harness
git -C tools/mc-datapack-harness checkout <tag-or-full-commit>
git add .gitmodules tools/mc-datapack-harness
```

### Git subtree

A subtree imports the harness history into the consumer repository and avoids extra submodule steps after cloning.

```bash
git subtree add \
  --prefix tools/mc-datapack-harness \
  https://github.com/asgrcat/mc-datapack-harness \
  <tag-or-commit> --squash
```

### Release archive or copy

If Git integration is not needed, copy the complete distribution unit from one tag or full-commit archive. Keep `LICENSE` and record the source tag or full commit in the installation record.

If a revision has no public release or tag, pin it by full commit SHA. Do not use a moving branch name as the installed version.

## Initial setup

1. Copy [`templates/datapack-project.json`](templates/datapack-project.json) to the consumer repository root.
2. Set `target_version`, `namespace`, `pack_root`, and the required `validation_level`. If the harness is installed at a different path, update `$schema` to the actual `<harness-root>`.
3. Add [`templates/AGENTS.snippet.md`](templates/AGENTS.snippet.md) to the consumer repository's `AGENTS.md` or equivalent instructions, then replace `<harness-root>` with the actual path.

The five required project fields are `schema_version`, `target_version`, `namespace`, `pack_root`, and `validation_level`. Omitted optional fields use these defaults:

| Field | Default |
|---|---|
| `edition` | `java` |
| `supported_versions.min` / `.max` | `target_version` |
| `experimental_features` | `false` |
| `server_type` | `vanilla` |
| `cache_dir` | `.cache/minecraft` |
| `report_dir` | `build/minecraft/<target_version>/generated` |

Read the installed harness version from `<harness-root>/VERSION`. A submodule pins the revision with its gitlink, a subtree with its imported history, and an archive or copy with its installation record. Add the optional `harness.version`, `harness.source`, and `harness.commit` fields only when the project file should also retain archive or source metadata.

Health check:

```bash
HARNESS_ROOT="tools/mc-datapack-harness"
python3 "$HARNESS_ROOT/tools/datapack_harness.py" --version
python3 "$HARNESS_ROOT/tools/datapack_harness.py" profiles
python3 "$HARNESS_ROOT/tools/datapack_harness.py" \
  project-check --project datapack-project.json
```

These commands do not require network access, Java, or EULA acceptance.

## AI implementation workflow

```bash
HARNESS_ROOT="tools/mc-datapack-harness"

python3 "$HARNESS_ROOT/tools/datapack_harness.py" \
  project-check --project datapack-project.json

python3 "$HARNESS_ROOT/tools/datapack_harness.py" resolve 1.20.5

python3 "$HARNESS_ROOT/tools/datapack_harness.py" \
  validate-project --project datapack-project.json
```

The version passed to `resolve` must match the project's `target_version`. The AI should validate through the level requested by the project and must not report an unexecuted higher level as successful.

## Validation levels

| Level | Required evidence | Supported claim |
|---|---|---|
| `generated` | Profile resolution and file generation | Generated for the target game version |
| `static` | Successful `validate-project` | Passed the harness's static checks |
| `server` | Enabled and reloaded on the exact server | Loaded on the target game version's server |
| `functional` | Successful functional tests | Passed the recorded functional tests |

Completing a project at `static` is a normal use case. `server` and `functional` checks are run explicitly after the user evaluates their necessity, EULA acceptance, and production impact.

Automation for the `generated` level is still under development. The minimum guarantee of the distributed consumer CI template is `static`; generation alone is not treated as CI success.

## CI

Copy [`templates/github/workflows/datapack-harness.yml`](templates/github/workflows/datapack-harness.yml) to the consumer repository's `.github/workflows/` directory.

Set `DATAPACK_HARNESS_ROOT` and `DATAPACK_PROJECT` to the actual paths. On pull requests, the template runs `validate-project` once to check both the project configuration and the data pack statically. It does not implicitly download a JAR or start a server.

The template does not assume a submodule installation. Repositories that install the harness as a submodule should add the following setting to the checkout step:

```yaml
with:
  submodules: recursive
```

## Updating

Before updating, review [`CHANGELOG.md`](CHANGELOG.md) and the changes made in the consumer repository.

- Submodule: check out the new tag or full commit inside the harness, then commit the updated gitlink in the consumer repository.
- Subtree: run `git subtree pull --prefix ... <tag-or-commit> --squash`.
- Archive or copy: compare the old and new distribution units, preserve consumer-side changes, and then replace the installed files.

After updating:

1. Verify `<harness-root>/VERSION` and the tag or full commit pinned by the installation method.
2. If optional `harness` metadata is present, update it as well.
3. Run `profiles`, `project-check`, and the harness unit tests.
4. Re-run the requested validation level for the generated pack.

## Uninstalling

The removable scope is the complete installed `<harness-root>`. For a submodule, remove the gitlink and its `.gitmodules` entry. For a subtree or copy, remove the installed directory.

The consumer repository owns its `datapack-project.json`, additions to `AGENTS.md`, CI workflow, and generated data packs. Do not remove them automatically. Review the configured paths before removing caches or reports.

## Scope

The harness does not automatically update existing worlds or production servers, and it does not perform world backups, distribution, or production deployment. See [`docs/harness.md`](docs/harness.md) for details about each validation level.
