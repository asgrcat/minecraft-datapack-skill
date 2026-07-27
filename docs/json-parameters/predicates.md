# predicate・loot condition パラメータ

この文書は Java Edition 1.13〜26.2 の predicate 関連データについて、独立 predicate resource、loot condition、entity/location/item/block predicate、条件の合成、評価 context、主要 parameter、バージョン境界、検証方法を整理します。

全 condition type と全入れ子 codec を Markdown に固定して複製するものではありません。対象バージョンに存在する type ID は公式 server JAR の `registries.json`、実際の field は Mojang のリリースノート、vanilla data、対象 server の reload 結果を正本とします。

## 最初に区別するもの

Minecraft では複数の異なる値が predicate と呼ばれます。

| 用語 | 役割 | 単独の `predicate(s)/<id>.json` に置けるか |
|---|---|---|
| 独立 predicate resource | 再利用可能な loot condition、または condition の AND list | 1.15 以降で可能 |
| loot condition | 与えられた loot context が条件を満たすか判定する object | 可能。独立 resource の構成要素でもある |
| entity predicate | entity の種類、距離、状態、装備等を照合する入れ子の値 | 単独では不可。通常は `entity_properties.predicate` 等に入る |
| location predicate | 座標、dimension、biome、structure、block、fluid、light 等を照合する入れ子の値 | 単独では不可。通常は `location_check.predicate` 等に入る |
| item predicate | item stack の item ID、count、NBT/component 等を照合する入れ子の値 | 単独では不可。通常は `match_tool.predicate` 等に入る |
| gameplay block predicate | location 内の block、state、block entity data/component 等を照合する値 | 単独では不可 |
| worldgen block predicate | configured feature 等で block 配置可否を判定する `predicate_type` dispatcher | 独立 predicate resource とは別系統 |
| advancement の条件 | trigger 固有条件。バージョンによって entity check 等に loot condition listを利用 | trigger 全体は独立 predicate ではない |
| enchantment の `requirements` | enchantment effect を適用する inline loot condition | 独立 resource参照とは限らない |

次の JSON は entity predicate ではなく、entity predicate を内包した loot condition です。

```json
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "type": "minecraft:player"
  }
}
```

この外側に `condition` があるため、1.15〜1.20.6 の独立 predicate file として使用できます。内側の `{"type":"minecraft:player"}` だけを `predicates/<id>.json` に置いても、独立 resource の root codecにはなりません。

## 配置と呼び出し

### 1.13〜1.14

独立 predicate resource はありません。predicate に相当する判定は advancement trigger、loot table の `conditions`、その中の `entity_properties` 等へ埋め込みます。

### 1.15〜1.20.6

```text
data/<namespace>/predicates/<path>.json
```

### 1.21〜26.2

```text
data/<namespace>/predicate/<path>.json
```

1.21 のデータフォルダ単数形化により、`predicates` は `predicate` へ変わりました。pack metadata の互換範囲を広げても、同じ物理 path で複数形と単数形を兼用はできません。

独立 predicate の主な利用箇所は次です。

```mcfunction
execute if predicate example:is_ready run function example:ready
execute unless predicate example:is_ready run function example:not_ready
```

entity selector では次の形です。

```mcfunction
execute as @e[predicate=example:is_ready] run function example:matched
```

loot condition 内から参照する場合は `minecraft:reference` を使います。

```json
{
  "condition": "minecraft:reference",
  "name": "example:is_ready"
}
```

`reference` は別の JSON を文字列置換で展開する機能ではありません。参照先も同じ評価時の loot context を使うため、参照元に存在しない context parameter を参照先が要求すると成立しません。

## root 形式と条件合成

### 1.15 の単一 condition

1.15 の独立 predicate は、基本的に単一の loot condition objectです。

```json
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "team": "builders"
  }
}
```

### 1.16 以降の top-level AND

1.16 以降は root を配列にでき、全要素が成立した場合だけ全体が成立します。

```json
[
  {
    "condition": "minecraft:entity_properties",
    "entity": "this",
    "predicate": {
      "type": "minecraft:player"
    }
  },
  {
    "condition": "minecraft:time_check",
    "value": {
      "min": 13000,
      "max": 23000
    },
    "period": 24000
  }
]
```

この配列は OR ではありません。

### 明示的な合成 condition

| condition | 主要 field | 意味 |
|---|---|---|
| `minecraft:all_of` | `terms` | 全 condition が成立 |
| `minecraft:any_of` | `terms` | 1つ以上の condition が成立 |
| `minecraft:inverted` | `term` | 内側の condition の結果を反転 |
| `minecraft:reference` | `name` | 独立 predicate resource を評価 |

1.20 では旧 `minecraft:alternative` が `minecraft:any_of` へ置換され、`minecraft:all_of` が追加されました。1.20.2 以降は condition list を inline arrayとして書ける場所がありますが、許可される省略形は外側の codecごとに確認が必要です。top-level array、`terms`、loot function の condition listを同じ構文として扱いません。

循環する `reference`、存在しないID、対象バージョンに存在しない condition typeは利用可能な合成方法ではありません。

## loot context

loot condition は JSON だけで完結せず、評価元が作る loot context に依存します。context は「現在の entity」「座標」「tool」「block state」「damage source」等の parameter 集合です。

| condition | 主に必要となる context | contextがない場合の問題 |
|---|---|---|
| `entity_properties` | `entity` fieldで選んだ entity parameter | 対象entityを取得できない |
| `entity_scores` | scoreを読む対象entity | 対象entityを取得できない |
| `location_check` | origin | 評価座標を取得できない |
| `match_tool` | tool | toolのない評価元では一致しない |
| `block_state_property` | block state | block破壊等以外では利用できない場合がある |
| `damage_source_properties` | damage source と関連entity | damage event外では利用できない場合がある |
| `survives_explosion` | explosion radius | explosion外では前提parameterがない |
| `table_bonus` | tool上のenchantment等 | tool contextに依存 |
| `killed_by_player` | last damage player | player kill情報に依存 |
| `time_check`, `weather_check` | server level | worldの時刻・天候を参照 |
| `value_check` | `value` number providerが要求するparameter | providerの種類ごとに異なる |

`execute if predicate`、selector、loot table、advancement、enchantment effect、trade は同じ context を提供するとは限りません。ある場所で成立した predicate resource が、別の場所でも同じ結果になるという保証はありません。

condition が JSON として読み込めることと、利用場所の context parameter setで有効であることは別の検査です。loot table には `type` ごとの許可parameterがあり、contextに合わない condition はvalidation errorになる場合があります。

## 主要 loot condition

次は複数バージョンで中心となる conditionです。fieldの必須性、短縮形、number providerの許容typeは対象バージョンで確定します。

| condition | 主要 field | 判定 |
|---|---|---|
| `minecraft:entity_properties` | `entity`, `predicate` | 指定context entityをentity predicateで照合 |
| `minecraft:entity_scores` | `entity`, `scores` | scoreboard値をrangeで照合 |
| `minecraft:location_check` | `predicate`, `offsetX?`, `offsetY?`, `offsetZ?` | originまたはoffset先をlocation predicateで照合 |
| `minecraft:match_tool` | `predicate` | tool item stackをitem predicateで照合 |
| `minecraft:block_state_property` | `block`, `properties?` | context block stateを照合 |
| `minecraft:damage_source_properties` | `predicate` | damage source predicateで照合 |
| `minecraft:random_chance` | `chance` | 固定確率 |
| `minecraft:random_chance_with_looting` | `chance`, `looting_multiplier` | looting levelを考慮。1.20.6以前 |
| `minecraft:random_chance_with_enchanted_bonus` | `unenchanted_chance`, `enchanted_chance`, `enchantment` | 指定enchantmentを考慮。1.21以降 |
| `minecraft:table_bonus` | `enchantment`, `chances` | enchantment levelごとの確率表 |
| `minecraft:time_check` | `value`, `period?` | game timeまたは周期内時刻 |
| `minecraft:weather_check` | `raining?`, `thundering?` | 天候 |
| `minecraft:value_check` | `value`, `range` | number providerの結果 |
| `minecraft:survives_explosion` | バージョン依存 | explosionからdropが生存する確率 |
| `minecraft:enchantment_active_check` | `active` | enchantment effectのactive状態。1.21以降 |
| `minecraft:environment_attribute_check` | 対象attributeと照合値 | environment attributeを照合。26.1追加 |

`registries.json` の `minecraft:loot_condition_type` は、対象JARに存在するcondition IDの完全な確認に使えます。ただし各IDの内部fieldを列挙するJSON Schemaではありません。

## entity predicate

### 1.13〜26.1.2 のfield object

26.1.2 以前のentity predicateは、複数のoptional fieldを持つobjectです。代表的なfieldは次のとおりです。

| field | 照合対象 |
|---|---|
| `type` | entity type。対応バージョンではID、ID list、entity type tag |
| `distance` | originからのabsolute/horizontal/x/y/z距離range |
| `location`, `stepping_on` | entity位置、足元位置のlocation predicate |
| `effects` | status effectとamplifier/duration等 |
| `nbt` | entity NBTの部分一致 |
| `flags` | on fire、sneaking、sprinting、swimming、baby等 |
| `equipment` | head/chest/legs/feet/mainhand/offhand等のitem predicate |
| `slots` | slot名またはrangeごとのitem predicate。1.20.5追加 |
| `player` | player固有のlevel、gamemode、stats、recipes、advancements等 |
| `team` | scoreboard team名 |
| `vehicle`, `passenger`, `targeted_entity` | 関連entityの再帰predicate |
| `type_specific` | entity種別固有のsub-predicate。1.19以降 |

空objectは「どのentityにも一致しない」ではなく、通常は制約なしです。対象entity自体がcontextに存在しない場合の結果とは区別されます。

#### 1.19〜26.1.2 の `type_specific`

1.19 ではentity固有条件が `type_specific` に集約されました。1.19.3では axolotl、boat、fox、mooshroom、painting、rabbit、horse、llama、villager、parrot、tropical fish 等のsub-predicateが追加されました。その後のバージョンでもvariantやentity component化に伴ってtype集合が変化しています。

概念上の形は次のとおりです。

```json
{
  "type": "minecraft:player",
  "type_specific": {
    "type": "minecraft:player",
    "gamemode": "survival"
  }
}
```

外側の `type` と内側の `type_specific.type` は別の役割です。sub-predicateが対応しないentityへ適用された場合は一致しません。

### 1.21.5 のentity component対応

1.21.5ではentity predicateに `components` と `predicates` が追加され、variant判定の多くが旧type-specific fieldからentity component判定へ移りました。

- `components` は指定component値の完全一致
- `predicates` はcomponent固有の部分条件・range等
- axolotl、fox、mooshroom、rabbit、horse、llama、villager、parrot、tropical fish、painting、cat、frog、wolf、pig等の旧type-specific variant判定はcomponentとの組合せへ移行

item component predicateと名前が似ていますが、照合対象はentityが保持するcomponentです。

### 26.2 のcomponent-map形式

26.2ではrootが「optional fieldを集めたobject」から、namespaced sub-predicate IDをkeyとするmapへ変わりました。

```json
{
  "minecraft:entity_type": "minecraft:player",
  "minecraft:flags": {
    "is_sneaking": true
  }
}
```

主な移行は次のとおりです。

| 26.1.2以前 | 26.2 |
|---|---|
| `type` | `minecraft:entity_type` |
| `distance` | `minecraft:distance` |
| `effects` | `minecraft:effects` |
| `equipment` | `minecraft:equipment` |
| `flags` | `minecraft:flags` |
| `location` | `minecraft:location` |
| `nbt` | `minecraft:nbt` |
| `passenger` | `minecraft:passenger` |
| `slots` | `minecraft:slots` |
| `team` | `minecraft:team` |
| `vehicle` | `minecraft:vehicle` |
| `type_specific.type=player` | `minecraft:type_specific/player` |
| `type_specific.type=slime` | `minecraft:type_specific/cube_mob` |

26.2 JARの `minecraft:entity_sub_predicate_type` registryには、上記のほか `components`、`entity_tags`、`movement`、`movement_affected_by`、`periodic_tick`、`predicates`、`stepping_on`、`targeted_entity`、`type_specific/fishing_hook`、`type_specific/lightning`、`type_specific/raider`、`type_specific/sheep` 等が含まれます。

namespace省略時は `minecraft` が補われますが、unknown keyは拒否されます。26.1.2以前のunknown fieldが無視される挙動を、将来用placeholderとして利用はできません。

26.2で追加された `minecraft:entity_tags` は `/tag` で付与される文字列tagを照合し、`any_of`、`all_of`、`none_of` を取ります。entity type tagやdata packのregistry tagとは別物です。

## location predicate

location predicateは「dimensionを生成するJSON」ではなく、ある座標の状態を判定する値です。

代表的なfieldは次のとおりです。

| field | 照合対象 |
|---|---|
| `position` | x/y/z座標range |
| `dimension` | dimension ID |
| `biome` / `biomes` | biome ID、対応バージョンではlist/tag |
| `feature` / `structure` / `structures` | configured featureまたはstructure。バージョンにより意味と名称が異なる |
| `smokey` | campfireの煙が届く位置か |
| `light` | light level range |
| `block` | gameplay block predicate |
| `fluid` | fluid predicate |
| `can_see_sky` | 空が見えるか。対応バージョンのみ |

重要な境界は次です。

- 1.15でblock、fluid、light判定を追加
- 1.18.2の`feature`はconfigured feature reference
- 1.19で`feature`を`structure`へ変更
- 1.20.5で `biome→biomes`、`structure→structures` 等を更新し、単一ID、list、`#tag` を扱う形式へ移行

`light`は実際のgameplay light判定です。dimension typeの`ambient_light`やenvironment attributeによる画面の見え方と同じ値ではありません。

## item predicate

item predicateはitem stackを判定し、recipe ingredientやitem stack生成値とは別のcodecです。

### 1.13〜1.16

代表的なfieldには `item`、`tag`、`count`、`durability`、`enchantments`、`stored_enchantments`、`potion`、`nbt` 等があります。1.15では通常のenchantmentとenchanted bookのstored enchantmentが分離されました。

### 1.17〜1.20.4

1.17で `item` が `items` へ変わり、複数item IDを受け付けます。後続バージョンでもitem NBTを基準にする旧形式が続きます。

### 1.20.5以降

1.20.5でitem stackがdata componentへ移行し、item predicateも再編されました。

```json
{
  "items": "minecraft:diamond_pickaxe",
  "components": {
    "minecraft:damage": 0
  },
  "predicates": {
    "minecraft:damage": {
      "durability": {
        "min": 3
      }
    }
  },
  "count": {
    "min": 1
  }
}
```

| field | 意味 |
|---|---|
| `items` | item ID、item ID list、対応バージョンでは`#item_tag` |
| `components` | 指定componentの完全値一致 |
| `predicates` | component固有sub-predicate |
| `count` | stack countの整数またはrange |

旧 `tag`、`durability`、`potions`、`nbt`、`enchantments` 等はrootから削除・移動されました。NBTの部分一致は `minecraft:custom_data` sub-predicate、残耐久は `minecraft:damage` sub-predicate、enchantmentは対応するcomponent sub-predicateで扱います。

componentが存在しないstackは、そのcomponentを要求するsub-predicateに一致しません。ただしitem typeのdefault componentも存在判定に含まれます。

commandのitem predicate argumentは同じ判定概念を使いますが、JSON objectではなくitem argumentとSNBTの構文です。

```mcfunction
clear @s minecraft:diamond_pickaxe[minecraft:damage=0] 0
clear @s *[minecraft:damage~{durability:{min:3}}] 0
clear @s minecraft:stick[minecraft:custom_data~{example:{kind:"token"}}] 0
```

- `=` はcomponent値の完全一致
- `~` はcomponent sub-predicate
- bare component IDは存在判定
- `!` はtestの否定
- `|` はtest内の選択肢
- `count=` と `count~` はstack count判定

1.21.11では空のcomponent sub-predicateによる存在判定も利用可能になりました。JSON predicateとcommand predicateは外側の文法が異なるため、command例をJSONへ貼り付けることはできません。

item predicateの詳細は [`items.md`](items.md) も参照してください。

## block predicate

### gameplay block predicate

location predicate、advancement、item component等で使うblock predicateは、主に次を照合します。

| field | 照合対象 |
|---|---|
| `block` / `blocks` | block ID。対応バージョンではlist/tag |
| `tag` | 旧形式のblock tag指定 |
| `state` | block state property |
| `nbt` | block entity NBT |
| `components` | block entity componentの完全一致。1.21.5以降 |
| `predicates` | block entity component sub-predicate。1.21.5以降 |

1.17で `block` は `blocks`へ拡張されました。1.20.5ではrootの `tag` を削除し、`blocks` 自体が単一ID、list、`#tag`を受け付ける形式へ移りました。block state propertyの値は1.20.2以降JSON stringが必要です。

block entityを持たないblockへblock entity data/component条件を要求した場合は一致しません。

### worldgen block predicate

worldgen configured feature等のblock predicateは、上記とは別のdispatcherです。objectの `predicate_type` で種類を選びます。

26.2 JARの `minecraft:block_predicate_type` registryには、次のtypeが含まれます。

```text
all_of
any_of
has_sturdy_face
inside_world_bounds
matching_biomes
matching_block_tag
matching_blocks
matching_fluids
not
replaceable
solid
true
unobstructed
would_survive
```

`matching_biomes` は26.2追加です。worldgenの `all_of` / `any_of` / `not` と、loot conditionの同名typeは別registry・別field構造です。

## バージョン境界

`継承`はpredicate系の主要な破壊的変更が記録されていないことを示します。完全に同じcodecを保証する記号ではありません。

| 正式リリース | predicate関連の状態 |
|---|---|
| 1.13 | 独立resourceなし。advancement/lootへ入れ子 |
| 1.13.1 | 1.13を継承 |
| 1.13.2 | 1.13.1を継承 |
| 1.14 | loot context/condition再編、`entity_properties`等を拡張 |
| 1.14.1 | 1.14を継承 |
| 1.14.2 | 1.14.1を継承 |
| 1.14.3 | 1.14.2を継承 |
| 1.14.4 | 1.14.3を継承。独立resourceは未対応 |
| 1.15 | `predicates/`、`execute if predicate`、selector `predicate=`、`reference`を追加 |
| 1.15.1 | 1.15を継承 |
| 1.15.2 | 1.15.1を継承 |
| 1.16 | top-level condition arrayのAND、advancement entity checkのloot condition化、entity関連field追加 |
| 1.16.1 | 1.16を継承 |
| 1.16.2 | predicate rootは継承。worldgen block predicateとは別系統 |
| 1.16.3 | 1.16.2を継承 |
| 1.16.4 | 1.16.3を継承 |
| 1.16.5 | 1.16.4を継承 |
| 1.17 | item `item→items`、block `block→blocks`、entity passenger/stepping_on/lightning等 |
| 1.17.1 | 1.17を継承 |
| 1.18 | 1.17.1のpredicate形を継承 |
| 1.18.1 | 1.18を継承 |
| 1.18.2 | location `feature`がconfigured featureを参照 |
| 1.19 | location `feature→structure`、entity固有条件を`type_specific`へ |
| 1.19.1 | 1.19を継承 |
| 1.19.2 | 1.19.1を継承 |
| 1.19.3 | 多数のentity `type_specific` sub-predicateを追加 |
| 1.19.4 | damage source predicateの旧boolean群をtag判定へ置換 |
| 1.20 | `alternative→any_of`、`all_of`追加。advancementの一部条件をlocation loot condition listへ |
| 1.20.1 | 1.20を継承 |
| 1.20.2 | `all_of`のinline array、block/fluid state property値をJSON stringへ限定 |
| 1.20.3 | 1.20.2のpredicate形を継承 |
| 1.20.4 | item NBT基準predicateの最終系列 |
| 1.20.5 | item component predicateへ全面移行。entity `slots`、ID/list/tag対応を拡張 |
| 1.20.6 | 1.20.5を継承 |
| 1.21 | `predicates/→predicate/`。looting確率conditionをenchanted bonus形へ、enchantment condition追加 |
| 1.21.1 | 1.21を継承 |
| 1.21.2 | container `lock`がitem predicate値へ |
| 1.21.3 | 1.21.2を継承 |
| 1.21.4 | 1.21.3の主要predicate形を継承 |
| 1.21.5 | entity/block predicateに`components`、`predicates`。variant判定をentity componentへ移行 |
| 1.21.6 | 全JSONをstrict parse。comment/trailing comma不可 |
| 1.21.7 | 1.21.6を継承 |
| 1.21.8 | 1.21.7を継承 |
| 1.21.9 | 主要predicate rootは継承。profile componentの値 semantics変更に注意 |
| 1.21.10 | 1.21.9を継承 |
| 1.21.11 | command item predicateのcomponent存在判定を拡張 |
| 26.1 | `environment_attribute_check`、`time_check.clock`、player sub-predicateの`food`を追加。trade等にinline predicate利用箇所を追加 |
| 26.1.1 | 26.1を継承 |
| 26.1.2 | 26.1.1を継承。26.2 component-mapは未対応 |
| 26.2 | entity predicateをnamespaced component-mapへ変更し、unknown keyを拒否 |

## よくある誤解

- `predicate/<id>.json` のrootはraw entity predicateではなくloot conditionです
- top-level arrayはORではなくANDです
- `minecraft:any_of`、worldgen `any_of`、advancement `requirements`は同名でも同じcodecではありません
- `execute if predicate`で成功したconditionが、loot tableやenchantmentでも同じcontextを得るとは限りません
- `reference`は不足contextを補いません
- selectorの `predicate=` は対象entityごとに評価されますが、selectorの全条件をJSONへ移せる万能selectorではありません
- `nbt`部分一致とcomponent完全一致は同じ比較ではありません
- item `components`の空objectは全default component削除を意味しません
- `items`や`blocks`の`#tag`はregistry tagであり、旧item NBTの`tag`やentity `/tag`とは別物です
- locationの`light`とdimensionの`ambient_light`は別の値です
- block predicateはblock typeの追加機能ではありません
- unknown fieldの無視を互換性戦略に使えません。特に26.2 entity predicateはunknown keyを拒否します
- JSONのparse成功は、context適合とgameplay結果の確認を代替しません

## 検証

### 1. 対象バージョンのregistry IDを列挙

```bash
python3 tools/datapack_harness.py reports 26.2 \
  --cache-dir .cache/minecraft \
  --output build/minecraft/26.2/generated \
  --java /path/to/java
```

loot condition type:

```bash
jq -r \
  '."minecraft:loot_condition_type".entries | keys[]' \
  build/minecraft/26.2/generated/reports/registries.json
```

entity sub-predicate type:

```bash
jq -r \
  '."minecraft:entity_sub_predicate_type".entries | keys[]' \
  build/minecraft/26.2/generated/reports/registries.json
```

item/data component predicate type:

```bash
jq -r \
  '."minecraft:data_component_predicate_type".entries | keys[]' \
  build/minecraft/26.2/generated/reports/registries.json
```

worldgen block predicate type:

```bash
jq -r \
  '."minecraft:block_predicate_type".entries | keys[]' \
  build/minecraft/26.2/generated/reports/registries.json
```

1.20.5や1.21ではitem側registry名が `minecraft:item_sub_predicate_type` です。後年のregistry名を古いJARへ固定適用しません。

### 2. loadとfalseを区別

```mcfunction
reload
execute if predicate example:test run say matched
execute unless predicate example:test run say not_matched
```

- load error: folder、JSON、condition ID、field type、参照ID等の問題
- `not_matched`: 正常に評価されてfalse、または必要contextが得られない可能性
- matched: その時点のcommand contextでtrue

server logにはresource load時のcodec error、unknown field、context validation errorを含めて確認します。

### 3. 利用場所ごとに発火

同じ判定を利用する全contextで個別に確認します。

```text
[ ] execute if/unless predicate
[ ] selector predicate=
[ ] 実際のloot table type
[ ] advancement trigger
[ ] enchantment requirements/effect
[ ] item predicateを使うcommand・loot function
[ ] multiplayerでのexecutor/対象entity差
[ ] dimension、origin、chunk load差
```

random conditionは1回の成功だけで判定せず、固定条件へ一時置換するか十分な試行数と乱数設計を用います。

## 出典

- [Mojang: Java Edition 1.14](https://www.minecraft.net/en-us/article/village---pillage-out-java-) — loot context、condition、entity predicate
- [Mojang: Java Edition 1.15](https://www.minecraft.net/en-us/article/buzzy-bees-out-now-in-java) — 独立predicate、`reference`、entity/location/item拡張
- [Mojang: Java Edition 1.16](https://www.minecraft.net/en-us/article/nether-update-java) — top-level array、advancement entity check
- [Mojang: Java Edition 1.17](https://feedback.minecraft.net/hc/en-us/articles/4402626897165-Minecraft-Caves-Cliffs-Part-1-1-17-Java) — item/block predicateの複数形化
- [Mojang: Java Edition 1.19](https://feedback.minecraft.net/hc/en-us/articles/6731464524941-Minecraft-Java-Edition-1-19) — location/entity predicate変更
- [Mojang: Java Edition 1.19.3](https://feedback.minecraft.net/hc/en-us/articles/11280166737293-Minecraft-Java-Edition-1-19-3) — entity sub-predicate追加
- [Mojang: Java Edition 1.19.4](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-19-4) — damage source predicate
- [Mojang: Java Edition 1.20](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20) — condition合成とadvancement変更
- [Mojang: Java Edition 1.20.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-2) — inline condition、state property
- [Mojang: Java Edition 1.20.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-5) — item component predicate、entity/location/block predicate
- [Mojang: Java Edition 1.21](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21) — 単数形folder、enchantment condition
- [Mojang: Java Edition 1.21.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-5) — entity/block component predicate
- [Mojang: Java Edition 1.21.6](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-6) — strict JSON
- [Mojang: Java Edition 1.21.11](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-11) — component存在predicate
- [Mojang: Java Edition 26.1](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-1) — trade等のinline predicate
- [Mojang: Java Edition 26.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-2) — entity predicate component-map、unknown key拒否
- [Minecraft Wiki: Predicate](https://minecraft.wiki/w/Predicate) — condition resourceと利用箇所のcross-check
- [Minecraft Wiki: Entity predicate](https://minecraft.wiki/w/Entity_predicate) — entity fieldのcross-check
- [Minecraft Wiki: Item predicate](https://minecraft.wiki/w/Item_predicate) — item fieldのcross-check
- [Minecraft Wiki: Location predicate](https://minecraft.wiki/w/Location_predicate) — location/block/fluid fieldのcross-check
