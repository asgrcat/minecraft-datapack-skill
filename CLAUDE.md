# Repository guide

- Start with `docs/README.md`; documentation is written in Japanese.
- Keep one Java Edition release per `docs/versions/<version>.md`.
- Treat Mojang release notes as primary and Minecraft Wiki as a cross-check.
- Preserve the shared headings and update indexes whenever version data changes.
- Keep `skills/minecraft-datapack` synchronized with the source documentation, templates, schemas, tool, `VERSION`, and `LICENSE`.
- Keep `SKILL.md` portable across Claude Code, Codex, and Cursor; use only shared Agent Skills frontmatter fields.
- Run the skill validator, synchronization check, profile check, and unit tests after changing public skill content.
