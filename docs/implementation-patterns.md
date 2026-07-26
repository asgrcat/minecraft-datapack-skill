# 中上級の実装パターン

この文書は、個別構文を組み合わせて保守可能なデータパックを設計する定型を示します。先に [`execution-model.md`](execution-model.md)、[`state-management.md`](state-management.md)、[`advancements.md`](advancements.md) を参照してください。

例は概念を示す最小形です。対象バージョンのdirectory、command、item/text/predicate形式へ解決してから使用します。

## 構成

```text
data/example/function/
├── load.mcfunction
├── tick.mcfunction
├── migrate/
│   ├── 1_to_2.mcfunction
│   └── 2_to_3.mcfunction
├── player/
│   ├── initialize.mcfunction
│   └── tick.mcfunction
├── event/
│   ├── on_trade.mcfunction
│   └── process_queue.mcfunction
├── state/
│   ├── idle.mcfunction
│   ├── active.mcfunction
│   └── cooldown.mcfunction
└── admin/
    ├── reset_player.mcfunction
    └── uninstall.mcfunction
```

責務:

- `load`: objective作成、schema migration、定数初期化
- `tick`: dispatcher。重い具体処理を直接並べない
- `player/*`: player単位の処理
- `event/*`: advancement等のevent入口
- `state/*`: 状態機械
- `admin/*`: 明示的な運用command

## 冪等なload

loadは `/reload` のたびに走るため、何度実行しても同じ状態へ収束させます。

```mcfunction
scoreboard objectives add example.meta dummy
scoreboard objectives add example.state dummy
scoreboard objectives add example.timer dummy
scoreboard players add #schema example.meta 0
execute if score #schema example.meta matches ..1 run function example:migrate/1_to_2
execute if score #schema example.meta matches 2 run function example:migrate/2_to_3
execute if score #schema example.meta matches 3 run data modify storage example:config defaults merge value {enabled:true}
```

避ける例:

```mcfunction
# reloadごとにplayer進捗を破壊する
scoreboard players set @a example.state 0
data modify storage example:state queue set value []
```

一時runtimeをreload時に破棄する設計なら、その判断と影響を明記します。

## player初期化

初参加処理はhidden advancementの `minecraft:tick` triggerを使うと、毎tickの未初期化player検索を避けられます。

```mcfunction
# reward: example:player/initialize
scoreboard players add @s example.state 0
scoreboard players add @s example.timer 0
tag @s add example.initialized
```

tagはtick処理の索引、scoreは正本とします。tagが欠損した場合に再構築できるよう、管理用repair functionを用意します。

## tick dispatcher

```mcfunction
execute as @a[tag=example.active] at @s run function example:player/tick
execute if score #queue_size example.meta matches 1.. run function example:event/process_queue
```

`player/tick`:

```mcfunction
execute if score @s example.state matches 0 run return run function example:state/idle
execute if score @s example.state matches 1 run return run function example:state/active
execute if score @s example.state matches 2 run return run function example:state/cooldown
return fail
```

この `return run` dispatcherは1.20.3以降です。それ以前は条件付きfunction呼出しを並べ、複数stateへ同時一致しない不変条件をtestします。

## timerとcooldown

playerごとの短いtimer:

```mcfunction
scoreboard players remove @a[scores={example.timer=1..}] example.timer 1
execute as @a[scores={example.timer=0},tag=example.cooling] at @s run function example:cooldown/finish
```

開始:

```mcfunction
scoreboard players set @s example.timer 100
tag @s add example.cooling
```

完了:

```mcfunction
tag @s remove example.cooling
scoreboard players reset @s example.timer
```

設計上の選択:

- game tick基準: scoreboard
- world全体の少数task: schedule
- 実時間基準: Minecraft tickだけで厳密に測らない
- offline中も進める期限: world clock/timeや保存timestampを対象バージョンの機能に合わせて検討する

## 状態機械

数値stateを列挙として使い、遷移を専用functionへ集約します。

```text
0 idle
1 active
2 cooldown
3 disabled
```

```mcfunction
# example:transition/idle_to_active
execute unless score @s example.state matches 0 run return fail
scoreboard players set @s example.state 1
scoreboard players set @s example.timer 200
tag @s add example.active
function example:effect/on_activate
return 1
```

原則:

- 遷移前条件を最初に検査する
- stateを先に確定し、その後に音・particle・item等の副作用を実行する
- entry/exit effectを遷移functionへ置く
- 任意のfunctionからstateを直接setしない
- 未知stateは黙ってidleへ戻さずerrorとして観測可能にする

## event queue

advancement rewardで重い処理を完遂せず、eventをqueueへ積む構成です。

```mcfunction
# reward contextでは @s がplayer
data modify storage example:incoming event set value {type:"trade"}
execute store result storage example:incoming event.player_id int 1 run scoreboard players get @s example.id
data modify storage example:queue events append from storage example:incoming event
scoreboard players add #queue_size example.meta 1
advancement revoke @s only example:internal/trade
```

この例では、初期化時に割り当てた一意な `example.id` scoreをplayer参照に使います。entity NBTのUUID field名をバージョンをまたいで固定しません。ID採番時は重複防止とoffline playerの保持方針を別途定義します。

processor:

```mcfunction
execute unless score #queue_size example.meta matches 1.. run return 0
data modify storage example:queue current set from storage example:queue events[0]
data remove storage example:queue events[0]
scoreboard players remove #queue_size example.meta 1
function example:event/dispatch with storage example:queue current
return 1
```

macroは1.20.2以降です。event `type`をそのままfunction IDへ挿入せず、許可した値を通常functionの条件分岐へ対応付けるとcommand injectionとtypoを防げます。

queue設計で決めること:

- 1tickあたりの最大処理件数
- 不正eventの隔離・破棄
- processor途中失敗時の再試行
- 同一eventの重複排除
- pack更新時の旧event schema migration

## selectorの段階的絞り込み

避ける例:

```mcfunction
execute as @e at @s if entity @a[distance=..32] run function example:entity/tick
```

改善:

```mcfunction
execute as @e[type=#example:managed,tag=example.active] at @s if entity @a[distance=..32,limit=1] run function example:entity/tick
```

- type/tag/scoreの安い条件をselectorへ入れる
- 距離、predicate、block/NBT検査を後段にする
- 同じ集合を複数回走査するならtagを索引として維持する
- `limit=1` は単一entity parserを保証する指定ではない

## 定数と一時値

定数:

```mcfunction
scoreboard players set #20 example.const 20
scoreboard players set #1000 example.const 1000
```

一時値:

```mcfunction
scoreboard players operation #work example.tmp = @s example.value
scoreboard players operation #work example.tmp *= #20 example.const
```

- `const`, `tmp`, 永続player stateをobjectiveで分ける
- fake player名に意味を持たせる
- nested functionが同じtmpを上書きする可能性を文書化する
- 再入可能にするならentity/player自身のtmp scoreを使うか、storage frameを分ける

## API境界

他packから呼べるfunctionを `api/` へ限定します。

```text
example:api/enable
example:api/disable
example:api/get_state
```

API functionは次を定義します。

- 必要なexecutor: player、entity、server
- 必要なposition/dimension
- 入力: storage path、macro compound、score
- success/result
- 変更する状態
- 対応version

内部functionを直接APIにすると、refactorやmigrationが難しくなります。function tagをextension pointに使う場合は、呼出順と失敗の扱いを定義します。

## errorの観測

上級packは失敗を黙殺せず、開発時に観測可能にします。

```mcfunction
execute store success score #ok example.tmp run data get storage example:config schema
execute unless score #ok example.tmp matches 1 run tellraw @a[tag=example.admin] {"text":"[example] config.schema is missing","color":"red"}
```

本番では毎tick同じerrorをspamしないよう、error codeをscore/storageへ記録し、最初の1回だけ通知します。

記録候補:

- schema mismatch
- queueの未知event
- 想定外state
- resource参照切れ
- migration失敗
- command chain/fork上限接近

## performance budget

処理量は「function行数」だけでなく実行コンテキスト数で見積もります。

```text
1 command × 100 entities × 20 ticks = 2,000 executions/second
```

確認:

- tick入口ごとのselector数
- selectorが返す最大entity数
- `execute as`を重ねた積
- macroの異なる引数集合数
- storageの大きなlistを毎tickcopyしていないか
- particle/sound/network effectの送信数

`/debug`, profiler、tick command等の利用可否は対象バージョンとserver環境に合わせます。開発worldで最悪入力を作り、平均ではなく上限を測ります。

## test pyramid

### 静的

- JSON parse
- path/namespace
- 対象バージョンのdirectory
- resource参照
- command graphとの一致

### reload

- codec errorなし
- loadが2回走っても状態不変
- tag/function/advancementを全て解決

### 機能

- 正常入力
- 対象0件
- 複数対象
- 未設定score/path
- offline/login
- dimension移動
- chunk unload

### 永続・移行

- server再起動
- 旧pack schemaから更新
- Minecraft version upgrade
- uninstall/reset

### GameTest

1.21.5以降では、決定的なblock/entity/loot結果を `test_instance` へします。乱数やAIを含むtestは複数rotation・反復検証を使い、失敗率を観測します。

## 完了条件

```text
[ ] entry pointごとの実行コンテキストが定義済み
[ ] 永続状態にschema versionがある
[ ] player初期化とworld loadが冪等
[ ] 状態遷移が専用functionに集約されている
[ ] tickの最大実行数を見積もった
[ ] event再入と途中失敗を扱った
[ ] APIの入力・result・副作用を定義した
[ ] reset/uninstall/migrationをtestした
[ ] 対応する全正式リリースでreloadした
```

## 参照

- [`validation.md`](validation.md)
- [Mojang: Java Edition 1.20.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-2)
- [Mojang: Java Edition 1.20.3](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-3)
- [Mojang: Java Edition 1.21.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-5)
- [Minecraft Wiki: Function](https://minecraft.wiki/w/Function_(Java_Edition))
- [Minecraft Wiki: Game test](https://minecraft.wiki/w/Game_test)
