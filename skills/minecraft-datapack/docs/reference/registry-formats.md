# データ駆動registryの書式

この文書は、26.2の`reports/datapack.json`で`elements: true`となるregistryのうち、専用のJSON resourceを持つ型を説明します。配置は1.21以降の単数形ディレクトリです。1.20.6以前は対象バージョンのvanilla dataで複数形を確認します。

`stable: false`は「正式リリースに存在しない」という意味ではありません。worldごとのregistryとして読み込まれ、変更がworld互換性へ影響し得ることを示します。

## 共通規則

```text
data/<namespace>/<registry-path>/<resource-path>.json
```

ファイル`data/example/instrument/alert.json`のregistry IDは`example:alert`です。root JSONに`id`を重ねて書く型と、path自体をIDにする型を混同しません。

`type`を持つresourceはdispatch codecです。

1. `type`のIDがserializer／type registryに存在することを確認する
2. 同じ`type`の26.2 vanilla JSONを選ぶ
3. type固有fieldを表に従って変更する
4. 参照するID、tag、componentを確認する
5. reload logでunknown field、missing field、range errorを確認する

## 基本registry

### `banner_pattern`

```json
{
  "asset_id": "example:star",
  "translation_key": "block.example.banner.star"
}
```

| field | 型 | 説明 |
|---|---|---|
| `asset_id` | ID | resource pack側のbanner pattern asset |
| `translation_key` | string | 表示名の翻訳key |

利用可能なpatternをloom itemで選べるようにする場合は、対応するbanner pattern tagや`provides_banner_patterns` item componentも別に設定します。

### `chat_type`

```json
{
  "chat": {
    "translation_key": "chat.type.text",
    "parameters": ["sender", "content"]
  },
  "narration": {
    "translation_key": "chat.type.text.narrate",
    "parameters": ["sender", "content"]
  }
}
```

`chat`と`narration`はmessage decorationです。

| field | 型 | 説明 |
|---|---|---|
| `translation_key` | string | `%s`placeholderを持つ翻訳key |
| `parameters` | string array | `sender`、`target`、`content`等を翻訳引数へ渡す順序 |
| `style` | text style object | 任意の色、font、装飾 |

### `damage_type`

```json
{
  "message_id": "example",
  "scaling": "never",
  "exhaustion": 0.1
}
```

| field | 必須性 | 型 | 説明 |
|---|---|---|---|
| `message_id` | 必須 | string | death message keyのsuffix |
| `scaling` | 必須 | enum | difficultyによるdamage scale。`never`、`when_caused_by_living_non_player`、`always`等 |
| `exhaustion` | 必須 | 非負float | playerへ加えるfood exhaustion |
| `effects` | 任意 | enum | hurt effect／soundの分類 |
| `death_message_type` | 任意 | enum | death messageの組み立て方 |

armor bypass、fire、projectile等の性質はdamage type JSONのbooleanではなく`tags/damage_type/`で分類します。

### `instrument`

```json
{
  "sound_event": "example:alert",
  "use_duration": 7.0,
  "range": 256.0,
  "description": {
    "translate": "instrument.example.alert"
  }
}
```

| field | 型 | 説明 |
|---|---|---|
| `sound_event` | sound event IDまたはinline sound event | 使用時のsound |
| `use_duration` | 正のfloat、seconds | item使用時間 |
| `range` | 非負float、blocks | soundの可聴距離 |
| `description` | text component | tooltip用の説明 |

### `jukebox_song`

```json
{
  "sound_event": "example:music_disc.alert",
  "description": {
    "translate": "jukebox_song.example.alert"
  },
  "length_in_seconds": 120.0,
  "comparator_output": 10
}
```

| field | 型 | 説明 |
|---|---|---|
| `sound_event` | sound event IDまたはinline sound event | 再生するsound |
| `description` | text component | song名 |
| `length_in_seconds` | 正のfloat | 再生時間とjukebox状態に使う長さ |
| `comparator_output` | 0〜15のinteger | jukeboxから出るcomparator signal |

itemから使うには`minecraft:jukebox_playable` componentでsong IDを参照します。

### `painting_variant`

```json
{
  "asset_id": "example:landscape",
  "width": 2,
  "height": 1,
  "title": {
    "text": "Landscape"
  },
  "author": {
    "text": "Example"
  }
}
```

| field | 型 | 説明 |
|---|---|---|
| `asset_id` | ID | resource pack側のpainting asset |
| `width` | 正のinteger | block単位の横幅 |
| `height` | 正のinteger | block単位の縦幅 |
| `title` | text component | 任意の作品名 |
| `author` | text component | 任意の作者名 |

item componentからinline variantを使えるかはバージョン境界があります。1.21.6以降はregistry IDを参照します。

### `trim_material`

```json
{
  "asset_name": "amethyst",
  "description": {
    "text": "Amethyst",
    "color": "#9a5cc6"
  },
  "override_armor_assets": {
    "minecraft:iron": "amethyst_darker"
  }
}
```

| field | 型 | 説明 |
|---|---|---|
| `asset_name` | string | armor trim textureのasset suffix |
| `description` | text component | material名 |
| `override_armor_assets` | map | armor material IDごとのasset上書き |

### `trim_pattern`

```json
{
  "asset_id": "example:bolt",
  "description": {
    "text": "Bolt"
  },
  "decal": false
}
```

| field | 型 | 説明 |
|---|---|---|
| `asset_id` | ID | trim pattern asset |
| `description` | text component | pattern名 |
| `decal` | boolean | armor base色を覆うdecalとして描画するか |

## entity variant

### 共通spawn condition

多くのvariantは次の配列を持ちます。

```json
{
  "spawn_conditions": [
    {
      "priority": 1,
      "condition": {
        "type": "minecraft:biome",
        "biomes": "#minecraft:spawns_cold_variant_farm_animals"
      }
    }
  ]
}
```

| field | 必須性 | 型 | 説明 |
|---|---|---|---|
| `priority` | 必須 | integer | 複数conditionが一致した場合の優先度 |
| `condition` | 任意 | spawn condition object | biome、structure、moon brightness等のtype別条件。省略はfallback |

同じpriorityの複数variantが一致した場合の選択へ重要な状態を依存させません。

### `cat_variant`

| field | 必須性 | 型 | 説明 |
|---|---|---|---|
| `asset_id` | 必須 | ID | texture asset。`assets/<namespace>/textures/<path>.png`へ解決 |
| `spawn_conditions` | 必須 | array | 共通spawn condition |

### `pig_variant`

配置は`data/<namespace>/pig_variant/<id>.json`です。`pig_variants`という
複数形folderはありません。

| field | 必須性 | 型 | 説明 |
|---|---|---|---|
| `model` | 必須 | enum | `normal`または`cold` |
| `asset_id` | 必須 | ID | texture asset。`assets/<namespace>/textures/<path>.png`へ解決 |
| `spawn_conditions` | 必須 | array | 共通spawn condition |

### `cow_variant`

| field | 必須性 | 型 | 説明 |
|---|---|---|---|
| `model` | 必須 | enum | `normal`、`cold`、`warm`のいずれか |
| `asset_id` | 必須 | ID | texture asset。`assets/<namespace>/textures/<path>.png`へ解決 |
| `spawn_conditions` | 必須 | array | 共通spawn condition |

### `chicken_variant`

| field | 必須性 | 型 | 説明 |
|---|---|---|---|
| `model` | 必須 | enum | `normal`または`cold` |
| `asset_id` | 必須 | ID | texture asset。`assets/<namespace>/textures/<path>.png`へ解決 |
| `spawn_conditions` | 必須 | array | 共通spawn condition |

### `frog_variant`

| field | 必須性 | 型 | 説明 |
|---|---|---|---|
| `asset_id` | 必須 | ID | frog texture asset |
| `spawn_conditions` | 必須 | array | 共通spawn condition |

### `wolf_variant`

```json
{
  "assets": {
    "wild": "example:entity/wolf/wild",
    "tame": "example:entity/wolf/tame",
    "angry": "example:entity/wolf/angry"
  },
  "spawn_conditions": []
}
```

`assets`は`wild`、`tame`、`angry`の各asset IDを持ちます。
`spawn_conditions`は共通形式です。1.20.5の初期形式では
`wild_texture`、`tame_texture`、`angry_texture`と`biome`をrootに置き、
1.21.5でこの形式へ移行しました。

| field | 必須性 | 型 | 説明 |
|---|---|---|---|
| `assets` | 必須 | object | `wild`、`tame`、`angry`のasset ID |
| `spawn_conditions` | 必須 | array | 共通spawn condition |

### spawn condition type

1.21.5で定義されたtype固有field:

| `type` | field | 型と意味 |
|---|---|---|
| `minecraft:biome` | `biomes` | biome ID、list、または`#`付きbiome tag |
| `minecraft:moon_brightness` | `range` | float、または`min`／`max`を持つfloat range |
| `minecraft:structures` | `structures` | structure ID、list、または`#`付きstructure tag |

未知のtypeを例から推測しません。`priority`が最大の候補群から1件が選ばれ、
`condition`省略は常に一致するfallbackです。

### `zombie_nautilus_variant`

| field | 型 | 説明 |
|---|---|---|
| `asset_id` | ID | texture asset |
| `model` | model variant | modelの分類。variantで必要な場合に指定 |
| `spawn_conditions` | array | 共通spawn condition |

### variantをentity／itemへ指定する

variant registryを定義しただけでは既存entityのvariantを置換しません。spawn condition、entity component、item componentのいずれがconsumerかを確認します。26.2ではentity predicateもcomponent-map化されているため、variant IDの判定は [`components-and-predicates.md`](components-and-predicates.md) を使います。

## sound variant

26.1以降の`cat_sound_variant`、`pig_sound_variant`、`chicken_sound_variant`と、1.21.5以降の`wolf_sound_variant`は、通常`adult_sounds`と`baby_sounds`を持ちます。

```json
{
  "adult_sounds": {
    "ambient_sound": "example:entity.example.ambient",
    "hurt_sound": "example:entity.example.hurt",
    "death_sound": "example:entity.example.death",
    "step_sound": "example:entity.example.step"
  },
  "baby_sounds": {
    "ambient_sound": "example:entity.example_baby.ambient",
    "hurt_sound": "example:entity.example_baby.hurt",
    "death_sound": "example:entity.example_baby.death",
    "step_sound": "example:entity.example_baby.step"
  }
}
```

speciesごとのfield:

| registry | sound set内のfield |
|---|---|
| `cat_sound_variant` | `ambient_sound`, `stray_ambient_sound`, `hiss_sound`, `hurt_sound`, `death_sound`, `eat_sound`, `beg_for_food_sound`, `purr_sound`, `purreow_sound` |
| `pig_sound_variant` | `ambient_sound`, `hurt_sound`, `death_sound`, `step_sound`, `eat_sound` |
| `chicken_sound_variant` | `ambient_sound`, `hurt_sound`, `death_sound`, `step_sound` |
| `wolf_sound_variant` | `ambient_sound`, `hurt_sound`, `death_sound`, `growl_sound`, `pant_sound`, `whine_sound` |

26.2の`cow_sound_variant`はwrapperを持たず、rootに`ambient_sound`、`hurt_sound`、`death_sound`、`step_sound`を置きます。

各値はsound event IDまたは対象codecが許すinline sound eventです。resource pack側の`sounds.json`だけを追加してregistry entryを定義したことにはなりません。

## `enchantment`

```json
{
  "description": {
    "text": "Example"
  },
  "supported_items": "#example:enchantable/example",
  "primary_items": "#example:enchantable/example_primary",
  "weight": 5,
  "max_level": 3,
  "min_cost": {
    "base": 5,
    "per_level_above_first": 8
  },
  "max_cost": {
    "base": 20,
    "per_level_above_first": 8
  },
  "anvil_cost": 2,
  "slots": ["mainhand"],
  "effects": {}
}
```

| field | 必須性 | 型 | 説明 |
|---|---|---|---|
| `description` | 必須 | text component | enchantment名 |
| `supported_items` | 必須 | item ID／list／tag | enchantmentを保持できるitem |
| `primary_items` | 任意 | item ID／list／tag | enchanting table等で主対象となるitem。`supported_items`の部分集合 |
| `weight` | 必須 | 正のinteger | random選択weight |
| `max_level` | 必須 | 正のinteger | 最大level |
| `min_cost` | 必須 | level-based value | 各levelの最小enchanting cost |
| `max_cost` | 必須 | level-based value | 各levelの最大enchanting cost |
| `anvil_cost` | 必須 | 非負integer | anvil計算用cost |
| `slots` | 必須 | slot group array | effectを適用する装備slot |
| `effects` | 必須 | component map | enchantment effect component IDから値へのmap |
| `exclusive_set` | 任意 | enchantment ID／list／tag | 同時に付けられないenchantment |

level-based valueの主な`type`:

| type | 主なfield | 説明 |
|---|---|---|
| `minecraft:linear` | `base`, `per_level_above_first` | levelごとの線形値 |
| `minecraft:levels_squared` | `added` | level平方を使う値 |
| `minecraft:fraction` | `numerator`, `denominator` | 2つのlevel-based valueの比 |
| `minecraft:clamped` | `value`, `min`, `max` | 値を範囲へ制限 |
| `minecraft:lookup` | `values`, `fallback` | levelをindexとして選択 |
| `minecraft:exponent` | `base`, `power` | level-based valueのべき乗 |

26.2のeffect component IDには、`attributes`、`damage`、`damage_protection`、`post_attack`、`location_changed`、`tick`、`run_function`相当のentity effect等があります。各componentの値はさらにeffect typeで分岐します。利用可能な完全一覧は次のregistryを正本にします。

```text
minecraft:enchantment_effect_component_type
minecraft:enchantment_entity_effect_type
minecraft:enchantment_location_based_effect_type
minecraft:enchantment_value_effect_type
minecraft:enchantment_level_based_value_type
```

effectごとの条件はloot conditionと同系統ですが、利用可能なcontext parameterが異なります。

## `enchantment_provider`

| type | field | 説明 |
|---|---|---|
| `minecraft:single` | `enchantment`, `level` | 1種類を指定levelで付与 |
| `minecraft:by_cost` | `enchantments`, `cost`またはcost範囲 | costに基づいて候補から選択 |
| `minecraft:by_cost_with_difficulty` | `enchantments`, cost関連field | local difficultyを加味して選択 |

26.2のvanilla dataではcostが`min_cost`、`max_cost_span`等へ分かれるproviderがあります。同じ`type`のvanilla JSONを基底にします。

## `dialog`

dialogは1.21.6以降です。

```json
{
  "type": "minecraft:notice",
  "title": {
    "text": "Notice"
  },
  "body": {
    "type": "minecraft:plain_message",
    "contents": {
      "text": "Message"
    }
  }
}
```

26.2のdialog type:

| type | 主な目的・field |
|---|---|
| `minecraft:notice` | 通知。`title`、`body`、終了action |
| `minecraft:confirmation` | 確認。yes/no action |
| `minecraft:dialog_list` | 別dialogの一覧。`dialogs`、`columns`、`button_width` |
| `minecraft:multi_action` | 複数action button |
| `minecraft:server_links` | server links表示 |

共通またはtype間で再利用されるfield:

| field | 型 | 説明 |
|---|---|---|
| `type` | dialog type ID | root codecを選択 |
| `title` | text component | 内部title |
| `external_title` | text component | dialogを参照するbutton等の外部表示名 |
| `body` | body objectまたはlist | `plain_message`、`item`等 |
| `exit_action` | action object | 閉じるbuttonのlabel、width、実行action |
| `dialogs` | dialog ID／list／tag | `dialog_list`に表示するentry |
| `columns` | 正のinteger | button列数 |
| `button_width` | 正のinteger | button幅 |

26.2のbody typeは`minecraft:plain_message`と`minecraft:item`です。action typeは`run_command`、`suggest_command`、`show_dialog`、`open_url`、`copy_to_clipboard`、`custom`等です。client actionはsecurityとUIの影響があるため、対象typeの公式vanilla例を最小化します。

## `trial_spawner`

```json
{
  "spawn_potentials": [
    {
      "weight": 1,
      "data": {
        "entity": {
          "id": "minecraft:breeze"
        }
      }
    }
  ],
  "simultaneous_mobs": 1.0,
  "simultaneous_mobs_added_per_player": 0.5,
  "ticks_between_spawn": 20,
  "total_mobs": 2.0,
  "total_mobs_added_per_player": 1.0
}
```

| field | 型 | 説明 |
|---|---|---|
| `spawn_potentials` | weighted list | spawnするentity data候補 |
| `simultaneous_mobs` | 非負float | 同時に存在できる基準mob数 |
| `simultaneous_mobs_added_per_player` | 非負float | 追加playerごとの同時mob増分 |
| `ticks_between_spawn` | 正のinteger | spawn間隔 |
| `total_mobs` | 非負float | wave全体の基準mob数 |
| `total_mobs_added_per_player` | 非負float | 追加playerごとの総mob増分 |
| `loot_tables_to_eject` | weighted list | 完了時に排出するloot table候補 |

normalとominousは別registry IDとして構成し、block entity／processor等の参照先を合わせます。

## villager trade

### `villager_trade`

```json
{
  "wants": {
    "id": "minecraft:emerald",
    "count": 4
  },
  "gives": {
    "id": "minecraft:iron_boots"
  },
  "max_uses": 12,
  "reputation_discount": 0.2,
  "xp": 1
}
```

| field | 必須性 | 型 | 説明 |
|---|---|---|---|
| `wants` | 必須 | wanted item object | 1つ目のcost |
| `wants.id` | 必須 | item ID | 要求するitem |
| `wants.count` | 任意 | number provider | 省略時1 |
| `wants.components` | 任意 | component map | 要求itemへ必要なcomponent。省略時空map |
| `additional_wants` | 任意 | wanted item object | 2つ目のcost |
| `gives` | 必須 | item stack | 取引結果 |
| `given_item_modifiers` | 任意 | inline item modifier list | 結果へ順に適用。空itemになればtradeを破棄 |
| `max_uses` | 任意 | number provider | 使用回数。provider結果は最低1、既定4 |
| `reputation_discount` | 任意 | number provider | reputation、demand等による割引係数。既定0 |
| `xp` | 任意 | number provider | merchantが得るXP。既定0 |
| `merchant_predicate` | 任意 | entity predicate | merchant条件 |
| `double_trade_price_enchantments` | 任意 | enchantment集合 | price倍化対象 |

### `trade_set`

```json
{
  "trades": "#example:armorer/level_1",
  "amount": 2,
  "random_sequence": "example:trade_set/armorer/level_1"
}
```

| field | 型 | 説明 |
|---|---|---|
| `trades` | villager trade ID／list／tag | 候補集合 |
| `amount` | 正のintegerまたはnumber provider | 集合から選ぶ数 |
| `random_sequence` | ID | world seedに基づく決定的なrandom sequence |

profession、level、wandering traderのconsumerはvanillaのtrade set IDを参照します。独自IDを作っただけで職業の既定tradeへ自動登録されません。

## `sulfur_cube_archetype`

26.2で追加され、`data/<namespace>/sulfur_cube_archetype/<id>.json`へ
配置します。

```json
{
  "items": "#example:sulfur_cube_food",
  "buoyant": true,
  "attribute_modifiers": [
    {
      "attribute": "minecraft:movement_speed",
      "id": "example:sulfur_cube_speed",
      "amount": 0.1,
      "operation": "add_value"
    }
  ],
  "knockback_modifiers": {
    "horizontal_power": 1.0,
    "vertical_power": 0.5
  },
  "sound_settings": {
    "hit_sound": "minecraft:block.slime_block.hit",
    "push_sound": "minecraft:block.slime_block.place",
    "push_sound_impulse_threshold": 0.1,
    "push_sound_cooldown": 0.25
  }
}
```

| field | 必須性 | 型 | 説明 |
|---|---|---|---|
| `items` | 必須 | item tag | このarchetypeへ対応する、与えられるitemの集合 |
| `buoyant` | 必須 | boolean | liquid内で浮くか |
| `attribute_modifiers` | 必須 | attribute modifier array | Sulfur Cubeへ適用するattribute変更 |
| `contact_damage` | 任意 | object | 接触したentityへ与えるdamage |
| `explosion` | 任意 | object | 存在する場合に点火後の爆発を設定 |
| `knockback_modifiers` | 必須 | object | knockbackの水平・垂直成分 |
| `sound_settings` | 必須 | object | hit／push soundと再生条件 |

`attribute_modifiers[]`:

| field | 型 | 制約・意味 |
|---|---|---|
| `attribute` | attribute ID | 変更するentity attribute |
| `id` | ID | modifierの一意な識別子 |
| `amount` | double | operationへ渡す量 |
| `operation` | enum | `add_value`、`add_multiplied_base`、`add_multiplied_total` |

`contact_damage`:

| field | 型 | 制約・意味 |
|---|---|---|
| `amount` | float | 0以上のdamage量 |
| `damage_type` | damage type ID | 使用するdamage type |
| `attribute_to_source` | boolean | damage sourceをSulfur Cubeへ帰属させるか |

`explosion`:

| field | 型 | 制約・意味 |
|---|---|---|
| `fuse` | integer | 1以上のfuse時間 |
| `power` | integer | 0以上の爆発威力 |
| `causes_fire` | boolean | 爆発でfireを発生させるか |

`knockback_modifiers`:

| field | 型 | 説明 |
|---|---|---|
| `horizontal_power` | float | 水平方向のknockback強度 |
| `vertical_power` | float | 垂直方向のknockback強度 |

`sound_settings`:

| field | 型 | 説明 |
|---|---|---|
| `hit_sound` | sound event ID | block吸収中にhitされたときのsound |
| `push_sound` | sound event ID | block吸収中に押されたときのsound |
| `push_sound_impulse_threshold` | float | push soundを鳴らす最小impulse |
| `push_sound_cooldown` | float | push soundのcooldown秒数 |

item側は`minecraft:sulfur_cube_content` componentとarchetype consumerの両方を確認します。

## resourceを定義しない組み込みregistry

`reports/datapack.json`で`elements: false`のregistryは、data packから新しいentry JSONを追加できません。tagを作れるregistryでも、tagは既存entryの集合を定義するだけです。

例:

- block、item、entity type
- attribute、data component type
- loot condition type、loot function type
- recipe serializer
- environment attribute
- command argument type

これらは`registries.json`のIDを参照し、存在しないIDを独自namespaceで追加しません。

## バージョン境界

| 正式リリース | 主な追加・移行 |
|---|---|
| 1.19 | `chat_type` |
| 1.19.4 | `damage_type` |
| 1.20系 | trim registry |
| 1.20.5 | banner pattern、wolf variant等のデータ駆動化 |
| 1.21 | enchantment、enchantment provider、painting、jukebox song |
| 1.21.2 | instrument、trial spawner等のcodec変更 |
| 1.21.5 | farm animal variant、wolf sound variant、GameTest |
| 1.21.6 | dialog |
| 1.21.11 | timeline、Zombie Nautilus variant |
| 26.1 | world clock、villager trade、trade set、Pig/Cat/Cow/Chicken sound variant |
| 26.2 | sulfur cube archetype |

## 検証

```text
[ ] reports/datapack.jsonでelements:trueのregistryだけを追加した
[ ] file pathから導かれるIDをconsumer側で正しく参照した
[ ] typeが対象バージョンのserializer registryに存在する
[ ] tagをregistry entryの新規定義と誤認していない
[ ] text、item stack、component、predicateを対象バージョン形式にした
[ ] 同じtypeのvanilla JSONとfieldを照合した
[ ] /reload後に実際のconsumerからentryを使用した
[ ] world registry変更を新規worldと再起動でも検証した
```
