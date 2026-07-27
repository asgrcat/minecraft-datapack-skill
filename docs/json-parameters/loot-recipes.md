# loot table・item modifier・recipe パラメータ

この文書は Java Edition 1.13〜26.2 の loot table、item modifier、recipe を、JSON の階層、値の意味、実行context、バージョン境界から選ぶためのリファレンスです。全 loot condition/function、number provider、recipe serializer の完全な codec を Markdown に固定して複製するものではありません。対象の正式リリースの Mojang server JAR が生成する vanilla data、registry report、実際の reload 結果を機械的な正本とします。

## 先に区別するもの

| resource | 役割 | 自動的に起きること | 起きないこと |
|---|---|---|---|
| loot table | contextから0個以上のitem stackを生成する | block、entity、container等がそのIDを参照した時、または`/loot`等で呼ばれた時に評価される | 任意のpathへ置いただけでは新しいeventを追加しない |
| predicate | loot conditionを独立resourceとして再利用する | 参照された時にtrue/falseを返す | lootを生成しない |
| item modifier | 既にあるitem stackへloot functionを順に適用する | `/item modify`、loot function `reference`等から参照された時にstackを変更する | itemを新規生成せず、recipeにも自動適用されない |
| recipe | serializerが定める入力と出力を登録する | crafting、cooking、stonecutting、smithing等の対応UIで照合される | 新item IDや任意のscript処理を登録しない |
| advancement | recipeのunlockやcrafted eventを扱える | 条件成立時にreward/functionを実行できる | recipe JSON自身の一部ではない |

loot tableの`functions`とitem modifierは同じloot function codecを使いますが、利用できるcontext parameterは呼出場所で変わります。recipeの`ingredient`は通常item ID/tagの集合であり、loot conditionのitem predicateとは別の型です。

## 保存場所

| バージョン | loot table | item modifier | recipe |
|---|---|---|---|
| 1.13〜1.16.5 | `data/<namespace>/loot_tables/<path>.json` | 未対応 | `data/<namespace>/recipes/<path>.json` |
| 1.17〜1.20.6 | `data/<namespace>/loot_tables/<path>.json` | `data/<namespace>/item_modifiers/<path>.json` | `data/<namespace>/recipes/<path>.json` |
| 1.21〜26.2 | `data/<namespace>/loot_table/<path>.json` | `data/<namespace>/item_modifier/<path>.json` | `data/<namespace>/recipe/<path>.json` |

1.21の単数形renameはファイル内容の自動変換ではありません。複数バージョン対応では、1.20.6以前と1.21以降のdirectory treeをoverlay等で分けます。

resource IDはfolder以下の相対pathです。例えば`data/example/loot_table/chests/reward.json`は`example:chests/reward`です。`chests`、`entities`、`blocks`等の中間folderは整理とvanilla hookのために意味を持つ場合がありますが、独自namespaceの任意loot tableを置くだけで同名のblock/entityへ接続されるわけではありません。

## loot tableの評価モデル

概念上の処理順は次です。

```text
loot tableを、実際の呼出元が作るloot contextで開始
  → rootのpoolsを上から評価
    → pool conditionsをすべて検査
    → rollsとbonus_rollsから試行回数を得る
    → entryを展開し、条件を満たす候補からweightで選ぶ
    → entry functionsを順に適用
    → pool functionsを順に適用
  → root functionsを順に適用
  → 0個以上のitem stackを呼出元へ返す
```

「`entries`の各要素を1回ずつ抽選する」のではありません。composite entryが子を候補へ展開し、その候補集合から各rollで1候補を選びます。同じ候補が複数rollで繰り返し選ばれることもあります。

### root

1.20.5以降にも通用する最小例です。1.21以降は保存folderだけを単数形へ変えます。

```json
{
  "type": "minecraft:chest",
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
              "count": {
                "type": "minecraft:uniform",
                "min": 1,
                "max": 3
              }
            }
          ]
        }
      ]
    }
  ]
}
```

| key | 型 | 必須性・既定 | 意味 | 境界・注意 |
|---|---|---|---|---|
| `type` | loot context type ID | 1.14以降は任意、通常は明示 | condition/function/providerが要求するcontext parameterを検証する契約 | `generic`または省略は、実行時に存在しないparameterを作らない |
| `pools` | pool objectの配列 | 任意、空ならlootなし | 上から順に評価する生成規則 | tableを空にして既存dropを抑止する用途と、参照漏れを区別する |
| `functions` | loot functionの配列 | 1.14以降任意 | 全poolが生成した各stackへ最後に順次適用 | item modifierと同じcodec。nested function listを推測しない |
| `random_sequence` | resource location | 1.20以降任意 | world seedから決まる名前付き乱数列を選ぶ | 固定結果を直接指定するseedではない |

root `type`はloot tableを呼ぶeventを選びません。`minecraft:block`と書いてもblockから自動dropせず、実際にblock lootとして呼ばれるID・参照が必要です。反対に、block contextで呼ぶtableへ`minecraft:chest`を指定すると、`tool`や`block_state`等の検証がずれます。

主なcontext typeは版ごとに増えます。代表例は`empty`、`chest`、`fishing`、`entity`、`equipment`、`block`、`advancement_reward`、`gift`、`barter`、`archaeology`、`shearing`です。1.21.9以降にはinteraction系、1.21.11のvanilla dataには`block_interact`と`entity_interact`も現れます。利用可能なIDとparameter集合は対象JARで確認します。

### pool

| key | 型 | 必須性・既定 | 意味 |
|---|---|---|---|
| `conditions` | loot conditionの配列 | 任意 | すべて成立した時だけpoolを評価する。暗黙のAND |
| `rolls` | integer number provider | 必須 | poolから選ぶ基本回数 |
| `bonus_rolls` | float number provider | 任意、従来の既定は0 | luckに比例して加える試行回数。乗算後の端数処理もcodec/runtimeに従う |
| `entries` | loot pool entryの配列 | 必須 | rollごとの候補を供給する |
| `functions` | loot functionの配列 | 1.14以降任意 | このpoolから生成された各stackへ順に適用 |

literal numberはconstant providerの短縮形として使える場所があります。

```json
{
  "rolls": {
    "type": "minecraft:uniform",
    "min": 1,
    "max": 3
  },
  "bonus_rolls": 0,
  "entries": []
}
```

number providerは同じようなobjectでも、整数を要求する`rolls`、浮動小数を許す確率・damage・enchantment level等でcodecが異なります。代表typeにはconstant、uniform、binomial、score、storage等がありますが、追加時期、field名、許容値は対象版のregistry/JARで決めます。

### entryの共通field

| key | 適用先 | 意味 |
|---|---|---|
| `type` | 全entry | entry type ID |
| `conditions` | entry | すべて成立した場合だけ候補を供給する |
| `functions` | itemを生成するentry | 生成stackへ順に適用 |
| `weight` | weighted singleton entry | 基本weight。多くのcodecで既定1 |
| `quality` | weighted singleton entry | luckによるweight補正。多くのcodecで既定0 |

`weight`は百分率ではありません。実際の確率は、そのrollで展開された全候補の有効weight、条件、luck、composite entryの結果に依存します。`weight: 10`を10%と扱わないでください。

### 主なsingleton entry

| `type` | 主なfield | 結果・注意 |
|---|---|---|
| `minecraft:item` | `name`: item ID | 指定itemのstackを候補へ追加。個数やcomponentはfunctionで変更 |
| `minecraft:tag` | `name`: item tag ID、`expand` | `expand:true`ならtag要素を個別のweighted候補として展開する。false側の生成単位は対象版で確認 |
| `minecraft:loot_table` | 参照先table | 別tableの結果を展開。1.18.2/1.19のvanillaは`name`、1.20.5以降のvanillaは`value`を使用 |
| `minecraft:dynamic` | `name` | 呼出元が提供するdynamic dropを得る。任意IDの保存領域ではない |
| `minecraft:empty` | 追加fieldなし | 「何も生成しない」候補。weightを持たせて外れを作れる |
| `minecraft:slots` | `slot_source` | 1.21.11追加。選択slot内のitemを候補へ供給 |

`minecraft:loot_table`の参照fieldのように、entry typeは同じでも版境界でfieldが変わります。最新例の`value`を1.19へ、旧例の`name`を1.20.5へ無条件で移さないでください。

1.21.11の`minecraft:slots`はslot source codecを使います。slot sourceはentity/block entity、slot range、filter、結合、item内contents等を表せますが、standalone registry resourceとは限りません。26.3以降の配置やtypeを26.2へ先取りしません。

### composite entry

| `type` | 主なfield | 評価 |
|---|---|---|
| `minecraft:alternatives` | `children` | 条件を満たす最初の子だけを展開 |
| `minecraft:sequence` | `children` | 子を順に展開し、実行できない子で停止 |
| `minecraft:group` | `children` | 自身の条件成立時、子をまとめて展開 |

これらのentry object自体と子entryの両方に条件があり得ます。`alternatives`はpoolのweight抽選と同じものではなく、順序に意味があります。先頭へ常に成立する子を置くと後続へ到達しません。

### condition

loot table、pool、entry、functionの`conditions`はloot condition objectの配列です。配列は原則としてすべて成立を要求します。ORは対象版の合成conditionを明示します。

```json
{
  "condition": "minecraft:any_of",
  "terms": [
    {
      "condition": "minecraft:killed_by_player"
    },
    {
      "condition": "minecraft:random_chance",
      "chance": 0.25
    }
  ]
}
```

| 分類 | 代表例 | 必要になり得るcontext |
|---|---|---|
| 確率 | `random_chance`, `table_bonus` | random、tool/enchantment |
| entity | `entity_properties`, `killed_by_player`, damage source系 | `this`、attacker、direct attacker等 |
| block/location | `block_state_property`, `location_check`, `survives_explosion` | block state、origin、explosion radius |
| item | `match_tool` | tool |
| 合成 | `inverted`, `any_of`, `all_of` | 子conditionが要求するparameterの和集合 |
| 再利用 | `reference` | predicate resourceと、その内部が要求するparameter |

1.20で旧`alternative` conditionを`any_of`へ移し、`all_of`も明示的な合成に使います。1.20.2では`all_of`のinline配列表現など周辺codecが変わるため、対象版vanilla例へ合わせます。

26.2ではcondition内に埋め込むentity predicateがcomponent-map形式へ変わります。

```json
{
  "condition": "minecraft:entity_properties",
  "entity": "this",
  "predicate": {
    "minecraft:entity_type": "minecraft:player"
  }
}
```

26.1.2以前の`{"type":"minecraft:player"}`や`type_specific` wrapperを26.2へ残しません。26.2は未知sub-predicate keyを拒否するため、typoが無視される前提にもできません。

### function

function objectは`function`でtypeを選び、そのtype固有fieldと任意の`conditions`を持ちます。

```json
{
  "function": "minecraft:set_count",
  "count": 2,
  "add": false,
  "conditions": [
    {
      "condition": "minecraft:random_chance",
      "chance": 0.5
    }
  ]
}
```

設計上は次の分類を分けます。

| 目的 | 代表type | 主な注意 |
|---|---|---|
| 個数・damage | `set_count`, `limit_count`, `set_damage` | literal/number provider、`add`、値域を対象版で確認 |
| enchant | `enchant_randomly`, `enchant_with_levels`, `set_enchantments` | tool/contextに依存するfunctionと、出力stackだけを変更するfunctionを区別 |
| 表示・component | `set_name`, `set_lore`, `set_components`, `copy_components` | text/component形式は1.20.5、1.21.5等の境界に従う |
| 内容物 | `set_contents`, `set_loot_table`, `modify_contents` | block entity typeやcontainer componentの版境界がある |
| NBT/custom data | `set_nbt`, `copy_nbt`、後続版の`set_custom_data`, `copy_custom_data` | 1.20.5で旧item NBT functionを移行 |
| 制御・再利用 | `reference`, `sequence`, `filtered`, `discard` | 子functionの順序、分岐、追加時期を確認 |

1.20.5ではitem stackのdata component化に合わせ、`set_nbt→set_custom_data`、`copy_nbt→copy_custom_data`へ移し、`set_components`、`copy_components`、`modify_contents`等を使います。`set_custom_data`は任意custom marker用です。既存の標準componentをcustom dataへ複製しても、その標準機能は有効になりません。

1.21.11では`minecraft:filtered`の旧`modifier`を次へ置換しました。

```json
{
  "function": "minecraft:filtered",
  "item_filter": {
    "items": "minecraft:iron_sword"
  },
  "on_pass": {
    "function": "minecraft:set_count",
    "count": 2
  },
  "on_fail": {
    "function": "minecraft:discard"
  }
}
```

`on_pass`と`on_fail`は単一functionまたはfunction listです。`minecraft:discard`は現在のstackをemptyへ置換し、追加fieldを持ちません。1.21.10以前の`modifier`と同居させません。

26.1では`enchant_randomly`と`enchant_with_levels`に任意の`include_additional_cost_component`が加わります。trade等のitem生成とも関係しますが、26.1以前へは出力しません。

### loot context

loot contextはJSONに保存された万能変数mapではなく、呼出元がその場で提供するparameter集合です。代表例には次があります。

| parameterの概念 | 供給される代表context |
|---|---|
| origin | chest、block、entity、fishing等 |
| this entity | entity drop、chestを開いたplayer、gift元等。意味はcontextで異なる |
| attacking/direct attacking entity | entity damage/drop |
| last damage player | player killに関連するentity drop |
| tool | block breaking、fishing等 |
| block state / block entity | block drop |
| damage source | entity death |
| explosion radius | explosionによるblock drop |
| luck | chest、fishing等、呼出経路により値が異なる |

`entity:"this"`は常にcommand executorという意味ではありません。`/loot`のsource、block/entityの自然drop、advancement reward、`/item modify`は異なるcontextを作ります。

root `type:"minecraft:generic"`または省略は、多くの版でload時のcontext検査を弱めます。実行時に`tool`、`block_state`、`this`等を補充する指定ではないため、警告を消す目的でgenericへ変更しないでください。

### `random_sequence`

1.20以降、loot table rootへ任意の`random_sequence`を指定できます。

```json
{
  "type": "minecraft:chest",
  "random_sequence": "example:rewards/main",
  "pools": []
}
```

- 名前付きsequenceはworld seedとsequence IDを基に決まる
- 同じworld、同じsequenceの呼出順が同じなら再現性を得やすい
- 複数tableが同じIDを共有すると、片方の呼出回数・順序が他方の後続結果へ影響し得る
- context、condition、roll数、呼出順まで無視して「常に同じlootを返す」指定ではない
- 省略時は名前付きの決定的sequenceを共有しない

乱数結果の独立性が必要ならtableごとに別IDを使い、意図的に列を共有する場合はその結合をAPI仕様として記録します。

## item modifier

item modifierは1.17で追加されました。rootは単一function object、または順に適用するfunctionの配列です。

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

| 項目 | 意味 |
|---|---|
| root object | functionを1個適用 |
| root array | functionを記述順に適用 |
| `function` | loot function type ID |
| `conditions` | このfunctionへ到達した時の追加条件。すべて成立で適用 |
| type固有field | count、name、components、source等 |

重要な制約:

- item modifierは対象slotのstackを変更する。空slotへ任意のitemを生成するrecipeではない
- functionが必要とするloot context parameterは`/item modify`の呼出contextに存在するとは限らない
- `set_count`等で不正なstack sizeを作った場合のclamp・分割・失敗を推測しない
- 同じstackへ複数functionを適用するため、順序が結果へ影響する
- 1.20.5より前は旧item NBT、以降はdata componentを使うfunctionへ移行する
- 1.21.11の`filtered`、26.2のentity/component predicateは旧版のitem modifierへ逆輸入しない

loot function `reference`からitem modifierを呼ぶ場合も、参照先が新しいcontextを作るわけではありません。参照元のcontextを引き継ぐので、参照先が要求するparameterを含めて検証します。

## recipeの共通モデル

recipe rootの`type`はserializerを選びます。serializerごとに必須field、ingredient数、result型、入力保持・component copyの規則が異なります。

| 共通的なkey | 型 | 意味 | 誤解しやすい点 |
|---|---|---|---|
| `type` | recipe serializer ID | shaped、smelting、smithing等の解釈を選ぶ | UI名や自由な識別子ではない |
| `group` | string | recipe book上で関連recipeをまとめる | item tag、unlock条件、同一ingredientの指定ではない |
| `category` | type別enum | recipe book内の分類 | crafting結果のrarityや用途を変更しない |
| `show_notification` | boolean | unlock通知の表示を制御。1.19.4のshaped recipeから始まり、26.1で主要serializerへ拡大 | recipeの存在、unlock条件、出力を無効化しない |
| `ingredient` / `ingredients` / `key` | ingredient codec | 許容item ID/tagを指定 | 通常のingredientは完全なitem predicateではない |
| `result` | 版・serializer依存 | 出力itemまたは変換先 | 全版・全typeで同じobjectではない |

recipe IDはrecipe book、advancementのrecipe参照、commandの`recipe give/take`等にも使われます。同じresource IDを別packで定義すると優先順位により置換され、2つの定義が自動mergeされません。

### ingredient

1.21.1以前の代表形:

```json
{
  "item": "minecraft:stick"
}
```

```json
{
  "tag": "minecraft:planks"
}
```

複数候補を許す場所ではingredient objectの配列を受ける版があります。

1.21.2以降:

```json
"minecraft:stick"
```

```json
"#minecraft:planks"
```

```json
[
  "minecraft:stick",
  "#minecraft:planks"
]
```

1.21.2で`{"item":"x"}`を`"x"`、`{"tag":"t"}`を`"#t"`へ変更しました。object形とinline形を同じoverlayへ混在させません。

通常のrecipe ingredientが検査するのはitem ID/tagへの所属です。1.20.5以降も任意の`components` patch、count、loot conditionをingredientへ書けるという意味ではありません。component付き入力を区別する処理は、対応するspecial serializer、hardcoded behavior、または別のadvancement/function設計が必要です。

空tag、空配列、`minecraft:air`を「空slot」の代用にしません。shaped craftingの空slotはpatternのspaceで表します。特定版のsmithingが空配列を特別扱いした履歴があっても、別版・別fieldへ一般化しません。

### result

result表現は最も移植事故が多い部分です。

| バージョン | craftingの代表形 | cooking/stonecutting等 | components |
|---|---|---|---|
| 1.13〜1.20.4 | `{"item":"minecraft:x","count":1}` | bare item IDまたはtype固有旧object | recipe serializerはcustom NBT付きresultを一般には受けない |
| 1.20.5〜1.21.11 | `{"id":"minecraft:x","count":1,"components":{...}}` | `{id,...}`へ移るが、許容fieldはserializerごとに確認 | item component対応。全special recipeが任意patchを受けるとは限らない |
| 26.1〜26.2 | `"minecraft:x"`または共通`{id,count,components}` | smelting系を含め同じresult表現へ統一 | count/componentの制約は最終stack codecとserializerで検証 |

1.20.5以降の例:

```json
{
  "id": "minecraft:stick",
  "count": 1,
  "components": {
    "minecraft:custom_data": {
      "example": {
        "kind": "reward"
      }
    }
  }
}
```

26.1以降の短縮形:

```json
"minecraft:stick"
```

短縮形は既定count・既定componentsを使う場合に選びます。componentsやcountが必要ならobject形にします。26.1の統一形を1.21.11以前へ単純に戻す場合、serializerごとの旧result型へ分解し直す必要があります。

## 主要recipe type

### shaped crafting

1.21.2以降の例:

```json
{
  "type": "minecraft:crafting_shaped",
  "category": "building",
  "group": "example_lamps",
  "pattern": [
    "GG",
    "SS"
  ],
  "key": {
    "G": "minecraft:glass",
    "S": "#minecraft:planks"
  },
  "result": {
    "id": "minecraft:lantern",
    "count": 1
  },
  "show_notification": true
}
```

| key | 必須性 | 意味・制約 |
|---|---|---|
| `pattern` | 必須 | 1〜3行、各行1〜3文字の矩形。spaceは空slot |
| `key` | 必須 | patternで使うspace以外の1文字をingredientへ対応付ける |
| `result` | 必須 | 対象版のresult型 |
| `category` | 任意 | craftingでは代表的に`building`, `redstone`, `equipment`, `misc` |
| `group` | 任意 | recipe book上のまとめ名 |
| `show_notification` | 1.19.4以降任意 | unlock toast制御 |

行幅を揃え、patternで使う記号をすべて`key`に定義します。spaceを`key`へ定義しません。左右・上下の余分な空白を含めたpatternの正規化や拒否は版のcodecで確認し、見えない末尾spaceへ依存しない例を優先します。

### shapeless crafting

```json
{
  "type": "minecraft:crafting_shapeless",
  "category": "misc",
  "ingredients": [
    "minecraft:paper",
    "minecraft:gunpowder"
  ],
  "result": {
    "id": "minecraft:firework_rocket",
    "count": 3
  }
}
```

`ingredients`は各slotで消費するingredientの配列です。同じingredientを2回要求するなら2要素書きます。配列内の候補数と必要個数を混同せず、crafting gridの上限を超えないことを確認します。

### cooking

対象は`minecraft:smelting`、1.14以降の`blasting`、`smoking`、`campfire_cooking`です。

```json
{
  "type": "minecraft:smelting",
  "category": "food",
  "ingredient": "minecraft:potato",
  "result": {
    "id": "minecraft:baked_potato"
  },
  "experience": 0.35,
  "cookingtime": 200
}
```

| key | 意味 |
|---|---|
| `ingredient` | 入力slotのingredient |
| `result` | 対象版・typeのresult |
| `experience` | 完了時に蓄積する経験値量 |
| `cookingtime` | tick単位の処理時間 |
| `category` | cookingでは代表的に`food`, `blocks`, `misc` |
| `group` | recipe book上のまとめ |

26.1以降はsmelting系resultでも`count`を利用できます。それ以前のcooking recipeへcount付きの最新objectを逆輸入しません。fuel、furnace slot、経験値回収手順をrecipe JSONだけで自由定義できるわけではありません。

### stonecutting

```json
{
  "type": "minecraft:stonecutting",
  "ingredient": "minecraft:stone",
  "result": {
    "id": "minecraft:stone_slab",
    "count": 2
  }
}
```

入力候補と出力stackを定義します。shaped pattern、cookingtime、経験値は取りません。category/groupの対応は対象版のvanilla例とcodecに限定します。

### smithing

| バージョン | type | 主なfield |
|---|---|---|
| 1.16〜1.19.4 | `minecraft:smithing` | `base`, `addition`, `result` |
| 1.20〜26.2 | `minecraft:smithing_transform` | `template`, `base`, `addition`, `result` |
| 1.20〜26.2 | `minecraft:smithing_trim` | `template`, `base`, `addition`、後続版の`pattern` |

1.20のtemplate-based smithingは旧`minecraft:smithing`の単純field追加ではなくserializerの置換です。

1.21.5以降のtransform例:

```json
{
  "type": "minecraft:smithing_transform",
  "template": "minecraft:netherite_upgrade_smithing_template",
  "base": "minecraft:diamond_sword",
  "addition": "#minecraft:netherite_tool_materials",
  "result": {
    "id": "minecraft:netherite_sword"
  }
}
```

1.21.5では`smithing_transform`の`base`を必須として扱います。`smithing_trim`では`base`、`template`、`addition`が必須です。古い版に存在した空配列等の特殊な省略表現を移植しません。

`smithing_trim`は通常の固定result stackを返すrecipeではなく、base itemへtrimを適用する専用処理です。1.21.5のvanilla例は`pattern`にtrim pattern IDを持ちます。transform/trimが入力stackのcomponentをどう保持・置換するかはserializer固有であり、通常craftingのresultと同一視しません。

### crafting transmute

1.21.2で追加され、入力itemのdataを変換先へ引き継ぐ用途に使われます。

```json
{
  "type": "minecraft:crafting_transmute",
  "category": "misc",
  "group": "example_recolor",
  "input": "#minecraft:shulker_boxes",
  "material": "minecraft:blue_dye",
  "result": {
    "id": "minecraft:blue_shulker_box"
  }
}
```

| key | 意味 |
|---|---|
| `input` | 変換元item |
| `material` | 変換に消費する追加ingredient |
| `result` | 変換先item stack |
| `material_count` | 26.1以降。materialに一致するslot数の範囲。許容範囲内で指定 |
| `add_material_count_to_result` | 26.1以降。materialのslot数をresult countへ加えるか |

1.21.5で`result`へcomponent patchとcountを指定できる形が拡張されました。26.1では複数materialを扱う上の2 fieldを追加し、旧`crafting_special_mapcloning`の機能もtransmuteへ吸収しました。transmuteは「任意recipe resultへ全componentを必ずそのままcopyする」という一般規則ではありません。保持・上書きされるcomponentを実際のcrafted resultで検査します。

### special crafting

`crafting_special_*`は、通常の`pattern`/`ingredients`だけでは表せないhardcoded処理のserializerです。古い版では多くがtype以外の自由なparameterを受けず、同typeを書けば任意のspecial処理を新規プログラムできるわけではありません。

26.1では一部を設定可能な形へ拡張し、26.2のvanilla dataには次のようなtype・fieldが観測されます。

| typeの例 | 主なfieldの例 | 役割 |
|---|---|---|
| `minecraft:crafting_dye` | `target`, `dye`, `result` | dye componentを使う染色 |
| `minecraft:crafting_imbue` | `source`, `material`, `result` | sourceの内容をresultへ反映する変換 |
| configurable map extending | `map`, `material`, `result` | map拡張用入力と出力 |
| configurable shield decoration | `banner`, `target`, `result` | banner情報をtargetへ反映 |

special recipeには通常recipeと異なるcomponent必須条件、入力保持、出力patchがあります。type名だけから共通schemaを推測せず、対象版の同じtypeのvanilla JSONを基底にします。

## 正式リリース境界

次の表はloot/recipe familyに影響する主な境界です。記載のないpatch版でも、対象JARでreloadします。

| 正式リリース | loot / item modifier | recipe |
|---|---|---|
| 1.13 | データパック起点。legacy loot tableをnamespace配下へ配置 | shaped、shapeless、smelting等を`recipes/`へ配置。Flattening後のitem ID |
| 1.14 | root/pool function、context `type`、block loot、dynamic/tag/composite entry、多数のcondition/functionを再編。`/loot`追加 | blasting、smoking、campfire cooking、stonecutting追加 |
| 1.15 | 独立`predicate` resource、condition `reference`等 | 1.14形を継承 |
| 1.16 | predicate root配列等の周辺変更 | 旧`minecraft:smithing`追加 |
| 1.17 | item modifierと`/item`追加。number provider `score`、condition `value_check`、複数functionの型を更新 | 1.16形を継承 |
| 1.18 | `set_contents`/`set_loot_table`にblock entity `type`必須、`set_potion`追加 | 1.17形を継承 |
| 1.19 | `set_instrument`追加 | 旧smithing等を継承 |
| 1.19.3 | loot/item stackは旧NBT形 | 任意`category`追加。craftingとcookingでenumが異なる |
| 1.19.4 | lootは1.19.3形 | `show_notification`追加 |
| 1.20 | condition `alternative→any_of`、`all_of`、function `reference`、root `random_sequence` | `smithing_transform`/`smithing_trim`へ移行 |
| 1.20.2 | function `sequence`、合成predicateのinline形等 | 1.20形。周辺text/state codecも対象版で確認 |
| 1.20.5 | item component化。NBT functionをcustom data/component functionへ移行。loot table entry参照等のcodecも再検証 | resultを`id/count/components`系へ移行 |
| 1.21 | `loot_table/`、`item_modifier/`へ単数形rename | `recipe/`へ単数形rename |
| 1.21.2 | item/component/enchantment関連function・predicate IDを再検証 | ingredientをID/`#tag`のinline形へ変更。`crafting_transmute`追加 |
| 1.21.5 | item function内のtext/component形を更新 | transmute resultへcomponent patch/count。transformの`base`、trimの`base`/`template`/`addition`を必須化。trim pattern |
| 1.21.9 | interaction用loot context/tableを拡張 | 1.21.5形を継承 |
| 1.21.11 | `filtered.modifier→on_pass/on_fail`、`discard`、slot source、`minecraft:slots` entry | 1.21.5形を継承 |
| 26.1 | enchant functionへ追加cost component制御 | resultをIDまたは共通item stackへ統一。smelting系count、`show_notification`を主要serializerへ拡張、stonecutting/smithingの未使用`group`を削除、transmuteとspecial recipe設定を拡張 |
| 26.2 | 埋め込みentity predicateをnamespaced component-mapへ変更しunknown keyを拒否 | 26.1 result/ingredient形を継承。special type一覧は26.2 JARで確定 |

同じdata pack formatでもschema差分がある版を省略しません。特に1.19.2→1.19.3の`category`はformat 10のまま、1.20.4→1.20.5と1.20.6→1.21は大きな境界です。

## 複数バージョン対応

### 共通化してよいもの

- 同じ対象版でJAR検証したresource IDとvanilla例
- 外部APIとして固定した独自loot table/item modifier/recipe ID
- serializerとfieldが同一と確認できた範囲のJSON
- function内部を対象版別に分けても維持できる呼出側の抽象名

### overlayまたは別packへ分けるもの

- 1.20.6以前の複数形folderと1.21以降の単数形folder
- 1.20.4以前の旧item NBT result/functionと1.20.5以降のcomponent形
- 1.21.1以前のobject ingredientと1.21.2以降のinline ingredient
- 1.21.10以前と1.21.11以降の`filtered`
- 1.21.11以前と26.1以降のrecipe result union
- 26.1.2以前と26.2のentity predicate

resourceの削除をoverlayだけで表せない場合があります。旧folder/resourceが基底packに残る設計では、不要な旧定義も読み込まれ得ます。互換範囲ごとにpackを分けるか、基底を最小共通集合にして新しい定義だけoverlayへ置きます。

## よくある誤解

### 「loot tableを置けば任意のeventでdropする」

loot tableは呼出元を登録しません。vanillaが既定IDを参照する場所をoverrideするか、block/entity/container/component/command/advancement等から明示的に参照します。

### 「`type:"generic"`なら全context parameterが使える」

主にload時の検査を緩める指定です。実際の呼出元が供給しない`tool`、entity、block state等は生成されません。正しいcontext typeを明示した方が欠損を早く検出できます。

### 「weightは確率の百分率」

weightは候補間の相対値です。条件で残った候補、composite展開、quality/luck、roll数を含めて確率が決まります。

### 「conditions配列はどれか1つ成立すればよい」

通常は暗黙のANDです。ORは`any_of`等、その版の合成conditionを使います。

### 「random_sequenceに固定値を書けば毎回同じ結果」

IDは名前付き乱数列を選びます。同じsequenceを共有するtableの呼出順、roll、条件によって後続状態が進みます。結果itemを固定するfieldではありません。

### 「item modifierはcustom itemの定義」

既存stackへfunctionを適用するresourceです。新しいitem registry entryを追加せず、recipe・loot・creative tabへ自動登録もしません。

### 「recipe ingredientで名前・NBT・componentsを判定できる」

通常ingredientはitem ID/tagの集合です。resultは1.20.5以降componentを持てても、入力ingredientが同じ能力を持つとは限りません。custom stackだけを材料にしたい要件はserializer/runtime hookの可否から設計し直します。

### 「categoryが違えば別のcrafting stationで使われる」

categoryは主にrecipe bookの表示分類です。使用stationは`type`が決めます。

### 「groupが同じrecipeは材料やunlockを共有する」

groupはrecipe book上のまとめです。unlockはadvancement等、材料は各recipeのingredientが決めます。

### 「result objectは全バージョン・全typeで同じ」

旧`item`、bare ID、`id`付きstack、serializer固有result、26.1統一形が存在します。対象版かつ同じserializerのvanilla例を使います。

### 「特殊recipe typeを指定すれば独自ロジックを書ける」

special serializerの処理はゲーム側に実装されています。公開fieldの値を変えられる範囲を超えて、新しいalgorithmをJSONだけで登録できません。

## 検証手順

### 1. 対象版の生成物を得る

```bash
python3 tools/datapack_harness.py reports 1.21.11 \
  --cache-dir .cache/minecraft \
  --output build/minecraft/1.21.11/generated \
  --java /path/to/java
```

対象版によってvanilla dataのfolderは複数形または単数形です。

```bash
find build/minecraft/1.21.11/generated/data/minecraft/loot_table \
  -type f -name '*.json'

find build/minecraft/1.21.11/generated/data/minecraft/recipe \
  -type f -name '*.json'
```

同じ`type`、同じloot context、同じrecipe serializerのvanilla fileを選び、IDだけを置換するところから始めます。別typeのfieldを寄せ集めません。

### 2. 静的確認

```bash
find path/to/pack -type f -name '*.json' -print0 |
  xargs -0 -n1 jq empty

python3 tools/datapack_harness.py validate-pack 1.21.11 path/to/pack
```

この段階で確認する項目:

```text
[ ] 対象版とfolderの単数・複数が一致する
[ ] loot root typeと実際の呼出contextが一致する
[ ] condition/function/entry/recipe type IDが対象版に存在する
[ ] type固有の必須field、値型、値域を満たす
[ ] item/tag/loot table/item modifier参照先が存在する
[ ] ingredientとresultを対象版の形にした
[ ] 1.20.5、1.21、1.21.2、1.21.11、26.1、26.2境界を混在させていない
```

`jq empty`はJSON文法だけを検査します。codec、registry ID、loot context、recipe serializerの妥当性は検査しません。

### 3. server reload

対象の正式リリースserverで`/reload`し、`logs/latest.log`のcodec error、unknown type、missing reference、context parameter warningを確認します。警告を`generic`へ変えて隠さず、呼出場所と必要parameterを修正します。

### 4. 実際のcontextで発火

loot tableは最低でも次を分けます。

- `/loot ... loot <id>`による直接評価
- block tableならSilk Touch/Fortune、explosion、正しい/誤ったtool
- entity tableならplayer kill、非player kill、projectile、fire、looting
- chest/tableなら複数seed、複数luck、満杯inventory/container
- `random_sequence`ありなら同一worldの呼出順、別world seed、sequence共有有無
- 0 roll、複数roll、全condition失敗、empty entry選択

item modifierは空slot、1個stack、最大stack、damageable item、component付きstackへ`/item modify`を実行し、変更前後を`/data get`またはpredicateで確認します。

recipeは次を分けます。

- recipe unlock前後とrecipe book表示
- 正しい材料、似た別item、tag追加item
- shapedのmirror/offset、shapelessの順序
- resultのcount、components、入力componentの保持・消失
- cooking time/experience、stonecutting、smithing、transmuteの実UI
- multiplayerでのunlock、craft回数、advancement `recipe_crafted`

load成功とgameplay結果は別のassertionにします。

### 5. 複数バージョン

対応範囲の全正式リリースでreloadし、少なくとも境界の直前・直後を機能testします。

```text
1.13 / 1.14
1.16.5 / 1.17
1.19.2 / 1.19.3 / 1.19.4
1.20.4 / 1.20.5
1.20.6 / 1.21
1.21.1 / 1.21.2
1.21.10 / 1.21.11
1.21.11 / 26.1
26.1.2 / 26.2
```

同じworldをupgrade testに使う場合はcopyを作り、recipe unlock、containerの未展開loot table、item component、random sequenceの状態も確認します。downgradeを互換試験として扱いません。

## 根拠と保証範囲

この文書のfieldと境界は次の順で確認します。

1. Mojangの正式リリースノートと正式版へ残ったsnapshot technical changes
2. 公式version manifestから取得した対象release server JAR
3. JAR data generatorの`generated/data/minecraft/{loot_table,loot_tables,recipe,recipes}`とregistry report
4. 対象serverのreload logと実際のloot/crafting結果
5. Minecraft WikiのLoot table、Item modifier、Recipe、各正式リリースページによるcross-check

JARのvanilla JSONにfieldがないことは、そのcodecで使用不能という証明ではありません。反対に、別バージョンのvanilla JSONで観測したfieldは対象版で有効という証明になりません。必須性、任意field、値域、相互排他、context parameterは同じ正式リリースで検査します。

主な一次資料:

- [Mojang: Village & Pillage out today on Java](https://www.minecraft.net/en-us/article/village---pillage-out-java-)
- [Mojang: Buzzy Bees out now in Java](https://www.minecraft.net/en-us/article/buzzy-bees-out-now-in-java)
- [Mojang: Java Edition 1.20](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20)
- [Mojang: Java Edition 1.20.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-5)
- [Mojang: Java Edition 1.21.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-2)
- [Mojang: Java Edition 1.21.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-5)
- [Mojang: Java Edition 1.21.11](https://feedback.minecraft.net/hc/en-us/articles/41809981427213-Minecraft-Java-Edition-1-21-11-Mounts-of-Mayhem)
- [Mojang: Java Edition 26.1](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-1)
- [Mojang: Java Edition 26.1 Snapshot 5](https://www.minecraft.net/en-us/article/minecraft-26-1-snapshot-5)
- [Mojang: Java Edition 26.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-2)
- [公式version manifest v2](https://piston-meta.mojang.com/mc/game/version_manifest_v2.json)

cross-check:

- [Minecraft Wiki: Loot table](https://minecraft.wiki/w/Loot_table)
- [Minecraft Wiki: Loot context](https://minecraft.wiki/w/Loot_context)
- [Minecraft Wiki: Item modifier](https://minecraft.wiki/w/Item_modifier)
- [Minecraft Wiki: Recipe](https://minecraft.wiki/w/Recipe)
- [Minecraft Wiki: Data pack](https://minecraft.wiki/w/Data_pack)
