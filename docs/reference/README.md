# データパック書式リファレンス

このディレクトリは、Java Edition 1.13から26.2までの正式リリースを対象に、データパックの配置、書式、パラメータ、参照関係を人間が追える形でまとめます。対象バージョンの差分は [`../versions/README.md`](../versions/README.md)、完全なコマンド木とregistry IDは対象バージョンの公式server JARが生成するreportを正本とします。

## 読み方

1. [`../versions/README.md`](../versions/README.md) で対象バージョンを完全一致させる
2. 対象バージョンファイルでdata pack formatと単数形・複数形のディレクトリ境界を確定する
3. このリファレンスで配置、共通構造、パラメータの意味を確認する
4. `type`で分岐するcodecは、対象バージョンの同じ`type`を持つvanilla JSONと照合する
5. `/reload`、server再起動、必要なら新規worldまたは未生成chunkで検証する

「26.2の例」は、そのまま古い正式リリースへコピーしません。各ページの「バージョン境界」を先に適用します。

## 文書一覧

| 文書 | 対象 |
|---|---|
| [`pack-and-paths.md`](pack-and-paths.md) | `pack.mcmeta`、namespace、resource location、ディレクトリ、tag、overlay |
| [`command-tree.md`](command-tree.md) | `commands.json`、argument parser、構文分岐、result検証 |
| [`world-and-environment.md`](world-and-environment.md) | `dimension`、`dimension_type`、biome、environment attributes、timeline、world clock |
| [`registry-formats.md`](registry-formats.md) | 26.2でデータパックから定義できるregistry entryの配置とパラメータ |
| [`components-and-predicates.md`](components-and-predicates.md) | item stack、data component、entity component、predicate、advancement条件 |
| [`recipes-loot-and-tests.md`](recipes-loot-and-tests.md) | recipe、loot table、item modifier、GameTest |
| [`worldgen.md`](worldgen.md) | biome、feature、placement、noise、structure、dimension generator |
| [`coverage.md`](coverage.md) | 26.2の全データ種別と、説明先・正本・検証方法の対応表 |

コマンドの字句、引数、実行文脈は [`../commands.md`](../commands.md) と [`../execution-model.md`](../execution-model.md) を使います。状態の保存は [`../state-management.md`](../state-management.md)、バージョンをまたぐpackは [`../compatibility.md`](../compatibility.md) を使います。

## パラメータ表の規則

各表では次の表記を使います。

| 表記 | 意味 |
|---|---|
| 必須 | 省略すると対象codecを読み込めない |
| 任意 | 省略可能。既定値が分かる場合は表へ記載 |
| 条件付き | `type`や別フィールドにより必要性が変わる |
| ID | `namespace:path`形式のresource location |
| ID／list／tag | 単一ID、IDの配列、または`#namespace:path`のtag参照 |
| text component | 対象バージョンのtext component表現。1.21.5以降のcommandとJSONを混同しない |
| item stack | item ID、count、data component mapを持つ対象バージョン固有のitem stack |
| number provider | 定数または`type`付きの数値provider。利用可能な型はregistry reportで制限する |

必須性や既定値をvanilla JSONの出現頻度だけで推測しません。公式リリースノートに明記がないcodecは、同型のvanilla JSONを最小化し、対象serverのreload結果で確定します。

## 網羅性の層

このリファレンスは、次の3層を組み合わせます。

1. **人間向け説明**: 配置、fieldの役割、値の型、既定値、相互参照、代表例
2. **機械生成された正本**: `commands.json`、`registries.json`、`datapack.json`、block/component report
3. **実際にcodecを通る例**: `generated/data/minecraft/`のvanilla JSON

Minecraftのcodecは`type`ごとに分岐し、正式リリース間でfieldが変わります。Markdownだけへ全分岐を複製すると正本と乖離するため、各ページは「構造と意味」を説明し、利用可能なIDと最終的な分岐は公式server JARの生成物で閉じます。

## 26.2の正本を生成する

```bash
python3 tools/datapack_harness.py reports 26.2 \
  --cache-dir .cache/minecraft \
  --output build/minecraft/26.2/generated \
  --java /path/to/java25
```

重要な出力:

| 出力 | 確定できる内容 |
|---|---|
| `reports/datapack.json` | データパックから要素を定義できるregistry、tag対応、安定性 |
| `reports/commands.json` | 全コマンド分岐、argument parser、実行可能node |
| `reports/registries.json` | 全registryとentry ID |
| `reports/minecraft/components/item/` | vanilla itemの既定component |
| `data/minecraft/` | 26.2のcodecで生成されたvanilla resource |

生成物は文書へcommitしません。対象バージョンごとに再生成します。
