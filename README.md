# Minecraft Java Edition データパックスキル

[日本語](README.md) | [English](README.en.md)

Minecraft Java Edition 1.13 から 26.2 までの正式リリースと、収録済みの26.3スナップショットを対象に、AIがデータパックを設計・実装・検証するための Agent Skill です。対象ゲームバージョンを完全一致で解決し、そのバージョンで利用できるコマンド、データ形式、ディレクトリ構造だけを選びます。

Claude Code、Codex、Cursor で共通の [`SKILL.md`](skills/minecraft-datapack/SKILL.md) を利用できます。詳細な仕様、バージョン別プロファイル、テンプレート、検証ハーネスはスキルへ同梱されています。

## 追加

利用中のAIへ、次のようにリポジトリURLと追加したい旨を伝えてください。

> このリポジトリの `skills/minecraft-datapack` を Agent Skill として追加してください: https://github.com/asgrcat/mc-datapack-harness

AIは利用中の環境を判別し、スキル一式を対応する領域へ配置します。追加後は次の名前で明示的に呼び出せます。

| 環境 | 呼び出し |
|---|---|
| Claude Code | `/minecraft-datapack` |
| Codex | `$minecraft-datapack` |
| Cursor | `/minecraft-datapack` |

スキルの説明に一致する依頼では、AIが自動的に選択することもできます。

## バージョニング

リリースにはCalVerの`YYYY.MM.N`を使用します。`N`は同じ月に公開したリリースの連番で、月が変わると`1`へ戻ります。スキルのバージョンは[`skills/minecraft-datapack/VERSION`](skills/minecraft-datapack/VERSION)を正本とし、Gitタグには`v`を付けます（例: `v2026.08.1`）。

## 依頼例

> Java Edition 1.21.5向けに、参加者ごとのスコアを記録するデータパックを作ってください。namespaceは`event`、静的検証まで行ってください。

> このデータパックを1.20.4から1.20.5へ移行し、item NBTをdata componentへ変更してください。

> 1.21.11と26.1の両方へ対応できるか調査し、共通部分と分ける必要がある部分を整理してください。

ゲームバージョン、namespace、配置先、要求する検証レベルが未指定なら、AIが既存プロジェクトから推定し、安全に確定できない値だけを確認します。

## できること

- 正式リリース／収録済みスナップショットID、data pack format、ディレクトリ構造の完全一致
- `.mcfunction`、JSON、SNBT、resource locationのバージョン別生成
- item component、predicate、advancement、loot、recipe、worldgenなどの仕様参照
- 単一バージョン実装、既存データパックの移行、複数バージョン対応
- scoreboard、storage、entity tagを使う状態管理とmigration設計
- 静的検査、公式server JARのreport照合、任意のserver reload検査
- 実行済み検証と未実施検証を分けた結果報告

## 安全な動作

- 一覧にないsnapshot、pre-release、Bedrock Editionを近い収録済みバージョンへ置き換えません。
- 対象バージョンで確認できないコマンド、ID、JSON fieldを推測で生成しません。
- 公式server JARの取得やserver起動へ暗黙に進みません。
- Minecraft EULAへの同意、既存worldの更新、本番serverへの配置を代行しません。
- 静的検査だけを実行した場合、server検証済みとは報告しません。

## スキルの構成

| パス | 役割 |
|---|---|
| [`skills/minecraft-datapack/SKILL.md`](skills/minecraft-datapack/SKILL.md) | AIが適用する実装・検証ワークフロー |
| [`skills/minecraft-datapack/docs/README.md`](skills/minecraft-datapack/docs/README.md) | 仕様索引と対象バージョンの選択手順 |
| [`skills/minecraft-datapack/docs/versions/README.md`](skills/minecraft-datapack/docs/versions/README.md) | 全正式リリースとdata pack formatの対応 |
| [`skills/minecraft-datapack/docs/snapshots/README.md`](skills/minecraft-datapack/docs/snapshots/README.md) | 収録済み26.3スナップショットとdata pack formatの対応 |
| [`skills/minecraft-datapack/docs/ai-authoring.md`](skills/minecraft-datapack/docs/ai-authoring.md) | 生成時の決定規則と報告契約 |
| [`skills/minecraft-datapack/templates/datapack-project.json`](skills/minecraft-datapack/templates/datapack-project.json) | プロジェクト設定のひな形 |
| [`skills/minecraft-datapack/tools/datapack_harness.py`](skills/minecraft-datapack/tools/datapack_harness.py) | プロファイル解決と段階的な検証 |

文書とテンプレートの参照だけで設計・生成できます。付属ハーネスを利用できる環境では、プロファイル解決と静的検査を追加できます。公式server JARを使う検証は、利用者が必要性と実行条件を判断した場合だけ行います。

## 対象範囲

Java Editionの正式リリースと、明示的に収録した26.3スナップショットを対象とします。Bedrock Edition、Modローダー固有仕様、リソースパックだけの仕様、未収録の開発バージョンは対象外です。

仕様の正本はMojangのリリースノートと対象バージョンの公式server JARです。Minecraft Wikiは境界と説明の照合に使用します。

ライセンスはリポジトリ直下の [`LICENSE`](LICENSE) を参照してください。スキル配布物には同じ正本を [`skills/minecraft-datapack/LICENSE`](skills/minecraft-datapack/LICENSE) として含めます。
