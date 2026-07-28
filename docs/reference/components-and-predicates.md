# item stack、component、predicate

## item stackのバージョン境界

### 1.20.4以前

commandのitemはIDの後ろに旧item NBTを付けます。

```mcfunction
give @s minecraft:diamond_sword{Damage:1,display:{Name:'{"text":"Blade"}'}}
```

JSON内のitem stackは型ごとに`item`または`name`等の旧fieldを使います。command表現をJSONへコピーしません。

### 1.20.5から1.21.4

item機能はtyped data componentへ移行しました。

```mcfunction
give @s minecraft:diamond_sword[minecraft:damage=1,minecraft:custom_name='{"text":"Blade"}']
```

JSON内の共通item stack:

```json
{
  "id": "minecraft:diamond_sword",
  "count": 1,
  "components": {
    "minecraft:damage": 1
  }
}
```

### 1.21.5以降

commandのcomponent値とtext componentはSNBT表現を取る場面が増えます。

```mcfunction
give @s minecraft:diamond_sword[minecraft:custom_name={text:"Blade"}]
```

JSON resourceでは引き続き厳密なJSONを使います。

```json
{
  "id": "minecraft:diamond_sword",
  "components": {
    "minecraft:custom_name": {
      "text": "Blade"
    }
  }
}
```

## item stackのパラメータ

| field | 必須性 | 型 | 説明 |
|---|---|---|---|
| `id` | 必須 | item ID | item type |
| `count` | 任意 | 正のinteger | stack数。省略時1として扱うcodecが多いが、consumer固有制約を確認 |
| `components` | 任意 | component map | itemの既定componentを上書きまたは追加 |

component mapはcomponent IDをkeyにし、値をそのcomponentのcodecで読みます。item IDごとの既定値は26.2の`reports/minecraft/components/item/<id>.json`で確認できます。

commandのcomponent patchでは`!minecraft:component_id`により既定componentを削除できるバージョンがあります。JSONのcomponent mapで削除表現を使えるかはconsumerごとに異なります。

## 26.2のitem component

次の表は26.2の`minecraft:data_component_type` registryを用途別にまとめます。「値概要」は完全なcodecの代用ではなく、値の種類と責務を示します。nested fieldは同じcomponentを使うvanilla item、loot function、公式リリースノートで確定します。

### 表示、名前、model

| component ID | 値概要 | 説明 |
|---|---|---|
| `minecraft:custom_name` | text component | anvil等で付けた任意名 |
| `minecraft:item_name` | text component | item typeの基本表示名を上書き |
| `minecraft:lore` | text component list | tooltipのlore |
| `minecraft:rarity` | rarity ID／enum | tooltip色等のrarity |
| `minecraft:item_model` | model ID | resource packのitem model |
| `minecraft:custom_model_data` | object | float、flag、string、color等のmodel selector data |
| `minecraft:tooltip_display` | object | tooltipを隠すcomponent集合等を一元制御 |
| `minecraft:tooltip_style` | ID | tooltip background／frame style |
| `minecraft:enchantment_glint_override` | boolean | enchantment glintを強制on/off |
| `minecraft:map_color` | RGB color | item frame内map等で使う色 |
| `minecraft:note_block_sound` | sound event ID | head等がNote Block上で鳴らすsound |
| `minecraft:break_sound` | sound event ID | item破損時sound |

### durability、stack、使用

| component ID | 値概要 | 説明 |
|---|---|---|
| `minecraft:max_stack_size` | 1〜99のinteger | 最大stack数。durability等との組合せ制約あり |
| `minecraft:max_damage` | 正のinteger | 最大durability |
| `minecraft:damage` | 非負integer | 現在のdamage |
| `minecraft:unbreakable` | unit object | durabilityを減らさない |
| `minecraft:repair_cost` | 非負integer | anvil prior-work penalty |
| `minecraft:repairable` | item集合 | 修理材料 |
| `minecraft:use_cooldown` | object | cooldown secondsと任意のgroup ID |
| `minecraft:use_remainder` | item stack | 使用後に残すitem |
| `minecraft:use_effects` | object | item使用中／使用後の効果 |
| `minecraft:consumable` | object | consume時間、animation、sound、effect、particle |
| `minecraft:food` | object | nutrition、saturation等のfood値 |
| `minecraft:death_protection` | object | death時に消費して実行するeffect |
| `minecraft:potion_duration_scale` | float | potion effect duration倍率 |
| `minecraft:recipes` | recipe ID list | knowledge book等が提供するrecipe |

### combat、tool、equipment

| component ID | 値概要 | 説明 |
|---|---|---|
| `minecraft:attribute_modifiers` | modifier list | 装備slot／display等を含むattribute modifier |
| `minecraft:attack_range` | number／object | attack到達距離 |
| `minecraft:minimum_attack_charge` | float | 攻撃成立に必要なcharge |
| `minecraft:weapon` | object | item damage、disable blocking等のweapon規則 |
| `minecraft:kinetic_weapon` | object | 移動を使うweapon挙動 |
| `minecraft:piercing_weapon` | object | entity貫通挙動 |
| `minecraft:blocks_attacks` | object | blocking delay、damage reduction、disable条件 |
| `minecraft:damage_resistant` | damage type集合 | item entity等が耐えるdamage |
| `minecraft:tool` | rule list | block集合ごとのspeed、correct-for-drops、default speed |
| `minecraft:enchantable` | positive integer | enchantability |
| `minecraft:equippable` | object | slot、equip sound、asset、entity制限、dispensable等 |
| `minecraft:glider` | unit object | gliding可能にする |
| `minecraft:swing_animation` | object／enum | 使用時のswing表示 |
| `minecraft:intangible_projectile` | unit object | creative取得等を制限するprojectile marker |

### enchantment、potion、projectile

| component ID | 値概要 | 説明 |
|---|---|---|
| `minecraft:enchantments` | enchantment-level map | itemへ有効なenchantment |
| `minecraft:stored_enchantments` | enchantment-level map | enchanted book等の保存enchantment |
| `minecraft:charged_projectiles` | item stack list | crossbow等に装填済みのprojectile |
| `minecraft:potion_contents` | object | potion ID、custom color、custom effect、custom name |
| `minecraft:suspicious_stew_effects` | effect list | stewのmob effectとduration |
| `minecraft:ominous_bottle_amplifier` | integer | Ominous Bottle level |
| `minecraft:firework_explosion` | object | shape、colors、fade colors、trail、twinkle |
| `minecraft:fireworks` | object | flight durationとexplosion list |
| `minecraft:instrument` | instrument ID／inline object | Goat Horn等のinstrument |
| `minecraft:jukebox_playable` | song ID／inline object | jukebox song |

### container、entity、block data

| component ID | 値概要 | 説明 |
|---|---|---|
| `minecraft:container` | slot付きitem stack list | container itemの中身 |
| `minecraft:bundle_contents` | item stack list | bundleの中身 |
| `minecraft:container_loot` | object | loot table IDとseed |
| `minecraft:block_entity_data` | SNBT／NBT compound | 設置時にblock entityへ渡すdata |
| `minecraft:bucket_entity_data` | NBT compound | bucketからspawnするentity data |
| `minecraft:entity_data` | NBT compound | spawn egg等からentityへ渡すdata |
| `minecraft:bees` | bee entry list | Bee Nest／Beehive item内のbee |
| `minecraft:block_state` | string map | 設置時のblock state |
| `minecraft:lock` | item predicate | container lock条件 |
| `minecraft:pot_decorations` | item ID list | Decorated Potの各面 |
| `minecraft:profile` | profile object | player head／mannequin等のprofile |

### adventure、選択条件

| component ID | 値概要 | 説明 |
|---|---|---|
| `minecraft:can_break` | block predicate list | adventure modeで破壊できるblock |
| `minecraft:can_place_on` | block predicate list | adventure modeで設置できるblock |
| `minecraft:provides_banner_patterns` | banner pattern tag | itemが提供するpattern |
| `minecraft:provides_trim_material` | trim material ID／inline | itemが提供するtrim material |
| `minecraft:damage_type` | damage type ID | item固有damage source分類 |
| `minecraft:additional_trade_cost` | integer | trade生成中だけ使う一時cost補正 |
| `minecraft:creative_slot_lock` | unit object | creative inventoryのslot操作を制限 |

### contentと記録

| component ID | 値概要 | 説明 |
|---|---|---|
| `minecraft:custom_data` | NBT compound | 標準componentに対応しないpack独自data |
| `minecraft:writable_book_content` | page object list | 未署名bookのpage |
| `minecraft:written_book_content` | object | title、author、generation、resolved、pages |
| `minecraft:map_id` | integer | saved map ID |
| `minecraft:map_decorations` | map | map marker |
| `minecraft:map_post_processing` | enum | mapのlock／scale処理 |
| `minecraft:lodestone_tracker` | object | target dimension／positionとtracking状態 |
| `minecraft:debug_stick_state` | map | block IDごとの選択property |

### variantとappearance

| component ID | 値概要 | 説明 |
|---|---|---|
| `minecraft:base_color` | dye color | shield等のbase color |
| `minecraft:dyed_color` | RGB | leather armor等の染色色 |
| `minecraft:dye` | dye color | interactionに使うdye分類 |
| `minecraft:banner_patterns` | layer list | banner patternとdye color |
| `minecraft:trim` | object | trim materialとpattern |
| `minecraft:painting/variant` | painting variant ID | Paintingのvariant |
| `minecraft:cat/variant` | cat variant ID | Catのvariant |
| `minecraft:cat/sound_variant` | cat sound variant ID | Catのsound set |
| `minecraft:chicken/variant` | chicken variant ID | Chickenのvariant |
| `minecraft:chicken/sound_variant` | chicken sound variant ID | Chickenのsound set |
| `minecraft:cow/variant` | cow variant ID | Cowのvariant |
| `minecraft:cow/sound_variant` | cow sound variant ID | Cowのsound set |
| `minecraft:pig/variant` | pig variant ID | Pigのvariant |
| `minecraft:pig/sound_variant` | pig sound variant ID | Pigのsound set |
| `minecraft:frog/variant` | frog variant ID | Frogのvariant |
| `minecraft:wolf/variant` | wolf variant ID | Wolfのvariant |
| `minecraft:wolf/sound_variant` | wolf sound variant ID | Wolfのsound set |
| `minecraft:wolf/collar` | dye color | Wolf collar |
| `minecraft:cat/collar` | dye color | Cat collar |
| `minecraft:axolotl/variant` | variant enum | Axolotl variant |
| `minecraft:fox/variant` | variant enum | Fox variant |
| `minecraft:horse/variant` | variant object／enum | Horse color／marking |
| `minecraft:llama/variant` | variant enum | Llama variant |
| `minecraft:mooshroom/variant` | variant enum | Mooshroom variant |
| `minecraft:parrot/variant` | variant enum | Parrot variant |
| `minecraft:rabbit/variant` | variant enum／ID | Rabbit variant |
| `minecraft:salmon/size` | enum | Salmon size |
| `minecraft:sheep/color` | dye color | Sheep wool color |
| `minecraft:shulker/color` | dye color | Shulker color |
| `minecraft:tropical_fish/base_color` | dye color | Tropical Fish base color |
| `minecraft:tropical_fish/pattern` | enum | Tropical Fish pattern |
| `minecraft:tropical_fish/pattern_color` | dye color | Tropical Fish pattern color |
| `minecraft:villager/variant` | villager type ID | Villager biome variant |
| `minecraft:zombie_nautilus/variant` | variant ID | Zombie Nautilus variant |

### その他の26.2 component

| component ID | 値概要 | 説明 |
|---|---|---|
| `minecraft:sulfur_cube_content` | object | Sulfur Cube itemのcontent／archetype関連data |

component IDの完全な存在判定は26.2の`minecraft:data_component_type` registryを正本とします。上表にない新規IDがreportへ現れた場合は、対象正式リリースのページとvanilla component reportを追加してから使用します。

## item predicate

1.20.5以降のitem predicateは、item集合、完全一致component、component固有predicateを分けます。

```json
{
  "items": "#minecraft:swords",
  "count": {
    "min": 1
  },
  "components": {
    "minecraft:custom_data": {
      "example": true
    }
  },
  "predicates": {
    "minecraft:damage": {
      "durability": {
        "min": 1
      }
    }
  }
}
```

| field | 型 | 説明 |
|---|---|---|
| `items` | item ID／list／tag | item typeの候補 |
| `count` | integer range | stack count |
| `components` | component map | 指定component値との完全一致 |
| `predicates` | component predicate map | component固有の部分一致・range判定 |

26.2のcomponent predicate type:

```text
attribute_modifiers
bundle_contents
container
custom_data
damage
enchantments
firework_explosion
fireworks
jukebox_playable
potion_contents
stored_enchantments
trim
villager/variant
writable_book_content
written_book_content
```

`components`と`predicates`は用途が違います。例えばdamage値そのものを固定するときは`components`、durability範囲を判定するときは`predicates`を使います。

## standalone predicate

配置:

```text
data/<namespace>/predicate/<id>.json
```

単一loot condition object、または暗黙の`all_of`となる配列です。

```json
[
  {
    "condition": "minecraft:entity_properties",
    "entity": "this",
    "predicate": {
      "minecraft:entity_type": "minecraft:player"
    }
  },
  {
    "condition": "minecraft:random_chance",
    "chance": 0.25
  }
]
```

26.2のloot condition:

| condition | 主なパラメータ |
|---|---|
| `all_of` | `terms`。全条件がtrue |
| `any_of` | `terms`。いずれかがtrue |
| `inverted` | `term`。結果を反転 |
| `reference` | `name`。別predicate ID |
| `random_chance` | `chance` |
| `random_chance_with_enchanted_bonus` | base chance、enchantment、levelごとのbonus |
| `value_check` | `value` number provider、`range` |
| `time_check` | `value` range、任意の`period`、26.1以降の`clock` |
| `weather_check` | raining／thundering条件 |
| `location_check` | 任意の`offsetX/Y/Z`とlocation predicate |
| `block_state_property` | block IDとproperty map |
| `match_tool` | item predicate |
| `entity_properties` | entity targetとentity predicate |
| `entity_scores` | entity targetとobjectiveごとのrange |
| `damage_source_properties` | damage source predicate |
| `killed_by_player` | 任意のinverse |
| `survives_explosion` | explosion radius context |
| `table_bonus` | enchantmentとchance list |
| `enchantment_active_check` | enchantment active状態 |
| `environment_attribute_check` | environment attributeと期待値／range |

conditionが使えるかだけでなく、呼出側のloot contextに必要parameterがあるかを確認します。

## 26.2のentity predicate

26.2では旧field objectを廃止し、entity sub-predicate IDをkeyにするcomponent-map形式です。

```json
{
  "minecraft:entity_type": "#minecraft:undead",
  "minecraft:distance": {
    "absolute": {
      "max": 16
    }
  },
  "minecraft:entity_tags": {
    "all_of": ["example.active"],
    "none_of": ["example.disabled"]
  }
}
```

26.2のsub-predicate:

| key | 説明 |
|---|---|
| `minecraft:entity_type` | entity type ID／list／tag |
| `minecraft:distance` | x、y、z、horizontal、absoluteの距離range |
| `minecraft:effects` | mob effect IDごとのamplifier、duration、ambient、visible |
| `minecraft:entity_tags` | `any_of`、`all_of`、`none_of`の文字列tag |
| `minecraft:equipment` | slotごとのitem predicate |
| `minecraft:flags` | fire、sneaking、sprinting、swimming、baby等の状態 |
| `minecraft:location` | entity位置のlocation predicate |
| `minecraft:movement` | speed等のmovement range |
| `minecraft:movement_affected_by` | movementへ影響する位置条件 |
| `minecraft:nbt` | entity NBT部分一致 |
| `minecraft:passenger` | passenger entity predicate |
| `minecraft:periodic_tick` | tick周期条件 |
| `minecraft:components` | component値の完全一致 |
| `minecraft:predicates` | component predicate map |
| `minecraft:slots` | slot範囲／slot sourceごとのitem predicate |
| `minecraft:stepping_on` | 足元のlocation predicate |
| `minecraft:targeted_entity` | target entity predicate |
| `minecraft:team` | team名 |
| `minecraft:vehicle` | vehicle entity predicate |
| `minecraft:type_specific/player` | player固有のgamemode、advancement、input、food等 |
| `minecraft:type_specific/cube_mob` | Slime／Magma Cube等のsize |
| `minecraft:type_specific/fishing_hook` | open water等 |
| `minecraft:type_specific/lightning` | blocks set on fire、struck entity |
| `minecraft:type_specific/raider` | captain／raid状態 |
| `minecraft:type_specific/sheep` | sheared状態 |

26.1以前の`type`、`distance`、`type_specific`等をtop-levelへ残すと26.2はunknown keyとして拒否します。

## advancement condition

advancementのcriterion:

```json
{
  "criteria": {
    "use_item": {
      "trigger": "minecraft:consume_item",
      "conditions": {
        "player": {
          "minecraft:entity_type": "minecraft:player"
        },
        "item": {
          "items": "minecraft:apple"
        }
      }
    }
  }
}
```

| field | 説明 |
|---|---|
| `trigger` | advancement trigger ID |
| `conditions.player` | criterionを達成するplayerのentity predicate |
| その他の`conditions` | trigger固有。item、entity、location、damage等 |

同じtrigger名でも正式リリース間でconditionsが変わります。trigger一覧とfieldをvanilla advancementから抽出し、最新形式を古い対象バージョンへコピーしません。

## 検証

```text
[ ] item stackのcommand表現とJSON表現を混同していない
[ ] item IDの既定componentとpatch後のcomponentを区別した
[ ] component IDが対象バージョンのregistryに存在する
[ ] componentsの完全一致とpredicatesの部分一致を使い分けた
[ ] entity predicateは対象バージョンの旧object／26.2 component-mapを選んだ
[ ] conditionが必要とするloot context parameterを呼出側が提供する
[ ] advancement trigger固有conditionsを同バージョンのvanilla例で確認した
[ ] command、loot、recipe、trade等の各consumerで実際に発火させた
```
