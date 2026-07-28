# recipe、loot、item modifier、GameTest

## recipe

配置:

```text
data/<namespace>/recipe/<id>.json
```

1.20.6以前は`recipes/`です。

### 共通ingredient

26.2のingredientは次のいずれかです。

| 形 | 例 | 説明 |
|---|---|---|
| item ID | `"minecraft:iron_ingot"` | 1 item |
| item tag | `"#minecraft:planks"` | tag内のいずれか |
| list | `["minecraft:coal","minecraft:charcoal"]` | 候補のいずれか |

1.21.1以前のobject形`{"item":"..."}`や`{"tag":"..."}`を26.2へ混ぜません。

26.1以降のresult:

```json
{
  "id": "example:result",
  "count": 2,
  "components": {
    "minecraft:custom_name": {
      "text": "Result"
    }
  }
}
```

consumerによってitem IDだけの短縮形も使えます。`count`省略時は1、`components`省略時はitemの既定componentです。

### `minecraft:crafting_shaped`

```json
{
  "type": "minecraft:crafting_shaped",
  "category": "building",
  "group": "example",
  "pattern": [
    "SS",
    "SS"
  ],
  "key": {
    "S": "#minecraft:stone_crafting_materials"
  },
  "result": {
    "id": "minecraft:stone_bricks",
    "count": 4
  },
  "show_notification": true
}
```

| field | 必須性 | 説明 |
|---|---|---|
| `type` | 必須 | `minecraft:crafting_shaped` |
| `pattern` | 必須 | 同じ長さのstring配列。spaceは空slot |
| `key` | 必須 | pattern文字からingredientへのmap。spaceをkeyにしない |
| `result` | 必須 | item stack |
| `category` | 任意 | recipe book分類 |
| `group` | 任意 | recipe bookでまとめるgroup |
| `show_notification` | 任意 | unlock時toastを出すか |

未使用key、keyのないpattern文字、空patternはerrorです。

### `minecraft:crafting_shapeless`

```json
{
  "type": "minecraft:crafting_shapeless",
  "category": "misc",
  "ingredients": [
    "minecraft:flint",
    "minecraft:iron_ingot"
  ],
  "result": {
    "id": "minecraft:flint_and_steel"
  }
}
```

| field | 必須性 | 説明 |
|---|---|---|
| `ingredients` | 必須 | ingredient配列。各要素は1 slotを要求 |
| `result` | 必須 | item stack |
| `category`、`group` | 任意 | recipe book表示 |

### cooking

`minecraft:smelting`、`blasting`、`smoking`、`campfire_cooking`は同じ基本形です。

```json
{
  "type": "minecraft:smelting",
  "category": "misc",
  "ingredient": "minecraft:raw_iron",
  "result": {
    "id": "minecraft:iron_ingot",
    "count": 1
  },
  "experience": 0.7,
  "cookingtime": 200
}
```

| field | 必須性 | 説明 |
|---|---|---|
| `ingredient` | 必須 | 入力ingredient |
| `result` | 必須 | 26.1以降はitem IDまたはitem stack |
| `experience` | 任意 | 取り出し時XP |
| `cookingtime` | 任意 | tick。serializerごとにvanilla既定値が異なる |
| `category`、`group` | 任意 | recipe book表示 |

### `minecraft:stonecutting`

| field | 説明 |
|---|---|
| `ingredient` | 入力ingredient |
| `result` | item stack |
| `group` | 任意のgroup |

### smithing

`minecraft:smithing_transform`:

```json
{
  "type": "minecraft:smithing_transform",
  "template": "minecraft:netherite_upgrade_smithing_template",
  "base": "#minecraft:netherite_upgrade_base",
  "addition": "#minecraft:netherite_upgrade_materials",
  "result": {
    "id": "minecraft:netherite_sword"
  }
}
```

`template`、`base`、`addition`はingredient、`result`はitem stackです。base itemのcomponentをresultへ引き継ぐ挙動を機能テストします。

`minecraft:smithing_trim`は`template`、`base`、`addition`を持ち、resultはtrim適用で決まるためtransformと同一のresult fieldを前提にしません。

### `minecraft:crafting_transmute`

| field | 説明 |
|---|---|
| `input` | componentを引き継ぐ元ingredient |
| `material` | 変換材料ingredient |
| `result` | result item ID |
| `category`、`group` | 任意のrecipe book分類 |

### 26.2のrecipe serializer

```text
blasting
campfire_cooking
crafting_decorated_pot
crafting_dye
crafting_imbue
crafting_shaped
crafting_shapeless
crafting_special_bannerduplicate
crafting_special_bookcloning
crafting_special_firework_rocket
crafting_special_firework_star
crafting_special_firework_star_fade
crafting_special_mapextending
crafting_special_repairitem
crafting_special_shielddecoration
crafting_transmute
smelting
smithing_transform
smithing_trim
smoking
stonecutting
```

special recipeはcode側に固定された処理を選ぶserializerです。vanillaにない新しいspecial serializer IDはdata packから追加できません。

## loot table

配置:

```text
data/<namespace>/loot_table/<id>.json
```

```json
{
  "type": "minecraft:generic",
  "random_sequence": "example:reward",
  "pools": [
    {
      "rolls": 1,
      "bonus_rolls": 0,
      "conditions": [],
      "entries": [
        {
          "type": "minecraft:item",
          "name": "minecraft:diamond",
          "weight": 1,
          "quality": 0
        }
      ],
      "functions": []
    }
  ],
  "functions": []
}
```

### root

| field | 必須性 | 説明 |
|---|---|---|
| `type` | 条件付き | loot context type。consumerによって固定または必要 |
| `random_sequence` | 任意 | world seedから独立系列を得るID |
| `pools` | 任意 | loot pool配列 |
| `functions` | 任意 | table結果全体へ順に適用するloot function |

### pool

| field | 必須性 | 説明 |
|---|---|---|
| `rolls` | 必須 | number provider |
| `bonus_rolls` | 任意 | luckで増えるnumber provider |
| `entries` | 必須 | loot entry配列 |
| `conditions` | 任意 | poolを使う条件 |
| `functions` | 任意 | pool結果へ適用するfunction |

### entry

| type | 主なfield | 説明 |
|---|---|---|
| `minecraft:item` | `name` | item entry |
| `minecraft:tag` | `name`, `expand` | item tagを1 entryまたは各itemへ展開 |
| `minecraft:loot_table` | `value`／`name` | 別loot tableまたはinline table |
| `minecraft:dynamic` | `name` | consumerが提供するdynamic drop |
| `minecraft:empty` | なし | 空結果 |
| `minecraft:group` | `children` | 全childを実行 |
| `minecraft:alternatives` | `children` | 最初に成功するchild |
| `minecraft:sequence` | `children` | 順に実行し失敗で停止 |
| `minecraft:slots` | slot source関連field | 1.21.11以降のslot由来entry |

全entryに共通して`conditions`、`functions`、`weight`、`quality`を取れるかはentry typeに依存します。

### number provider

| type | 主なfield |
|---|---|
| constant | JSON number短縮形 |
| `minecraft:uniform` | `min`, `max`または`min_inclusive`, `max_inclusive` |
| `minecraft:binomial` | `n`, `p` |
| `minecraft:score` | target、score、scale |
| `minecraft:storage` | storage ID、NBT path |
| `minecraft:enchantment_level` | amount等のlevel依存値 |

field名は正式リリース間で変更されます。同じnumber providerをrecipe、trade、worldgenへ使えるとは限りません。

## item modifier／loot function

配置:

```text
data/<namespace>/item_modifier/<id>.json
```

単一objectまたは順次適用するarrayです。

```json
[
  {
    "function": "minecraft:set_count",
    "count": 2
  },
  {
    "function": "minecraft:set_name",
    "name": {
      "text": "Reward"
    }
  }
]
```

26.2のloot function:

| function | 主なパラメータ・目的 |
|---|---|
| `apply_bonus` | enchantment、formula、parameters。drop数へbonus |
| `copy_components` | source、include／exclude。別objectからcomponentをcopy |
| `copy_custom_data` | source、ops。custom dataのNBT path操作 |
| `copy_name` | source。nameをcopy |
| `copy_state` | block、properties。block stateをitem componentへcopy |
| `discard` | itemを空にする |
| `enchant_randomly` | options、only_compatible。候補からenchant |
| `enchant_with_levels` | levels、options。costでenchant |
| `enchanted_count_increase` | enchantment、count、limit |
| `exploration_map` | destination、decoration、zoom、search radius等 |
| `explosion_decay` | explosion survivalでcountを減らす |
| `fill_player_head` | entity target |
| `filtered` | item filter、`on_pass`、`on_fail`。1.21.11でfield変更 |
| `furnace_smelt` | recipeに従いsmelt |
| `limit_count` | count rangeへclamp |
| `modify_contents` | component、modifier。container内容を変更 |
| `reference` | item modifier ID |
| `sequence` | functions array |
| `set_attributes` | modifier array |
| `set_banner_pattern` | patterns、append |
| `set_book_cover` | title、author、generation |
| `set_components` | component patch |
| `set_contents` | component、entries |
| `set_count` | count、任意のadd |
| `set_custom_data` | NBT tag |
| `set_custom_model_data` | colors／flags／floats／stringsの操作 |
| `set_damage` | damage fraction、任意のadd |
| `set_enchantments` | enchantment-level map、任意のadd |
| `set_firework_explosion` | shape、colors、fade colors、trail、twinkle |
| `set_fireworks` | flight durationとexplosion操作 |
| `set_instrument` | instrument集合 |
| `set_item` | item ID |
| `set_loot_table` | loot table、seed、block entity type |
| `set_lore` | lore、mode、entity target |
| `set_name` | name、entity target |
| `set_ominous_bottle_amplifier` | amplifier |
| `set_potion` | potion ID |
| `set_random_dyes` | dye候補 |
| `set_random_potion` | potion候補 |
| `set_stew_effect` | effectとduration候補 |
| `set_writable_book_pages` | pages、mode |
| `set_written_book_pages` | pages、mode |
| `toggle_tooltips` | componentごとのtooltip表示 |

各functionは任意の`conditions`を持てます。sourceやentity targetが必要なfunctionは、loot contextに対象parameterがなければ失敗します。

## GameTest

GameTestは1.21.5以降です。

```text
data/<namespace>/test_environment/<id>.json
data/<namespace>/test_instance/<id>.json
data/<namespace>/structure/<id>.nbt
```

### `test_instance`

```json
{
  "type": "minecraft:block_based",
  "environment": "minecraft:default",
  "structure": "example:tests/basic",
  "max_ticks": 100,
  "setup_ticks": 1,
  "required": true,
  "rotation": "none",
  "manual_only": false,
  "sky_access": false,
  "max_attempts": 1,
  "required_successes": 1
}
```

| field | 必須性 | 説明 |
|---|---|---|
| `type` | 必須 | `minecraft:block_based`または`minecraft:function` |
| `environment` | 必須 | test environment ID |
| `structure` | 必須 | test structure ID |
| `max_ticks` | 必須 | timeoutまでの正のtick数 |
| `setup_ticks` | 任意 | structure配置後の待機tick。既定0 |
| `required` | 任意 | suite成功に必須か。既定true |
| `rotation` | 任意 | `none`、`clockwise_90`、`180`、`counterclockwise_90` |
| `manual_only` | 任意 | 自動suiteから除外。既定false |
| `sky_access` | 任意 | barrier天井を開けるか。既定false |
| `max_attempts` | 任意 | 最大試行回数。既定1 |
| `required_successes` | 任意 | 必要成功数。既定1、`max_attempts`以下 |
| `function` | function typeで必須 | 組み込みtest function ID |

data packだけで任意のJava test functionを追加できません。通常のdata packは`block_based`とTest Blockを使います。

### `test_environment`

空のenvironment:

```json
{
  "type": "minecraft:all_of",
  "definitions": []
}
```

26.2のdefinition type:

| type | パラメータ |
|---|---|
| `minecraft:all_of` | `definitions`。複数definitionを順に適用 |
| `minecraft:function` | 任意の`setup`、`teardown` function ID |
| `minecraft:game_rules` | namespaced game rule IDからboolean／integerへのmap |
| `minecraft:weather` | `weather`: `clear`、`rain`、`thunder` |
| `minecraft:difficulty` | difficulty値 |
| `minecraft:clock_time` | `clock` world clock IDと`time` |
| `minecraft:timeline_attributes` | `timelines` ID list |

1.21.5当初の`time_of_day`やcamelCase gameruleを26.2へ使いません。26.1のworld clock化と1.21.11のnamespaced gamerule化を適用します。

### 実行

game内:

```mcfunction
test run example:basic
```

CI entry point:

```bash
java -DbundlerMainClass=net.minecraft.gametest.Main \
  -jar server.jar \
  --packs /path/to/packs \
  --tests 'example:*' \
  --report build/gametest-report.xml
```

GameTest用worldは破棄可能な専用directoryを使います。既存worldを`--universe`の対象にしません。

## バージョン境界

| 正式リリース | 境界 |
|---|---|
| 1.14 | loot table `type`とloot context |
| 1.17 | item modifier、number providerの厳格化 |
| 1.18 | 一部loot functionの`type`必須化 |
| 1.20 | recipe、advancement、predicateのfield変更 |
| 1.20.5 | item component化、recipe result、loot functionを大改編 |
| 1.21.2 | ingredientをinline ID／tagへ変更、`crafting_transmute` |
| 1.21.5 | GameTest、recipe result componentの厳格化 |
| 1.21.11 | `filtered`、`discard`、slot source、environment condition |
| 26.1 | recipe resultをIDまたは`{id,count,components}`へ統一、GameTestのclock対応 |
| 26.2 | entity predicate component-map化がconditionへ波及 |

## 検証

```text
[ ] recipe serializerが対象バージョンに存在する
[ ] ingredientとresultが対象バージョンの形
[ ] special recipeへ存在しない独自serializerを追加していない
[ ] loot table typeと実際のconsumerのcontextが一致する
[ ] condition/functionが参照するcontext parameterが存在する
[ ] item modifierの適用順と空item結果を確認した
[ ] GameTestのenvironment、structure、instance参照がすべて解決する
[ ] required_successes <= max_attempts
[ ] GameTestを破棄可能な専用worldで実行した
```

## 一次資料

- [Mojang: Java Edition 1.20.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-5)
- [Mojang: Java Edition 1.21.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-5)
- [Mojang: Java Edition 26.1](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-1)
