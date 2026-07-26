# Changelog

このファイルは、共通ハーネスとして利用者側へ影響する変更を記録します。

## Unreleased

- project設定を必須5 fieldへ簡素化し、版依存pathを含む既定値を追加
- 配布元metadataを任意化し、導入済みversionの正本を `VERSION` に統一
- consumer CI templateをpull request時の静的検査1回へ簡素化
- AI向けの日常生成手順から重複するprofile単独検査を削除

## 0.1.0

- Java Edition 1.13〜26.2の正式版profileを追加
- 対象版resolve、公式JAR取得とSHA-1検証、report生成を追加
- pack静的検査と任意のserver検査を追加
- project設定、導入template、検証levelを追加
