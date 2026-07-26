# 進捗とplayer event

この文書はadvancementを、表示上の進捗だけでなくplayer単位の永続状態とevent入口として利用する方法を扱います。JSONの基本形は [`json-formats.md`](json-formats.md)、状態全体の選択は [`state-management.md`](state-management.md) を参照してください。

## 配置とモデル

```text
# 1.13〜1.20.6
data/example/advancements/player/first_join.json

# 1.21以降
data/example/advancement/player/first_join.json
```

resource locationはどちらも `example:player/first_join` です。

advancementの進行状況はplayerごとに保存されます。定義されたcriterionがtrigger条件を満たすと、そのcriterionが完了します。`requirements`を満たした瞬間にadvancement全体が完了し、display通知とrewardsが処理されます。

## criteriaとrequirements

```json
{
  "criteria": {
    "find_village": {
      "trigger": "minecraft:location",
      "conditions": {}
    },
    "trade": {
      "trigger": "minecraft:villager_trade",
      "conditions": {}
    }
  },
  "requirements": [
    [
      "find_village",
      "trade"
    ]
  ]
}
```

`requirements`は「外側をAND、内側をOR」として読みます。この例は、村へ到達するか取引するか、どちらか一方で完了します。

両方を必須にする例:

```json
{
  "requirements": [
    [
      "find_village"
    ],
    [
      "trade"
    ]
  ]
}
```

`requirements`を省略した場合は、各criterionを個別の必須groupとする形が基本です。生成時は意図を明確にするため、複数criterionでは明示することを推奨します。

- requirements内の名前はcriteria keyと完全一致させる
- 同じcriterionを重複させて条件式を表現しない
- 複雑なboolean条件はpredicateへ分離する
- triggerの `conditions` schemaはバージョンごとに確認する

## trigger

代表的な用途:

| 用途 | trigger例 |
|---|---|
| 常時評価・初回入口 | `minecraft:tick` |
| 位置・biome・dimension | `minecraft:location`, `minecraft:changed_dimension` |
| item取得・使用 | `minecraft:inventory_changed`, `minecraft:consume_item`, `minecraft:used_totem` |
| block操作 | `minecraft:placed_block`, `minecraft:item_used_on_block` |
| combat | `minecraft:player_hurt_entity`, `minecraft:entity_hurt_player`, `minecraft:player_killed_entity` |
| interaction | `minecraft:player_interacted_with_entity`, `minecraft:villager_trade` |
| packから手動制御 | `minecraft:impossible` |

この表を全trigger一覧として使わないでください。追加・rename・conditions統合があります。対象バージョンのvanilla advancement、release note、server JARのvanilla dataを正本にします。

triggerはevent駆動のため、毎tick全playerのinventoryや周辺entityを走査するより効率的な場合があります。ただし、条件に使うitem stack、entity predicate、location predicateはバージョン境界の影響を受けます。

## rewards

```json
{
  "criteria": {
    "event": {
      "trigger": "minecraft:impossible"
    }
  },
  "rewards": {
    "experience": 10,
    "loot": [
      "example:rewards/basic"
    ],
    "recipes": [
      "example:special"
    ],
    "function": "example:advancement/on_complete"
  }
}
```

reward functionでは、達成したplayerを `@s` として扱えるため、player単位の処理を置けます。

```mcfunction
# example:advancement/on_complete
scoreboard players add @s example.level 1
tellraw @s {"text":"Level up"}
```

実行位置・dimensionもplayer依存の処理で使われますが、バージョンや呼出経路に依存する仮定を減らすため、block/entity操作は必要に応じて `execute at @s` を明示します。

rewardは完了への遷移に伴うeffectです。revocationは配布済みexperience、loot、recipeやfunctionの副作用を巻き戻しません。

## `/advancement`

基本形:

```mcfunction
advancement grant @s only example:story/root
advancement grant @s only example:story/root criterion_name
advancement revoke @s only example:story/root
advancement revoke @s only example:story/root criterion_name
```

範囲指定:

| mode | 対象 |
|---|---|
| `only` | 指定advancement。criterionも指定可能 |
| `from` | 指定advancementと全子孫 |
| `through` | rootから指定advancementへの経路と子孫 |
| `until` | rootから指定advancementへの経路 |
| `everything` | 全advancement |

parent graphの広い `from`/`through` や `everything` は、vanillaや他packまで対象にし得ます。通常の実装では自namespaceの `only` を優先します。

`grant`/`revoke`のresultが「変更したadvancement数」「player数」など何を表すかはバージョンで修正されています。26.2にもresult/reportの変更があるため、制御値に使う場合は対象バージョンで確認します。

## 表示用と内部用を分ける

表示用advancement:

- `display`を持つ
- parent tree、icon、title、descriptionを利用する
- toast、chat announcement、hiddenを要件に合わせる

内部event:

- `display`を省略
- reward functionへの入口として使う
- IDを `example:internal/...` のように分離する
- 意図しない `/advancement ... from` の対象範囲に注意する

`parent`は表示treeと関連付けを表しますが、それだけで親完了を子の論理条件として代用しません。親完了が必須なら、trigger condition、predicate、score、reward function側で明示します。

## 一度だけのplayer初期化

```json
{
  "criteria": {
    "join": {
      "trigger": "minecraft:tick"
    }
  },
  "rewards": {
    "function": "example:player/initialize"
  }
}
```

advancementを完了状態のまま残せば、playerごとに一度だけrewardが走ります。

```mcfunction
# example:player/initialize
scoreboard players add @s example.level 0
scoreboard players set @s example.ready 1
```

これは「pack導入後、そのplayerが最初に評価されたとき」です。厳密な初ログイン日時とは限らず、既存worldへpackを追加したplayerにも発火します。

## 反復event

eventを毎回処理するには、reward functionの最後で自分のadvancementをrevokeします。

```mcfunction
# example:event/on_trade
function example:event/process_trade
advancement revoke @s only example:internal/trade
```

設計上の注意:

- state更新をrevokeより前に完了する
- function途中で失敗してrevokeへ到達しない場合、次回発火しなくなる
- `return`で早期終了する全経路からcleanupへ到達させる
- rewardから同じ条件を再発生させるcommandを呼ぶ再入経路を避ける

安全性を上げるなら、入口ではqueue/tag/scoreだけを設定し、重い処理をtick functionへ渡してからrevokeします。

## 手動criteria

`minecraft:impossible` は自然には完了しないため、pack側がcriterionを明示的に進める状態機械に使えます。

```json
{
  "criteria": {
    "stage_1": {
      "trigger": "minecraft:impossible"
    },
    "stage_2": {
      "trigger": "minecraft:impossible"
    }
  },
  "requirements": [
    [
      "stage_1"
    ],
    [
      "stage_2"
    ]
  ]
}
```

```mcfunction
advancement grant @s only example:quest/main stage_1
```

数値progressや分岐の正本として無理にcriteria数を増やすより、scoreboardで状態を持ち、advancementは表示・完了・event入口へ限定した方がmigrationしやすい場合があります。

## selectorからの照合

```mcfunction
execute as @a[advancements={example:quest/root=true}] run function example:quest/completed
execute as @a[advancements={example:quest/root={stage_1=true}}] run function example:quest/stage_1
```

- `true`/`false` がadvancement全体の状態かcriterion状態かを区別する
- 大量のadvancement条件を毎tickselectorへ詰め込まず、頻出状態はtag/scoreへcacheする
- cacheを持つならadvancementを正本とし、grant/revoke経路で同期する

## version境界

特に注意する境界:

- 1.13: 現行データパックとadvancement command体系の起点
- 1.20: 一部advancement triggerのcondition fieldを `location` へ統合
- 1.20.5: display icon、item predicate等をdata component形式へ移行
- 1.21: directoryを `advancements` から `advancement` へ単数化
- 1.21.5: text component、entity/item predicate、background path等を変更
- 1.21.6以降: JSON codecの厳格化を継続
- 26.2: entity predicateをcomponent-map化しunknown keyを拒否

同じtrigger名でもconditions内部が変わるため、最新バージョンの例を古いバージョンへ流用しません。

## test

最低限のtest matrix:

```text
[ ] 未達成playerでcriterionが発火する
[ ] 条件外playerでは発火しない
[ ] requirementsのAND/ORが意図どおり
[ ] rewardが1回だけ実行される
[ ] revoke後の再発火が意図どおり
[ ] reward途中の失敗で詰まらない
[ ] logout/loginとserver再起動後も進捗が維持される
[ ] 複数playerの状態が混ざらない
[ ] 旧worldを更新しても既存達成を壊さない
```

1.21.5以降は決定的な部分をGameTestへ含められます。ただしplayer advancementの完全なE2Eは、test playerと実serverの操作も併用します。

## 参照

- [Minecraft Wiki: Advancement](https://minecraft.wiki/w/Advancement)
- [Minecraft Wiki: Advancement definition](https://minecraft.wiki/w/Advancement_definition)
- [Minecraft Wiki: `/advancement`](https://minecraft.wiki/w/Commands/advancement)
- [Mojang: Java Edition 1.20](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20)
- [Mojang: Java Edition 1.20.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-5)
- [Mojang: Java Edition 1.21.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-5)
- [Mojang: Java Edition 26.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-2)
