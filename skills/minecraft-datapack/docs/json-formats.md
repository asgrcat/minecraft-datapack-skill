# JSON、SNBT、データ種別

この文書はデータパック内ファイルの配置と記法を横断的に定義します。個々の codec は頻繁に変わるため、対象バージョン server JAR の vanilla data と registry report を、そのバージョンのフィールド定義の実例として併用します。item、dimension/worldgen、enchantment、variantのパラメータの意味とバージョン別索引は[`json-parameters/README.md`](json-parameters/README.md)から参照します。

fieldごとの型、既定値、参照関係、26.2の全resource種別は [`reference/README.md`](reference/README.md) と [`reference/coverage.md`](reference/coverage.md) を参照してください。

## JSON と SNBT を混同しない

### JSON

`pack.mcmeta`、advancement、recipe、loot table、tag、predicate、worldgen 等に使います。

```json
{
  "replace": false,
  "values": [
    "minecraft:stone"
  ]
}
```

- object key と string はダブルクォート
- コメント、末尾カンマ、single quote、`1b` のような NBT suffix は不可
- `true`, `false`, `null` は小文字
- ファイルは UTF-8。1.19.3 以降は非 ASCII を `\uXXXX` にせず直接書けることが明文化された
- 不明フィールドが無視されるかエラーかは codec とバージョンで異なる。26.2 の entity predicate のように「以前は無視、以後は拒否」へ変わることがある

### SNBT

command 引数、entity/block entity NBT、storage、structure の文字列表現等に使います。

```snbt
{Tags:["example.active"],NoGravity:1b,Health:20.0f}
```

- key や単純な string は引用を省ける場合がある
- byte/short/long/float/double の suffix (`b`, `s`, `L`, `f`, `d`) がある
- typed array は `[I;1,2,3]` のように書く
- 1.21.5 以降は heterogeneous list を扱えるが、古いバージョン向け SNBT へ混在型 list を出力しない

### text component

- 1.20.4 以前の多くの command/NBT 例は「JSON 文字列を SNBT string に入れる」二重 quoting を使う
- 1.21.5 で text component の保存と command 引数が大きく変わり、多くの場面で JSON 文字列ではなく SNBT object を直接取る
- text component は使う場所ごとに許容表現が異なる。対象バージョンの vanilla data または command graph で確認する

## namespace と resource path

```text
data/<namespace>/<type>/<path>.<json|mcfunction|nbt>
```

例:

```text
data/example/advancement/root.json
```

は resource location `example:root` の advancement です。`minecraft` namespace に置くと vanilla resource を上書きまたは tag へ追加できます。独自 resource は自分の namespace に置き、`load`/`tick` tag のような vanilla の入口だけ `minecraft` を使います。

## ディレクトリ規則

### 1.13〜1.20.6

主要な型名は複数形です。

```text
data/<namespace>/
├── advancements/
├── functions/
├── item_modifiers/       # 1.17以降
├── loot_tables/
├── predicates/           # 1.15以降
├── recipes/
├── structures/
└── tags/
    ├── blocks/
    ├── fluids/
    ├── functions/
    └── items/
```

レジストリの追加に応じて `tags/entity_types`, `tags/game_events` 等も存在します。

### 1.21〜26.2

データ種別と tag の registry folder は原則単数形です。

```text
data/<namespace>/
├── advancement/
├── function/
├── item_modifier/
├── loot_table/
├── predicate/
├── recipe/
├── structure/
└── tags/
    ├── block/
    ├── fluid/
    ├── function/
    ├── item/
    └── <registry-name>/
```

1.21 で `functions → function`, `loot_tables → loot_table`, `tags/items → tags/item` のように rename されました。旧フォルダを同居させて済ませず、複数バージョン対応では overlay を使います。

## データ種別の導入・変更表

| 種別 | 最初の正式リリース | 配置と役割 |
|---|---:|---|
| function | 1.13 | command を列挙する `.mcfunction` |
| advancement | 1.13 | trigger、criteria、requirements、reward |
| loot table | 1.13 | mob/block/container/fishing 等の loot |
| recipe | 1.13 | crafting、cooking、stonecutting、smithing 等 |
| structure | 1.13 | structure block 互換の圧縮 NBT (`.nbt`) |
| tag | 1.13 | registry entry または function の集合 |
| predicate | 1.15 | loot condition を再利用可能な JSON にしたもの |
| dimension / dimension_type | 1.16 | カスタムdimension。1.16.0/1.16.1の初期schemaはexperimental |
| worldgen registry folder群 | 1.16.2 | カスタムworld generationを拡大。導入当初からバージョン間変更が多い |
| item modifier | 1.17 | loot function の再利用可能な JSON |
| chat_type | 1.19 | chat message の decoration/narration |
| damage_type | 1.19.4 | damage の message/scaling/exhaustion/effects |
| trim_pattern / trim_material | 1.20 系 | armor trim のデータ駆動 registry |
| banner_pattern / wolf_variant | 1.20.5 | banner/wolf variant のデータ駆動化 |
| enchantment / enchantment_provider | 1.21 | enchantment と選択 provider |
| jukebox_song / painting_variant | 1.21 | jukebox song と painting のデータ駆動化 |
| instrument | 1.21.2 | goat horn instrument のデータ駆動化 |
| pig/cow/chicken/cat/frog variant | 1.21.5 | entity variant と spawn condition |
| wolf_sound_variant | 1.21.5 | wolf の adult/baby sound set |
| test_environment / test_instance | 1.21.5 | GameTest 定義 |
| trial_spawner | 1.21.2 | trial spawner configuration |
| dialog | 1.21.6 | client に表示する dialog |
| zombie_nautilus_variant / timeline | 1.21.11 | variant と時間に応じた event/attribute |
| world_clock / trade_set / villager_trade | 26.1 | clock と villager/wandering trader trade |
| cat/chicken/cow/pig_sound_variant | 26.1 | mob の adult/baby sound set |
| sulfur_cube_archetype | 26.2 | Sulfur Cube の item 群、浮力、爆発 |

この表は「その型が使用可能になる下限」です。型の内部フィールドは導入後も変わるため、バージョンファイルの差分を優先します。

## 26.2 の安定リリースフォルダ一覧

`data/<namespace>/`直下で26.2が読み込む全resource path:

```text
advancement
banner_pattern
cat_sound_variant
cat_variant
chat_type
chicken_sound_variant
chicken_variant
cow_sound_variant
cow_variant
damage_type
dialog
dimension
dimension_type
enchantment
enchantment_provider
frog_variant
function
instrument
item_modifier
jukebox_song
loot_table
painting_variant
pig_sound_variant
pig_variant
predicate
recipe
structure
sulfur_cube_archetype
tags
test_environment
test_instance
timeline
trade_set
trial_spawner
trim_material
trim_pattern
villager_trade
wolf_sound_variant
wolf_variant
world_clock
worldgen
zombie_nautilus_variant
```

worldgen の下:

```text
worldgen/biome
worldgen/configured_carver
worldgen/configured_feature
worldgen/density_function
worldgen/flat_level_generator_preset
worldgen/multi_noise_biome_source_parameter_list
worldgen/noise
worldgen/noise_settings
worldgen/placed_feature
worldgen/processor_list
worldgen/structure
worldgen/structure_set
worldgen/template_pool
worldgen/world_preset
```

この一覧を古いバージョンへそのまま使ってはいけません。対象バージョンで実在する folder は server JAR から生成した `data/minecraft/` で確認します。

## `pack.mcmeta`

時代別の完全な最小形と overlay は [`compatibility.md`](compatibility.md) を参照してください。root object の主要 section:

| section | 導入 | 説明 |
|---|---:|---|
| `pack` | 1.13以前 | description と format/range |
| `filter` | 1.19 | 下位優先度の pack resource を正規表現で除外 |
| `features` | 1.19.3 | experimental feature flag |
| `overlays` | 1.20.2 | format 範囲別の上書き sub-pack |

`pack_format`/`supported_formats` と `min_format`/`max_format` の切替は 1.21.9 が境界です。

## tag

配置例:

```text
data/example/tags/block/mineable.json          # 1.21以降
data/example/tags/blocks/mineable.json         # 1.20.6以前
```

```json
{
  "replace": false,
  "values": [
    "minecraft:stone",
    "#minecraft:logs",
    {
      "id": "example:optional_block",
      "required": false
    }
  ]
}
```

- `replace` 省略時は false。下位 pack の同名 tag へ追加
- string は entry ID、`#` 付きは別 tag
- optional object の使用可否と field 名は対象バージョンで確認する
- tag file があるだけでは registry entry 自体を新規作成できない。存在する entry を分類する
- function tag の `values` は順序に意味がある

## advancement

root、criteria、trigger、requirements、rewardsのparameterとバージョン境界は[`json-parameters/advancements.md`](json-parameters/advancements.md)を参照してください。

criteria/requirementsのAND・OR、rewardの実行、grant/revoke、反復eventへの利用は [`advancements.md`](advancements.md) を参照してください。

最小の trigger-only 例:

```json
{
  "criteria": {
    "tick": {
      "trigger": "minecraft:tick"
    }
  },
  "rewards": {
    "function": "example:on_first_tick"
  }
}
```

一般形:

```json
{
  "parent": "example:root",
  "display": {
    "icon": {
      "id": "minecraft:stone"
    },
    "title": {
      "text": "Title"
    },
    "description": {
      "text": "Description"
    },
    "frame": "task",
    "show_toast": true,
    "announce_to_chat": false,
    "hidden": false
  },
  "criteria": {
    "condition_name": {
      "trigger": "minecraft:location",
      "conditions": {}
    }
  },
  "requirements": [
    [
      "condition_name"
    ]
  ],
  "rewards": {
    "experience": 0,
    "function": "example:on_complete"
  }
}
```

注意:

- `display.icon` の item stack 形式は 1.20.5 の component 化で変わる
- advancement trigger の `conditions` はバージョンごとに変わる。1.20 では `placed_block`, `item_used_on_block`, `allay_drop_item_on_block` の複数 field が `location` へ統合された
- trigger 名を推測しない。vanilla advancement または registry report を確認する

## predicate

独立predicate、loot condition、entity/location/item/block predicateの型とバージョン境界は[`json-parameters/predicates.md`](json-parameters/predicates.md)を参照してください。

predicate file は単一の loot condition、または暗黙の `all_of` となる配列です。

1.15〜26.1 の代表例:

```json
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "type": "minecraft:player"
  }
}
```

26.2 では entity predicate が component-map 型へ変わり、`type` は `minecraft:entity_type` へ rename されました。

```json
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "minecraft:entity_type": "minecraft:player"
  }
}
```

26.2 は不明な sub-predicate key を拒否します。古い typo が黙って無視される前提で移行しないでください。

command から:

```mcfunction
execute if predicate example:is_player run function example:matched
```

predicate の有効な loot context parameter は呼出場所に依存します。`this`, `killer`, `direct_killer`, `origin`, `tool` 等が常に揃うとは限りません。

## item modifier

loot functionとの共有codec、実行context、バージョン境界は[`json-parameters/loot-recipes.md`](json-parameters/loot-recipes.md)を参照してください。

単一 loot function object または、順に適用する配列です。

```json
[
  {
    "function": "minecraft:set_count",
    "count": 2,
    "add": false
  },
  {
    "function": "minecraft:set_name",
    "name": {
      "text": "Reward"
    }
  }
]
```

```mcfunction
item modify entity @s weapon.mainhand example:reward
```

- 1.17 以降
- 1.21.11 の `filtered`、26.2 の component/predicate など内部 function は変化する
- item stack component 化以後は NBT を書く旧 loot function から component 用 function へ移行する

## loot table

root、pool、entry、condition、function、provider、contextのparameterとバージョン境界は[`json-parameters/loot-recipes.md`](json-parameters/loot-recipes.md)を参照してください。

```json
{
  "type": "minecraft:generic",
  "pools": [
    {
      "rolls": 1,
      "entries": [
        {
          "type": "minecraft:item",
          "name": "minecraft:diamond",
          "functions": [
            {
              "function": "minecraft:set_count",
              "count": 2
            }
          ]
        }
      ]
    }
  ],
  "functions": []
}
```

構造:

- root: `type`, `random_sequence`, `pools`, root `functions`
- pool: `rolls`, `bonus_rolls`, `entries`, `conditions`, `functions`
- entry: item/tag/loot_table/dynamic/empty と、group/alternatives/sequence 等の合成
- condition: predicate と同じ condition codec
- function: item modifier と同じ loot function codec
- number provider: constant、uniform、binomial、score、storage 等。利用可否はバージョン依存

`type` は利用可能な loot context を決めます。context にない `tool` や entity target を参照すると validation error または実行時失敗になります。

主な破壊点:

- 1.17: number provider と `set_damage` 等の型が厳格化
- 1.18: `set_contents`, `set_loot_table` の `type` 必須化
- 1.20: `alternative` を `any_of` へ rename
- 1.20.5: item component 対応、item sub-predicate/loot function の大改編
- 1.21.11: `filtered` の fields 変更、`discard` 追加

## recipe

主要serializer、ingredient、result、category、componentのバージョン境界は[`json-parameters/loot-recipes.md`](json-parameters/loot-recipes.md)を参照してください。

### shaped crafting: 1.20.4 以前

```json
{
  "type": "minecraft:crafting_shaped",
  "pattern": [
    "SS",
    "SS"
  ],
  "key": {
    "S": {
      "item": "minecraft:stone"
    }
  },
  "result": {
    "item": "minecraft:stone_bricks",
    "count": 4
  }
}
```

### shaped crafting: 1.20.5〜1.21.1

```json
{
  "type": "minecraft:crafting_shaped",
  "category": "building",
  "pattern": [
    "SS",
    "SS"
  ],
  "key": {
    "S": {
      "item": "minecraft:stone"
    }
  },
  "result": {
    "id": "minecraft:stone_bricks",
    "count": 4
  }
}
```

1.21.2 以降は ingredient をinline ID/tagにします。

```json
{
  "type": "minecraft:crafting_shaped",
  "category": "building",
  "pattern": [
    "SS",
    "SS"
  ],
  "key": {
    "S": "minecraft:stone"
  },
  "result": {
    "id": "minecraft:stone_bricks",
    "count": 4
  }
}
```

`result` は component を持てるバージョンがあります。ingredient の object/list/inline 表現は変更されているため、対象バージョンの vanilla recipe と同じ形にします。

代表 type:

- `crafting_shaped`, `crafting_shapeless`
- `smelting`, `blasting`, `smoking`, `campfire_cooking`
- `stonecutting`
- smithing 系。1.20 で template を使う `smithing_transform`/`smithing_trim` へ変更
- `crafting_transmute`。1.21.2 以降
- special crafting。26.1 で一部がよりデータ駆動化

## damage type

1.19.4 以降:

```json
{
  "message_id": "example",
  "scaling": "never",
  "exhaustion": 0.1
}
```

damage の性質は旧 boolean field ではなく damage type tag で分類します。

```mcfunction
damage @s 4 example:custom
```

data-driven registry を追加すると experimental 扱いになるバージョンがあります。world 作成/読み込み時の警告も検査してください。

## structure

`structure` は JSON ではなく gzip 圧縮 NBT (`.nbt`) です。

- structure block で保存するか、data generator で `.snbt` と相互変換する
- resource path は 1.20.6 以前の `structures/`、1.21 以降の `structure/`
- 直接 binary をテキスト編集しない
- block/entity palette と data version の変換は対象バージョンで実際に load/save して確認する

## world generation

worldgen は1つの固定 schema ではなく、registry と dispatch `type` ごとの codec 群です。AI は次の順で作成します。

dimension type、generator、biome source、各worldgen familyの役割と主要fieldは
[`json-parameters/dimensions-worldgen.md`](json-parameters/dimensions-worldgen.md)、
dimension、biome、environment attributes、timeline、world clockの詳細fieldは
[`reference/world-and-environment.md`](reference/world-and-environment.md)、
feature、placement、noise、structureの共通構造は
[`reference/worldgen.md`](reference/worldgen.md)を参照してください。

1. 対象バージョン server JAR から vanilla data を生成
2. 作りたい `type` と同じ vanilla file を最小の基底例に選ぶ
3. `type` 固有 field だけ変更し、参照する biome/feature/noise/tag が対象バージョン registry に存在するか確認
4. `/reload` だけでなく、新規 world または未生成 chunk で検査
5. バージョンをまたぐときは worldgen JSON を共有せず、差分の大きい境界ごとに overlay または別 pack を使う

主な folder:

- `dimension`, `dimension_type`
- `worldgen/biome`
- `worldgen/configured_carver`
- `worldgen/configured_feature`
- `worldgen/placed_feature`
- `worldgen/noise`, `worldgen/noise_settings`, `worldgen/density_function`
- `worldgen/structure`, `worldgen/structure_set`
- `worldgen/processor_list`, `worldgen/template_pool`
- `worldgen/world_preset`, `worldgen/flat_level_generator_preset`

1.16.2、1.18、1.18.2、1.19.3、1.20.5、1.21、1.21.5、26.1、26.2 は特に codec 差分を確認します。

## データ駆動 registry

enchantment、variant、dialog、trade 等も `type` や effect の組合せが多いため、共通の空 object を「最小例」として生成してはいけません。対象バージョン vanilla に同型がない custom entry では、公式リリースノートの field list を codec として使います。

26.2で要素を定義できる全registryとパラメータの説明は [`reference/registry-formats.md`](reference/registry-formats.md)、item componentとpredicateは [`reference/components-and-predicates.md`](reference/components-and-predicates.md)、recipe、loot、GameTestは [`reference/recipes-loot-and-tests.md`](reference/recipes-loot-and-tests.md) を参照します。

AI の規則:

- file path が registry ID になる
- registry 参照は resource location で明示する
- inline definition と registry reference の両方を許す field でも、再利用する場合は registry entry を優先
- experimental と記された registry を追加するときは、通常 world への導入と world upgrade の影響を利用者へ明示
- tag だけを作って registry entry を作成したと扱わない

26.2 の `sulfur_cube_archetype` の公式 field:

```json
{
  "items": "#example:sulfur_cube_food",
  "buoyant": true,
  "explosion": {
    "fuse": 40,
    "power": 2,
    "causes_fire": false
  }
}
```

`contact_damage`と`explosion`は省略可能です。その他のroot fieldと各nested
parameterの型・値域は
[`reference/registry-formats.md`](reference/registry-formats.md)を参照します。

## JSON を生成する AI のチェックリスト

1. 対象正式リリースを1つに固定したか
2. そのバージョンの単数/複数 folder を使ったか
3. file path と参照 resource location が一致するか
4. JSON と SNBT の引用・数値 suffix を混ぜていないか
5. item stack が 1.20.5 境界の正しい形式か
6. text component が 1.21.5 境界の正しい表現か
7. entity predicate が 26.2 境界の正しい key か
8. `type` に対応する field と loot context だけを使ったか
9. 参照 ID と tag が対象バージョン registry に存在するか
10. 対象バージョン server JAR で reload、log、機能テストを完了したか

## 参照

- [Minecraft Wiki: Data pack folder structure](https://minecraft.wiki/w/Data_pack#Folder_structure)
- [Minecraft Wiki: `pack.mcmeta`](https://minecraft.wiki/w/Pack.mcmeta)
- [Minecraft Wiki: Tag](https://minecraft.wiki/w/Tag)
- [Minecraft Wiki: Advancement definition](https://minecraft.wiki/w/Advancement_definition)
- [Minecraft Wiki: Predicate](https://minecraft.wiki/w/Predicate)
- [Minecraft Wiki: Item modifier](https://minecraft.wiki/w/Item_modifier)
- [Minecraft Wiki: Loot table](https://minecraft.wiki/w/Loot_table)
- [Minecraft Wiki: Recipe](https://minecraft.wiki/w/Recipe)
- [Minecraft Wiki: Custom world generation](https://minecraft.wiki/w/Custom_world_generation)
- [Mojang: Java Edition 26.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-2)
