# enchantment・variant・painting・jukebox のJSONパラメータ

この文書は Java Edition 1.13〜26.2 のエンチャントとvariant系データについて、定義対象、配置可能になるバージョン、主要field、`type` discriminator、自然スポーンとの関係、破壊的変更を整理します。

完全なcodec schemaをMarkdownへ複製する文書ではありません。対象正式リリースのserver JARが生成する `reports/registries.json` と `data/minecraft/` を正本とし、この文書の「必須/任意」はMojang公式field listと、そのバージョンのvanilla生成物で確認できた範囲を示します。

## データモデルと参照関係

エンチャントのデータモデルは次の3層に分かれます。

1. **item stackが持つ状態**: 「この剣には `minecraft:sharpness` がレベル3で付いている」というIDとレベル
2. **enchantment registryの定義**: 対応item、最大レベル、コスト、実際の効果
3. **tag/providerによる選択規則**: エンチャントテーブル、loot、村人取引、mob装備等で何を候補にするか

1.13〜1.20.4では主に1をNBTで変更でき、vanillaにない新しいエンチャントの効果をJSONで定義できません。1.20.5ではitem component化に加えて表示順用のenchantment tag `minecraft:tooltip_order`が追加されましたが、definitionとproviderはまだ固定です。2とproviderを含む選択規則がデータ駆動化された下限は1.21です。

variant系データは次の役割に分かれます。

- **visual variant**: entityやpaintingの見た目を選ぶregistry entry
- **spawn selection**: 自然スポーン位置でどのvariantを選ぶか
- **sound variant**: mobの行動ごとのsound eventを選ぶregistry entry
- **item component/entity component**: 生成済みの個体やitemがどのentryを参照するか

したがって「variantは見た目だけ」とは限りません。visual variant自体は描画資産を指定しますが、1.20.5のwolf variantは`biomes`、1.21.5以降のmob variantは`spawn_conditions`を持ち、自然スポーン時の選択にも使われます。一方、sound variantはvisual variantと独立して選択されます。

## バージョン境界

| 正式リリース | エンチャント/variant系の境界 |
|---|---|
| 1.13 | item NBTの旧`ench`を`Enchantments`へrenameし、数値enchantment IDをnamespaced IDへ移行 |
| 1.13〜1.20.4 | item NBTにbuilt-in enchantmentのIDとlevelを保存。データパックから新しいenchantment definitionは追加不可 |
| 1.20.5〜1.20.6 | item stackをstructured data componentsへ移行。enchantment表示順tag `minecraft:tooltip_order`とdata-driven `wolf_variant`を追加 |
| 1.21〜1.21.1 | `enchantment`、`enchantment_provider`、`painting_variant`、`jukebox_song`をデータ駆動化。data folderを単数形へrename |
| 1.21.2〜1.21.4 | entity/location effectの`minecraft:damage_item`を`minecraft:change_item_damage`へrename。paintingに任意の`author`、`title`を追加 |
| 1.21.5 | pig/cow/chicken/cat/frog variant、wolf sound variantをデータ駆動化。mob variantを共通`spawn_conditions`方式へ移行 |
| 1.21.6 | JSONをstrict parse。`minecraft:painting/variant` item componentのinline variantを禁止し、registry ID参照だけに制限 |
| 1.21.7〜1.21.8 | 新しいvanilla painting/song entryは増えるが、ここで扱うroot schemaの主要な破壊的変更はなし |
| 1.21.9 | `minecraft:explode` entity effectにblockごとのparticle候補`block_particles`を追加 |
| 1.21.10 | ここで扱うroot schemaの主要な破壊的変更はなし |
| 1.21.11 | `zombie_nautilus_variant`、`post_piercing_attack`、`apply_impulse`、`apply_exhaustion`、`exponent`等を追加 |
| 26.1 | cat/pig/cow/chicken sound variantを追加。wolf sound variantを`adult_sounds`/`baby_sounds` wrapperへ移行 |
| 26.2 | この系統のregistry ID集合は1.21.11/26.1を継承。effect条件内のentity predicateはcomponent-map形式へ移行し、未知keyを拒否 |

## 1.13〜1.20.6: itemに付与することと定義すること

### 1.13〜1.20.4

通常itemは`Enchantments`、enchanted bookは`StoredEnchantments`のlistを持ちます。

```snbt
{
  Enchantments: [
    {
      id: "minecraft:sharpness",
      lvl: 3s
    }
  ]
}
```

このNBTは既存enchantmentの参照とlevelを保存するだけです。`example:night_vision`のような未知IDを書いても、そのIDの効果をデータパックが定義したことにはなりません。独自効果が必要なら、advancement、predicate、function、scoreboard等で別の状態機械を実装します。

### 1.20.5〜1.20.6

item stackの自由形式NBTはstructured data componentsへ移行します。通常itemは`minecraft:enchantments`、enchanted bookは`minecraft:stored_enchantments`を使います。

```snbt
minecraft:diamond_sword[
  minecraft:enchantments={
    levels:{
      "minecraft:sharpness":3
    }
  }
]
```

この変更も「新しいenchantment definitionを作れる」という意味ではありません。独自definitionの下限は1.21です。

## 1.21以降: enchantment definition

配置:

```text
data/<namespace>/enchantment/<id>.json
```

ファイル `data/example/enchantment/cave_sight.json` はregistry ID `example:cave_sight`を定義します。1.21以降は単数形`enchantment/`です。

### root fields

| field | 型 | 必須/任意 | 意味 |
|---|---|---|---|
| `description` | text component | 必須 | tooltip等へ表示する名称 |
| `exclusive_set` | enchantment ID、ID list、または`#tag` | 任意、既定は空 | 同居不可のenchantment集合。どちらか一方が相手を指定すれば同居不可 |
| `supported_items` | item ID、ID list、または`#tag` | 必須 | このenchantmentを保持できるitem |
| `primary_items` | item ID、ID list、または`#tag` | 任意 | enchanting tableと取引装備で主候補になるitem。`supported_items`の部分集合でなければならない |
| `weight` | 1〜1024の整数 | 必須 | 候補内での相対的な出現しやすさ |
| `max_level` | 1〜255の整数 | 必須 | 最大level。最小levelは常に1 |
| `min_cost` | linear cost object | 必須 | enchanting cost範囲の下端 |
| `max_cost` | linear cost object | 必須 | enchanting cost範囲の上端 |
| `anvil_cost` | 0以上の整数 | 必須 | anvilで使う基本fee。実効値はlevel等の影響を受ける |
| `slots` | slot groupのlist | 必須 | effectが有効になる装備位置 |
| `effects` | effect component IDから値へのmap | 任意、既定は空map | 実際の挙動。`fortune`のようにこのkeyを持たないvanilla定義もある |

`slots`の1.21公式値は`any`、`hand`、`mainhand`、`offhand`、`armor`、`feet`、`legs`、`chest`、`head`、`body`です。後のバージョンでslot systemが増えても、新しい値を古いバージョンへ先取りしません。

`min_cost`と`max_cost`は次の同じ形です。

```json
{
  "base": 1,
  "per_level_above_first": 10
}
```

level `L`での値は`base + per_level_above_first * (L - 1)`です。

### rootの構造例

次は「どこへ何を書くか」を示す骨格です。効果のID、attribute、item tagは対象バージョンのregistryに存在するものへ置き換えます。

```json
{
  "description": {
    "text": "Cave Sight"
  },
  "supported_items": "#minecraft:enchantable/head_armor",
  "weight": 1,
  "max_level": 1,
  "min_cost": {
    "base": 1,
    "per_level_above_first": 0
  },
  "max_cost": {
    "base": 41,
    "per_level_above_first": 0
  },
  "anvil_cost": 4,
  "slots": [
    "head"
  ],
  "effects": {
    "minecraft:attributes": [
      {
        "id": "example:cave_sight",
        "attribute": "minecraft:player.submerged_mining_speed",
        "operation": "add_multiplied_total",
        "amount": 1.0
      }
    ]
  }
}
```

これは夜間視認性を変更する例ではありません。`attributes`に存在しない能力を名前から推測して作ることはできず、「画面を明るくする」効果componentも1.21の30種にはありません。

## effect component、effect type、condition

### objectの階層

`effects`直下のkeyは**effect component type**です。多くのcomponentは、`effect`と任意の`requirements`を持つentryのlistです。

```json
{
  "effects": {
    "minecraft:damage": [
      {
        "effect": {
          "type": "minecraft:add",
          "value": 1.0
        },
        "requirements": {
          "condition": "minecraft:entity_properties",
          "entity": "this",
          "predicate": {}
        }
      }
    ]
  }
}
```

ここには異なるdiscriminatorが2つあります。

- `effects`のkey `minecraft:damage`: いつ、何の値へ作用するかを決めるeffect component
- `effect.type`の`minecraft:add`: その値をどう変えるかを決めるvalue/entity/location effect type

`minecraft:attributes`は例外で、entryがattribute modifierそのものなので、entry内にdynamicな`type`を置きません。`crossbow_charge_time`等もlist wrapperでない特殊形です。同じ形だと推測せず、対象バージョンの同じcomponentを使うvanilla enchantmentを基底にします。

### requirements

`requirements`は任意のinline loot condition objectです。複数条件は`minecraft:all_of`や`minecraft:any_of`で1つのconditionへまとめます。

- predicate resourceへの参照ではなくinline objectにする
- componentごとに利用可能なloot context parameterが異なる
- damage contextでは`this`、`attacker`、`direct_attacker`、damage source等が使える
- item contextでは`tool`とenchantment level等が使える
- location contextでは`this`、origin、active状態等が使える
- hit-block contextではblock stateも使える

同じ`requirements`を別componentへコピーすると、存在しないcontext parameterのためloadまたは実行時に失敗し得ます。

26.2では、`minecraft:entity_properties`内のentity predicateもcomponent-map形式へ移行します。

```json
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "minecraft:entity_type": "minecraft:player",
    "minecraft:flags": {
      "is_on_ground": true
    }
  }
}
```

26.1以前の`"type": "minecraft:player"`や`"flags": {...}`を26.2へそのまま残さず、対象バージョンのcatalogのentity predicate keyへ変換します。

### level-based value

単なる数値は全levelで同じ定数です。levelで変化させる場合は`type`付きobjectを使います。

| 1.21 type | 主要field | 意味 |
|---|---|---|
| `minecraft:linear` | `base`, `per_level_above_first` | 一次式 |
| `minecraft:clamped` | `value`, `min`, `max` | 内側のlevel valueを範囲へ制限 |
| `minecraft:fraction` | `numerator`, `denominator` | 2つのlevel valueの比 |
| `minecraft:levels_squared` | `added` | `level² + added` |
| `minecraft:lookup` | `values`, `fallback` | `level - 1`をindexにlistから選び、範囲外はfallback |

1.21.11では`minecraft:exponent`が加わります。`base`と`power`はいずれもlevel-based valueです。26.2のregistry reportでもこの6種を確認できます。

### value effect type

| type | 主要field | 意味 |
|---|---|---|
| `minecraft:add` | `value` | 入力値へ加算 |
| `minecraft:all_of` | `effects` | 複数value effectを順番に適用 |
| `minecraft:multiply` | `factor` | 入力値へ乗算 |
| `minecraft:remove_binomial` | `chance` | 入力個数にbinomial判定を行い成功分を減算 |
| `minecraft:set` | `value` | 入力値を上書き |
| `minecraft:exponential` | 対象バージョンのcodecで確認 | 1.21.11/26.2 registryには存在するが、26.2 vanilla enchantmentに利用例がないためfieldを推測しない |

最後の`minecraft:exponential`はregistry IDの存在を確認できても、generated vanilla JSONだけではfield schemaを確認できない例です。公式JARのcodecまたは対象バージョンのserver reloadで確定します。

### entity/location effect type

entity effectはeventでentityへ作用します。location-based effectは装備時やblock座標をまたいだ移動時に有効/無効を更新します。多くのentity effectをlocation effectとしても利用でき、location専用の`minecraft:attribute`もあります。

| type | 主要field |
|---|---|
| `minecraft:all_of` | `effects` |
| `minecraft:apply_mob_effect` | `to_apply`, `min_duration`, `max_duration`, `min_amplifier`, `max_amplifier` |
| `minecraft:change_item_damage` | `amount` |
| `minecraft:damage_entity` | `damage_type`, `min_damage`, `max_damage` |
| `minecraft:explode` | `radius`, `damage_type?`, `immune_blocks?`, `knockback_multiplier?`, `offset?`, `create_fire`, `block_interaction`, particles、`sound`。1.21.9以降は`block_particles?` |
| `minecraft:ignite` | `duration` |
| `minecraft:play_sound` | `sound`, `volume`, `pitch` |
| `minecraft:replace_block` | `block_state`, `offset?`, `predicate?`, `trigger_game_event?` |
| `minecraft:replace_disk` | `block_state`, `radius`, `height`, `offset?`, `predicate?`, `trigger_game_event?` |
| `minecraft:run_function` | `function` |
| `minecraft:set_block_properties` | `properties`, `offset?`, `trigger_game_event?` |
| `minecraft:spawn_particles` | `particle`, horizontal/vertical position、horizontal/vertical velocity、`speed` |
| `minecraft:summon_entity` | `entity`, `join_team` |
| `minecraft:attribute` | location effect専用。`id`, `attribute`, `operation`, `amount` |
| `minecraft:apply_exhaustion` | 1.21.11以降。`amount`。playerにだけ実効 |
| `minecraft:apply_impulse` | 1.21.11以降。`direction`, `coordinate_scale`, `magnitude` |

1.21ではitem耐久を変えるtype名が`minecraft:damage_item`でした。1.21.2で`minecraft:change_item_damage`へrenameされ、負数による修復も扱えるようになりました。effect component keyの`minecraft:item_damage`とは別名である点に注意してください。

1.21.9以降の`explode.block_particles`はentry listです。各entryは0以上の整数`weight`と`particle`を持ち、任意の`scaling`と`speed`は省略時1.0です。これは爆発全体のparticle fieldとは別に、blockごとのparticle候補を重み付き選択します。

### 26.2 effect component typeの完全なID集合

以下は26.2 `registries.json`に露出した31 entryの完全一覧です。各componentの値のshapeまで完全という意味ではありません。

```text
minecraft:ammo_use
minecraft:armor_effectiveness
minecraft:attributes
minecraft:block_experience
minecraft:crossbow_charge_time
minecraft:crossbow_charging_sounds
minecraft:damage
minecraft:damage_immunity
minecraft:damage_protection
minecraft:equipment_drops
minecraft:fishing_luck_bonus
minecraft:fishing_time_reduction
minecraft:hit_block
minecraft:item_damage
minecraft:knockback
minecraft:location_changed
minecraft:mob_experience
minecraft:post_attack
minecraft:post_piercing_attack
minecraft:prevent_armor_change
minecraft:prevent_equipment_drop
minecraft:projectile_count
minecraft:projectile_piercing
minecraft:projectile_spawned
minecraft:projectile_spread
minecraft:repair_with_xp
minecraft:smash_damage_per_fallen_block
minecraft:tick
minecraft:trident_return_acceleration
minecraft:trident_sound
minecraft:trident_spin_attack_strength
```

`minecraft:crossbow_charging_sounds`や`minecraft:smash_damage_per_fallen_block`は、公式記事の節見出しと表記が異なる場合があります。JSONへ書くIDは上の正式リリースのregistry reportを採用します。

1.21の集合はここから`minecraft:post_piercing_attack`を除いた30種です。1.21.11でその1種と、entity/location effectの`apply_exhaustion`、`apply_impulse`、level valueの`exponent`が追加されました。

## enchantment tags

配置:

```text
data/<namespace>/tags/enchantment/<id>.json
```

tagはenchantment definitionを作りません。既に存在するentryを集合として分類します。

主な用途:

- `#minecraft:exclusive_set/*`: 同居不可の組
- `#minecraft:in_enchanting_table`: enchanting tableの候補
- `#minecraft:tradeable`: enchanted book取引の候補
- `#minecraft:on_traded_equipment`: 取引装備の候補
- `#minecraft:on_mob_spawn_equipment`: 自然スポーンmob装備の候補
- `#minecraft:on_random_loot`: chest等のrandom loot候補
- `#minecraft:curse`: curse表示とgrindstone挙動
- `#minecraft:tooltip_order`: tooltipの表示順
- `#minecraft:prevents_*`、`#minecraft:smelts_loot`: vanillaのhardcoded gameplay hookが参照する分類

独自enchantment JSONを追加しただけでは、全ての入手経路へ自動登録されません。必要なavailability tag、loot function、recipe、provider等へ明示的に加えます。

## enchantment provider

配置:

```text
data/<namespace>/enchantment_provider/<id>.json
```

providerは「候補から何を、何levelで選ぶか」を定義します。enchantmentそのものの効果は定義しません。

26.2までのprovider typeは3種です。

| `type` | 必須field | 意味 |
|---|---|---|
| `minecraft:single` | `enchantment`, `level` | 常に1種を返す。`level`はint provider |
| `minecraft:by_cost` | `enchantments`, `cost` | 指定costで候補集合からenchanting処理 |
| `minecraft:by_cost_with_difficulty` | `enchantments`, `min_cost`, `max_cost_span` | local difficultyを使ってcostを決める |

`enchantments`は単一ID、ID list、または`#enchantment_tag`です。

```json
{
  "type": "minecraft:single",
  "enchantment": "example:cave_sight",
  "level": 1
}
```

vanilla 1.21生成物で観測される実際のdiscriminatorは`minecraft:single`と`minecraft:by_cost_with_difficulty`です。公式説明の見出しにある`single_enchantment`等を、そのまま`type`値として書かないでください。正しいID集合は`registries.json`の`minecraft:enchantment_provider_type`です。

provider entryを追加しても、任意の時点で自動実行されるわけではありません。providerを読むvanilla経路から参照されるIDを使うか、そのproviderを受け取る別のJSON/loot処理から参照する必要があります。

## painting variant

### 1.21

配置:

```text
data/<namespace>/painting_variant/<id>.json
```

| field | 型 | 必須/任意 | 意味 |
|---|---|---|---|
| `width` | 1〜16の整数 | 必須 | block単位の横幅 |
| `height` | 1〜16の整数 | 必須 | block単位の高さ |
| `asset_id` | resource location | 必須 | paintings atlas内のsprite ID |

### 1.21.2以降

任意のtext component `author`と`title`が追加され、creative menu tooltipへ表示されます。

```json
{
  "width": 2,
  "height": 1,
  "asset_id": "example:cave_map",
  "title": {
    "text": "Cave Map"
  },
  "author": {
    "text": "Example"
  }
}
```

painting variantは自然スポーンするmobのvariantではありません。`#minecraft:placeable` painting variant tagはsurvivalでランダム配置される候補を制御します。個別itemから指定する場合は`minecraft:painting/variant` item componentを使います。

1.21.6以降、そのitem componentへpainting definitionをinline記述できません。`"example:cave_map"`のようなregistry ID参照を使います。

## jukebox song

`jukebox_song`はvariantではありませんが、1.21でpainting/enchantmentと同時に追加された参照型registryなのでここで扱います。

配置:

```text
data/<namespace>/jukebox_song/<id>.json
```

| field | 型 | 必須/任意 | 意味 |
|---|---|---|---|
| `sound_event` | sound event ID | 必須 | jukeboxがstream再生する音 |
| `description` | text component | 必須 | item tooltipに表示する曲名 |
| `length_in_seconds` | 正の数 | 必須 | 再生時間 |
| `comparator_output` | 0〜15の整数 | 必須 | 再生中のcomparator出力 |

```json
{
  "sound_event": "example:music_disc.cave",
  "description": {
    "text": "Cave"
  },
  "length_in_seconds": 120.0,
  "comparator_output": 8
}
```

songを定義しただけではitemになりません。item側の`minecraft:jukebox_playable` componentからsong IDを参照し、sound eventとresource pack側の音声資産も用意します。

## mob visual variant

### 1.20.5〜1.21.4: wolf variant旧形式

配置:

```text
data/<namespace>/wolf_variant/<id>.json
```

```json
{
  "wild_texture": "example:entity/wolf/cave",
  "tame_texture": "example:entity/wolf/cave_tame",
  "angry_texture": "example:entity/wolf/cave_angry",
  "biomes": "#example:cave_wolf_biomes"
}
```

生成済み1.20.5 vanilla JSONのfield名は`biomes`です。Mojang 1.20.5 release note本文に単数`biome`と記載される箇所がありますが、対象正式リリースのJARの生成物を優先してください。

texture IDはresource packの`assets/<namespace>/textures/<path>.png`へ解決されます。このJSONはデータパック側ですが、画像そのものはresource pack側です。

### 1.21.5以降: uniform variant selection

自然スポーン規則を持つvariantは、共通の`spawn_conditions` listを使います。

```json
{
  "asset_id": "example:entity/pig/cave",
  "model": "normal",
  "spawn_conditions": [
    {
      "condition": {
        "type": "minecraft:biome",
        "biomes": "#example:cave_biomes"
      },
      "priority": 1
    },
    {
      "priority": 0
    }
  ]
}
```

選択手順:

1. そのentity typeの全variantについて、spawn位置で全entryのconditionを評価する
2. 成功したentryの最大`priority`より低いentryを除く
3. 最大priorityで残った成功entryから一様ランダムに1つを選ぶ
4. 選ばれたentryを所有するvariantを選ぶ
5. 成功entryがなければ、そのentityのdefault variantを維持する

`condition`を省略したentryは常に成功します。fallbackを必ず候補にしたい場合に`priority: 0`の無条件entryを使えます。同じvariantに同priorityで複数の成功entryがある場合、そのvariantはentry数に応じて選択確率が上がります。

26.2 `minecraft:spawn_condition_type` registryで確認できるtype:

| `type` | 追加field | 意味 |
|---|---|---|
| `minecraft:biome` | `biomes` | biome ID、list、または`#tag` |
| `minecraft:moon_brightness` | `range` | moon brightnessのfloat range |
| `minecraft:structure` | `structures` | structure ID、list、または`#tag` |

正式リリースのJARのdiscriminatorは単数`minecraft:structure`です。古い記事や要約の`minecraft:structures`をそのまま使わないでください。

### family別schema

以下のfieldはMojang公式リリースノートと1.21.5/26.2 vanilla生成物で確認した主要形です。

| registry | 導入 | visual fields | selection | 備考 |
|---|---:|---|---|---|
| `wolf_variant` | 1.20.5 | 1.20.5〜1.21.4は`wild_texture`, `tame_texture`, `angry_texture`。1.21.5以降は`assets.{wild,tame,angry}` | 旧`biomes`、1.21.5以降`spawn_conditions` | 26.2 vanillaでは`baby_assets.{wild,tame,angry}`も観測 |
| `cat_variant` | 1.21.5でpack定義化 | `asset_id` | `spawn_conditions` | 26.2 vanillaでは`baby_asset_id`も観測 |
| `frog_variant` | 1.21.5でpack定義化 | `asset_id` | `spawn_conditions` | adult/baby別asset fieldは26.2 vanillaで未観測 |
| `pig_variant` | 1.21.5 | `model`, `asset_id` | `spawn_conditions` | 1.21.5の`model`: `normal`/`cold`。26.2 vanillaでは`baby_asset_id`も観測 |
| `chicken_variant` | 1.21.5 | `model`, `asset_id` | `spawn_conditions` | 1.21.5の`model`: `normal`/`cold`。26.2 vanillaでは`baby_asset_id`も観測 |
| `cow_variant` | 1.21.5 | `model`, `asset_id` | `spawn_conditions` | `model`: `normal`/`cold`/`warm`。26.2 vanillaでは`baby_asset_id`も観測 |
| `zombie_nautilus_variant` | 1.21.11 | `model`, `asset_id` | `spawn_conditions` | `model`: `normal`/`warm` |

各バージョンのgenerated vanilla entryでは、その行のvisual fieldsとselection fieldが全て存在します。この文書ではそれらを基底例から残すfieldとして扱います。`baby_asset_id`/`baby_assets`は別扱いで、次の注意に従います。

`baby_asset_id`と`baby_assets`は26.2 vanilla生成物で観測したfieldです。全custom entryでの必須/既定値を観測だけから断定せず、26.1/26.2の同family vanilla entryをそのまま基底にします。

visual variantのentryは、spawn後のAI、health、drop、attack等を丸ごと別mobへする定義ではありません。`model`は列挙済みのrenderer形を選び、`asset_id`は見た目を選びます。独自のAIや新しいmodel typeを任意の文字列で追加できるわけではありません。

## mob sound variant

sound variantはvisual variantと独立しています。1.21.5のwolfでは、公式にvisual texture variantと無関係なrandom sound variantとして説明されています。

### 1.21.5 wolf旧形式

```json
{
  "ambient_sound": "example:entity.wolf.ambient",
  "death_sound": "example:entity.wolf.death",
  "growl_sound": "example:entity.wolf.growl",
  "hurt_sound": "example:entity.wolf.hurt",
  "pant_sound": "example:entity.wolf.pant",
  "whine_sound": "example:entity.wolf.whine"
}
```

配置は`data/<namespace>/wolf_sound_variant/<id>.json`です。`spawn_conditions`はありません。

### 26.1以降のwrapper

wolfのflatなsound fieldsは`adult_sounds`へ移され、同じfamilyの`baby_sounds`が追加されました。

```json
{
  "adult_sounds": {
    "ambient_sound": "example:entity.wolf.ambient",
    "death_sound": "example:entity.wolf.death",
    "growl_sound": "example:entity.wolf.growl",
    "hurt_sound": "example:entity.wolf.hurt",
    "pant_sound": "example:entity.wolf.pant",
    "step_sound": "example:entity.wolf.step",
    "whine_sound": "example:entity.wolf.whine"
  },
  "baby_sounds": {
    "ambient_sound": "example:entity.baby_wolf.ambient",
    "death_sound": "example:entity.baby_wolf.death",
    "growl_sound": "example:entity.baby_wolf.growl",
    "hurt_sound": "example:entity.baby_wolf.hurt",
    "pant_sound": "example:entity.baby_wolf.pant",
    "step_sound": "example:entity.baby_wolf.step",
    "whine_sound": "example:entity.baby_wolf.whine"
  }
}
```

26.1で追加されたfamily:

| registry | 26.1/26.2のshape | sound set内のfield |
|---|---|---|
| `wolf_sound_variant` | `adult_sounds`, `baby_sounds` | `ambient_sound`, `death_sound`, `growl_sound`, `hurt_sound`, `pant_sound`, `step_sound`, `whine_sound` |
| `cat_sound_variant` | `adult_sounds`, `baby_sounds` | `ambient_sound`, `stray_ambient_sound`, `hiss_sound`, `hurt_sound`, `death_sound`, `eat_sound`, `beg_for_food_sound`, `purr_sound`, `purreow_sound` |
| `pig_sound_variant` | `adult_sounds`, `baby_sounds` | `ambient_sound`, `hurt_sound`, `death_sound`, `step_sound`, `eat_sound` |
| `chicken_sound_variant` | `adult_sounds`, `baby_sounds` | `ambient_sound`, `hurt_sound`, `death_sound`, `step_sound` |
| `cow_sound_variant` | flat object | `ambient_sound`, `hurt_sound`, `death_sound`, `step_sound` |

26.2 generated vanillaでは、各entryに表の全sound fieldが存在します。cowは26.2 vanillaでもwrapperなしのflat objectであり、他familyから`adult_sounds`/`baby_sounds`をコピーしません。

sound variant JSONはsound eventを参照するだけです。実際の音声file、`sounds.json`、resource pack側の配布が別途必要です。

## 実装時の判断例

### 「洞窟にspawnしたpigだけ別texture」

`pig_variant`へ`minecraft:biome`の`spawn_conditions`を書きます。これは自然スポーン時のvariant選択に関係しますが、既に存在するpig全てをtickごとに自動再判定する規則ではありません。

### 「wolfの鳴き声だけ変える」

`wolf_sound_variant`を使います。texture用`wolf_variant`とは別registryです。26.1以降はadult/baby wrapperを使います。

### 「新しいpaintingを追加」

`painting_variant`とresource packのpainting spriteを用意します。ランダム設置候補へ入れるならpainting variant tagも更新します。1.21.6以降、item componentにはinline objectでなくregistry IDを書きます。

### 「Night Visionのような独自enchantment」

1.21以降でも、effect component registryに「night visionを任意に追加する」componentがあるとは限りません。`apply_mob_effect`を発火できるcomponent/contextへ組み合わせるか、functionを呼べるeventへ`run_function`を置く設計を検討します。装備中ずっと維持する場合は`tick`や`location_changed`の発火条件、解除時cleanup、複数装備、死亡・dimension移動を実ゲームで検査します。

1.20.6以前はcustom enchantment definition自体がないため、itemのcustom data、advancement/predicate/function等で独自状態を別実装します。

## observed coverage

このrepositoryで生成・集計したcatalogの保証:

- `registry_ids`: `registries.json`に露出したentry IDについて完全
- `observed_shapes`: generated vanilla JSONに実際に現れたpathと型だけ。codecの全field、全default、全union分岐ではない

| version | effect component type | provider type | variant registry | vanilla JSONで観測した主なentry数 |
|---|---:|---:|---:|---|
| 1.20.5 | 0 | 0 | 1 | wolf variant 9 |
| 1.21 | 30 | 3 | 2 | enchantment 42、provider 7、painting 50、jukebox song 19、wolf variant 9 |
| 1.21.5 | 30 | 3 | 8 | enchantment 42、provider 7、painting 50、song 19、visual mob variant 32、wolf sound 7 |
| 1.21.11 | 31 | 3 | 9 | catalogでenchantment 43、zombie nautilusを含むvariant registryを確認 |
| 26.2 | 31 | 3 | 13 | enchantment 43、provider 7、painting 51、song 22、visual mob variant 34、sound variant 16 |

1.21.5の「visual mob variant 32」はwolf 9、cat 11、frog 3、pig 3、chicken 3、cow 3の合計です。26.2の「visual mob variant 34」はそれらにzombie nautilus 2を加えたものです。これはvanilla entry数であり、custom packで作成できる数の上限ではありません。

## 対象バージョンで完全一覧と同型例を得る

1. 対象正式リリースを完全一致で取得する
2. [`../validation.md`](../validation.md)の手順でdata generatorを実行する
3. `generated/reports/registries.json`で次のregistryを調べる

```text
minecraft:enchantment_effect_component_type
minecraft:enchantment_entity_effect_type
minecraft:enchantment_location_based_effect_type
minecraft:enchantment_level_based_value_type
minecraft:enchantment_value_effect_type
minecraft:enchantment_provider_type
minecraft:spawn_condition_type
```

4. `generated/data/minecraft/enchantment/`等から、使いたいcomponent/type/familyと同じvanilla fileを選ぶ
5. 必須fieldを残したままIDと値だけ変更する
6. `jq empty`でJSON文法を検査し、対象バージョンのserverで`/reload`してcodec errorを確認する
7. effectは実際のevent、variantは新規spawn、painting/songはitemからの参照まで発火testする

vanillaに利用例がないregistry IDは、IDの存在だけからfieldを作りません。公式release noteのfield list、公式JARのcodec、reload errorを併用します。

## 出典

一次資料:

- [Mojang: Update Aquatic is out on Java](https://www.minecraft.net/en-us/article/update-aquatic-out-java)
- [Mojang: Java Edition 1.20.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-5)
- [Mojang: Java Edition 1.21](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21)
- [Mojang: Java Edition 1.21.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-2)
- [Mojang: Java Edition 1.21.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-5)
- [Mojang: Java Edition 1.21.6](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-6)
- [Mojang: Java Edition 1.21.9](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-9)
- [Mojang: Snapshot 25w16a (`painting/variant` inline禁止)](https://www.minecraft.net/en-us/article/minecraft-snapshot-25w16a)
- [Mojang: Java Edition 1.21.11](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-11)
- [Mojang: Java Edition 26.1](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-1)
- [Mojang: Java Edition 26.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-2)
- 対象正式リリースのserver JARの`generated/reports/registries.json`と`generated/data/minecraft/`

cross-check:

- [Minecraft Wiki: Enchantment definition](https://minecraft.wiki/w/Enchantment_definition)
- [Minecraft Wiki: Enchantment provider](https://minecraft.wiki/w/Enchantment_provider)
- [Minecraft Wiki: Enchantment tag](https://minecraft.wiki/w/Enchantment_tag_(Java_Edition))
- [Minecraft Wiki: Mob variant definitions](https://minecraft.wiki/w/Mob_variant_definitions)
- [Minecraft Wiki: Painting variant definition](https://minecraft.wiki/w/Painting_variant_definition)
- [Minecraft Wiki: Jukebox song definition](https://minecraft.wiki/w/Jukebox_song_definition)
