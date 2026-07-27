# advancement JSON パラメータ

この文書は Minecraft Java Edition 1.13〜26.2 の advancement definitionについて、root field、表示、criterion、trigger condition、requirements、reward、telemetry、predicateとの文脈差、バージョン境界を整理します。playerごとの状態管理、反復event、`/advancement`の運用例は [`../advancements.md`](../advancements.md) を参照してください。

ここに示す表は設計時の索引です。全triggerの全condition codecを1つの固定schemaとして複製するものではありません。利用可能なtrigger IDは対象正式リリースのserver JARが生成する`registries.json`、各triggerの実際の形は同版のvanilla advancementとMojang release note、受理可否は同版serverのreload結果を正本とします。

## 配置とresource ID

```text
# 1.13〜1.20.6
data/<namespace>/advancements/<path>.json

# 1.21以降
data/<namespace>/advancement/<path>.json
```

たとえば、どちらの版でも次のfileはadvancement ID `example:story/cave_sight`を表します。

```text
data/example/advancements/story/cave_sight.json  # 1.20.6以前
data/example/advancement/story/cave_sight.json   # 1.21以降
```

1.21の単数形renameはfolderだけの変更です。JSON内の`parent`、command、selector等で参照するresource IDにはfolder名を含めません。

## rootのデータモデル

advancement definitionのroot fieldは次の役割に分かれます。

| field | 型 | 必須性 | 役割 |
|---|---|---|---|
| `parent` | advancement ID | 任意 | 表示treeと`/advancement ... from|through|until`の親子関係 |
| `display` | display object | 任意 | tab、icon、title、description、toast等のclient表示 |
| `criteria` | criterion名からcriterion objectへのmap | 必須 | playerごとに追跡するevent条件 |
| `requirements` | criterion名のlistを要素に持つlist | 任意 | criteriaをどのAND/ORで完了とするか |
| `rewards` | reward object | 任意 | 完了へ遷移した時のexperience、loot、recipe、function |
| `sends_telemetry_event` | boolean | 1.20以降で任意、既定`false` | clientの任意telemetry event対象にする印 |

1.20.5〜26.2の公式JAR generated dataでは、この6種類以外のadvancement root fieldは観測されません。ただし、root fieldが同じでも`display.icon`、trigger condition、item/entity/location predicate等の内側は版ごとに変わります。

### 1.21.5〜26.1の骨格例

```json
{
  "parent": "minecraft:adventure/root",
  "display": {
    "icon": {
      "id": "minecraft:spyglass"
    },
    "title": {
      "text": "Cave Observer"
    },
    "description": {
      "text": "Obtain a spyglass"
    },
    "frame": "task",
    "show_toast": true,
    "announce_to_chat": false,
    "hidden": false
  },
  "criteria": {
    "has_spyglass": {
      "trigger": "minecraft:inventory_changed",
      "conditions": {
        "items": [
          {
            "items": "minecraft:spyglass"
          }
        ]
      }
    }
  },
  "requirements": [
    [
      "has_spyglass"
    ]
  ],
  "rewards": {
    "function": "example:advancement/cave_observer"
  },
  "sends_telemetry_event": false
}
```

この例の`display.icon`はstructured item stack、`criteria.*.conditions.items[]`はitem predicateです。同じitem IDを含んでいても、生成値と判定値は別codecです。1.20.4以前へ移す場合はiconとitem predicateを旧形式へ書き換え、1.21.5のtext/background表現も前倒ししません。

## `parent`と表示tree

`parent`は同namespaceまたは別namespaceのadvancement IDを参照します。

- `parent`を持たない表示付きadvancementはtreeのrootとなり、advancement画面のtabを作る
- 子の`parent`は表示上の配置とcommandの親子範囲へ作用する
- 親を完了しなくても、子のcriterion自体はeventを受け取って完了できる
- 親完了を論理条件にする場合はcriterion、predicate、score等で別に判定する
- 存在しない`parent`、循環するparent graph、別packで消える親参照はload時に検証する

`display`を省略した内部advancementでも`parent`関係は残ります。表示されないことと、`from`、`through`、`until`の対象外になることは同じではありません。

## `display`

### fields

| field | 型 | 必須性・既定 | 意味 |
|---|---|---|---|
| `icon` | 版依存のitem stack | 必須 | treeとtoastに表示するitem |
| `title` | text component | 必須 | 表示名 |
| `description` | text component | 必須 | 説明文 |
| `frame` | `task` / `goal` / `challenge` | 任意、既定`task` | frame、toast見出し、challenge音等の表示分類 |
| `background` | 版依存のtexture/sprite ID | 任意 | root tabの背景 |
| `show_toast` | boolean | 任意、既定`true` | 完了toastを表示するか |
| `announce_to_chat` | boolean | 任意、既定`true` | `announceAdvancements`が有効な時にchatへ告知するか |
| `hidden` | boolean | 任意、既定`false` | 未完了時にtree上で隠すか |

`frame`はcriterionの難しさを自動評価せず、requirementsやrewardの実行条件も変えません。`hidden`もevent listenerを止めるfieldではありません。

### iconの版境界

1.20.4以前の代表形:

```json
{
  "icon": {
    "item": "minecraft:spyglass",
    "nbt": "{CustomModelData:1}"
  }
}
```

1.20.5以降:

```json
{
  "icon": {
    "id": "minecraft:spyglass",
    "count": 1,
    "components": {
      "minecraft:custom_model_data": 1
    }
  }
}
```

1.20.5で旧`item`と`nbt`をstructured item stackの`id`、`count`、`components`へ移行しました。`count`は省略時1で、26.2 vanilla iconでは省略形も観測されます。item componentの値構造は [`items.md`](items.md) の対象版境界に従います。

### backgroundの版境界

1.21.4以前:

```json
{
  "background": "minecraft:textures/gui/advancements/backgrounds/stone.png"
}
```

1.21.5以降:

```json
{
  "background": "minecraft:gui/advancements/backgrounds/stone"
}
```

1.21.5で`textures/` prefixと`.png` suffixを除いたsprite IDへ変更されました。画像はresource pack側の資源です。data packのJSONだけで新しい背景画像を配布したことにはなりません。

## `criteria`

`criteria`はcriterion名をkeyとするmapです。criterion名はそのadvancement内だけで使う識別子で、namespaced IDではありません。

```json
{
  "criteria": {
    "entered_cave": {
      "trigger": "minecraft:location",
      "conditions": {
        "player": [
          {
            "condition": "minecraft:entity_properties",
            "entity": "this",
            "predicate": {
              "location": {
                "can_see_sky": false
              }
            }
          }
        ]
      }
    }
  }
}
```

| criterion field | 型 | 必須性 | 意味 |
|---|---|---|---|
| `trigger` | trigger type ID | 必須 | criterionを評価するevent |
| `conditions` | trigger固有object | 任意 | eventをさらに絞り込む条件 |

`conditions`省略は「常に毎tick成功」ではありません。選んだtriggerのeventが発生した時に、そのtrigger固有の追加条件を課さないという意味です。

criterionが一度完了すると、そのcriterionのlistenerは通常不要になります。advancementを完了状態のまま使う場合、`minecraft:tick`を選んでも完了後に毎tickrewardが実行されるわけではありません。revoke後は再度criterionを満たせます。

`minecraft:impossible`は通常のgame eventから自然完了しないmanual用triggerです。`/advancement grant ... <criterion>`等で進める状態に使えます。

## trigger type

### 26.2の完全ID集合

26.2の`minecraft:trigger_type` registry reportには58 entryがあります。

```text
minecraft:allay_drop_item_on_block
minecraft:any_block_use
minecraft:avoid_vibration
minecraft:bee_nest_destroyed
minecraft:bred_animals
minecraft:brewed_potion
minecraft:changed_dimension
minecraft:channeled_lightning
minecraft:construct_beacon
minecraft:consume_item
minecraft:crafter_recipe_crafted
minecraft:cured_zombie_villager
minecraft:default_block_use
minecraft:effects_changed
minecraft:enchanted_item
minecraft:enter_block
minecraft:entity_hurt_player
minecraft:entity_killed_player
minecraft:fall_after_explosion
minecraft:fall_from_height
minecraft:filled_bucket
minecraft:fishing_rod_hooked
minecraft:hero_of_the_village
minecraft:impossible
minecraft:inventory_changed
minecraft:item_durability_changed
minecraft:item_used_on_block
minecraft:kill_mob_near_sculk_catalyst
minecraft:killed_by_arrow
minecraft:levitation
minecraft:lightning_strike
minecraft:location
minecraft:nether_travel
minecraft:placed_block
minecraft:player_generates_container_loot
minecraft:player_hurt_entity
minecraft:player_interacted_with_entity
minecraft:player_killed_entity
minecraft:player_sheared_equipment
minecraft:recipe_crafted
minecraft:recipe_unlocked
minecraft:ride_entity_in_lava
minecraft:shot_crossbow
minecraft:slept_in_bed
minecraft:slide_down_block
minecraft:spear_mobs
minecraft:started_riding
minecraft:summoned_entity
minecraft:tame_animal
minecraft:target_hit
minecraft:thrown_item_picked_up_by_entity
minecraft:thrown_item_picked_up_by_player
minecraft:tick
minecraft:used_ender_eye
minecraft:used_totem
minecraft:using_item
minecraft:villager_trade
minecraft:voluntary_exile
```

これはIDの完全一覧であり、58種の`conditions`が同じshapeという意味ではありません。1.18.2の`registries.json`には同名registryが公開されていないため、現在版の一覧を古い版へ適用せず、その版のvanilla dataとrelease noteからtriggerを確定します。

### 用途別に見るcondition

| event family | trigger例 | trigger固有conditionの例 |
|---|---|---|
| inventory・item | `inventory_changed`, `consume_item`, `using_item` | item predicate、slot/count range |
| block操作 | `placed_block`, `item_used_on_block`, `any_block_use` | location条件、tool/item、block state |
| combat | `player_hurt_entity`, `entity_killed_player`, `killed_by_arrow` | entity、damage、killing blow、victim集合 |
| 移動・位置 | `location`, `changed_dimension`, `fall_from_height` | location、dimension、distance、start position |
| entity interaction | `bred_animals`, `villager_trade`, `tame_animal` | parent/partner/child、villager、item |
| crafting・loot | `recipe_crafted`, `crafter_recipe_crafted`, `player_generates_container_loot` | recipe ID、ingredients、loot table ID |
| manual・周期 | `impossible`, `tick` | 自然発火なし、player条件 |

同じ名前の`item`、`location`、`entity` fieldでも、triggerごとに型とevent上の対象が異なります。たとえば`villager_trade.conditions.item`は取引item、`consume_item.conditions.item`は消費itemです。名前だけで対象を推測せず、同じtriggerを使う対象版vanilla advancementを基底にします。

## trigger conditionとpredicate/loot conditionの文脈差

### 4つの層

```text
criterion
└─ trigger
   └─ conditions                    trigger固有object
      ├─ item / entity / location   各種predicate value
      └─ player等のcondition list  inline loot condition
         └─ predicate               entity/item/location predicate
```

これらは外見が似ていても交換可能ではありません。

| 文脈 | rootの形 | 利用できるcontext |
|---|---|---|
| advancement `criteria.*.conditions` | trigger固有object | そのeventが提供するplayer、item、entity、位置等 |
| `conditions.player`等の拡張entity check | inline loot conditionのlist | そのfieldが対象にするentityを`this`として構築したcontext |
| standalone `predicate/<id>.json` | loot condition objectまたは版依存の合成形 | 呼出元が渡すorigin、`this_entity`等 |
| loot tableのcondition | loot contextごとのcondition | killer、tool、block entity、damage source等、loot type依存 |

1.16で、`minecraft:impossible`を除くtriggerに`player` checkが加わり、entity checkがinline loot condition listを受け取れるようになりました。listの各conditionは全て満たす必要があります。

```json
{
  "player": [
    {
      "condition": "minecraft:entity_properties",
      "entity": "this",
      "predicate": {
        "flags": {
          "is_sneaking": true
        }
      }
    }
  ]
}
```

この1.16〜26.1形を26.2へ移す場合、内側のentity predicate自体をcomponent-map形式へ変換します。

```json
{
  "player": [
    {
      "condition": "minecraft:entity_properties",
      "entity": "this",
      "predicate": {
        "minecraft:flags": {
          "is_sneaking": true
        }
      }
    }
  ]
}
```

`this`の意味は常に同じentityではありません。`player` checkではeventを受け取るplayer、victim用fieldではそのvictimというように、外側fieldが組み立てるloot contextに依存します。また、`tool`や`damage_source`を必要とするloot conditionを、それらを提供しないtrigger fieldへコピーするとload時または評価時に失敗します。

standalone predicate IDはtrigger condition objectへ文字列で直接代入しません。対象版に`minecraft:reference` loot conditionがあり、そのfieldのloot contextで利用できる場合は、inline conditionとして明示的に参照します。

```json
{
  "condition": "minecraft:reference",
  "name": "example:player/in_cave"
}
```

参照先がparseできても、必要なcontext parameterが呼出元にない場合は同じ意味になりません。

### 1.20のblock event統合

1.20では`placed_block`、`item_used_on_block`、`allay_drop_item_on_block`の個別`location`、`item`、`block`、`state`等を、`location`というinline loot condition listへ統合しました。

```json
{
  "trigger": "minecraft:item_used_on_block",
  "conditions": {
    "location": [
      {
        "condition": "minecraft:match_tool",
        "predicate": {
          "items": [
            "minecraft:glow_ink_sac"
          ]
        }
      }
    ]
  }
}
```

1.19.4以前のlocation predicate objectを、このlistの要素へそのまま置くだけでは移行できません。位置は`location_check`、itemは`match_tool`、block/stateは`block_state_property`等のloot conditionへ分けます。`alternative` conditionも1.20で`any_of`へrenameされ、`all_of`が追加されました。

## `requirements`

`requirements`はcriteria名から作る積和形です。

```text
外側list: 全groupを満たす（AND）
内側list: group内のどれかを満たす（OR）
```

`a`と`b`の両方:

```json
{
  "requirements": [
    [
      "a"
    ],
    [
      "b"
    ]
  ]
}
```

`a`または`b`のどちらか:

```json
{
  "requirements": [
    [
      "a",
      "b"
    ]
  ]
}
```

`requirements`を省略すると、全criterionを個別の必須groupとして扱います。明示する場合は、criteriaに存在しない名前を含めず、対象criterionを漏らさないようload logで検証します。空の内側listはcodecに拒否されます。

requirementsはtriggerのevent順や回数を表しません。一度完了したcriterionの時刻やevent payloadを、別criterionと比較するfieldもありません。順番、回数、時間制限を必要とする場合はscoreboard、function、別advancement等に状態を持たせます。

## `rewards`

| field | 型 | 既定 | 意味 |
|---|---|---|---|
| `experience` | integer | `0` | playerへexperienceを与える |
| `loot` | loot table IDのlist | 空 | reward用loot tableを生成してplayerへ与える |
| `recipes` | recipe IDのlist | 空 | recipe bookでrecipeを解放する |
| `function` | function ID | なし | 完了playerを実行主体としてfunctionを呼ぶ |

全fieldは任意です。`function`は単一function IDで、function tagではありません。

rewardはadvancementが未完了から完了へ遷移した時に処理されます。criterionをrevokeして再達成可能にすれば再び実行されますが、revokeは既に与えたexperience、item、recipeやfunctionの副作用を巻き戻しません。

reward functionでは完了playerが`@s`です。ただし、criterionが見ていたvictim、traded item、block、damage source等がscoreやstorageへ自動で渡されるわけではありません。reward lootもtrigger conditionと同じloot contextを継承するとは限らないため、trigger固有payloadをreward側から取得できると仮定しません。

## `sends_telemetry_event`

1.20で追加されたbooleanで、既定は`false`です。`true`の場合、そのadvancementの完了をclientの任意`advancement_made` telemetry eventの対象にします。

- advancementの達成条件、表示、rewardを変えるfieldではない
- server内のanalytics callbackやfunction実行を追加するfieldではない
- clientのtelemetry設定と送信対象の規則を置き換えない
- custom packのgameplay状態追跡にはscoreboard、storage、function等を使う
- 1.19.4以前へこのfieldを持ち込まない

vanilla advancementは1.20以降のgenerated dataで`true`を多く使用しますが、custom advancementで同じ値を機械的にコピーする必要はありません。

## バージョン境界

| 正式リリース | advancement JSONの重要点 |
|---|---|
| 1.13 | custom advancementをdata packへ配置する基準版。数値IDや旧achievement systemと混在させない |
| 1.14〜1.15.2 | triggerとpredicate fieldが追加・変更される。1.15でstandalone predicate resourceを追加したが、trigger condition rootと同一型ではない |
| 1.16〜1.16.5 | 全trigger（`impossible`を除く）へ`player` checkを追加。entity checkがloot condition listを受け付ける。旧entity object形は当時のdeprecated互換であり、後続版の根拠にしない |
| 1.17〜1.17.1 | item predicateの`item`を`items`へ変更。trigger固有item fieldも同版predicateへ更新 |
| 1.18〜1.18.2 | `nether_travel`の`entered`を`start_position`へrenameし`exited`を削除。`fall_from_height`、`ride_entity_in_lava`等を追加 |
| 1.19〜1.19.2 | 一部triggerの重複`location`を削除し`player.location`へ統合。entity predicateを`type_specific`へ再編。sculk/allay/item pickup系triggerを追加 |
| 1.19.3〜1.19.4 | 同じpack format 10内でもentity `type_specific` optionやInteraction entity対応が増えるため、1.19.2のcondition一覧を固定しない |
| 1.20〜1.20.1 | `sends_telemetry_event`追加。3種のblock event triggerを`location` loot condition listへ統合。`recipe_crafted`追加。`alternative`を`any_of`へrenameし`all_of`追加 |
| 1.20.2〜1.20.4 | effect NBT、block/fluid state matcher、text component等の埋め込み型が変わる。trigger rootが同じでもnested predicateを対象版へ更新 |
| 1.20.5〜1.20.6 | `display.icon`とitem predicateをstructured componentsへ全面移行。`any_block_use`、`default_block_use`、crafter系trigger等を含む56 triggerを正式版reportで確認 |
| 1.21〜1.21.1 | data folderを`advancements/`から`advancement/`へ単数化。内側のpredicate/tag folderも対象版の単数形に合わせる |
| 1.21.2〜1.21.4 | trigger ID `killed_by_crossbow`を`killed_by_arrow`へ置換。item component、ingredient、entity/block data等の変更がnested item predicateやiconへ波及 |
| 1.21.5 | `background`をsprite IDへ変更。entity/item/block predicateをcomponent対応へ更新 |
| 1.21.6 | data pack JSONをstrict parse。`player_sheared_equipment` triggerを追加 |
| 1.21.7〜1.21.10 | 1.21.6のstrict JSONとtrigger集合を継承 |
| 1.21.11 | `spear_mobs`を追加し58 trigger。既存triggerのnested item/entity schemaも同版を使う |
| 26.1〜26.1.2 | advancement rootとtrigger ID集合は1.21.11を継承。recipe、item、loot側の変更をreward参照とpredicateへ反映 |
| 26.2 | trigger ID集合は58種を継承。entity predicateをcomponent-mapへ変更しunknown keyを拒否するため、`conditions.player`やtrigger固有entity checkも再生成 |

同じdata pack formatを共有するpatch版でもtrigger optionや参照先IDが増える場合があります。`pack_format`だけでadvancement compatibilityを決めず、正式リリースIDを完全一致させます。

## 互換性上の確認点

### definitionを上書きする場合

同じadvancement IDを高優先度packで置換すると、field単位mergeではなくdefinition全体が置き換わります。

- vanilla advancementを上書きする場合はparent、display、criteria、requirements、rewards、telemetryを全体として再評価する
- criterion名のrenameや削除が既存player progressへ与える影響をcopy worldで確認する
- parent graphの変更がtab表示と`/advancement from|through|until`の範囲を変える
- packを外した時に既存progressとvanilla definitionが再結合する挙動を確認する

### player progress

definition JSONとplayer progressは別dataです。JSONの条件を変更しても、既に完了済みのcriterionが自動で未達成へ戻るとは限りません。

```text
definition: data pack内のcriteria、requirements、display、reward
progress:   world内のplayerごとのcriterion完了時刻・状態
```

既存worldを更新する場合は、未達成player、部分達成player、完了playerを分けて検証します。reward追加後に既達成playerへ副作用を遡及適用したい場合は、migration function等で明示的に処理します。

## よくある誤解

- `parent`は親advancementの完了を必須にしない
- `display`を省略してもcriterionとrewardは有効
- `show_toast:false`はchat告知を自動で無効にしない
- `announce_to_chat:true`でもgamerule `announceAdvancements`等の表示条件を無視しない
- `hidden:true`は未完了criterionのevent評価を止めない
- `frame:"challenge"`はexperienceを自動で付けない
- `conditions:{}`は全trigger共通schemaではなく、そのtriggerの追加条件なしを表す
- item stack、item predicate、ingredientは別codec
- trigger内のentity predicateとstandalone predicate resourceは外側のloot contextが違う
- reward functionへtrigger対象entity/item/blockが自動で渡されるわけではない
- revokeはrewardの副作用を巻き戻さない
- advancement JSONの変更だけではresource packのicon modelやbackground画像を追加できない
- telemetry fieldはpack内event loggerではない
- JSON parse成功だけではeventが実際に発火することを保証しない

## 対象版での検証

### 1. vanilla dataとtrigger IDを取得

```bash
python3 tools/datapack_harness.py reports 26.2 \
  --cache-dir .cache/minecraft \
  --output build/minecraft/26.2/generated \
  --java /path/to/java
```

1.20.5以降の正式版ではtrigger IDを次のように取得できます。

```bash
jq -r \
  '."minecraft:trigger_type".entries | keys[]' \
  build/minecraft/26.2/generated/reports/registries.json
```

1.21以降のvanilla例:

```text
build/minecraft/26.2/generated/data/minecraft/advancement/
```

1.20.6以前:

```text
build/minecraft/1.20.5/generated/data/minecraft/advancements/
```

古い版で`minecraft:trigger_type` registryがreportにない場合、それを「triggerが存在しない」と解釈しません。vanilla advancementとMojang release noteを列挙元にします。

### 2. 静的検査

```bash
jq empty data/example/advancement/story/cave_sight.json

python3 tools/datapack_harness.py validate-pack \
  26.2 path/to/pack \
  --reports build/minecraft/26.2/generated
```

静的検査で確認する項目:

```text
[ ] 対象版の複数形/単数形folder
[ ] parent、function、recipe、loot table、predicate参照先
[ ] criteria名とrequirements名の一致
[ ] trigger IDの存在
[ ] display.iconのitem stack形式
[ ] backgroundのtexture/sprite境界
[ ] nested item/entity/location/damage predicateの対象版形式
[ ] sends_telemetry_eventの導入版
```

### 3. serverでの実動作

1. 対象正式版serverで起動または`/reload`し、advancement parse errorと参照errorを確認する
2. 未達成playerで条件外eventを発生させ、criterionが進まないことを確認する
3. 条件内eventを発生させ、意図したcriterionだけが進むことを確認する
4. requirementsの各AND/OR経路を別playerまたはrevoke後に試す
5. display、toast、chat、hidden、parent treeをclientで確認する
6. experience、loot、recipe、function rewardを個別に確認する
7. revokeと再達成でrewardが再実行されるか確認する
8. logout/login、server再起動後のprogressを確認する
9. upgrade用copy worldで既存player progressと新definitionの組合せを確認する
10. multiplayerでplayer、victim、trader、item等のevent対象が混線しないことを確認する

`/advancement grant`だけでは自然event時のloot contextを再現しません。grant/revoke testと、実際のtrigger eventを発生させるE2E testを分けます。

## 出典

一次資料:

- [Mojang: Java Edition 1.16](https://www.minecraft.net/en-us/article/nether-update-java) — player check、extended entity check、trigger追加
- [Mojang: Java Edition 1.18](https://feedback.minecraft.net/hc/en-us/articles/4415128577293-Minecraft-Java-Edition-1-18) — travel/fall系trigger
- [Mojang: Java Edition 1.19](https://feedback.minecraft.net/hc/en-us/articles/6731464524941-Minecraft-Java-Edition-1-19) — sculk/allay系trigger、location/type-specific変更
- [Mojang: Java Edition 1.20](https://feedback.minecraft.net/hc/en-us/articles/16499677456781-Minecraft-Java-Edition-1-20-Trails-Tales) — block event condition統合、telemetry
- [Mojang: Java Edition 1.20.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-5) — item stack/component/predicate移行
- [Mojang: Java Edition 1.21](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21) — data folder単数形
- [Mojang: Java Edition 1.21.5](https://feedback.minecraft.net/hc/en-us/articles/35298208390797-Minecraft-Java-Edition-1-21-5-Spring-to-Life) — background sprite、predicate変更
- [Mojang: Java Edition 1.21.11](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-11) — trigger追加
- [Mojang: Java Edition 26.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-2) — entity predicate component-map
- 対象正式リリースserver JARの`generated/reports/registries.json`と`generated/data/minecraft/advancement*/`

cross-check:

- [Minecraft Wiki: Advancement definition](https://minecraft.wiki/w/Advancement_definition)
- [Minecraft Wiki: Advancement](https://minecraft.wiki/w/Advancement)
- [Minecraft Wiki: Advancement trigger](https://minecraft.wiki/w/Advancement_trigger)
