# item stack・data component パラメータ

この文書は Java Edition 1.13〜26.2 の item 系データについて、用語、値の文脈、主要parameter、バージョン境界、検証手順を整理します。全 item ID と全 component codec を Markdown に固定して複製するものではありません。存在する ID、item ごとの既定値、実際に読み込める field は、対象バージョンの公式 server JAR が生成する report、vanilla data、対象 server の reload 結果を正本とします。

## 用語区分

| 用語 | 意味 | 例 | データパックで新規追加できるか |
|---|---|---|---|
| item type / item ID | item の種類。レジストリにある namespaced ID | `minecraft:stick` | 1.13〜26.2 の通常のデータパックでは新しい item type は追加できない |
| item stack | item type、個数、その stack 固有データを合わせた値 | stick 3個、独自名付き sword 1個 | 既存 item type から作成・変更できる |
| item component | 1.20.5 以降に stack の性質を型付きで表す値 | `minecraft:damage`, `minecraft:food` | 既存 component typeをstackへ付加・上書き・削除できる |
| item predicate | item stack が条件に合うかを判定する値 | 「damageが0」「custom_dataの一部が一致」 | JSON、`clear`、`execute if items` 等で使える |
| ingredient | recipe の入力として許容する item type/tag の集合 | `minecraft:stick`, `#minecraft:planks` | recipe JSON に記述できるが、component付きstackそのものとは別型 |

「custom item」は通常、vanilla の item ID に `custom_data`、名前、model、使用動作等を付けた item stackです。新しいIDを item registryへ登録したことにはなりません。同じ `minecraft:stick` を基底にしたcustom item同士は、componentsが違うstackとして扱われます。

また、1.21.2以降の`minecraft:item_model`はstackに入るdata componentです。参照先のitem modelはリソースパック側の資源であり、data packだけで画像やmodelを追加するものではありません。

## 同じ値でも書式の文脈が違う

item stackの概念は複数の場所に現れますが、外側の文法と許可される省略形は同一ではありません。

| 場所 | 外側の文法 | 例 | 注意 |
|---|---|---|---|
| `.mcfunction` の item argument | Brigadier item構文。component値はSNBT | `minecraft:stick[minecraft:custom_data={example:1b}]` | JSONではない。`1b`、single quote等のSNBT表現を取り得る |
| entity/block/storageの保存値 | NBT / SNBT | `{id:"minecraft:stick",count:1,components:{...}}` | 1.20.5境界でkeyと型が変わる |
| recipe、advancement icon等 | JSON | `{"id":"minecraft:stick","count":1,"components":{...}}` | コメント、末尾カンマ、数値suffixは不可 |
| loot function | JSONのcomponent patch | `"components":{"minecraft:damage":0}` | functionごとのfieldが必要 |
| item predicate JSON | 条件object | `{"items":"minecraft:stick","components":{...},"predicates":{...}}` | stack生成値ではない |
| recipe ingredient | item/tag/list | 1.21.2以降: `"minecraft:stick"` | component patchやcountを受けるitem stack型ではない。1.21.1以前はobject形式 |

ある場所で `{id,count,components}` が通っても、別の場所が同じ完全形を受けるとは限りません。対象バージョンの同じdata type・同じ`type`を持つvanilla JSONを基底にしてください。

## バージョン境界

| バージョン | item 系の確定境界 |
|---|---|
| 1.13〜1.16.5 | Flattening後のnamespaced item IDを使う。stack固有データは旧`tag` NBT。数値ID・metadataを使わない |
| 1.17〜1.20.4 | `/replaceitem`を削除し`/item`と`item_modifier`を追加。item stack自体はまだ旧NBT形式 |
| 1.20.5〜1.20.6 | 旧item `tag`をstructured data componentsへ全面移行。保存形を`id`, `count`, `components`へ変更。recipe resultもcomponent対応 |
| 1.21〜1.21.1 | data directoryを原則単数形へ変更。component削除patch `!component`、attribute形式等を更新 |
| 1.21.2〜1.21.4 | 使用・装備・model・修理等のcomponentを大幅追加。`food`と`consumable`を分離。`fire_resistant`を`damage_resistant`へrename。ingredientを文字列/`#tag`へ簡略化 |
| 1.21.5〜1.21.8 | text componentのSNBT境界。tooltip制御を`tooltip_display`へ集約し、複数componentを簡略形へ固定。`weapon`、`blocks_attacks`等を追加 |
| 1.21.9〜1.21.10 | `profile`のstatic/dynamic semanticsを更新。対象JARの一覧を再取得する |
| 1.21.11 | component存在predicate、item sprite atlas等を更新 |
| 26.1〜26.1.2 | recipe `result`を短縮IDまたは共通item stackへ統一。default component reportをitemごとのfileへ変更 |
| 26.2 | `sulfur_cube_content`等を追加。item component predicate typeも増加。26.1の一覧を固定利用しない |

patchリリースでも新機能を先取りしません。例えば1.20.6は1.20.5形式、1.21.3は1.21.2形式を継承しますが、1.21.5の`tooltip_display`を前倒ししません。

## 1.13〜1.20.4: 旧 item NBT

### 保存形

代表的な保存値は次の形です。

```snbt
{id:"minecraft:diamond_sword",Count:1b,tag:{Damage:5,display:{Name:'{"text":"古い形式"}'}}}
```

| key | 型 | 必須性 | 意味 |
|---|---|---|---|
| `id` | namespaced item ID | 非empty stackで必須 | item type |
| `Count` | byte | 保存文脈で必要 | stack個数 |
| `tag` | compound | 任意 | 旧形式のstack固有NBT |

コマンドのitem argumentでは外側の保存形を書かず、item IDの直後へ旧tagを書きます。

```mcfunction
give @s minecraft:diamond_sword{Damage:5} 1
```

`tag`内は自由形式に見えますが、vanillaがゲーム上の意味を与えるkeyには正しい名前・型が必要です。未知keyをcustom markerとして保存する手法も使われていました。1.20.5以降、その用途は`minecraft:custom_data`へ移します。

### 主な旧NBTからcomponentへの対応

| 1.20.4以前 | 1.20.5以降の主な移行先 |
|---|---|
| 任意のcustom tag | `minecraft:custom_data` |
| `Damage` | `minecraft:damage` |
| `RepairCost` | `minecraft:repair_cost` |
| `Unbreakable` | `minecraft:unbreakable` |
| `Enchantments` | `minecraft:enchantments` |
| `StoredEnchantments` | `minecraft:stored_enchantments` |
| `display.Name` | `minecraft:custom_name` |
| `display.Lore` | `minecraft:lore` |
| `display.color` | `minecraft:dyed_color` |
| `CustomModelData` | `minecraft:custom_model_data` |
| `CanDestroy` / `CanPlaceOn` | `minecraft:can_break` / `minecraft:can_place_on` |
| `AttributeModifiers` | `minecraft:attribute_modifiers` |
| `BlockEntityTag` | 専用component群と`minecraft:block_entity_data`へ分割 |
| `EntityTag` | `minecraft:entity_data` |
| `HideFlags` | component別tooltip設定、1.21.5以降は`minecraft:tooltip_display` |

これは単純なkey rename表ではありません。値の構造、既定値、許容範囲も変わるため、文字列置換だけで移行しないでください。

## 1.20.5以降: item type既定値 + stack component patch

### 基本モデル

各item typeは既定component集合を持ち、個々のstackの`components`はその既定値へのpatchです。

```text
最終的なstackの性質
  = item IDが持つ既定components
  + stackで追加・上書きしたcomponents
  - stackで明示削除した既定components
```

そのため、保存値に`minecraft:max_stack_size`が見えなくても、そのstackの最大個数が未定義という意味ではありません。item IDの既定値が使われます。反対に、componentを既定値と同じ値へ戻すと、差分として保存されない場合があります。

### JSON文脈のitem stack

1.20.5以降にitem stack codecを取るJSON fieldの基本形です。entity、block、storage等へ保存された値を表す場合は、同じ論理構造をNBT/SNBTで記述します。

```json
{
  "id": "minecraft:stick",
  "count": 3,
  "components": {
    "minecraft:custom_data": {
      "example": {
        "kind": "cave_lamp"
      }
    }
  }
}
```

| key | 型 | 必須性 | 意味 |
|---|---|---|---|
| `id` | namespaced item ID | 非empty stackで必須 | 基底item type |
| `count` | integer | 入力時は任意、既定`1`。ゲームの保存時は常に出力 | stack個数。旧`Count` byteではない |
| `components` | component IDから値へのmap | 任意 | 既定componentに対する追加・上書き・削除patch |

空stackは`minecraft:air`や`count:0`のitem stackで表さず、そのfield自体を省略するか、その文脈が要求する空objectを使います。

### command item argument

```mcfunction
give @s minecraft:stick[minecraft:custom_data={example:{kind:"cave_lamp"}}] 3
give @s minecraft:diamond_pickaxe[minecraft:damage=12,minecraft:repair_cost=2] 1
```

- componentはitem ID直後の`[...]`にcomma区切りで書く
- 値はcomponentごとのcodecでparseされる。未知field、不正な型、範囲外の値は拒否され得る
- 任意dataは`custom_data`へ置き、既存gameplay機能は対応するtyped componentへ置く
- 保存形の`count`と、`give` command末尾の個数引数を混同しない

1.21以降のcommand item argumentでは、既定componentの削除patchに`!`を使います。1.20.5の保存item stackの`components` mapや`set_components` loot functionにも`!`付きcomponent IDによる削除がありますが、command item argumentでの`!`は1.21からです。

```mcfunction
give @s minecraft:diamond_pickaxe[!minecraft:tool]
```

### componentの「存在」と「既定値」

componentそのものは通常patch上では任意ですが、item typeが既定で持つ場合があります。また、一部componentは別componentを要求したり排他的です。

- `max_damage`は`damage`を必要とし、`max_stack_size`が1より大きい構成と両立しない
- `damage=0`を省略したdamageable itemでも、既定componentによりpredicate上は存在すると扱われる場合がある
- `{}`は「空の値を持つ存在component」であり、「componentなし」と同じではない。`glider={}`等は存在自体が機能を有効にする
- component削除は値を`null`にする操作ではない
- item IDを変えてもcomponentを保持するloot functionやtransmuteでは、新item typeとの組合せが妥当か別途検証する

## 主要componentパラメータ

以下は設計時の索引です。「必須」はそのcomponentを記述する場合の内部fieldを指します。component自体が全item stackで必須という意味ではありません。fieldの追加・rename・短縮形はバージョンごとに変わるため、表の「境界」より前後へコピーしません。

### 識別・表示

| component | 値 / 主なfield | 必須・既定 | ゲーム上の意味 | 境界・誤解 |
|---|---|---|---|---|
| `minecraft:custom_data` | 任意compound | 任意 | pack独自の識別子・状態 | 標準機能を発生させる万能componentではない。predicateでは部分一致と完全一致を区別 |
| `minecraft:custom_name` | text component | 任意 | 金床名相当の名前override | 1.20.5ではcommand例がJSON chat component文字列、1.21.5以降のcommand文脈はSNBT text component |
| `minecraft:item_name` | text component | item typeに既定あり | itemの基礎名 | 1.21.2以降全itemに存在し、優先度は低い。`custom_name`と役割が違う |
| `minecraft:lore` | text componentのlist | 任意、既定空listの場合あり | tooltipの追加行 | 1.21.5 text/SNBT境界を適用。list全体の上限もcodecで検証 |
| `minecraft:rarity` | `common`等のenum | item typeに既定あり | 名前色等のrarity | loot確率そのものではない |
| `minecraft:enchantment_glint_override` | boolean | 任意 | glint表示を強制on/off | enchantmentを付与するcomponentではない |
| `minecraft:custom_model_data` | バージョン依存の数値/構造 | 任意 | resource packのmodel選択用data | model本体はresource pack。対象バージョンのresource pack形式も必要 |
| `minecraft:item_model` | namespaced ID | 1.21.2で全itemに既定 | item model参照 | data packだけではmodelを提供しない。参照pathの方式はresource packバージョンにも依存 |
| `minecraft:tooltip_style` | namespaced ID | 任意 | tooltip背景・frameのsprite参照 | spriteはresource pack側 |
| `minecraft:tooltip_display` | `{hide_tooltip?,hidden_components?}` | 1.21.5以降。両fieldに既定あり | tooltip全体またはcomponent由来行を隠す | gameplay componentを消すのではなく表示だけを抑制 |

1.21.5では旧`hide_tooltip`、`hide_additional_tooltip` componentと、各component内の`show_in_tooltip`を`tooltip_display`へ移します。同時に次のような値が簡略形へ固定されました。

```snbt
# 1.21.4以前の代表形
minecraft:enchantments={levels:{"minecraft:sharpness":2},show_in_tooltip:false}

# 1.21.5以降
minecraft:enchantments={"minecraft:sharpness":2},
minecraft:tooltip_display={hidden_components:["minecraft:enchantments"]}
```

`attribute_modifiers`は`{modifiers:[...]}`からlist直書き、`dyed_color`は`{rgb:...}`から色値直書き、`can_break`/`can_place_on`は`{predicates:[...]}`からpredicateまたはlist直書きへ移りました。

### 個数・耐久・強化

| component | 値 / 主なfield | 必須・既定 | ゲーム上の意味 | 制約 |
|---|---|---|---|---|
| `minecraft:max_stack_size` | integer | item typeに既定、1.20.5では`1..99` | stack可能な最大個数 | `max_damage`との排他を確認 |
| `minecraft:max_damage` | positive integer | damageable itemに既定 | 最大耐久 | `damage`が必要 |
| `minecraft:damage` | non-negative integer | damageable itemで既定0 | 失った耐久。残耐久ではない | `max_damage - damage`が残耐久 |
| `minecraft:unbreakable` | `{}`またはバージョン依存object | 任意 | 使用による耐久減少を防ぐ | 1.21.5で`show_in_tooltip`を削除 |
| `minecraft:repair_cost` | non-negative integer | 既定0の場合あり | 金床の追加cost | repair素材の指定ではない |
| `minecraft:repairable` | `{items:<item/list/#tag>}` | `items`必須 | 金床で修理できる素材 | 1.21.2追加。itemがdamageableであることも必要 |
| `minecraft:enchantable` | `{value:<positive integer>}` | `value`必須 | enchant tableで選択される強さ | enchantmentそのものは付与しない |
| `minecraft:enchantments` | enchantment ID→level map | 既定空mapの場合あり | stackへ実際に作用するenchantment | 1.21.5で`levels` wrapperを常にinline化 |
| `minecraft:stored_enchantments` | enchantment ID→level map | enchanted bookに既定 | 保存enchantment | stackへ直接効果を与える`enchantments`と違う |
| `minecraft:attribute_modifiers` | modifierのlist | 既定空listの場合あり | 装備/保持中のattribute補正 | attribute ID、operation、slot形式はバージョン境界あり。1.21.5でlist直書き |

耐久12消費を指定する例です。

```mcfunction
give @s minecraft:diamond_pickaxe[minecraft:damage=12]
```

これは「残り耐久12」ではありません。残り耐久の範囲判定はitem sub-predicateの`damage`/`durability`を使います。

### 使用・食料・装備・戦闘

| component | 値 / 主なfield | 必須・既定 | ゲーム上の意味 | 境界 |
|---|---|---|---|---|
| `minecraft:food` | `nutrition`, `saturation`, `can_always_eat?` | 前2field必須 | 消費時の空腹・飽和data | 1.20.5では食べる動作も含んだ。1.21.2以降は`consumable`も必要 |
| `minecraft:consumable` | `consume_seconds?`, `animation?`, `sound?`, `has_consume_particles?`, `on_consume_effects?` | fieldは既定あり | 使用でitemを消費する動作と副作用 | 1.21.2追加。`food`がなくても消費可能 |
| `minecraft:use_remainder` | item stack | component値として必須 | 消費後に残すitem | 1.21.2追加。stack内の再帰的componentにも注意 |
| `minecraft:use_cooldown` | `seconds`, `cooldown_group?` | `seconds`必須 | 使用後cooldown | 同groupのitemへ共有可能 |
| `minecraft:equippable` | `slot`, `equip_sound?`, model/asset参照、`allowed_entities?`, flags | `slot`必須 | 指定slotへ装備可能にする | 1.21.2追加。field名は後続バージョンで変わり得る。1.21.5で`saddle`や`equip_on_interact` |
| `minecraft:glider` | `{}` | componentの存在が条件 | 装備中の滑空 | 装備slotを自動指定しないため`equippable`との組合せを検証 |
| `minecraft:death_protection` | `death_effects?` | field任意 | 手に持つitemが致死damageから保護 | 1.21.2追加。totemの見た目やcustom modelとは別 |
| `minecraft:weapon` | `item_damage_per_attack?`, `disable_blocking_for_seconds?` | fieldに既定あり | 攻撃時の統計・耐久消費・blocking無効化 | 1.21.5追加 |
| `minecraft:blocks_attacks` | delay、damage reduction、item damage、sound等 | 多くは任意、内側entryに必須fieldあり | shield型blocking | 1.21.5追加。単なる使用animationではない |
| `minecraft:tool` | `rules`, `damage_per_block?`, `can_destroy_blocks_in_creative?` | `rules`を中心にバージョン依存 | 採掘速度・適正drop・block破壊時耐久 | Adventure modeの`can_break`とは別 |

1.21.2以降、食料dataだけでは使用できません。

```mcfunction
give @s minecraft:stick[minecraft:food={nutrition:4,saturation:2.4},minecraft:consumable={}]
```

`consumable.on_consume_effects`の1.21.2時点の主な`type`は`apply_effects`、`remove_effects`、`clear_all_effects`、`teleport_randomly`、`play_sound`です。後続バージョンでeffect typeや配置が変わる可能性があるため、最新例を1.21.2へ逆輸入しません。

### 内容物・配置・entity

| component | 値 / 主なfield | 意味 | 注意 |
|---|---|---|---|
| `minecraft:bundle_contents` | item stackのlist | bundle内部 | 入れ子stackにも対象バージョンの形式を使う |
| `minecraft:container` | `{slot,item}`相当entryのlist | chest/shulker等の内容 | blockへ置いた時のcopy挙動とloot tableによるdrop復元を別に確認 |
| `minecraft:container_loot` | `loot_table`, `seed?` | 未展開loot table | `container`の確定内容と同じではない |
| `minecraft:charged_projectiles` | item stackのlist | crossbowの装填内容 | 対応item以外でのgameplay効果を推測しない |
| `minecraft:can_break` | block predicateまたはlist | Adventure modeで破壊可能 | `tool`の採掘性能とは別。1.21.5形を古いバージョンへ使わない |
| `minecraft:can_place_on` | block predicateまたはlist | Adventure modeで設置可能 | 通常modeの設置許可ではない |
| `minecraft:block_state` | property名→string値 | block item設置時のstate | 数値/booleanに見えるstate値もstring |
| `minecraft:block_entity_data` | `id`を含むcompound | 設置先block entityへ適用する未構造化data | operator制限があるblock type、専用componentへ分離済みfieldがある |
| `minecraft:entity_data` | `id`を含むcompound | spawn item等からentityへ適用するdata | 1.21.4以降は実体typeと`id`一致を要求 |
| variant component群 | registry IDやenum | spawnされるentityのvariant等 | 1.21.5で多数追加。component名、値がregistry参照かinlineかをJARで確認 |

`block_entity_data`へblock stateを書く、`block_state`へinventoryを書く、といった境界越えはしません。block state、block entity NBT、item componentは別の層です。

### potion・book・map等の専用component

`potion_contents`、`suspicious_stew_effects`、`writable_book_content`、`written_book_content`、`firework_explosion`、`fireworks`、`map_id`、`map_decorations`、`profile`、`trim`、`banner_patterns`等は、それぞれ独立したcodecを持ちます。

- potion effect instanceのdefault省略やtext component形式はバージョン境界を受ける
- written bookとwritable bookは同じpage形式とは限らない
- `profile`は1.21.9で自動resolve/書換のsemanticsが変更された
- `trim`、variant等のregistry参照は、対象versionの`registries.json`とvanilla dataで存在を確認する
- 専用componentが存在するからといって、任意の基底itemでvanillaと同じ操作・UIが必ず発生するとは限らない

これらの完全な内部fieldは、目的と同じcomponentを既定で持つitemのreport、同componentを書くvanilla loot/recipe、公式release noteを選んで確認します。

## 1.21.2の大きな意味変更

### `food`と`consumable`

1.20.5の`food`は食べる動作まで有効化しました。1.21.2では役割を分けます。

```text
food        = 消費された時に適用するnutrition/saturation
consumable  = 使用して消費できること、時間、animation、sound、副作用
```

したがって1.20.5用custom foodを1.21.2へ移すときは、`food`を残すだけでなく`consumable`を追加します。

### `fire_resistant`から`damage_resistant`

1.21.2では`minecraft:fire_resistant`を`minecraft:damage_resistant`へ置換し、`types`へdamage type tagを指定します。これはground item entityが対象damageへ耐える性質に加え、装備品が着用者の被damage時に傷むかにも影響します。表示上「火に強そう」にするcomponentではありません。

### recipe ingredient

```json
{
  "key": {
    "#": "minecraft:stick",
    "X": "#minecraft:planks"
  }
}
```

1.21.2以降はitemを文字列、tagを`#`付き文字列で書きます。1.21.1以前の`{"item":"..."}`、`{"tag":"..."}` objectを混在させません。itemのlistは残りますが、そのlistへtagを入れられない等の制約があります。

## recipe・loot・predicateとの接続

### recipe result

1.20.5で、crafting、stonecutting、smithing transform等のresultがcomponentsを受けられるようになり、smelting系resultもobject化されました。

```json
{
  "type": "minecraft:crafting_shapeless",
  "ingredients": [
    "minecraft:stick"
  ],
  "result": {
    "id": "minecraft:stick",
    "count": 1,
    "components": {
      "minecraft:custom_data": {
        "example": {
          "kind": "token"
        }
      }
    }
  }
}
```

このingredientの文字列形は1.21.2以降の例です。1.20.5用なら同versionのvanilla recipeが使うingredient object形へ戻します。

26.1では`result` fieldを持つrecipe type間でitem stack表現を統一し、次の短縮形も許可します。

```json
{
  "type": "minecraft:crafting_shapeless",
  "ingredients": [
    "minecraft:stick"
  ],
  "result": "minecraft:stick"
}
```

この`result`値は`{"id":"minecraft:stick","count":1}`と同等です。smelting、blasting、smoking、campfire cookingも`count`を受けられるようになりました。26.1の短縮形・count対応を1.21.xへ逆輸入しません。

`crafting_transmute`等は入力stackのcomponentsを結果へ引き継ぎ、最後にresultのcomponentsを適用します。通常のrecipeが常に入力componentsを引き継ぐとは考えないでください。

### loot function

1.20.5の主な移行は次です。

| 旧loot function / 目的 | component以降 |
|---|---|
| `set_nbt` | `set_custom_data` |
| `copy_nbt` | `copy_custom_data` |
| componentを追加・上書き・削除 | `set_components` |
| block entityからcomponentをcopy | `copy_components` |
| container/bundle/projectile内のitemを変更 | `modify_contents` |
| item typeだけ変更 | `set_item` |

`set_custom_data`は`custom_data`だけを扱います。`damage`、`food`、`equippable`等の標準componentをcustom compoundへ書いても、その標準機能にはなりません。

### item predicate JSON

1.20.5以降の概念上の形です。

```json
{
  "items": "minecraft:diamond_pickaxe",
  "components": {
    "minecraft:damage": 0
  },
  "predicates": {
    "minecraft:custom_data": {
      "example": {
        "kind": "miner"
      }
    }
  }
}
```

- `components`は指定componentの値を完全一致させる。追加componentの存在は許容される
- `predicates`はcomponent専用の部分条件・range・collection matcher等を使う
- `custom_data`は完全一致とNBT部分一致を使い分ける
- `count`はstackのcomponentではなく、predicate側の特別な条件
- componentが存在しないitemは、そのcomponentを要求するsub-predicateに一致しない。ただしitem typeの既定componentも存在判定に含まれる

commandのitem predicateでは次のoperatorを区別します。

```mcfunction
# exact component value
clear @s minecraft:diamond_pickaxe[minecraft:damage=0] 0

# component sub-predicate: 残耐久3以上
clear @s *[minecraft:damage~{durability:{min:3}}] 0

# custom_dataの部分一致
clear @s minecraft:stick[minecraft:custom_data~{example:{kind:"token"}}] 0
```

`=`は完全値、`~`はsub-predicateです。存在test、`!`による否定、`|`による選択、`count=`/`count~`も1.20.5で追加されました。JSON predicateとcommand predicateは役割を共有しますが、外側の文法はJSONとSNBTで異なります。

## よくある誤解

- `custom_data`へ`night_vision:1b`と書くだけではnight vision機能にならない。pack側のpredicate/command等がそのmarkerを読み、処理を実装する必要がある
- `item_model`を設定してもresource packなしで新しいtexture/modelは現れない
- `enchantment_glint_override=true`はenchantment効果を追加しない
- `food`、`consumable`、consume effect、status effectは同じ層ではない
- `max_damage`を付けるだけで、全行動時に自動で耐久が減るとは限らない。`tool`、`weapon`、`equippable.damage_on_hurt`等の消費契機も確認する
- `count`は通常data componentではない。stack field、command引数、predicate特別条件の各文脈で扱う
- `components:{}`は「そのitemの全既定componentを削除」ではない。空patchである
- item tag `#minecraft:...`はitemの分類集合であり、旧item stackの`tag` NBTとは無関係
- recipe ingredientはitem predicateではないため、任意component条件をそのまま書けるとは限らない
- `/data`でplayer entity NBTを直接変更できない。player inventoryは`/item`、loot、`give`等の対応経路を使う
- world upgrade時にitemがDataFixされても、pack内のcommand・JSONは自動変換されない
- unknown component/fieldが無視されると期待しない。structured componentはparse時に検証される

## 対象バージョンの完全一覧を得る

### 1. reportを生成

```bash
python3 tools/datapack_harness.py reports 1.21.5 \
  --cache-dir .cache/minecraft \
  --output build/minecraft/1.21.5/generated \
  --java /path/to/java
```

公式manifestのrelease ID完全一致、server JARのSHA-1、必要Java majorを固定します。

### 2. component type IDを列挙

```bash
jq -r \
  '."minecraft:data_component_type".entries | keys[]' \
  build/minecraft/1.21.5/generated/reports/registries.json
```

component predicate typeがregistry化されているバージョンでは次も確認します。

```bash
jq -r \
  '."minecraft:data_component_predicate_type".entries | keys[]' \
  build/minecraft/1.21.5/generated/reports/registries.json
```

`registries.json`で分かるのは主にIDの存在です。component内部の全field、必須性、相互制約まで保証するJSON Schemaではありません。

このrepositoryで対象JARから生成済みのcatalogがある場合は、正規化された完全ID一覧も利用できます。

```bash
jq -r \
  '.registry_ids.item_component_types[]' \
  build/minecraft/1.21.5/json-catalog.json
```

`observed_shapes.item_defaults.fields`はvanilla既定値で実際に観測したpathとJSON型です。vanillaで使われなかったoptional fieldや、許容される別表現を含む完全codec schemaではありません。

### 3. item typeの既定componentを確認

1.20.5〜1.21.xの生成物では、まず次を確認します。

```bash
jq '."minecraft:iron_sword"' \
  build/minecraft/1.21.5/generated/reports/items.json
```

26.1以降はdefault component reportがitemごとのfileへ変更されています。

```bash
jq . \
  build/minecraft/26.2/generated/reports/minecraft/components/item/iron_sword.json
```

reportのpath・形は固定せず、そのversionの生成結果を確認します。既定値だけでcomponent codecの全分岐は分からないため、目的のfieldを使う公式release noteとvanilla dataも併用します。

### 4. 今回の生成物で観測したcoverage

公式JARから生成した`data_component_type` registry entry数は次でした。

| バージョン | component type数 | default component report |
|---|---:|---|
| 1.20.5 | 56 | `generated/reports/items.json` |
| 1.21 | 57 | `generated/reports/items.json` |
| 1.21.5 | 96 | `generated/reports/items.json` |
| 1.21.11 | 104 | `generated/reports/items.json` |
| 26.2 | 111 | `generated/reports/<namespace>/components/item/<path>.json` |

これは「このページが111種類の全fieldを網羅した」という意味ではありません。対象JARから完全なID集合を取得できたというcoverageです。26.2のitem別default component reportは1537 fileでした。今回の生成物では`data_component_predicate_type`は1.21.5と1.21.11で14、26.2で15 entryを観測しました。1.20.5と1.21ではこの名前のregistry自体がreportにないため、後年のregistry構造を過去バージョンへ当てはめません。

### 5. codecと動作を検証

1. 同じcomponentまたは同じrecipe/loot typeを使うvanilla fileを探す
2. 公式release noteのfield、型、default、範囲を照合する
3. `jq empty`でJSON文法を検査する
4. `validate-pack`でdirectory、既知ID、静的境界を検査する
5. exact release serverで起動・`/reload`しcodec errorを確認する
6. `give`、`clear ... 0`、`execute if items`、recipe、lootを実際に発火する
7. client表示、消費、装備、耐久、multiplayer同期等のgameplay結果を確認する

```bash
python3 tools/datapack_harness.py validate-pack \
  1.21.5 path/to/pack \
  --reports build/minecraft/1.21.5/generated
```

静的検査はMinecraftの全codecを再実装しません。reload成功は構文・参照の重要な確認ですが、消費時間、装備slot、攻撃時耐久、model表示等の動作保証には機能testが必要です。

## 出典

- [Mojang: Java Edition 1.20.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-5) — item component全面移行、保存形、command predicate、loot/recipe変更
- [Mojang: Java Edition 1.21](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21) — component削除patch、attribute・directory境界
- [Mojang: Java Edition 1.21.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-2) — `food`分離、使用・装備component、ingredient変更
- [Mojang: Java Edition 1.21.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-5) — tooltip、text/SNBT、weapon/blocking、component簡略形
- [Mojang: Java Edition 1.21.9](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-9) — `profile` semantics等
- [Mojang: Java Edition 26.1](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-1) — recipe result統一、default component report変更
- [Mojang: Java Edition 26.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-2) — 26.2 component/registry追加
- 対象バージョンの公式server JARが生成する`registries.json`、default component report、`generated/data/minecraft/`
- [Minecraft Wiki: Data component format](https://minecraft.wiki/w/Data_component_format) — cross-check
- [Minecraft Wiki: Item format](https://minecraft.wiki/w/Item_format) — cross-check
