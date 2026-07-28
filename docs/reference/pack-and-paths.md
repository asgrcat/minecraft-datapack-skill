# pack metadata、namespace、配置

## pack root

データパックのrootには`pack.mcmeta`を置き、resourceは`data/`以下へ置きます。

```text
example-pack/
├── pack.mcmeta
└── data/
    ├── example/
    │   ├── function/
    │   ├── recipe/
    │   └── ...
    └── minecraft/
        └── tags/
            └── function/
                ├── load.json
                └── tick.json
```

1.13から1.20.6までは`function`、`recipe`などの一部ディレクトリが複数形です。1.21以降は原則として単数形へ移行します。対象バージョンの完全な配置は [`../json-formats.md`](../json-formats.md) と対象バージョンの`generated/data/minecraft/`で確定します。

## `pack.mcmeta`

### 1.13から1.20.1

```json
{
  "pack": {
    "pack_format": 15,
    "description": "Example"
  }
}
```

### 1.20.2から1.21.8

```json
{
  "pack": {
    "pack_format": 48,
    "supported_formats": {
      "min_inclusive": 48,
      "max_inclusive": 48
    },
    "description": "Example"
  }
}
```

### 1.21.9から26.2

```json
{
  "pack": {
    "description": "Example",
    "min_format": [107, 1],
    "max_format": [107, 1]
  }
}
```

`pack`のパラメータ:

| field | 対象 | 型 | 説明 |
|---|---|---|---|
| `description` | 全対象 | text componentまたは互換文字列 | pack一覧へ表示する説明 |
| `pack_format` | 1.13〜1.21.8 | integer | 基準となるdata pack format |
| `supported_formats` | 1.20.2〜1.21.8 | integer、list、range object | 読み込みを許可するformat範囲 |
| `min_format` | 1.21.9以降 | `[major,minor]` | 許可する最小format。minorまで固定する |
| `max_format` | 1.21.9以降 | `[major,minor]` | 許可する最大format。minorまで固定する |

1.21.9以降で整数の`max_format`を使うと、そのmajorの全minorを許可する意味になります。単一の正式リリースへ固定する場合は2要素配列を使います。

rootの追加section:

| section | 導入 | パラメータ |
|---|---:|---|
| `filter` | 1.19 | `block`配列。各要素は任意の`namespace`正規表現と`path`正規表現 |
| `features` | 1.19.3 | `enabled`配列。要求するfeature flag ID |
| `overlays` | 1.20.2 | `entries`配列。各要素は`directory`と`formats` |

`filter`は低い優先度のpackから見えるresourceを除外し、自分自身のresourceを削除しません。

`overlays.entries[]`:

| field | 型 | 説明 |
|---|---|---|
| `directory` | string | pack rootから見たoverlayディレクトリ。親へ脱出しない |
| `formats` | integer、list、range object | overlayを有効にするdata pack format |

overlayはbase packへresourceを追加または同じIDで置換します。overlay側にファイルがないことを削除指定として扱いません。

## namespace

namespaceは`[a-z0-9_.-]+`、pathは小文字英数字に`_`、`-`、`.`、`/`を組み合わせます。

```text
data/example/function/admin/reset.mcfunction
```

このファイルのresource locationは`example:admin/reset`です。

- 独自resourceは独自namespaceへ置く
- vanilla resourceを意図的に置換するときだけ`minecraft` namespaceへ同じpathで置く
- `#minecraft:load`、`#minecraft:tick`などvanillaが読む入口tagは`minecraft` namespaceへ置く
- 相対pathやfilesystemの大文字小文字へ依存しない

## tagのフォルダ

tag resourceの配置は次の式で決まります。

```text
data/<namespace>/tags/<registry-path>/<tag-path>.json
```

たとえば26.2では、item tag `example:tools/mining` は
`data/example/tags/item/tools/mining.json`、biome tag
`example:cold`は`data/example/tags/worldgen/biome/cold.json`です。
`tags`直下の名前を用途から推測せず、tag対象のregistry IDから
`minecraft:`を除いたpathを使います。

1.18.2でuniversal tagが導入され、blockやitemに限らず任意のregistryへ
tagを定義できるようになりました。新しいregistryのtag pathは
registry pathと同じです。ただし、従来から存在した次の6種は
1.20.6まで旧来の複数形を維持し、1.21で単数形へrenameされました。

| registry ID | 1.20.6以前の名前 | 1.21以降 |
|---|---|---|
| `minecraft:block` | `tags/blocks` | `tags/block` |
| `minecraft:item` | `tags/items` | `tags/item` |
| `minecraft:fluid` | `tags/fluids` | `tags/fluid` |
| `minecraft:entity_type` | `tags/entity_types` | `tags/entity_type` |
| `minecraft:game_event` | `tags/game_events` | `tags/game_event` |
| `minecraft:function` | `tags/functions` | `tags/function` |

1.18.2以降に同じ規則で導ける例:

| registry ID | tag directory |
|---|---|
| `minecraft:potion` | `tags/potion` |
| `minecraft:damage_type` | `tags/damage_type` |
| `minecraft:enchantment` | `tags/enchantment` |
| `minecraft:instrument` | `tags/instrument` |
| `minecraft:painting_variant` | `tags/painting_variant` |
| `minecraft:pig_variant` | `tags/pig_variant` |
| `minecraft:villager_trade` | `tags/villager_trade` |
| `minecraft:worldgen/biome` | `tags/worldgen/biome` |
| `minecraft:worldgen/configured_feature` | `tags/worldgen/configured_feature` |
| `minecraft:worldgen/structure` | `tags/worldgen/structure` |
| `minecraft:worldgen/world_preset` | `tags/worldgen/world_preset` |

この表は許可listではありません。26.2で要素を定義できるregistryは
[`coverage.md`](coverage.md)の各pathを、組み込みregistryは対象バージョンの
registry一覧を同じ式へ当てはめます。tagを読み込めることと、そのtagを参照する
command、JSON field、gameplay consumerが存在することは別です。

## resourceの置換と統合

通常の同一ID resourceは、pack優先順位が高い側のファイルが置換します。tagは`replace`の値で統合方法を制御します。

```json
{
  "replace": false,
  "values": [
    "example:init",
    {
      "id": "example:optional",
      "required": false
    }
  ]
}
```

tagのパラメータ:

| field | 必須性 | 型 | 説明 |
|---|---|---|---|
| `replace` | 任意 | boolean | `false`または省略で低優先度tagへ追加。`true`で置換 |
| `values` | 必須 | array | ID、`#`付きtag ID、またはentry object |
| `values[].id` | object時必須 | IDまたはtag ID | 追加するentry |
| `values[].required` | object時任意 | boolean | `false`なら参照先がなくてもtag全体を失敗させない |

function tagの配列順は実行順です。一般registry tagの順序にゲームロジックを依存させません。

## ファイル形式

| 拡張子 | 用途 | 注意 |
|---|---|---|
| `.json` | registry entry、recipe、loot、advancement、tag、worldgen | UTF-8の厳密なJSON。コメント、末尾カンマ、SNBT suffixは禁止 |
| `.mcfunction` | command列 | 先頭`/`を付けない。1論理行1command |
| `.nbt` | structure | gzip圧縮NBT。テキストエディタで直接変更しない |
| `pack.mcmeta` | metadata | 拡張子はないが内容は厳密なJSON |

JSONの数値はintegerとfloating pointをcodecが区別する場合があります。SNBTの`1b`、`1.0f`をJSONへ持ち込みません。

## 参照切れを検査する

最低限、次を分けて検査します。

1. resource pathから導かれるID
2. JSON内部のIDまたはtag ID
3. `type`が参照するserializer registry
4. `function`、loot table、predicate、item modifierなど別resourceへの参照
5. item、block、entityなど組み込みregistryへの参照

独自namespaceの参照先はpack内の存在を確認し、`minecraft` namespaceは対象バージョンの`registries.json`とvanilla dataで確認します。
