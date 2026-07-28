# Minecraft Java Edition データパック仕様

このディレクトリは、データパックが正式導入された Java Edition 1.13 から 26.2 までの**正式リリース**を対象にした、実装用の仕様索引です。スナップショット固有の形式は、正式リリースに残った変更を説明するために必要な場合だけ扱います。Bedrock Edition、Mod ローダー固有仕様、リソースパックだけの仕様は対象外です。

## 最短の使い方

導入と更新はrepository rootの [`README.md`](../README.md) を先に読みます。

1. 利用者repositoryの `datapack-project.json` を `project-check` する
2. [`versions/README.md`](versions/README.md) から完全一致する対象ゲームバージョンを解決する
3. 対象バージョンファイルの `data_pack_format`、ディレクトリ名、破壊的変更を固定する
4. [`commands.md`](commands.md) と [`json-formats.md`](json-formats.md) のうち、対象バージョンで利用可能と明記された構文だけを使う
5. fieldの型、既定値、参照関係は [`reference/README.md`](reference/README.md) から該当する書式リファレンスを選ぶ
6. 複雑な処理では [`execution-model.md`](execution-model.md) と [`state-management.md`](state-management.md) で実行文脈・永続状態を設計する
7. 追加block/entityを企画へ使う場合は [`content-hooks.md`](content-hooks.md) から観測・制御手段を選ぶ
8. 複数バージョン対応なら [`compatibility.md`](compatibility.md) に従い、共通部分と overlay を分ける
9. project設定が要求する検証levelまで実行し、未実施の上位levelを明記する

「最新の構文を古いバージョン向けに書き戻す」より、対象バージョンの仕様を最初から選ぶことを優先してください。`pack_format` が同じでも、コマンド、NBT、レジストリ、JSON の意味が変わる場合があります。

## 文書の役割

| 文書 | 用途 |
|---|---|
| [`versions/README.md`](versions/README.md) | 全正式リリース、公開日、data pack format の対応表 |
| [`versions/<version>.md`](versions/README.md) | そのゲームバージョンの確定プロファイル、前バージョンとの差分、互換性 |
| [`ai-authoring.md`](ai-authoring.md) | AIがバージョンを解決し、ファイルを生成する決定手順 |
| [`commands.md`](commands.md) | `.mcfunction` の書式、引数、実行文脈、コマンドのバージョン境界 |
| [`json-parameters/README.md`](json-parameters/README.md) | 主要なデータ駆動JSONの値の意味、全正式リリース境界、JARカタログ |
| [`execution-model.md`](execution-model.md) | executor、位置、分岐、function結果、load/tick/scheduleの細かな挙動 |
| [`reference/README.md`](reference/README.md) | 配置、field、値型、既定値、参照関係をデータ種別ごとに引く詳細リファレンス |
| [`state-management.md`](state-management.md) | scoreboard、storage、entity tag、永続性、migration |
| [`advancements.md`](advancements.md) | criteria、requirements、reward、grant/revoke、player event |
| [`json-formats.md`](json-formats.md) | `pack.mcmeta` と全データ種別の配置・JSON/SNBT の基本形 |
| [`content-hooks.md`](content-hooks.md) | 追加block/entity/itemと観測・制御手段、データパック企画の着眼点 |
| [`gameplay-requirements.md`](gameplay-requirements.md) | 共同eventを例にした複合要件の可否、状態遷移、競合、cleanup |
| [`implementation-patterns.md`](implementation-patterns.md) | 状態機械、timer、event queue、API、性能、testの実装パターン |
| [`harness.md`](harness.md) | バージョン解決、JAR/SHA-1、report生成、静的検査、server reloadの実行方法 |
| [`compatibility.md`](compatibility.md) | 後方互換、前方互換、overlay、移行方針 |
| [`validation.md`](validation.md) | 公式 JAR から正確なコマンド木・レジストリ・vanilla JSON を得る方法 |
| [`sources.md`](sources.md) | 採用した一次資料と Minecraft Wiki の使い分け |

## 目的別の参照経路

### 最小pack

`versions/<version>.md` → `commands.md` → `json-formats.md` → `json-parameters/README.md` → `reference/README.md` → `validation.md`

対象バージョンで読み込める最小packを作り、構文・配置・JSON codecを確認します。各JSON familyは、パラメータ索引でデータ型とgameplay判定を分けてから対象バージョンのfieldを選びます。

### 状態を持つpack

上記に `execution-model.md`、`state-management.md`、`advancements.md` を加えます。

player別状態、event駆動、timer、function結果、reload・再起動後の永続性まで設計します。

### 複合要件を持つpack

`content-hooks.md` からvanilla gameplay要素を選び、複合要件は `gameplay-requirements.md` で可否を判定し、`implementation-patterns.md` に従ってmigration、API、性能上限、GameTestを含めます。

完了条件は「構文が通る」だけでなく、対象0件・複数対象・chunk unload・multiplayer・旧world更新で挙動が定義されていることです。

## 実行ハーネス

最初にprofile schemaと継承を検査します。

```bash
python3 tools/datapack_harness.py profiles
python3 tools/datapack_harness.py resolve 1.20.5
```

project設定、公式JARの任意取得、report生成、pack静的検査、server reloadまでの手順は [`harness.md`](harness.md) を参照してください。

## AI が対象バージョンを決める規則

入力にゲームバージョンがある場合、次の順序を変えてはいけません。

1. 文字列を正式リリース ID として完全一致させる。`1.20` と `1.20.1`、`26.1` と `1.26.1` は別物である
2. 対応するバージョンファイルの YAML front matter を読み、`data_pack_format` と `directory_schema` を採用する
3. `inherits` はmetadataと規則の履歴追跡に使い、生成へ適用するのは対象バージョン自体の `AI 生成規則` だけとする。コマンド・registry・vanilla JSONの機械判定は自然言語の見出しでなく、対象バージョンのJARのreport/dataで確定する
4. 未指定の機能を、対象バージョンより後に導入されたという理由だけで代替実装なしに使わない
5. 対象バージョンより新しい公式例を流用する場合、コマンド木、フォルダ名、JSON フィールド、ID、NBT、item component をすべて対象バージョンへ変換する
6. 検証できない構文を推測で出力せず、対象バージョン server JAR の `generated/reports/commands.json` または vanilla data を参照する

## 重要な境界

| ゲームバージョン | 形式 | 実装上の境界 |
|---|---:|---|
| 1.13 | 4 | データパック正式導入、Brigadier ベースのコマンド体系 |
| 1.15 | 5 | predicate JSON |
| 1.16 | 5 | カスタムdimension/dimension typeの初期experimental schema |
| 1.16.2 | 6 | カスタムworldgen registry folder群を拡大 |
| 1.17 | 7 | `/replaceitem` を `/item` へ置換 |
| 1.18.2 | 9 | configured structure と `/locate` の変更 |
| 1.19 | 10 | `pack.mcmeta` filter、`/place`、`/locatebiome` 統合 |
| 1.19.4 | 12 | damage type レジストリ |
| 1.20 | 15 | sign NBT、predicate/advancement の破壊的変更 |
| 1.20.2 | 18 | function macro、行継続、overlay |
| 1.20.3 | 26 | `return` と function の結果、厳格な text component |
| 1.20.5 | 41 | item NBT から structured data components へ |
| 1.21 | 48 | データフォルダ名を原則単数形へ変更、enchantment 等をデータ駆動化 |
| 1.21.5 | 71 | text component の SNBT 化、entity/equipment NBT の大改編 |
| 1.21.6 | 80 | dialog、waypoint、`/version`、`/datapack create` |
| 1.21.9 | 88.0 | pack format の minor バージョンと新しい `pack.mcmeta` 範囲指定 |
| 1.21.11 | 94.1 | gamerule の namespaced snake_case 化、timeline、slot source |
| 26.1 | 101.1 | 年ベースのゲームバージョン番号、world clock、trade/variant のデータ駆動化 |
| 26.2 | 107.1 | entity predicate の component-map 化と厳格化 |

## 完全性の意味

このリポジトリで「網羅」は、正式リリースごとに次を一意に決められることを指します。

- pack metadata とフォルダ構造
- `.mcfunction` の字句規則と、使用可能なコマンド/引数
- JSON データ種別、配置、主要な最小形
- バージョンをまたぐ追加・変更・削除と移行上の注意
- server JAR から、そのバージョンの完全なコマンド木・レジストリ・vanilla 例を再生成する方法

ゲーム内の全 block/item/entity ID や、worldgen の全組合せを Markdown に複製はしません。これらはバージョンごとに数と内容が変わるため、公式 JAR が生成するレポートと vanilla data を正本とします。
