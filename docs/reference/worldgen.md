# world generation

worldgenは単一schemaではなく、registryと`type` discriminatorで分岐するcodec群です。この文書はresource間の接続、共通field、26.2で利用できるtypeの確定方法を説明します。

## 依存関係

```text
dimension
└── generator
    ├── dimension_type
    ├── biome_source
    │   ├── biome
    │   └── multi_noise_biome_source_parameter_list
    └── noise_settings
        ├── noise_router
        │   ├── density_function
        │   └── noise
        └── surface_rule

biome
├── configured_carver
└── placed_feature
    └── configured_feature

world_preset
└── dimension map

structure_set
└── structure
    ├── template_pool
    │   └── structure NBT
    └── processor_list
```

参照先のIDを追加するだけでは、既存のworld presetやbiomeへ自動登録されません。consumer側の配列、tag、presetも接続します。

## 共通配置

1.21以降:

```text
data/<namespace>/dimension/<id>.json
data/<namespace>/dimension_type/<id>.json
data/<namespace>/worldgen/biome/<id>.json
data/<namespace>/worldgen/configured_carver/<id>.json
data/<namespace>/worldgen/configured_feature/<id>.json
data/<namespace>/worldgen/density_function/<id>.json
data/<namespace>/worldgen/noise/<id>.json
data/<namespace>/worldgen/noise_settings/<id>.json
data/<namespace>/worldgen/placed_feature/<id>.json
data/<namespace>/worldgen/processor_list/<id>.json
data/<namespace>/worldgen/structure/<id>.json
data/<namespace>/worldgen/structure_set/<id>.json
data/<namespace>/worldgen/template_pool/<id>.json
data/<namespace>/worldgen/world_preset/<id>.json
data/<namespace>/worldgen/flat_level_generator_preset/<id>.json
data/<namespace>/worldgen/multi_noise_biome_source_parameter_list/<id>.json
```

### 歴史的なworldgen path

worldgenは単なる単数形／複数形renameではなく、registry自体が追加・削除されて
います。現在の一覧を古い正式リリースへコピーしません。

| 正式リリース | folder構造の主な境界 |
|---|---|
| 1.16.2〜1.17.1 | `biome`、`configured_carver`、`configured_feature`、`configured_structure_feature`、`configured_surface_builder`、`noise_settings`、`processor_list`、`template_pool` |
| 1.18〜1.18.1 | `configured_surface_builder`を削除。surface ruleを`noise_settings`へ統合し、`noise`と`placed_feature`を追加 |
| 1.18.2 | `density_function`、data-driven configured structure／structure set、universal registry tagを追加 |
| 1.19 | configured structureを`structure`へ移行し、`world_preset`と`flat_level_generator_preset`を追加 |
| 1.21 | root resource folderとtagの従来名を原則単数形へrename。`worldgen/*`の既存pathは元から単数形 |
| 26.2 | この文書の共通配置に列挙した14種 |

`configured_surface_builder`と`configured_structure_feature`は26.2のfolder一覧から
欠落しているのではなく、過去の正式リリースだけに存在するresourceです。旧形式の
fieldは[`../versions/1.16.2.md`](../versions/1.16.2.md)から対象バージョンの差分を
順に適用します。

## biome

26.2の共通形:

```json
{
  "has_precipitation": true,
  "temperature": 0.8,
  "downfall": 0.4,
  "effects": {
    "water_color": "#3f76e4",
    "foliage_color": "#77ab2f",
    "dry_foliage_color": "#a0a05c",
    "grass_color": "#91bd59"
  },
  "attributes": {
    "minecraft:visual/fog_color": "#c0d8ff",
    "minecraft:visual/water_fog_color": "#050533"
  },
  "carvers": {
    "air": []
  },
  "features": [
    [],
    []
  ],
  "spawners": {},
  "spawn_costs": {}
}
```

| field | 型 | 説明 |
|---|---|---|
| `has_precipitation` | boolean | rain／snowを許可 |
| `temperature` | float | biome temperature |
| `temperature_modifier` | enum | 高度等でtemperatureを変えるmodifier |
| `downfall` | float | precipitationの強さ |
| `effects` | object | water、foliage、grass等biome固有の残存visual field |
| `attributes` | environment attribute map | 1.21.11以降のfog、sky、sound、music等 |
| `carvers` | generation step map | configured carver ID／list／tag |
| `features` | generation step順のnested list | placed feature ID／list／tag。外側indexの意味を変えない |
| `spawners` | mob category map | weighted entity spawn data |
| `spawn_costs` | entity type map | `energy_budget`と`charge` |
| `creature_spawn_probability` | 0〜1のfloat | creature spawn試行確率 |

`features`の外側配列はgeneration stepに対応します。要素を途中から削ってindexを詰めると後続featureのstepが変わります。

1.21.11で`effects.fog_color`、`water_fog_color`、`sky_color`、particle、ambient sound、music等がenvironment attributeへ移行しました。`water_color`、foliage／grass colorは26.2でも`effects`側です。

## configured feature

```json
{
  "type": "minecraft:ore",
  "config": {
    "size": 9,
    "discard_chance_on_air_exposure": 0.0,
    "targets": []
  }
}
```

| field | 説明 |
|---|---|
| `type` | feature type ID |
| `config` | feature type固有object |

26.2のfeature type:

```text
bamboo
basalt_columns
basalt_pillar
block_blob
block_column
block_pile
blue_ice
bonus_chest
chorus_plant
coral_claw
coral_mushroom
coral_tree
delta_feature
desert_well
disk
end_gateway
end_island
end_platform
end_spike
fallen_tree
fill_layer
fossil
freeze_top_layer
geode
glowstone_blob
huge_brown_mushroom
huge_fungus
huge_red_mushroom
iceberg
kelp
lake
large_dripstone
monster_room
multiface_growth
nether_forest_vegetation
netherrack_replace_blobs
no_op
ore
random_boolean_selector
random_selector
replace_single_block
root_system
scattered_ore
sculk_patch
sea_pickle
seagrass
sequence
simple_block
simple_random_selector
speleothem
speleothem_cluster
spike
spring_feature
template
tree
twisting_vines
underwater_magma
vegetation_patch
vines
void_start_platform
waterlogged_vegetation_patch
weeping_vines
weighted_random_selector
```

この一覧は26.2の`minecraft:worldgen/feature` registryを正本にします。各`config`は同じtypeのvanilla fileを使用します。別typeのfieldを組み合わせません。

26.2固有の主な追加:

- `sequence`: `features`を順に配置し、失敗後のfeatureをskip
- `template`: `templates`のweighted listからstructure templateとrotationを選択
- `weighted_random_selector`: weighted placed feature候補から選択
- `speleothem`／`speleothem_cluster`: 旧pointed dripstone系をrenameし、base／pointed block、replaceable block集合を指定

## placed feature

```json
{
  "feature": "example:configured",
  "placement": [
    {
      "type": "minecraft:count",
      "count": 4
    },
    {
      "type": "minecraft:in_square"
    },
    {
      "type": "minecraft:height_range",
      "height": {
        "type": "minecraft:uniform",
        "min_inclusive": {
          "absolute": 0
        },
        "max_inclusive": {
          "absolute": 64
        }
      }
    },
    {
      "type": "minecraft:biome"
    }
  ]
}
```

| field | 説明 |
|---|---|
| `feature` | configured feature IDまたはinline definition |
| `placement` | placement modifier配列。上から順にposition streamを変換 |

26.2のplacement modifier type:

| type | 主なfield |
|---|---|
| `biome` | なし。現在biomeでfeature登録を確認 |
| `block_predicate_filter` | `predicate` |
| `count` | `count` int provider |
| `count_on_every_layer` | `count` |
| `environment_scan` | direction、target condition、allowed search condition、max steps |
| `fixed_placement` | 固定position集合 |
| `height_range` | `height` height provider |
| `heightmap` | `heightmap` type |
| `in_square` | なし。chunk内X/Zを分散 |
| `noise_based_count` | noise level、factor、offset |
| `noise_threshold_count` | threshold、below／above count |
| `random_offset` | XZ／Y spread |
| `rarity_filter` | `chance` |
| `surface_relative_threshold_filter` | heightmap、min／max inclusive |
| `surface_water_depth_filter` | max water depth |

modifier順は可換ではありません。

## configured carver

```json
{
  "type": "minecraft:cave",
  "config": {}
}
```

`type`はcarver type ID、`config`はprobability、height provider、Y scale、lava level、replaceable block、debug settings等のtype固有fieldです。cave、Nether cave、canyon等で形が異なるため、空objectを共通最小形として生成しません。

## noise

```json
{
  "firstOctave": -7,
  "amplitudes": [
    1.0,
    1.0
  ]
}
```

| field | 説明 |
|---|---|
| `firstOctave` | 最初のoctave index |
| `amplitudes` | octaveごとのamplitude |

空配列や極端なoctave数は生成負荷と地形へ影響します。

## density function

density function resourceのrootはdensity function objectまたは許される数値短縮形です。

```json
{
  "type": "minecraft:add",
  "argument1": 0.0,
  "argument2": "example:base_density"
}
```

共通の組合せ:

| 分類 | 例 |
|---|---|
| 定数／参照 | number、density function ID |
| 二項演算 | `add`、`mul`、`min`、`max` |
| 単項変換 | `abs`、`square`、`cube`、`half_negative`、clamp |
| noise | noise ID、XZ／Y scale |
| 座標gradient | `y_clamped_gradient` |
| cache／補間 | cache type、interpolated |
| spline | coordinateとpoint list |

typeごとのfield名は`minecraft:density_function_type` registryと同型vanilla fileで確定します。循環参照を作りません。

## noise settings

主なroot field:

| field | 説明 |
|---|---|
| `sea_level` | sea level Y |
| `disable_mob_generation` | 初期mob生成を抑止 |
| `aquifers_enabled` | aquiferを生成 |
| `ore_veins_enabled` | ore veinを生成 |
| `legacy_random_source` | legacy random sourceを使う |
| `default_block` | 地形の既定block state |
| `default_fluid` | 地形の既定fluid block state |
| `noise` | min_y、height、horizontal／vertical size |
| `noise_router` | temperature、vegetation、continents、erosion、depth、ridges、density等のdensity function |
| `surface_rule` | surface rule dispatch |
| `spawn_target` | climate parameter point list |

`noise.height`と`noise.min_y`はdimension typeのbuild heightと整合させます。routerの一部だけを別バージョンから移植しません。

## structure

configured structure:

```json
{
  "type": "minecraft:jigsaw",
  "biomes": "#example:has_structure/example",
  "step": "surface_structures",
  "spawn_overrides": {},
  "terrain_adaptation": "beard_thin",
  "start_pool": "example:start_pool",
  "size": 6,
  "max_distance_from_center": 80,
  "use_expansion_hack": false
}
```

共通field:

| field | 説明 |
|---|---|
| `type` | structure type ID |
| `biomes` | biome ID／list／tag |
| `step` | generation step |
| `spawn_overrides` | mob categoryごとのbounding boxとspawn list |
| `terrain_adaptation` | `none`、`bury`、`beard_thin`、`beard_box`、`encapsulate`等 |

`start_pool`、`size`、`start_height`、`project_start_to_heightmap`、`max_distance_from_center`等はjigsaw固有です。

## structure set

```json
{
  "structures": [
    {
      "structure": "example:structure",
      "weight": 1
    }
  ],
  "placement": {
    "type": "minecraft:random_spread",
    "salt": 123456,
    "spacing": 32,
    "separation": 8
  }
}
```

| field | 説明 |
|---|---|
| `structures` | structure IDとpositive weightのlist |
| `placement` | structure placement object |

placementはrandom spread、concentric rings等でfieldが異なります。`spacing`は`separation`より大きくします。既存structure setとsaltが衝突した場合の分布も検査します。

## template pool

```json
{
  "fallback": "minecraft:empty",
  "elements": [
    {
      "weight": 1,
      "element": {
        "element_type": "minecraft:single_pool_element",
        "location": "example:room",
        "processors": "minecraft:empty",
        "projection": "rigid"
      }
    }
  ]
}
```

| field | 説明 |
|---|---|
| `fallback` | 配置不能時に使うtemplate pool ID |
| `elements` | weighted pool element list |
| `elements[].weight` | positive integer |
| `elements[].element` | pool element type固有objectまたは参照 |

single elementはstructure NBT ID、processor list、projectionを結び付けます。

## processor list

```json
{
  "processors": [
    {
      "processor_type": "minecraft:block_ignore",
      "blocks": [
        "minecraft:structure_block"
      ]
    }
  ]
}
```

processorは配列順にblock infoを変換します。rule、block ignore、gravity、jigsaw replacement、protected block等でfieldが異なります。

## world preset

```json
{
  "dimensions": {
    "minecraft:overworld": {
      "type": "example:bright_overworld",
      "generator": {
        "type": "minecraft:noise",
        "biome_source": {
          "type": "minecraft:multi_noise",
          "preset": "minecraft:overworld"
        },
        "settings": "minecraft:overworld"
      }
    }
  }
}
```

`dimensions`はdimension IDからdimension definitionへのmapです。通常のworld作成画面へ表示するには対応するworld preset tagやresource pack側の表示も確認します。

## flat level generator preset

```json
{
  "display": {
    "id": "minecraft:grass_block"
  },
  "settings": {
    "biome": "minecraft:plains",
    "features": false,
    "lakes": false,
    "layers": [
      {
        "block": "minecraft:bedrock",
        "height": 1
      }
    ],
    "structure_overrides": []
  }
}
```

| field | 説明 |
|---|---|
| `display` | preset一覧のitem stack |
| `settings.biome` | biome ID |
| `settings.layers` | 下から順のblockとheight |
| `settings.features` | biome feature生成 |
| `settings.lakes` | lake生成 |
| `settings.structure_overrides` | structure set集合 |

## バージョン境界

worldgenは特に次の正式リリースでJSONを共有しません。

| 正式リリース | 主な境界 |
|---|---|
| 1.16／1.16.1 | experimental custom dimension初期形式 |
| 1.16.2 | data-driven worldgen registry |
| 1.18 | cave、height、noise routerを大改編 |
| 1.18.2 | density function、configured structure、tag参照を変更 |
| 1.19.3 | biome、placement、feature flag等を変更 |
| 1.20.5 | block／item representationとworldgen codecの厳格化 |
| 1.21 | 単数形folder |
| 1.21.5 | biome visual、entity／block component関連を変更 |
| 1.21.11 | biome／dimension visualとgameplay fieldをenvironment attributeへ移行 |
| 26.1 | world clockとtimeline接続 |
| 26.2 | feature、surface rule、density functionを追加・rename |

## 検証

```text
[ ] 対象バージョンの同じtypeを持つvanilla JSONを基底にした
[ ] 全参照IDとtagが対象registryに存在する
[ ] biome featuresのgeneration step indexを維持した
[ ] placed featureのmodifier順を意図どおりにした
[ ] dimension type、noise settings、generatorの高さが一致する
[ ] density functionに循環参照がない
[ ] structure、pool、processor、NBTの参照が閉じている
[ ] /reloadだけでなく新規worldと未生成chunkで生成を確認した
[ ] 異なるseedとchunk境界で確認した
[ ] 旧worldの更新はcopyで行いdowngradeしない
```

## 一次資料

- [Mojang: Java Edition 1.16.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-16-2)
- [Mojang: Java Edition 1.18](https://www.minecraft.net/en-us/article/caves---cliffs--part-ii-out-today-java)
- [Mojang: Java Edition 1.21.11](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-11)
- [Mojang: Java Edition 26.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-2)
