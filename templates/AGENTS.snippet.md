## Minecraft data pack

- Harness root: `tools/mc-datapack-harness`
- 実装前に `<harness-root>/docs/README.md` と `<harness-root>/docs/ai-authoring.md` を読む
- `datapack-project.json` を対象版、namespace、pack root、要求検証levelの正本とする
- 生成前に `project-check` と対象版の `resolve` を実行する
- 生成後はproject設定が要求するlevelまで検証する
- 実行していないserver検証・機能検証を成功と表現しない
- EULA同意、既存world、本番serverに関する判断を自動化しない

`<harness-root>` は上記の Harness root の値へ置換する。
