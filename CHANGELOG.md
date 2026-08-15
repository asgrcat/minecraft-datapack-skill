# Changelog

このファイルは、スキルと付属ハーネスの利用者へ影響する変更を記録します。

## 2026.08.1

- 最初のGitHub Releaseとして、バージョン表記をCalVerの`YYYY.MM.N`へ移行
- Claude Code、Codex、Cursorで共有できる`minecraft-datapack` Agent Skillを配布
- Java Edition 1.13〜26.2の正式リリース50件と、`26.3-snapshot-1`〜`26.3-snapshot-8`のプロファイルを収録
- data pack format 4〜116.0のバージョン境界、コマンド、JSON、SNBT、ディレクトリ構造、互換性資料を収録
- 対象バージョンの完全一致解決、公式server JARの取得とSHA-1検証、report生成、pack静的検査、任意のserver reload検査を行うハーネスを同梱
- project設定、schema、導入template、consumer CI template、スキル内ライセンスを同梱
- 旧バージョン`0.1.0`〜`0.2.4`の開発内容を統合

## 0.2.4

- Java Edition `26.3-snapshot-8`プロファイルとdata pack format 116.0を追加
- desert wellのデータ駆動化、placement modifier／block predicate追加、Explorer Map ID renameを収録
- 公式server JARのSnapshot 7／8比較を基に、command tree不変とvanilla JSON差分を記録
- Snapshot 8を最新収録スナップショットとして仕様索引、ハーネス、テストへ反映

## 0.2.3

- Java Edition `26.3-snapshot-7`プロファイルとdata pack format 115.0を追加
- block state field、item animation component、exploration map loot function、density function精度の変更を収録
- Snapshot 7を最新収録スナップショットとして仕様索引、ハーネス、テストへ反映

## 0.2.2

- Java Edition `26.3-snapshot-1`〜`26.3-snapshot-6`のプロファイルとdata pack format 108.0〜113.0を追加
- snapshotを正式リリース索引から分離しつつ、完全一致のresolve、公式JAR取得、report、静的検査へ対応
- slot source、block transformer、number provider、brewing recipe、loot／predicate／advancement再編、noise／density function再編を収録
- リポジトリ直下へ、スキル配下の正本を指す`LICENSE`を追加

## 0.2.1

- 文書、バージョンプロファイル、schema、template、検証ハーネス、`VERSION`、`LICENSE`の正本を`skills/minecraft-datapack`へ一本化
- リポジトリ直下の重複する配布物と同期処理を削除
- README、保守ガイド、CI、テストをスキル配下の正本へ直接接続

## 0.2.0

- Claude Code、Codex、Cursorで共有できるAgent Skills形式の`minecraft-datapack`スキルを追加
- 実装手順を`SKILL.md`へ集約し、詳細仕様、バージョンプロファイル、テンプレート、検証ハーネスを段階的に参照する構成へ変更
- 利用者向けREADMEを、AIへの依頼例から追加・利用できる案内へ刷新
- スキル配布物と正本の文書・ツール・テンプレートが一致することを検査する仕組みを追加
- 文書内の表現を「バージョン」「正式リリース」へ統一

## 0.1.4

- Java Edition 1.13から26.2までのバージョン境界と26.2の公式生成物を基準に、詳細なデータパック書式リファレンスを追加
- pack metadata、namespace、resource path、tag、overlayのパラメータと置換規則を追加
- command tree、argument parser、properties、構文と実行時意味の検証方法を追加
- dimension、dimension type、biome、environment attributes、timeline、world clockのパラメータ、優先順位、modifier、補間を追加
- 26.2の全データ駆動registry、item component、predicate、recipe、loot、GameTest、worldgenの配置とfield説明を追加
- 26.2の全resource種別を説明先と公式server JAR生成物へ対応付けるカバレッジ表を追加
- universal tagのバージョン別配置、歴史的worldgen path、mob variant／sound variantの種別別field、Sulfur Cube archetypeのnested fieldを補完
- 文書内の対象表現を「バージョン」「正式リリース」「Java Edition」へ統一

## 0.1.3

- item、dimension/worldgen、enchantment、variantのJSONパラメータ資料を追加
- 用語、gameplay上の意味、誤解、codec、バージョン境界、検証手順をfamily別リファレンスへ統合
- 全正式リリースから適用するJSON familyの境界を選べる索引を追加
- 全50正式リリースへ直前のバージョンからのJSONパラメータ差分と互換性を追加
- 公式JAR生成物からregistry IDとvanilla観測fieldを集約する`json-catalog`を追加
- predicate、advancement、loot table、recipe、item modifierのパラメータ資料とバージョン別履歴を追加

## 0.1.2

- Claude Code向けにroot `CLAUDE.md`を追加

## 0.1.1

- project設定を必須5 fieldへ簡素化し、バージョン依存pathを含む既定値を追加
- 配布元metadataを任意化し、導入済みversionの正本を `VERSION` に統一
- consumer CI templateをpull request時の静的検査1回へ簡素化
- AI向けの日常生成手順から重複するprofile単独検査を削除
- Pythonを付属CLI利用時だけの要件として明確化
- Minecraftのversion表記を「バージョン」「正式リリース」に統一
- rootに英語READMEを追加

## 0.1.0

- Java Edition 1.13〜26.2の正式リリースのprofileを追加
- 対象バージョンのresolve、公式JAR取得とSHA-1検証、report生成を追加
- pack静的検査と任意のserver検査を追加
- project設定、導入template、検証levelを追加
