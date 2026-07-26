# 互換性と複数バージョン対応

## 用語

- **後方互換**: 新しいゲームが、古い仕様で作られたパックを正しく読み込めること
- **前方互換**: 古いゲームが、新しい仕様で作られたパックを正しく読み込めること
- **pack format**: 互換性を申告する番号。完全なスキーマ検証や自動変換を行う番号ではない
- **overlay**: 指定した pack format の範囲だけ、基底パックへ上書きするサブディレクトリ

## 絶対に仮定しないこと

1. `pack_format` が同じだからコマンドや NBT も同じ、とは限らない。例として 1.19〜1.19.3 は形式 10 のまま `/fillbiome` などが加わる
2. 警告なしで読み込めたから全ファイルが有効、とは限らない。不明な JSON、存在しない ID、構文エラーの function は reload 時に失敗し得る
3. 形式番号を古い値へ書き換えるだけで前方互換にはならない。フォルダ名、JSON、command、NBT、ID をすべて対象版へ合わせる必要がある
4. vanilla の保存 NBT は公開 API ではない。版をまたぐ rename/removal があるため、entity/block entity NBT を直接扱う処理は版ごとに検査する
5. スナップショットの pack format を正式版へ持ち込まない。正式版の版ファイルに記載した値を使う

## `pack.mcmeta` の時代別最小形

### 1.13〜1.20.1

```json
{
  "pack": {
    "pack_format": 15,
    "description": "Example data pack"
  }
}
```

`15` は例として 1.20/1.20.1 の値です。対象版の値へ置換します。`description` は text component ですが、単純な文字列が最も広く互換です。

### 1.20.2〜1.21.8

単一形式だけなら従来形で構いません。複数形式を宣言するときは `supported_formats` が使えます。

```json
{
  "pack": {
    "pack_format": 18,
    "supported_formats": {
      "min_inclusive": 18,
      "max_inclusive": 48
    },
    "description": "Example multi-version pack"
  }
}
```

`pack_format` は必須で、`supported_formats` の範囲内でなければなりません。これは対応を**申告**するだけで、互換変換はしません。

### 1.21.9〜26.2

pack version は `[major, minor]` です。単一の正式版へ厳密に固定する場合は次の形を使います。

```json
{
  "pack": {
    "description": "Example data pack for 26.2",
    "min_format": [107, 1],
    "max_format": [107, 1]
  }
}
```

`min_format` と `max_format` は必須です。

- `min_format: 107` は `[107, 0]` と同じ
- `max_format: 107` は major 107 のすべての minor を許可する
- minor を厳密に制限するなら `[107, 1]` のように2要素で書く
- 対応範囲が data pack format 82 未満を含まない場合、`supported_formats` は書いてはいけない
- 対応範囲が 82 未満を含まない場合、`pack_format` は省略できる

旧形式を含む範囲では、古いゲームが metadata を読めるよう `pack_format` と `supported_formats` も必要です。

## overlay

overlay は 1.20.2 で導入されました。基底の `data/` を全対象版で共通にし、破壊的に変わったファイルだけ overlay に置きます。

```text
example_pack/
├── pack.mcmeta
├── data/
│   └── example/
│       └── functions/          # 古い版向けの基底（1.21 未満）
└── v1_21/
    └── data/
        └── example/
            └── function/       # 1.21 以降の単数形
```

1.20.2〜1.21.8 で読む metadata 例:

```json
{
  "pack": {
    "pack_format": 18,
    "supported_formats": {
      "min_inclusive": 18,
      "max_inclusive": 48
    },
    "description": "1.20.2 through 1.21.1"
  },
  "overlays": {
    "entries": [
      {
        "formats": {
          "min_inclusive": 48,
          "max_inclusive": 48
        },
        "directory": "v1_21"
      }
    ]
  }
}
```

1.21.9 以降だけを対象にする overlay 例:

```json
{
  "pack": {
    "description": "1.21.9 through 1.21.11",
    "min_format": [88, 0],
    "max_format": [94, 1]
  },
  "overlays": {
    "entries": [
      {
        "directory": "v1_21_11",
        "min_format": [94, 0],
        "max_format": [94, 1]
      }
    ]
  }
}
```

overlay は列挙順に適用され、後から適用される内容が同じ resource location を上書きします。overlay ディレクトリ内の `pack.mcmeta` と `pack.png` は無視されます。

## 互換性クラス

各版ファイルでは次の語を使います。

| クラス | 意味 | AI の動作 |
|---|---|---|
| `same-format` | 前版と同じ pack format | 差分を適用し、構文まで同じとは仮定しない |
| `minor-compatible` | 1.21.9 以降で pack major が同じ、minor だけ増加 | 以前の同 major パックは原則読める。新 minor の機能を使うなら `min_format` を上げる |
| `breaking-format` | pack major が変化 | 自動的に共通化せず、移行項目を処理する |
| `metadata-break` | metadata schema 自体が変化 | `pack.mcmeta` を対象版用に生成し直す |
| `hotfix` | データパック仕様の意図的変更がない修正版 | 直前版の仕様を継承する。ただし既知バグの挙動差はあり得る |

## 版をまたぐ設計手順

1. 対象となる最古・最新の正式版を決める
2. その区間にある全版ファイルの `breaking_changes` を集める
3. 最古版でも使えるコマンド・JSON・IDだけを基底に置く
4. フォルダ rename、item component、text component、gamerule など同一ファイル内で両立しない差分を overlay へ分離する
5. 新機能がなくても動く代替実装を用意できなければ、その版を対応範囲から外す
6. 範囲内の**各正式版**で reload と機能テストを行う。両端だけの検査では、途中の同形式変更を見落とす

## filter

1.19 以降の `filter` は、当該パックより**低い優先度**で読み込まれたパックの resource を正規表現で隠します。当該パック自身には作用しません。

```json
{
  "pack": {
    "pack_format": 10,
    "description": "Filter example"
  },
  "filter": {
    "block": [
      {
        "namespace": "example",
        "path": "recipe/legacy_.*"
      }
    ]
  }
}
```

空欄の `namespace` または `path` は `.*` と同様に全件へ一致します。意図しない大量除外を防ぐため、AI は両方を明示するのを既定とします。

## 参照

- [Mojang: Java Edition 1.21.9 — Pack Formats](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-9)
- [Minecraft Wiki: `pack.mcmeta`](https://minecraft.wiki/w/Pack.mcmeta)
- [Minecraft Wiki: Pack format](https://minecraft.wiki/w/Pack_format)
