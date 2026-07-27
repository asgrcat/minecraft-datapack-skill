# Changelog

このファイルは、共通ハーネスとして利用者側へ影響する変更を記録します。

## 0.1.3

- item、dimension/worldgen、enchantment、variantのJSONパラメータ資料を追加
- 用語、gameplay上の意味、誤解、codec、バージョン境界、検証手順をfamily別リファレンスへ統合
- 全正式リリースから適用するJSON familyの境界を選べる索引を追加
- 全50正式リリースへ前版からのJSONパラメータ差分と互換性を追加
- 公式JAR生成物からregistry IDとvanilla観測fieldを集約する`json-catalog`を追加
- predicate、advancement、loot table、recipe、item modifierのパラメータ資料と版別履歴を追加

## 0.1.2

- Claude Code向けにroot `CLAUDE.md`を追加

## 0.1.1

- project設定を必須5 fieldへ簡素化し、バージョン依存pathを含む既定値を追加
- 配布元metadataを任意化し、導入済みversionの正本を `VERSION` に統一
- consumer CI templateをpull request時の静的検査1回へ簡素化
- AI向けの日常生成手順から重複するprofile単独検査を削除
- Pythonを付属CLI利用時だけの要件として明確化
- Minecraftのversion表記を「バージョン」「正式リリース」に統一
- root READMEの英語版を追加

## 0.1.0

- Java Edition 1.13〜26.2の正式リリースのprofileを追加
- 対象バージョンのresolve、公式JAR取得とSHA-1検証、report生成を追加
- pack静的検査と任意のserver検査を追加
- project設定、導入template、検証levelを追加
