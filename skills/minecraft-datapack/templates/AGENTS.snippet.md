## Minecraft data pack

- Java Editionデータパックの設計、実装、移行、検証には`minecraft-datapack`スキルを使用する
- 実装前にスキル内の`docs/README.md`と`docs/ai-authoring.md`を読む
- `datapack-project.json`を対象バージョン、namespace、pack root、要求検証levelの正本とする
- 生成前にproject設定と対象バージョンを完全一致で解決する
- 生成後はproject設定が要求するlevelまで検証する
- 実行していないserver検証・機能検証を成功と表現しない
- EULA同意、既存world、本番serverに関する判断を自動化しない
