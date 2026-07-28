# dimension、environment attributes、timeline

この文書は、カスタムdimensionと、1.21.11以降のenvironment attributes、26.1以降のworld clockを扱います。26.2の書式を基準にし、古い正式リリースへ適用するときは最後のバージョン境界を使います。

## resourceの関係

```text
dimension
├── type ───────────────→ dimension_type
└── generator ──────────→ biome/noise_settings/flat settings

dimension_type
├── attributes ─────────→ environment attribute map
├── timelines ──────────→ timeline ID/list/tag
└── default_clock ──────→ world_clock

timeline
├── clock ──────────────→ world_clock
├── time_markers
└── tracks ─────────────→ environment attribute IDごとのkeyframe
```

`dimension`はworldのgeneratorとdimension typeを結び付けます。`dimension_type`は高さ、座標倍率、光、bedなどの環境規則を定義します。environment attributeはdimension typeまたはbiomeの`attributes`から値を供給し、timelineは時間に応じて値を重ねます。

## `dimension`

配置:

```text
data/<namespace>/dimension/<id>.json
```

共通形:

```json
{
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
```

| field | 必須性 | 型 | 説明 |
|---|---|---|---|
| `type` | 必須 | dimension type IDまたはinline object | 高さ、時間、環境規則 |
| `generator` | 必須 | generator object | chunkの生成方法 |
| `generator.type` | 必須 | `minecraft:noise`、`minecraft:flat`、`minecraft:debug`等 | generator codecを選択 |

`generator.type`以降はtype別です。noise、flat、debugのパラメータは [`worldgen.md`](worldgen.md) を参照します。

## 26.2の`dimension_type`

配置:

```text
data/<namespace>/dimension_type/<id>.json
```

### rootパラメータ

| field | 型 | 説明 |
|---|---|---|
| `ambient_light` | 0〜1のfloat | 従来からあるdimensionの環境光係数。26.1以降の色と明るさは`minecraft:visual/ambient_light_color`も併用する |
| `attributes` | environment attribute map | dimensionを最低優先度の属性sourceとして使う |
| `cardinal_light` | `default`または`nether` | block面へ適用する方角光。省略時`default` |
| `coordinate_scale` | 正のdouble | Overworldとの座標倍率。Netherは`8.0` |
| `default_clock` | world clock ID | `/time`でclockを省略したときに使うclock |
| `has_ceiling` | boolean | 高さmapやspawn処理等で天井があるdimensionとして扱う |
| `has_ender_dragon_fight` | boolean | Ender Dragon fight用のdimensionか |
| `has_fixed_time` | boolean | 固定時間のdimensionとして扱う。視覚的な天体角度はenvironment attributeで別に指定する |
| `has_skylight` | boolean | sky lightを計算するか |
| `height` | 16の倍数のinteger | 生成可能な縦幅。`min_y + height`も許容範囲内にする |
| `infiniburn` | block ID／list／tag | 無限燃焼するblock集合。26.2で単一IDとlistも受付 |
| `logical_height` | integer | chorus fruitやNether portal等が論理的に使う高さ。`height`以下 |
| `min_y` | 16の倍数のinteger | 最低生成Y |
| `monster_spawn_block_light_limit` | 0〜15のinteger | monster spawnで許容するblock lightの上限 |
| `monster_spawn_light_level` | integerまたはint provider | monster spawnで許容する総合light level |
| `skybox` | `none`、`overworld`、`end` | 描画するskybox。省略時`overworld` |
| `timelines` | timeline ID／list／tag | このdimensionで有効なtimeline |

`height`、`min_y`、`logical_height`の数値制約は正式リリースごとにcodecで検査されます。16の倍数、論理高さが物理高さ以下、上下端がゲームのbuild height内という3条件を同時に満たし、対象serverでreloadします。

### 26.2の明るいdimension type

次はOverworld相当の設定を独自IDへ複製し、暗所の視覚的な環境光を白へ近付ける例です。

```json
{
  "ambient_light": 1.0,
  "attributes": {
    "minecraft:audio/ambient_sounds": {
      "mood": {
        "block_search_extent": 8,
        "offset": 2.0,
        "sound": "minecraft:ambient.cave",
        "tick_delay": 6000
      }
    },
    "minecraft:audio/background_music": {
      "creative": {
        "max_delay": 24000,
        "min_delay": 12000,
        "sound": "minecraft:music.creative"
      },
      "default": {
        "max_delay": 24000,
        "min_delay": 12000,
        "sound": "minecraft:music.game"
      }
    },
    "minecraft:gameplay/bed_rule": {
      "can_set_spawn": "always",
      "can_sleep": "when_dark",
      "error_message": {
        "translate": "block.minecraft.bed.no_sleep"
      }
    },
    "minecraft:gameplay/nether_portal_spawns_piglin": true,
    "minecraft:gameplay/respawn_anchor_works": false,
    "minecraft:visual/ambient_light_color": "#ffffff",
    "minecraft:visual/cloud_color": "#ccffffff",
    "minecraft:visual/cloud_height": 192.33,
    "minecraft:visual/fog_color": "#c0d8ff",
    "minecraft:visual/sky_color": "#78a7ff"
  },
  "coordinate_scale": 1.0,
  "default_clock": "minecraft:overworld",
  "has_ceiling": false,
  "has_ender_dragon_fight": false,
  "has_skylight": true,
  "height": 384,
  "infiniburn": "#minecraft:infiniburn_overworld",
  "logical_height": 384,
  "min_y": -64,
  "monster_spawn_block_light_limit": 0,
  "monster_spawn_light_level": {
    "type": "minecraft:uniform",
    "max_inclusive": 7,
    "min_inclusive": 0
  },
  "timelines": "#minecraft:in_overworld"
}
```

この例は視覚的な暗さを変更します。洞窟内部のsky light値を生成するものではなく、block lightを配置するものでもありません。monster spawnを止める要件は`monster_spawn_*`を別に設計します。

既存の`minecraft:overworld`を置換する場合は、同じIDのdimension type全体を置換します。JSON objectはfield単位でmergeされないため、`ambient_light`だけの部分ファイルを置いてはいけません。world設定に関係する変更は`/reload`だけでなく、新規world、server再起動、未生成chunkで検証します。

## environment attribute map

1.21.11以降、dimension typeとbiomeは`attributes` objectを持てます。

```json
{
  "attributes": {
    "minecraft:visual/fog_color": "#ffaa00",
    "minecraft:visual/water_fog_end_distance": {
      "modifier": "multiply",
      "argument": 0.85
    }
  }
}
```

短縮形は値を上書きします。object形はmodifierを指定します。

| field | 必須性 | 型 | 説明 |
|---|---|---|---|
| `modifier` | 任意 | modifier ID | 省略時`override` |
| `argument` | object形で必須 | modifier固有 | 前のsourceから渡された値へ適用する引数 |

値のsourceは低い方からdimension、biome、timeline、weatherです。後段は前段を上書きするかmodifierで合成します。biome間やtimeline keyframe間で補間されるかはattributeの型に依存します。

### 共通値

| 型 | 書式 |
|---|---|
| RGB | `"#rrggbb"`、`[r,g,b]`（各0〜1）、packed integer |
| ARGB | `"#aarrggbb"`、`[a,r,g,b]`（各0〜1）、packed integer |
| particle | `{"type":"minecraft:...","<type固有field>":...}` |
| boolean | `true`または`false` |
| float | JSON number。attribute固有の範囲を守る |
| activity | `minecraft:activity` registryのID |

### modifier

| 値型 | 主なmodifier | 説明 |
|---|---|---|
| 全型 | `override` | 後段の値で置換 |
| boolean | `and`, `nand`, `or`, `nor`, `xor`, `xnor` | boolean演算 |
| float | `add`, `subtract`, `multiply`, `minimum`, `maximum` | 数値演算 |
| float | `alpha_blend` | `{value,alpha}`。`alpha`は0〜1 |
| RGB／ARGB | `add`, `subtract`, `multiply` | channel単位で演算 |
| RGB／ARGB | `alpha_blend` | alpha付きの色でblend |
| RGB／ARGB | `blend_to_gray` | `{brightness,factor}`でgrayへblend |

attributeごとに使えるmodifierは異なります。`registries.json`へmodifier対応表は出ないため、公式リリースノートとreloadで確認します。

## 26.2のenvironment attribute

### visual

| ID | 値型 | 説明 |
|---|---|---|
| `minecraft:visual/ambient_light_color` | RGB | light level 0へ加える環境光の色と明るさ。block lightとsky lightはこの上へ加算 |
| `minecraft:visual/ambient_particles` | `{particle,probability}`のlist | camera周辺へ出すambient particle。`probability`は0〜1 |
| `minecraft:visual/block_light_tint` | RGB | 画面内のblock light全体へ使う色。個別光源ごとの色分けではない |
| `minecraft:visual/cloud_color` | ARGB | cloudの色とalpha |
| `minecraft:visual/cloud_fog_end_distance` | 非負float | cloud内fogの終了距離 |
| `minecraft:visual/cloud_height` | float | cloudの基準Y |
| `minecraft:visual/default_dripstone_particle` | particle | 上にfluidがないdripstoneの既定particle |
| `minecraft:visual/fog_color` | RGB | 通常fogの色 |
| `minecraft:visual/fog_start_distance` | float | 通常fogの開始距離。負値はcamera後方から始まった密度として扱う |
| `minecraft:visual/fog_end_distance` | 非負float | 通常fogが最大密度になる距離 |
| `minecraft:visual/moon_angle` | float degree | moonの角度。`overworld` skyboxで使用 |
| `minecraft:visual/moon_phase` | enum | `full_moon`から`waxing_gibbous`までの8 phase |
| `minecraft:visual/night_vision_color` | RGB | Night Vision中にambient light colorとchannelごとの最大値を取る色 |
| `minecraft:visual/sky_color` | RGB | skyの色。`overworld` skyboxで使用 |
| `minecraft:visual/sky_fog_end_distance` | 非負float | sky fogの終了距離 |
| `minecraft:visual/sky_light_color` | RGB | lightmapへ渡すsky lightの色 |
| `minecraft:visual/sky_light_factor` | float | sky lightの視覚的な明るさ。gameplay値は`gameplay/sky_light_level` |
| `minecraft:visual/star_angle` | float degree | starの角度 |
| `minecraft:visual/star_brightness` | 0〜1のfloat | starの明るさ |
| `minecraft:visual/sun_angle` | float degree | sunの角度 |
| `minecraft:visual/sunrise_sunset_color` | ARGB | sunrise/sunsetの色。alpha 0なら描画しない |
| `minecraft:visual/water_fog_color` | RGB | water内fogの色 |
| `minecraft:visual/water_fog_end_distance` | 非負float | water内fogの終了距離 |
| `minecraft:visual/water_fog_start_distance` | float | water内fogの開始距離 |

### gameplay

| ID | 値型 | 説明 |
|---|---|---|
| `minecraft:gameplay/baby_villager_activity` | activity ID | baby villagerの現在activity |
| `minecraft:gameplay/bed_rule` | object | `can_sleep`、`can_set_spawn`、任意の`explodes`、`error_message` |
| `minecraft:gameplay/bees_stay_in_hive` | boolean | beeがhiveに留まる時間帯 |
| `minecraft:gameplay/can_pillager_patrol_spawn` | boolean | patrol spawnを許可 |
| `minecraft:gameplay/can_start_raid` | boolean | raid開始を許可 |
| `minecraft:gameplay/cat_waking_up_gift_chance` | 0〜1のfloat | sleeping playerを起こしたcatのgift chance |
| `minecraft:gameplay/creaking_active` | boolean | Creaking HeartとCreakingをactiveにする |
| `minecraft:gameplay/eyeblossom_open` | booleanまたは`default` | Eyeblossomの開閉遷移。`default`は現状態を維持 |
| `minecraft:gameplay/fast_lava` | boolean | lavaの拡散と押す力をNether相当にする。dimension全体で評価 |
| `minecraft:gameplay/increased_fire_burnout` | boolean | fireが速く消えるか |
| `minecraft:gameplay/monsters_burn` | boolean | daylight対象monsterが燃える時間帯 |
| `minecraft:gameplay/nether_portal_spawns_piglin` | boolean | portal blockからPiglinがspawnするか |
| `minecraft:gameplay/piglins_zombify` | boolean | Piglin／Hoglinがzombifyするか |
| `minecraft:gameplay/respawn_anchor_works` | boolean | Respawn Anchorがspawn設定に使えるか |
| `minecraft:gameplay/sky_light_level` | float | mob spawnやDaylight Detectorへ使うsky light。dimension全体で評価 |
| `minecraft:gameplay/snow_golem_melts` | boolean | Snow Golemが環境でdamageを受けるか |
| `minecraft:gameplay/surface_slime_spawn_chance` | 0〜1のfloat | 対象biomeでのsurface Slime spawn追加chance |
| `minecraft:gameplay/turtle_egg_hatch_chance` | 0〜1のfloat | random tickごとのTurtle Egg進行chance |
| `minecraft:gameplay/villager_activity` | activity ID | adult villagerの現在activity |
| `minecraft:gameplay/water_evaporates` | boolean | water配置時に蒸発するか |

### audio

| ID | 値型 | 説明 |
|---|---|---|
| `minecraft:audio/ambient_sounds` | object | `loop`、`mood`、`additions`等のambient sound設定 |
| `minecraft:audio/background_music` | object | `default`、`creative`等のmusic条件。各設定は`sound`、`min_delay`、`max_delay`、任意の`replace_current_music` |
| `minecraft:audio/firefly_bush_sounds` | boolean | Firefly Bushのambient soundを有効化 |
| `minecraft:audio/music_volume` | float | background music volumeへ適用 |

属性IDの存在は26.2の`minecraft:environment_attribute` registryで確認します。値型、既定値、位置評価かdimension全体評価かは属性ごとに異なります。

## `timeline`

配置:

```text
data/<namespace>/timeline/<id>.json
```

26.1以降の一般形:

```json
{
  "clock": "example:clock",
  "period_ticks": 24000,
  "time_markers": {
    "example:noon": {
      "ticks": 6000,
      "show_in_commands": true
    }
  },
  "tracks": {
    "minecraft:visual/ambient_light_color": {
      "ease": "linear",
      "modifier": "override",
      "keyframes": [
        {
          "ticks": 0,
          "value": "#202020"
        },
        {
          "ticks": 6000,
          "value": "#ffffff"
        }
      ]
    }
  }
}
```

| field | 必須性 | 型 | 説明 |
|---|---|---|---|
| `clock` | 26.1以降必須 | world clock ID | timelineが読むclock |
| `period_ticks` | 任意 | 正のinteger | 指定するとこのtick数で繰り返す。省略時は非反復 |
| `time_markers` | 任意 | map | `/time set`等で参照できる名前付き時刻 |
| `tracks` | 任意 | map | environment attribute IDからattribute trackへのmap |

`time_markers`の値:

| 形 | 説明 |
|---|---|
| 非負integer | markerのtick |
| object | `ticks`と任意の`show_in_commands` |

attribute track:

| field | 必須性 | 型 | 説明 |
|---|---|---|---|
| `keyframes` | 必須 | array | `ticks`昇順。同じtickは最大2件で即時遷移を表す |
| `keyframes[].ticks` | 必須 | integer | 反復時は0から`period_ticks`の範囲 |
| `keyframes[].value` | 必須 | attributeまたはmodifier固有型 | そのtickでの値またはmodifier引数 |
| `modifier` | 任意 | modifier ID | 省略時`override` |
| `ease` | 任意 | easing IDまたはcubic Bézier | 省略時`linear`。非補間attributeでは効果なし |

easingは`constant`、`linear`、`in_*`、`out_*`、`in_out_*`系、または次のobjectです。

```json
{
  "cubic_bezier": [0.25, 0.1, 0.25, 1.0]
}
```

`x1`と`x2`は0〜1、`y1`と`y2`はfloatです。

## `world_clock`

配置:

```text
data/<namespace>/world_clock/<id>.json
```

26.1のformatはfieldを持たないobjectです。

```json
{}
```

clockは毎tick進む独立した時刻を保持し、`/time of <clock> ...`でset、add、pause、resume、rate、queryを操作します。timelineの`clock`とdimension typeの`default_clock`は同じregistry IDを参照します。

## バージョン境界

| 正式リリース | 境界 |
|---|---|
| 1.16／1.16.1 | custom dimensionがexperimentalな初期形式 |
| 1.16.2 | `dimension`、`dimension_type`、worldgen registryをdata packから扱う形式へ |
| 1.18 | noise worldgenを大改編 |
| 1.19 | dimension typeにmonster spawn light field |
| 1.21.6 | `cloud_height`をdimension typeへ追加 |
| 1.21.11 | `attributes`、`timelines`、`skybox`、`cardinal_light`を導入し、旧visual/gameplay fieldをenvironment attributeへ移行 |
| 26.1 | world clockを導入。timelineの`clock`を必須化し`time_markers`を追加 |
| 26.2 | `infiniburn`がtagに加えて単一IDとlistを受付 |

1.21.10以前のdimension typeへ26.2の`attributes`や`timelines`を出力しません。1.21.11から26.1へ移す場合も、timelineの`clock`必須化を適用します。

## 検証

```text
[ ] dimensionとdimension_typeのIDが一致する
[ ] dimension typeから参照するtimelineとworld clockが存在する
[ ] height、min_y、logical_heightが対象codecの範囲内
[ ] environment attribute IDが対象バージョンのregistryに存在する
[ ] attributeの値型とmodifier引数型が一致する
[ ] biomeで使用できないdimension単位attributeをbiomeへ置いていない
[ ] 既存vanilla IDの置換範囲を明示した
[ ] /reloadだけでなく新規worldまたはserver再起動で確認した
[ ] 視覚光とmob spawn等のgameplay lightを別々に検証した
```

## 一次資料

- [Mojang: Java Edition 1.21.11](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-11)
- [Mojang: Java Edition 26.1](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-1)
- [Mojang: Java Edition 26.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-2)
