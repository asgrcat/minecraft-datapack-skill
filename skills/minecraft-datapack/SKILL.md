---
name: minecraft-datapack
description: Minecraft Java Editionのデータパックを、対象の正式リリースまたは収録済みスナップショットに合わせて設計、生成、修正、移行、調査、検証する。`.mcfunction`、`pack.mcmeta`、advancement、predicate、loot table、recipe、item component、worldgen、複数バージョン対応を扱う依頼や、既存データパックの互換性確認に使用する。Bedrock EditionとMod固有実装には使用しない。
---

# Minecraft Java Editionデータパック

対象ゲームバージョンの仕様を先に固定し、そのリリースで存在が確認できる構文とデータだけで実装する。

## ワークフロー

1. 利用者リポジトリの指示ファイルと既存データパックを確認する。
2. `datapack-project.json`があれば正本として読み、なければ既存ファイルと依頼から値を推定する。安全に確定できない`target_version`、`namespace`、`pack_root`、`validation_level`だけを確認し、必要なら[プロジェクト設定テンプレート](templates/datapack-project.json)を基に作成する。
3. [仕様索引](docs/README.md)と[AI生成契約](docs/ai-authoring.md)を最後まで読む。
4. `target_version`を[正式リリース索引](docs/versions/README.md)または[スナップショット索引](docs/snapshots/README.md)へ完全一致させ、対応するプロファイルを読む。一覧にない値を近いバージョンへ丸めない。
5. 要件に応じて下の「資料の選択」から必要な文書を読む。対象バージョンより新しい例をそのまま流用しない。
6. 完全なファイル群を実装する。既存プロジェクトでは利用者の変更を保ち、依頼範囲外のファイルを変更しない。
7. 要求された検証レベルまで検証し、実行済みの証拠、warning、未実施の上位検証を分けて報告する。

## バージョンの確定

- `1.20`と`1.20.1`、`26.1`と`26.1.1`を別の正式リリースとして扱う。
- `26.3`、`26.3-snapshot-1`、`26.3-snapshot-6`を別のIDとして扱い、スナップショットの短縮名を作らない。
- `pack_format`が同じでも、コマンド、NBT、registry、JSON field、ディレクトリ名が同じとは仮定しない。
- 対象プロファイルの`data_pack_format`、`directory_schema`、`AI 生成規則`を適用する。
- 継承元の規則は変更履歴として読み、対象バージョンへ禁止事項を累積適用しない。
- コマンド、registry ID、vanilla JSONの最終的な正本は、対象バージョンの公式server JARが生成するreportとdataとする。
- スナップショットは隔離した実験worldだけで検証し、既存worldや本番serverへ適用しない。

## 資料の選択

- コマンドと実行文脈: [commands.md](docs/commands.md)、[execution-model.md](docs/execution-model.md)
- JSON、SNBT、配置: [json-formats.md](docs/json-formats.md)、[reference/README.md](docs/reference/README.md)
- データ駆動JSONのfield: [json-parameters/README.md](docs/json-parameters/README.md)
- advancementとplayer event: [advancements.md](docs/advancements.md)
- 永続状態とmigration: [state-management.md](docs/state-management.md)
- gameplay要素の観測と制御: [content-hooks.md](docs/content-hooks.md)、[gameplay-requirements.md](docs/gameplay-requirements.md)
- 実装パターンと性能: [implementation-patterns.md](docs/implementation-patterns.md)
- 複数バージョン対応: [compatibility.md](docs/compatibility.md)
- 公式生成物と検証方法: [validation.md](docs/validation.md)、[harness.md](docs/harness.md)
- 出典の優先順位: [sources.md](docs/sources.md)

長い資料は、対象要件に関係する見出しを検索してから該当範囲を読む。ただし、対象バージョンのプロファイル、仕様索引、AI生成契約は部分読みで済ませない。

## 実装規則

- namespace、function参照、tag、storage、scoreboard objective、entity tagを全ファイルで一貫させる。
- `minecraft` namespaceはload/tick tagへのentry追加または明示されたvanilla overrideに限定する。
- entry pointごとにexecutor、位置、dimension、状態ownerを定義する。
- 永続状態には初期化、migration、cleanup、再実行時の挙動を定義する。
- 対象0件、複数対象、multiplayer、chunk unload、reload、既存world更新の該当ケースを考慮する。
- 実在を確認できないコマンドbranch、ID、必須field、値型を推測しない。公式生成物を確認できない場合は不確実性を明記する。

## 検証

付属ハーネスを実行できる場合は、[harness.md](docs/harness.md)に従い`tools/datapack_harness.py`を使用する。追加packageは要求しない。

| level | 必要な証拠 | 報告できること |
|---|---|---|
| `generated` | 対象プロファイルを解決し、必要ファイルを生成 | 対象バージョン向けに生成した |
| `static` | `validate-project`または同等の静的検査に成功 | 静的検査に成功した |
| `server` | 対象バージョンで有効化とreloadに成功 | 対象serverで読み込めた |
| `functional` | 記録した機能testに成功 | 機能testに成功した |

- 利用できない実行環境を構築するよう利用者へ要求せず、可能な検証まで進める。
- `server`検証は、利用者が必要性、Minecraft EULA、実行環境を判断した場合だけ行う。
- 既存worldや本番serverを検証対象にしない。
- 実行していないlevelを成功として報告しない。

## 完了報告

最低限、次を含める。

```text
target_version:
requested_level:
completed_level:
evidence:
warnings:
not_run:
```

変更したファイル、主要な設計判断、バージョン固有の互換性上の注意も簡潔に示す。
