# 対象版での生成と検証

Markdown の要約だけでコマンドや worldgen codec の全分岐を推測しないでください。Mojang が配布する対象版 server JAR には、その版の command graph、registry、vanilla data を生成する入口があります。

## 1. 正式版 server JAR を特定する

公式 version manifest から、完全一致する release ID を選びます。

```bash
TARGET_VERSION='1.20.5'
MANIFEST_URL='https://piston-meta.mojang.com/mc/game/version_manifest_v2.json'

VERSION_META_URL="$(
  curl --fail --silent --show-error "$MANIFEST_URL" |
    jq -r --arg version "$TARGET_VERSION" \
      '.versions[] | select(.id == $version and .type == "release") | .url'
)"

curl --fail --silent --show-error "$VERSION_META_URL" |
  jq -r '.downloads.server.url, .downloads.server.sha1'
```

- `TARGET_VERSION` を部分一致させない
- URL と同時に SHA-1 を得て、download 後に検証する
- manifest にない版名や snapshot を、最寄りの正式版として代用しない

## 2. data generator

### 1.13〜1.17.1

```bash
java -cp server.jar net.minecraft.data.Main --reports --server
```

### 1.18以降

```bash
java -DbundlerMainClass=net.minecraft.data.Main \
  -jar server.jar \
  --reports --server
```

Java の必要版もゲーム版に合わせます。代表的には 1.17 は Java 16、1.18〜1.20.4 は Java 17、1.20.5 以降は Java 21、26.1 以降は Java 25 です。付属 runtime を使うのが安全です。

出力の主な用途:

| 出力 | 使い方 |
|---|---|
| `generated/reports/commands.json` | literal、argument parser、分岐、実行可能な全 command tree |
| `generated/reports/registries.json` | 対象版に存在する registry と entry ID |
| block/item 等の report | block state、item、protocol/data の照合 |
| `generated/data/minecraft/` | 対象版 codec が実際に読む vanilla tag/recipe/advancement/worldgen の例 |

出力名は古い版で異なる場合があります。まず引数なしで data generator の help を表示し、その版の `--reports`/`--server` を確認します。

vanilla entry が空、またはcode側にだけ存在する型は `generated/data/minecraft/` にfolderが出ない場合があります。生成folderの不在だけで custom entry不可と判定せず、`registries.json`、release note、対象版でのreloadを併用します。

### command graph の読み方

`commands.json` は Brigadier の tree です。

- `type: "literal"`: 固定文字
- `type: "argument"`: `parser` が引数型。`properties` が追加制約
- `executable: true`: その node で command を終えられる
- `children`: 次の分岐
- `redirect`: 別 node へ接続する alias/redirect

AI は Wiki の短縮構文より command graph を優先し、`parser` の単数/複数 entity、resource/tag、整数/浮動小数、range を維持します。

## 3. vanilla data を schema example として使う

JSON Schema が配布されていない codec では、対象版の同型 vanilla file を選びます。

1. 目的と同じ data type、`type` discriminator、loot context の vanilla file を探す
2. 必須 field を残して最小化する
3. ID を独自 namespace へ変える
4. 参照先の registry/tag も対象版に存在することを確認する
5. 新しい版の vanilla file を古い版へコピーしない

vanilla に例がない data-driven registry は、対象版の公式 release note にある field list を使い、reload log で codec error がないことを確認します。

## 4. pack の静的検査

最低限、起動前に次を検査します。

```text
[ ] pack.mcmeta が厳密な JSON
[ ] 対象版の format/range
[ ] namespace/path が lowercase の許容文字だけ
[ ] 対象版の単数/複数 folder
[ ] JSON にコメント、末尾カンマ、SNBT suffix がない
[ ] .mcfunction に先頭 / がない
[ ] 全 resource location の参照先がある
[ ] load/tick tag の path が対象版用
[ ] item stack、text component、entity predicate が対象版用
```

`jq empty pack.mcmeta` と全 `.json` への `jq empty` は JSON 文法だけを検査できます。Minecraft codec、registry ID、command は検査しない点に注意してください。

## 5. 実ゲーム検査

1. 空のテスト world の `datapacks/` に pack を置く
2. 対象版の client/server で world を開く
3. `/datapack list enabled` で有効化を確認
4. `/reload` を実行
5. `logs/latest.log` で `Couldn't parse`, `Failed to load`, `Unknown`, `Not a JSON`, `syntax` を確認
6. `#minecraft:load` の初期化 state、`#minecraft:tick`、schedule、advancement reward を確認
7. loot/recipe/predicate/item modifier を、それぞれ実際の context で発火
8. custom worldgen は新規 world と未生成 chunk で確認
9. reload 後だけでなく、一度終了して再起動し永続 storage/scoreboard/schedule を確認

一般的な `/datapack validate` command はありません。pack metadata の警告がないことを validation 完了と扱わないでください。

## 6. 複数版対応の検査

- `min` と `max` だけでなく、範囲内の**全正式版**で reload する
- overlay が切り替わる境界の直前・直後を必ず含める
- 同じ pack format の版も省略しない。1.19.1、1.19.3 のような同形式の意味変更がある
- 旧 world の copy を upgrade する test と、新規 world test を分ける
- upgrade test 用 world は必ず複製し、元 world を新しい版で直接開かない
- downgrade は原則サポート外。特に 26.1 は world storage layout が大きく変わる

## 7. GameTest

1.21.5 以降は data-driven GameTest を pack に含められます。決定的な関数/ブロック挙動は `test_instance` と structure で自動化できます。

- `/test` で対象 test を実行
- server JAR の `net.minecraft.gametest.Main` entry point から CI 実行が可能
- JSON codec の load 成功だけでなく、score、block、entity、loot の結果を assertion にする
- GameTest 自体も版依存なので、古い対象版の共通 test 手段としては使わない

## 8. 振る舞いの検査

`commands.json` とJSON parseは構文を検査しますが、実行コンテキスト、永続状態、vanilla AI、複数対象時の分岐までは保証しません。

中上級packでは次もtestします。

```text
[ ] executor、position、dimensionがentry pointごとに正しい
[ ] selector対象が0件・1件・複数件の各場合
[ ] 未設定score、欠損storage path、未load chunk
[ ] loadを連続2回実行しても状態を壊さない
[ ] logout/loginとserver再起動後の状態
[ ] 旧pack schemaおよび旧Minecraft版worldからのmigration
[ ] entityのdeath、despawn、dimension移動、成長、変換、騎乗解除
[ ] vanilla AIや乱数の順序へ重要状態を依存させていない
```

設計上の確認は [`execution-model.md`](execution-model.md)、[`state-management.md`](state-management.md)、[`implementation-patterns.md`](implementation-patterns.md) を参照してください。追加block/entityの機能testは [`content-hooks.md`](content-hooks.md) の企画時チェックを併用します。

## 参照

- [公式 version manifest v2](https://piston-meta.mojang.com/mc/game/version_manifest_v2.json)
- [Minecraft Wiki: Running the data generator](https://minecraft.wiki/w/Tutorial:Running_the_data_generator)
- [Minecraft Wiki: Data generators](https://minecraft.wiki/w/Minecraft_Wiki:Projects/wiki.vg_merge/Data_Generators)
- [Minecraft Wiki: Game test](https://minecraft.wiki/w/Game_test)
