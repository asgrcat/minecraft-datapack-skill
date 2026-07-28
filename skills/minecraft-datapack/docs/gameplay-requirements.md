# 複合gameplay要件の可否判定

この文書は、複数のvanilla機構を組み合わせる要件について、データパック単独で可能な範囲、回避不能な挙動、代替実装、cleanup、機能testを決定します。

個々の構文が存在するだけで実現可能と判定しません。対象バージョンのcommand graph、観測可能な状態、永続状態、multiplayerでの競合を分けて評価します。

## 判定カード

複合要件は次の形式で記録します。

```text
要件:
対応する正式リリース:
利用するvanilla機構:
データパック単独で可能な範囲:
回避不能なvanilla挙動:
代替実装:
状態遷移:
cleanup条件:
機能test:
```

判定は次の3種類です。

| 判定 | 意味 |
|---|---|
| 可能 | 対象バージョンの公開command/data機構だけで要件を満たせる |
| 条件付き | 観測間隔、近似、入力制限、resource pack等の条件がある |
| 不可 | datapackから観測・制御できないclient/engine挙動が必須 |

## 例: 共同カウントダウンイベント

### 要件

指定エリアへ必要人数が集まるとカウントダウンを開始し、終了時まで残った参加者へ報酬を一度だけ配布します。人数が下限を割った場合は中断し、再び条件を満たしたときに最初から開始します。

### 対応する正式リリース

| 正式リリース | 判定 |
|---|---|
| 1.13以降 | scoreboard、selector、function tagを使って実装可能 |
| 複数dimensionを同時運用 | dimensionごとの実行位置とevent IDを分離する条件付き |
| server停止中も実時間で進行 | データパック単独では不可。tick時間として停止するか、外部時刻源が必要 |

この例では最小対応バージョンを1.13とします。新しいバージョンの構文を使う場合も、対象バージョンのprofileとcommand graphで下限を再確認します。

### 利用するvanilla機構

- `minecraft:load` と `minecraft:tick` function tag
- scoreboardのevent state、timer、participant flag
- 座標またはpredicateによるエリア判定
- storageまたはfake playerによるevent単位の状態
- advancement、loot、function等による冪等な報酬処理

### 正本となる状態

「現在エリア内にいるplayer」と「このeventへ参加登録されたplayer」を同じ集合として扱いません。

| 状態 | 保存先 | 用途 |
|---|---|---|
| event phase | fake playerまたはstorage | idle/counting/completing/cooldown |
| timer | scoreboard | 残りtick |
| participant | player score/tag | 開始時に確定した参加者 |
| reward issued | 永続score/advancement | 二重配布防止 |
| event generation | scoreboard/storage | 再開始時に古い参加状態を無効化 |

player selectorの反復順序をevent IDや報酬順へ利用しません。

## エリア判定

直方体ならselectorの `x`, `y`, `z`, `dx`, `dy`, `dz`、球形なら実行位置と `distance` を利用できます。

```mcfunction
execute positioned 100 64 100 as @a[distance=..8] run tag @s add example.in_area
```

このtagを永続状態として使わず、各tickの判定前に更新します。

```mcfunction
tag @a remove example.in_area
execute positioned 100 64 100 as @a[distance=..8] run tag @s add example.in_area
```

- selectorの座標とdistanceは実行dimension内で評価される
- 境界上のplayer、spectator、死亡直前、portal移動を参加対象に含めるか定義する
- 大量のeventごとに全playerを走査せず、dimensionや粗い範囲で先に絞る

## 参加者の確定

必要人数を満たしたtickでgenerationを進め、その時点の対象playerへ参加generationを保存します。

```mcfunction
scoreboard players add #event ex.gen 1
execute as @a[tag=example.in_area] run scoreboard players operation @s ex.join_gen = #event ex.gen
scoreboard players set #event ex.phase 1
scoreboard players set #event ex.timer 200
```

参加後に入ったplayerを途中参加させるかは要件として明示します。途中参加を認めない場合、現在位置だけでなくgeneration一致も確認します。

## 状態遷移

| phase | 意味 | entry | exit |
|---:|---|---|---|
| 0 | idle | cleanup済み | 必要人数を満たす |
| 1 | counting | 参加者確定、timer初期化 | timer完了または人数不足 |
| 2 | completing | 成功条件確定 | 全参加者の報酬処理完了 |
| 3 | cancelling | 中断理由確定 | 一時状態のcleanup完了 |
| 4 | cooldown | 再実行待ち | cooldown完了 |

### counting

```mcfunction
execute if score #event ex.phase matches 1 run scoreboard players remove #event ex.timer 1
execute if score #event ex.timer matches ..0 run scoreboard players set #event ex.phase 2
```

人数不足の判定とtimer減算の順序を固定します。同じtickで境界をまたいだ場合に、成功と中断の両方へ遷移させないでください。

### completing

報酬は「phaseが2だから毎tick配る」のではなく、playerごとの配布済み状態を検査して一度だけ確定します。

```mcfunction
execute as @a[scores={ex.rewarded=0}] if score @s ex.join_gen = #event ex.gen run function example:event/reward
```

`example:event/reward` 内では報酬確定後に `ex.rewarded` を設定します。途中のcommand失敗で再実行すると重複する処理は、先に配布予約を記録するか処理を分割します。

## 中断とcleanup

### 人数不足

- 誰を人数へ数えるかを参加者条件と一致させる
- 中断時にtimer、参加tag、一時表示を解除する
- generationは巻き戻さず、次回開始時に新しい値を使う

### 死亡

- 死亡者を成功対象へ残すか失格にするか定義する
- respawn後の座標だけで同じeventへ自動復帰させない
- playerに残る一時scoreを次回参加時に初期化する

### disconnect

- offline playerはselectorで取得できない
- 切断を即時失格、猶予付き復帰、参加維持のどれとして扱うか定義する
- offline参加者を待つ場合、player NBTではなくevent側へ期限を保存する
- 復帰時はgenerationを照合し、終了済みeventへ混入させない

### chunk unload

- world storageとscoreboardはentityのload状態から独立している
- marker等のentityだけをevent状態の正本にしない
- 常時loadを保証できない場所のblock/entity状態は、再load時にreconcileする
- `forceload`をeventごとに常用せず、必要性と上限を検討する

### dimension移動

- eventのdimensionを状態に含める
- 別dimensionにいるplayerを同じ座標値だけで参加扱いにしない
- portal移動を失格、保留、別eventへの移管のどれにするか定義する

### server再起動とreload

- `load` functionで進行中eventを無条件に初期化しない
- scoreboard objectiveの作成と状態初期化を分離する
- function変更後も既存phaseを継続できない場合はmigration versionを持つ
- server停止中の時間をtimerへ加算しないことを仕様として明示する

## 代替実装

| 要件の本質 | 代替 |
|---|---|
| 正確な実時間で開始したい | plugin/mod等の外部時刻源を使う |
| playerの明示参加が必要 | advancement trigger、interaction entity、dialog等の対象バージョンで使える入力を選ぶ |
| 広い領域で参加を検知したい | 常時全域走査ではなく、入口で候補tagを付けて局所判定する |
| 複数eventを同時進行したい | event IDとgenerationを分け、共有fake playerへ状態を混在させない |
| 報酬を厳密に一度だけにしたい | advancementまたは永続scoreを配布台帳にする |

## 機能test

```text
[ ] 対象人数が0人、下限未満、下限ちょうど、上限超過
[ ] 同じtickで複数playerが境界へ入る
[ ] counting中に参加者が離脱し、同じtickで別playerが入る
[ ] timerが1から0になるtickで人数不足になる
[ ] completing中にcommandの一部が失敗して再実行される
[ ] deathとrespawn
[ ] logoutと再接続
[ ] chunk unload/reload
[ ] dimension移動
[ ] /reloadとserver再起動
[ ] eventを連続実行してgenerationが衝突しない
[ ] 成功と中断で報酬が重複しない
[ ] cleanup後に一時tag、score、scheduleが残らない
```

client表示や外部時刻を要件に含む場合、server-side testだけで完了扱いにせず、必要なE2E testを追加します。

## 参照

- [`execution-model.md`](execution-model.md)
- [`state-management.md`](state-management.md)
- [`implementation-patterns.md`](implementation-patterns.md)
- [`validation.md`](validation.md)
