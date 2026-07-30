# 26.3 スナップショットプロファイル一覧

このディレクトリは Java Edition 26.3 の開発バージョンを、Mojang 公式 version manifest の ID へ完全一致させて扱います。スナップショットは仕様変更・削除や world 破損の可能性があるため、正式リリースの [`../versions/README.md`](../versions/README.md) とは分離しています。

各ファイルは直前のプロファイルを `inherits` し、そのスナップショットでの累積仕様を解決できます。`release_date` はこのディレクトリではスナップショットの公開日を表します。

| launcher ID | 公開日 | data pack format | 継承元 |
|---|---:|---:|---|
| [`26.3-snapshot-1`](26.3-snapshot-1.md) | 2026-06-23 | 108.0 | 26.2 |
| [`26.3-snapshot-2`](26.3-snapshot-2.md) | 2026-06-30 | 109.0 | 26.3-snapshot-1 |
| [`26.3-snapshot-3`](26.3-snapshot-3.md) | 2026-07-07 | 110.0 | 26.3-snapshot-2 |
| [`26.3-snapshot-4`](26.3-snapshot-4.md) | 2026-07-16 | 111.0 | 26.3-snapshot-3 |
| [`26.3-snapshot-5`](26.3-snapshot-5.md) | 2026-07-21 | 112.0 | 26.3-snapshot-4 |
| [`26.3-snapshot-6`](26.3-snapshot-6.md) | 2026-07-28 | 113.0 | 26.3-snapshot-5 |

## 使用上の制約

- `26.3` を `26.3-snapshot-6` の別名として扱わない
- 既存 world、本番 server、正式リリース用 pack の上書き検証に使わない
- `pack.mcmeta` は対象スナップショットの format へ厳密に固定する
- 次のスナップショットへ移るたびに公式 server JAR の report、reload、機能テストをやり直す
- 26.3 正式リリース後は、正式リリースプロファイルを新規作成し、スナップショット値をそのまま確定仕様にしない

## 出典

- [Mojang 公式 version manifest v2](https://piston-meta.mojang.com/mc/game/version_manifest_v2.json)
- [Minecraft Wiki: Java Edition 26.3](https://minecraft.wiki/w/Java_Edition_26.3)
