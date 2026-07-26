# Minecraft Java Edition データパック仕様

このディレクトリは、データパックが正式導入された Java Edition 1.13 から 26.2 までの**正式リリース**を対象にした、実装用の仕様索引です。スナップショット固有の形式は、正式版に残った変更を説明するために必要な場合だけ扱います。Bedrock Edition、Mod ローダー固有仕様、リソースパックだけの仕様は対象外です。

## 最短の使い方

1. [`versions/README.md`](versions/README.md) から対象ゲーム版を選ぶ
2. 対象版ファイルの `data_pack_format`、ディレクトリ名、破壊的変更を固定する
3. [`commands.md`](commands.md) と [`json-formats.md`](json-formats.md) のうち、対象版で利用可能と明記された構文だけを使う
4. 複数版対応なら [`compatibility.md`](compatibility.md) に従い、共通部分と overlay を分ける
5. 対象版の公式 server JAR で [`validation.md`](validation.md) の検査を行う

「最新の構文を古い版向けに書き戻す」より、対象版の仕様を最初から選ぶことを優先してください。`pack_format` が同じでも、コマンド、NBT、レジストリ、JSON の意味が変わる場合があります。

## 文書の役割

| 文書 | 用途 |
|---|---|
| [`versions/README.md`](versions/README.md) | 全正式版、公開日、data pack format の対応表 |
| [`versions/<version>.md`](versions/README.md) | そのゲーム版の確定プロファイル、前版との差分、互換性 |
| [`ai-authoring.md`](ai-authoring.md) | AIが版を解決し、ファイルを生成する決定手順 |
| [`commands.md`](commands.md) | `.mcfunction` の書式、引数、実行文脈、コマンドの版境界 |
| [`json-formats.md`](json-formats.md) | `pack.mcmeta` と全データ種別の配置・JSON/SNBT の基本形 |
| [`compatibility.md`](compatibility.md) | 後方互換、前方互換、overlay、移行方針 |
| [`validation.md`](validation.md) | 公式 JAR から正確なコマンド木・レジストリ・vanilla JSON を得る方法 |
| [`sources.md`](sources.md) | 採用した一次資料と Minecraft Wiki の使い分け |

## AI が対象版を決める規則

入力にゲーム版がある場合、次の順序を変えてはいけません。

1. 文字列を正式版 ID として完全一致させる。`1.20` と `1.20.1`、`26.1` と `1.26.1` は別物である
2. 対応する版ファイルの YAML front matter を読み、`data_pack_format` と `directory_schema` を採用する
3. `inherits` を辿って累積仕様を得た後、現在の版の `breaking_changes` と `ai_rules` で上書きする
4. 未指定の機能を、対象版より後に導入されたという理由だけで代替実装なしに使わない
5. 対象版より新しい公式例を流用する場合、コマンド木、フォルダ名、JSON フィールド、ID、NBT、item component をすべて対象版へ変換する
6. 検証できない構文を推測で出力せず、対象版 server JAR の `generated/reports/commands.json` または vanilla data を参照する

## 重要な境界

| ゲーム版 | 形式 | 実装上の境界 |
|---|---:|---|
| 1.13 | 4 | データパック正式導入、Brigadier ベースのコマンド体系 |
| 1.15 | 5 | predicate JSON |
| 1.16.2 | 6 | カスタム dimension/worldgen の試験的データ駆動化 |
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
| 1.21.9 | 88.0 | pack format の minor 版と新しい `pack.mcmeta` 範囲指定 |
| 1.21.11 | 94.1 | gamerule の namespaced snake_case 化、timeline、slot source |
| 26.1 | 101.1 | 年ベースのゲーム版番号、world clock、trade/variant のデータ駆動化 |
| 26.2 | 107.1 | entity predicate の component-map 化と厳格化 |

## 完全性の意味

このリポジトリで「網羅」は、正式版ごとに次を一意に決められることを指します。

- pack metadata とフォルダ構造
- `.mcfunction` の字句規則と、使用可能なコマンド/引数
- JSON データ種別、配置、主要な最小形
- 版をまたぐ追加・変更・削除と移行上の注意
- server JAR から、その版の完全なコマンド木・レジストリ・vanilla 例を再生成する方法

ゲーム内の全 block/item/entity ID や、worldgen の全組合せを Markdown に複製はしません。これらは版ごとに数と内容が変わるため、公式 JAR が生成するレポートと vanilla data を正本とします。
