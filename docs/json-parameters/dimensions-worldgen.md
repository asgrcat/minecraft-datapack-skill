# dimension / worldgen JSON パラメータ

Minecraft Java Edition 1.16 から 26.2 までの `dimension`、`dimension_type`、world generation registry を扱います。カスタム world generation は同じ名前の field でもバージョンによって codec や意味が変わります。対象バージョンを完全一致で決め、Mojang の release note と対象バージョン server JAR が生成した data/report を正本にしてください。

この文書は設計時の索引です。全 `type` の完全な codec を固定 schema として複製するものではありません。

## データ型の関係

`dimension`、`dimension_type`、`worldgen/*` は次の参照関係を持ちます。

```text
world preset または dimension registry
└─ dimension
   ├─ type ───────────────→ dimension_type
   │                         環境、座標尺度、高さ、描画、gameplay規則
   └─ generator
      ├─ biome_source ─────→ どのbiomeをどこへ割り当てるか
      └─ settings ─────────→ 地形、洞窟、表面、既定block/fluid
                                │
                                ├─ density_function / noise
                                ├─ biome → carver / placed_feature
                                └─ structure_set → structure
```

- `dimension` は「どの環境設定とchunk generatorを組み合わせるか」を定義します。
- `dimension_type` は空、光、座標尺度、建築可能高度、ベッド等の環境・gameplay特性を定義します。地形のblock配置そのものは作りません。
- `worldgen/*` は地形、biome分布、洞窟、装飾、structureを構成するregistry群です。

たとえば26.2の標準world presetでは、Overworld相当のdimensionは次の関係です。

```json
{
  "type": "minecraft:overworld",
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

これは `dimension_type` の `minecraft:overworld`、biome source presetの `minecraft:overworld`、noise settingsの `minecraft:overworld` を参照しています。同じ末尾名でも別registryなので、互いを自動的に参照するわけではありません。

## 配置

1.20.6以前と1.21以降で、一般データフォルダ名は複数形から単数形へ変わりました。ただしここで扱う `dimension`、`dimension_type`、`worldgen` の綴り自体は単複で変わりません。

```text
data/<namespace>/dimension/<id>.json
data/<namespace>/dimension_type/<id>.json
data/<namespace>/worldgen/biome/<id>.json
data/<namespace>/worldgen/configured_carver/<id>.json
data/<namespace>/worldgen/configured_feature/<id>.json
...
```

`data/example/dimension/bright_caves.json` は `example:bright_caves` というdimension IDになります。`type` に `example:bright_caves_type` と書いた場合、参照先は `data/example/dimension_type/bright_caves_type.json` です。

1.16.0/1.16.1と1.16.2以降、また各境界のfolder一覧は同一ではありません。対象JARの `generated/reports/registries.json` に加え、現在のバージョンでは `generated/data/minecraft/`、旧バージョンでは `generated/reports/worldgen/minecraft/` または `generated/reports/minecraft/` の生成例で存在を確認します。

## 独自dimensionと既存Overworldの変更

### 独自dimension

独自namespaceの `dimension` と、必要なら独自 `dimension_type` を作る方法です。

```text
data/example/dimension/cavern.json
data/example/dimension_type/cavern.json
```

利点は、vanillaや他packとの衝突を避けやすく、既存Overworldを壊さず試せることです。移動は対象バージョンのdimension IDを受け付けるコマンドを使います。

独自terrainは、対象バージョンのvanilla `dimension_type` と目的が同じgeneratorの定義を基底にし、field単位で変更します。

### 既存Overworldの上書き

`minecraft` namespaceの `dimension`、`dimension_type`、または標準 `world_preset` を高優先度packで置き換える設計も可能ですが、次の違いがあります。

- `dimension_type` の変更は、既存chunkにも適用される環境・gameplay特性へ影響します。
- generator、biome source、noise settings、featureの変更は、原則として変更後に初めて生成するchunkへ現れます。生成済みchunkを作り直しません。
- `world_preset` は新規world作成時のdimension構成を決める入口です。既存worldの生成済みchunkを再生成する設定ではありません。
- `data/minecraft/dimension/overworld.json` はバージョンによってvanilla generated dataに実ファイルが出ない場合があります。ファイルが生成されないことと、custom packでdimension registry entryを定義できないことを同一視しないでください。
- `minecraft` namespace上書きは他packと同じIDを奪い合います。pack順序、world upgrade、削除時の復旧手順まで設計します。

通常は独自dimensionで試作し、既存Overworldを変える必要が明確な場合だけ `minecraft` namespace上書きを検討してください。

## 表示上の明るさとgameplay lightは別

「明るく見える」「light levelが上がる」「mobが湧かない」は別の要件です。

| 要素 | 主な役割 | block/sky light値そのものを作るか |
|---|---|---|
| `ambient_light` | dimension全体の描画上のambient light係数 | 作らない |
| `minecraft:visual/ambient_light_color`（26.1以降） | light level 0で適用されるambient lightの色と明るさ | 作らない |
| `minecraft:visual/sky_light_factor`（1.21.11以降） | sky lightの表示上の明るさ | 作らない |
| `minecraft:gameplay/sky_light_level`（1.21.11以降） | mob spawningやdaylight detector等が使う有効sky light | gameplay判定へ作用 |
| `monster_spawn_light_level` | monster spawnに許される総合light側の上限 | 光を作らずspawn条件だけ変える |
| `monster_spawn_block_light_limit` | monster spawnに許されるblock light側の上限 | 光を作らずspawn条件だけ変える |
| torch、lantern、`minecraft:light`等のblock | 実際のblock light | 作る |
| `has_skylight` | そのdimensionがskylight systemを持つか | 地下へ光源を追加しない |

したがって `ambient_light` を上げても、作物やblock light predicateの値を上げたり、mob spawnを自動で止めたりはしません。dimension全体の視認性を変える用途であり、洞窟だけを条件付きで明るくするfieldでもありません。

1.21.11以降はdimension、biome、timeline、weatherの順にEnvironment Attribute sourceが重なります。優先度は低い方から次の順です。

```text
dimension → biome → timeline → weather
```

biomeの `attributes` で視覚を変えることはできますが、地下にあるすべての洞窟が「洞窟biome」になるわけではありません。囲まれた暗所の判定とは別です。洞窟だけを確実に実際の光量で明るくするなら、光源blockを置く処理が必要です。

### `ambient_light` の扱い

`ambient_light` は1.21.11のEnvironment Attributes移行後も削除されていません。公式JAR generated dataでは次を確認できます。

| version | Overworld | Nether | End |
|---|---:|---:|---:|
| 1.20.5 / 1.21 / 1.21.5 | `0.0` | `0.1` | `0.0` |
| 1.21.11 | `0.0` | `0.1` | `0.25` |
| 26.2 | `0.0` | `0.1` | `0.25` |

これらはvanillaの採用値であって、custom値の見た目を保証する推奨値ではありません。clientの明るさ設定、skybox、lightmap algorithm、Night Vision、Environment Attributesも結果へ影響します。値域とcodecは対象バージョンで検証し、見た目は対象clientで比較してください。

26.1ではlightmap algorithmが変更され、`minecraft:visual/ambient_light_color`、`minecraft:visual/block_light_tint`、`minecraft:visual/night_vision_color`がEnvironment Attributeとして追加されました。1.21.11の `ambient_light` と26.1以降の `visual/ambient_light_color`を同じfieldとして置換しないでください。26.2 vanillaは両方をdimension type内に持ちます。

## `dimension` root

1.16.2以降のdata pack resourceで使う概念上の基本形は次の2 fieldです。1.16.0/1.16.1の初期experimental exportへ、このrootやinline参照可否をそのまま適用しません。

| field | 型 | 意味 |
|---|---|---|
| `type` | dimension type IDまたはinline定義 | 環境・gameplay特性 |
| `generator` | chunk generator object | chunkをどう作るか |

### generator discriminator

`generator.type` がrootの分岐を選びます。26.2のregistry reportで確認できる種類は次の3つです。

| `generator.type` | 主なfield | 用途 |
|---|---|---|
| `minecraft:noise` | `settings`, `biome_source` | 通常のnoise terrain |
| `minecraft:flat` | `settings` | layerで構成するsuperflat |
| `minecraft:debug` | 対象バージョンのcodecを確認 | block state確認用debug world |

26.2のnoise generatorでは、`settings` はnoise settings IDまたはinline定義、`biome_source` はbiome source objectです。古いバージョンの参照・inline許可は対象バージョンのcodecで確認します。

### biome source discriminator

26.2のregistry reportでは次を確認できます。

| `biome_source.type` | 主なfield | 意味 |
|---|---|---|
| `minecraft:fixed` | `biome` | 全域を1 biomeにする |
| `minecraft:checkerboard` | biome集合、scale系 | biomeを格子状に配置する |
| `minecraft:multi_noise` | `preset`またはparameters系 | climate parameterからbiomeを選ぶ |
| `minecraft:the_end` | 対象バージョンのcodecを確認 | End固有分布 |

`multi_noise` のpreset形と直接parameters形は同じobjectの別分岐です。両方を混ぜず、対象バージョンのvanilla例を選びます。biome sourceはbiomeを選びますが、terrainのstone/air形状はnoise settings側が決めます。

### flat generator

26.2のflat settingsで見られる主要fieldは次のとおりです。

| field | 型 | 意味 |
|---|---|---|
| `layers` | `{block, height}` のlist | 下から積むblock layer |
| `biome` | biome ID | flat worldのbiome |
| `lakes` | boolean | lake生成 |
| `features` | boolean | biome feature生成 |
| `structure_overrides` | structure setのID/list/tag相当 | 使用するstructure set |

許容されるholder形式と省略時の値はバージョンごとに確認してください。

## `dimension_type` の主要パラメータ

### 1.16〜1.18.2

1.16.2以降の初期data pack resourceでは、`ultrawarm`、`natural`、`piglin_safe`、`respawn_anchor_works`、`bed_works`、`has_raids`、`has_skylight`、`has_ceiling`、`coordinate_scale`、`ambient_light`、`logical_height`、`infiniburn`、`effects`とoptional `fixed_time`が中心です。意味の概要は次節の同名fieldを参照できますが、現在のバージョンのJSONをこの時代へコピーしてはいけません。1.16.0/1.16.1はこの列挙から完全rootを組み立てず、そのバージョンのexportとcodecを直接確認します。

- 1.16.0/1.16.1のexport形式と1.16.2のdata pack registry形式は同一ではありません。
- 1.18の高さ・terrain全面改訂では、dimension typeの建築範囲とnoise settingsの生成範囲を一緒に見直します。
- `monster_spawn_light_level` と `monster_spawn_block_light_limit` は1.19で追加されたため、それ以前のdimension typeへ先取りしません。
- 1.18.2の `infiniburn` 等、tag-only fieldは `#` を含むtag IDを要求します。

初期形式はexperimentalでバージョン間変動が特に大きいため、古いバージョンの完全rootを現行field一覧から逆算せず、そのバージョンのJAR data/exportを基底にします。

### 1.19〜1.21.5の代表形

1.20.5、1.21、1.21.5の公式JAR generated dataでは、主要root fieldは同じです。

| field | 型 | 意味と相互作用 |
|---|---|---|
| `ambient_light` | float | 描画上のambient light。実light levelではない |
| `bed_works` | boolean | falseのdimensionでbed使用時の挙動に関与 |
| `coordinate_scale` | double | dimension間座標変換の尺度。portalと`execute in`の座標解釈を確認 |
| `effects` | dimension effects ID | sky/fog等の大分類。1.21.11で削除 |
| `fixed_time` | long、optional | 時刻表現を固定。1.21.11で `has_fixed_time` とattributes/timelineへ分割 |
| `has_ceiling` | boolean | 論理上のceiling特性。blockの天井を生成しない |
| `has_raids` | boolean | raid可否に関与。1.21.11でattributeへ移行 |
| `has_skylight` | boolean | skylight systemの有無。洞窟へ光を追加しない |
| `height` | integer | dimensionの総高さ |
| `infiniburn` | block tag ID | 永続燃焼対象。対象blockを配置はしない |
| `logical_height` | integer | portal/chorus fruit等が扱う論理高さ。`height`以下にする |
| `min_y` | integer | dimension下端 |
| `monster_spawn_block_light_limit` | integer | monster spawnのblock light制限 |
| `monster_spawn_light_level` | integerまたはint provider | monster spawnのlight制限。乱数providerなら試行ごとに閾値が変わり得る |
| `natural` | boolean | 複数の「自然なdimension」挙動を束ねる旧field。1.21.11でattributeへ分解 |
| `piglin_safe` | boolean | piglin/hoglinの変化に関与。1.21.11でattributeへ移行 |
| `respawn_anchor_works` | boolean | respawn anchor使用挙動。1.21.11でattributeへ移行 |
| `ultrawarm` | boolean | 水、lava等のNether系挙動を束ねる旧field。1.21.11でattributesへ分解 |

`height`、`min_y` は対象バージョンの倍数・上下限制約を満たす必要があります。さらにnoise generatorを使う場合、`dimension_type` と `noise_settings.noise.{min_y,height}` の範囲を意図的に一致させます。片方だけ変更すると、生成範囲、建築可能範囲、空洞や切断面がずれることがあります。

`monster_spawn_light_level` と `monster_spawn_block_light_limit` はmonster spawnの異なるlight条件です。片方を「表示の明るさ」として使わず、両方を同じ対象バージョンのvanilla例から開始してください。

### 1.21.6

`cloud_height` がdimension typeのoptional numberとして追加されました。cloudの下端Yを指定する表示fieldで、地形高度やskylightを変更しません。

### 1.21.11以降

1.21.11では旧fieldの多くが `attributes` へ移り、dimension type rootは次の構造へ変わりました。

| field | 型 | 状態 |
|---|---|---|
| `attributes` | Environment Attribute IDから値/修飾objectへのmap | 1.21.11追加 |
| `timelines` | timeline ID、ID list、またはtag | 1.21.11追加 |
| `skybox` | `overworld` / `none` / `end` | 旧 `effects` の表示責務を分割 |
| `cardinal_light` | `default` / `nether` | 旧 `effects` のblock面照明方向を分割 |
| `has_fixed_time` | boolean | 旧numeric `fixed_time`の一部責務を置換 |
| `ambient_light` | float | 移行後もrootに残る |
| `coordinate_scale` | double | 継続 |
| `has_ceiling` | boolean | 継続 |
| `has_skylight` | boolean | 継続 |
| `height`, `min_y`, `logical_height` | integer | 継続 |
| `infiniburn` | block tag ID。26.2ではblock holder set | 継続。26.2で受理形を拡張 |
| `monster_spawn_*` | integer / int provider | 継続 |

主な移行は次のとおりです。旧booleanを同名のattribute valueへ機械置換できるとは限りません。

| 1.21.10以前 | 1.21.11 |
|---|---|
| `ultrawarm` | `minecraft:gameplay/water_evaporates`、`minecraft:gameplay/fast_lava`、`minecraft:visual/default_dripstone_particle`等 |
| `bed_works` | `minecraft:gameplay/bed_rule` |
| `respawn_anchor_works` | `minecraft:gameplay/respawn_anchor_works` |
| `cloud_height` | `minecraft:visual/cloud_height` |
| `piglin_safe` | `minecraft:gameplay/piglins_zombify` |
| `has_raids` | `minecraft:gameplay/can_start_raid` |
| `natural` | `minecraft:gameplay/nether_portal_spawns_piglin`、eyeblossom/creaking関連等 |
| `effects` | `skybox`、`cardinal_light`、visual attributes |
| `fixed_time` | `has_fixed_time`とtime-based attributes/timeline |

`attributes` の値は直接値なら `override` として扱われます。modifierを使う展開形は概念的に次です。

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

利用できるattribute ID、値型、modifier、補間可否、評価位置はattributeごとに異なります。別attributeの値型を流用しないでください。

`timelines` に指定したtimelineだけが、そのdimensionでattributeを時間変化させます。1.21.11のtimeline rootは主に次の形です。

| field | 型 | 意味 |
|---|---|---|
| `period_ticks` | integer、optional | 指定tick数でtrackを反復。省略時は反復しない。許容範囲は対象バージョンのcodecで確認 |
| `tracks` | attribute IDからtrackへのmap | attributeごとの時間変化 |
| `tracks.*.keyframes` | `{ticks, value}` の昇順list | その時点のmodifier引数またはoverride値 |
| `tracks.*.modifier` | modifier ID、optional | 省略時は `override` |
| `tracks.*.ease` | easing ID/object、optional | 補間可能なattributeのkeyframe間補間 |

同じtickへ最大2 keyframeを置く形は即時遷移に使われます。補間されるかどうかはattribute側の型に依存します。

### 26.1

dimension typeへ次が加わりました。

| field | 型 | 意味 |
|---|---|---|
| `default_clock` | world clock ID、optional | `/time`の既定clockとsleep/village siegeのtime marker対象 |
| `has_ender_dragon_fight` | boolean | そのdimensionでEnder Dragon fightを保持できるか |

さらにlightmap algorithm更新に合わせ、`minecraft:visual/ambient_light_color`、`minecraft:visual/block_light_tint`、`minecraft:visual/night_vision_color`が追加されました。これらは `attributes` mapのkeyであり、`dimension_type` root fieldではありません。

26.1ではtimelineに `clock` が必須となり、`time_markers` mapも追加されました。1.21.11のtimelineをコピーするだけでは不足します。

| field | 型 | 意味 |
|---|---|---|
| `clock` | world clock ID | trackとmarkerが参照するclock |
| `time_markers` | marker IDからtickまたはmarker objectへのmap、optional | `/time`やsleep/village siege等が参照する名前付き時刻 |

`world_clock/<id>.json` はclock registry entryです。26.2 vanillaのworld clock定義は空objectですが、それをtimelineやdimension typeの空object例として流用してはいけません。

### 26.2

`infiniburn` はtagだけでなく、block ID、ID list、tagを受け付けるholder set形式へ拡張されました。古いバージョンへID/list形を戻さないでください。

26.2のvanilla `minecraft:overworld` dimension typeで確認できるroot fieldは次です。

```text
ambient_light
attributes
coordinate_scale
default_clock
has_ceiling
has_ender_dragon_fight
has_skylight
height
infiniburn
logical_height
min_y
monster_spawn_block_light_limit
monster_spawn_light_level
timelines
```

これはvanilla Overworldが実際に使ったfield一覧であり、codecの全optional field一覧ではありません。Nether/Endには `has_fixed_time`、`skybox`、`cardinal_light` も現れます。

## worldgen registry family

26.2の主なfamilyとroot/discriminatorは次のとおりです。全subtypeの固有fieldは対象バージョンのvanilla dataとrelease noteを参照します。

| folder / registry | rootまたはdiscriminator | 役割 |
|---|---|---|
| `worldgen/biome` | 固定root。`type`なし | 気候、spawn、carver、placed feature、表示/attributes |
| `worldgen/configured_carver` | `type`, `config` | cave/canyonを既存terrainから削る |
| `worldgen/configured_feature` | `type`, `config` | tree、ore、lake等の生成内容 |
| `worldgen/placed_feature` | `feature`, `placement[]`; 各要素の `type` | configured featureをどこへ何回置くか |
| `worldgen/noise` | `firstOctave`, `amplitudes` | density/surface等が参照するnoise parameter |
| `worldgen/density_function` | number、ID参照、またはinline `type` | 座標からdensity値を作る式 |
| `worldgen/noise_settings` | 固定root。内部のdensity/surface ruleが `type` dispatch | terrain形状、block/fluid、surface |
| `worldgen/structure` | root `type` | structureの開始条件とtype固有設定 |
| `worldgen/structure_set` | `structures[]`, `placement.type` | structure候補とworld内配置 |
| `worldgen/processor_list` | `processors[].processor_type` | template block/entityの置換・加工 |
| `worldgen/template_pool` | `elements[].element.element_type` | jigsaw pieceの重み付きpool |
| `worldgen/world_preset` | `dimensions` map | 新規worldのdimension構成 |
| `worldgen/flat_level_generator_preset` | `display`, `settings` | world作成画面用flat preset |
| `worldgen/multi_noise_biome_source_parameter_list` | `preset`または対象バージョンのparameter root | multi-noise biome配置 |

### biome

26.2の代表的なroot fieldは次です。

| field | 意味 |
|---|---|
| `has_precipitation`, `temperature`, `downfall` | 気候 |
| `effects` | 26.2でもwater/foliage/grass系の一部が残る |
| `attributes` | 1.21.11以降のvisual/audio/gameplay environment attributes |
| `spawners`, `spawn_costs` | mob spawn tableとspawn cost |
| `carvers` | configured carver参照 |
| `features` | generation step順のplaced feature list |

`features` は単なる順不同listではありません。外側listのindexがgeneration stepを表し、別biome間で同じplaced featureを異なる順序にするとfeature order cycleを起こす場合があります。vanilla biomeのstep数と配置を基底にします。

noise caveはnoise settingsが作り、configured carverのcave/canyonとは別経路です。

### configured feature と placed feature

次の2段階を分けます。

```text
configured_feature
└─ 何を生成するか

placed_feature
├─ feature ─→ configured_feature
└─ placement[]
   └─ 何回、どの高さ、どの範囲、どの条件で置くか
```

configured featureはroot `type` が `config` のcodecを選びます。placed featureの各placement modifierも `type` で分岐します。同じ `count`、`height` のようなfield名でも、選んだsubtypeが違えば型も違います。

26.2ではconfigured featureに `minecraft:sequence`、`minecraft:template`、`minecraft:weighted_random_selector`が追加され、`pointed_dripstone` / `dripstone_cluster` は `speleothem` / `speleothem_cluster`へrenameされました。26.1以前のIDと混ぜません。

### noise settings、density function、noise

noise settingsの主要な責務は次です。

| field group | 役割 |
|---|---|
| `noise.{min_y,height,size_horizontal,size_vertical}` | terrain sampling範囲とcell寸法 |
| `default_block`, `default_fluid` | terrainの既定block/fluid |
| `sea_level` | worldgen上のsea level |
| `noise_router` | density functionをterrain/climate/aquifer等の入力へ接続 |
| `surface_rule` | density生成後の表面blockを置換 |
| `spawn_target` | world spawn候補のclimate条件 |
| `aquifers_enabled`, `ore_veins_enabled`, `legacy_random_source`等 | 対象バージョンに存在する生成switch |

density functionはnumber literal、別registry ID、またはinline objectとして現れます。inline objectの `type` が式のcodecを選びます。`minecraft:add`、`mul`、`noise`、`spline`等は引数構造が異なるため、共通の `{type, value}` 形を仮定しません。

`worldgen/noise` 自体は通常 `firstOctave` と `amplitudes` の固定rootであり、density functionの `minecraft:noise`とは別registry/別codecです。

1.21.9ではnoise settingsの `initial_density_without_jaggedness` が2D density functionの `preliminary_surface_level`へ置換されました。旧挙動を近似するため `minecraft:find_top_surface` density functionが追加されています。field名だけrenameして旧3D式をそのまま入れません。

26.2では `minecraft:interval_select` density functionが追加され、`minecraft:weird_scaled_sampler`が削除されました。

### structure系

- `structure` はroot `type` が `jigsaw`、`stronghold`、`shipwreck`等の固有codecを選びます。共通fieldにはbiome集合、generation step、terrain adaptation、spawn override等があります。
- `structure_set` はstructure候補とweightを持ち、`placement.type` が `random_spread` または `concentric_rings`等の配置codecを選びます。
- `template_pool` はjigsaw pieceとweightを持ちます。各elementは `element_type` で分岐します。
- `processor_list` はtemplateを実worldへ置くときの加工列です。各processorは `processor_type`、rule内のpredicateは `predicate_type` で分岐します。

1.18.2正式リリースは `configured_structure_feature` と `structure_set` を使います。1.19では前者が `structure` へ移行するため、1.18.2と1.19以降のroot/folderを共有できません。

## バージョン境界

表にないpatch releaseでも意味変更はあり得ます。複数バージョン対応では対象範囲の全正式リリースで検証します。

| 境界 | dimension / worldgenの重要点 |
|---|---|
| 1.16 | experimentalなworld settings import/exportとしてcustom dimensionを導入。1.16.0/1.16.1の初期export schemaを1.16.2以降のdata pack resource形と同一視しない |
| 1.16.2 | pack format 6。`worldgen/biome`、configured carver/feature/structure feature/surface builder、noise settings、processor list、template pool等を追加。custom worldgenは引き続きexperimental |
| 1.18 | world heightとterrain/noise/biome generationを全面改訂。1.17以前のworldgen JSONを流用しない |
| 1.18.2 | `worldgen/density_function`、noise router、experimental `configured_structure_feature` / `structure_set`、registry tag対応。tag-only fieldの `#` を省略しない |
| 1.19 | `configured_structure_feature`を`structure`へ移行。custom dimensionの個別`seed`を削除しworld seedへ統一。`world_preset` / `flat_level_generator_preset`、dimension typeのmonster spawn light fields |
| 1.20.5 | worldgen number providerの余分な `value` wrapperを削除。provider使用箇所を再生成 |
| 1.21 | data folderを原則単数形へrename。worldgen folder名だけを見て他registryの旧複数形を残さない |
| 1.21.5 | `fallen_tree` featureと `attached_to_logs` tree decorator等を追加。既存rootの安定を全subtypeの安定と誤解しない |
| 1.21.6 | 全JSON strict parse。dimension typeに `cloud_height` |
| 1.21.9 | noise settingsの `initial_density_without_jaggedness` → `preliminary_surface_level`。`find_top_surface` / `invert` density function、jigsaw距離形を拡張 |
| 1.21.11 | dimension/biomeへ `attributes`、dimensionへ `timelines`。旧environment/gameplay fieldをattributesへ大移行。`effects`削除、`fixed_time`を分割 |
| 26.1 | world clock、dimension typeの `default_clock` / `has_ender_dragon_fight`。lightmap更新とvisual light attributes。world save layoutも大変更 |
| 26.2 | `infiniburn` holder set拡張。feature/surface rule/density functionの追加・rename・削除 |

各境界の間でも、追加されたblock、biome、feature、structure、tagによりvanilla dataの内容は変わります。「root fieldが同じ」だけでJSONを共有可能とは判定しません。

## 作成手順

### 1. 対象バージョンを固定する

```bash
python3 tools/datapack_harness.py resolve 1.21.11
```

`1.21`と`1.21.1`、`26.1`と`1.26.1`を混同しません。

### 2. 公式JARからreportとvanilla dataを生成する

```bash
python3 tools/datapack_harness.py reports 26.2 \
  --cache-dir .cache/minecraft \
  --output build/minecraft/26.2/generated \
  --java /path/to/java
```

確認対象はバージョンによって異なります。

```text
# 現在のバージョン
generated/reports/registries.json
generated/data/minecraft/dimension_type/
generated/data/minecraft/worldgen/

# 1.18.2
generated/reports/worldgen/minecraft/dimension_type/
generated/reports/worldgen/minecraft/worldgen/

# 1.19等の旧report layout
generated/reports/minecraft/dimension_type/
generated/reports/minecraft/worldgen/
```

`registries.json` は利用可能なregistry entry/discriminator IDを示しますが、各codecの全fieldを示すJSON Schemaではありません。いずれの生成例も、vanillaが実際に使った分岐だけです。

repositoryのcatalog helperを使える場合は、root fieldの差分把握に利用できます。

```bash
python3 tools/datapack_harness.py json-catalog 26.2 \
  --reports build/minecraft/26.2/generated
```

catalogは索引であり、Minecraftによるcodec検証の代わりではありません。

### 3. 同じdiscriminatorのvanilla例を選ぶ

たとえばoreを作るなら、別の `configured_feature.type` ではなく、対象バージョンのore featureを基底にします。jigsaw structureなら対象バージョンのjigsaw structureを選びます。

1. 目的と同じfolderを選ぶ
2. 同じ `type` / `processor_type` / `element_type` / `predicate_type` を選ぶ
3. 必須fieldを残して独自namespaceへコピーする
4. 参照先のID/tagも対象バージョンに存在することを確認する
5. 1 fieldずつ変更してreload/新規生成する

vanillaに同じ分岐例がない場合は、対象正式リリースのMojang release noteにあるfield listを使い、推測した空objectを作りません。

## 検証

worldgenの検証は `/reload` 成功だけでは完了しません。dimension/worldgen registryの変更はworldを閉じて開き直すかserverを再起動し、新規worldまたは未生成chunkで確認します。

1. 元worldとは別の空テストworldを作る
2. 起動時のexperimental警告と `latest.log` を確認する
3. 独自dimensionへ入り、dimension typeの環境特性を確認する
4. 新規worldでspawn周辺を生成する
5. 既存worldの未生成chunkへ移動して新generator結果を確認する
6. 生成済みchunkが変わらないことも確認する
7. dimension境界のportal/`execute in`座標、death/respawn、bed、anchorを確認する
8. clientを再接続し、serverも再起動してregistry同期と永続化を確認する
9. 旧world upgradeは必ずcopyで行い、downgradeしない

高さを変更した場合は、少なくとも次を調べます。

```text
[ ] dimension_typeのmin_y / height / logical_height
[ ] noise_settings.noiseのmin_y / height
[ ] density function内に埋め込まれたY境界
[ ] surface rule、carver、placed featureのheight provider
[ ] structureのstart heightとvertical restriction
[ ] spawn地点、portal、respawn位置
```

光を変更した場合は、同じ場所で次を別々に記録します。

```text
[ ] 画面上の見え方
[ ] block light
[ ] sky light
[ ] monster spawn
[ ] daylight detector等のgameplay判定
[ ] Night Vision、天候、時刻、biome境界
```

## 完全codecを推測しない

worldgenはdispatch codecが多重に入れ子になります。次の情報だけから「全field」を推測してはいけません。

- `registries.json` にtype IDがある
- vanilla fileが1例だけある
- Wikiに現在のバージョンのfield一覧がある
- 別バージョンで同名fieldが動いた
- `/reload` でその場のdimensionが見えた

対象バージョンの公式JAR generated data、Mojang release note、reload log、新規world/未生成chunkの実動作を組み合わせて判断します。Wikiは意味の確認と例の探索に使い、対象バージョンのcodec判断では公式JARを優先します。

## 出典

一次資料:

- [Mojang: Java Edition 1.16](https://www.minecraft.net/en-us/article/nether-update-java)
- [Mojang: Java Edition 1.16.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-16-2)
- [Mojang: Java Edition 1.18](https://feedback.minecraft.net/hc/en-us/articles/4415128577293-Minecraft-Java-Edition-1-18)
- [Mojang: Java Edition 1.18.2](https://feedback.minecraft.net/hc/en-us/articles/4531177623437-Minecraft-Java-Edition-1-18-2)
- [Mojang: Java Edition 1.19](https://feedback.minecraft.net/hc/en-us/articles/6731464524941-Minecraft-Java-Edition-1-19)
- [Mojang: Java Edition 1.20.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-5)
- [Mojang: Java Edition 1.21](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21)
- [Mojang: Java Edition 1.21.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-5)
- [Mojang: Java Edition 1.21.6](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-6)
- [Mojang: Java Edition 1.21.9](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-9)
- [Mojang: Java Edition 1.21.11](https://feedback.minecraft.net/hc/en-us/articles/41809981427213-Minecraft-Java-Edition-1-21-11-Mounts-of-Mayhem)
- [Mojang: Java Edition 26.1](https://feedback.minecraft.net/hc/en-us/articles/44551668333837-Minecraft-Java-Edition-26-1)
- [Mojang: Java Edition 26.2](https://feedback.minecraft.net/hc/en-us/articles/46690753273997-Minecraft-Java-Edition-26-2)
- 対象バージョンのserver JARの `generated/reports/registries.json` と、バージョン別のgenerated data/worldgen report

cross-check:

- [Minecraft Wiki: Tutorial: Adding a new dimension](https://minecraft.wiki/w/Tutorial:Adding_a_new_dimension)
- [Minecraft Wiki: Custom world generation](https://minecraft.wiki/w/Custom_world_generation)
- [Minecraft Wiki: Running the data generator](https://minecraft.wiki/w/Tutorial:Running_the_data_generator)
