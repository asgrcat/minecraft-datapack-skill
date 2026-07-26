# コマンド実行モデル

この文書は、構文が正しいコマンドが「誰として、どこで、何回、どの順で」実行されるかを扱います。個々のコマンド構文は [`commands.md`](commands.md)、バージョン境界は [`versions/README.md`](versions/README.md) を先に確認してください。

例は特記がなければ Java Edition 1.21.5〜26.2 の単数形ディレクトリを想定します。古いバージョンへ移植するときは対象バージョンプロファイルを適用します。

## 実行コンテキスト

コマンドの実行コンテキストは、少なくとも次の状態を持ちます。

| 状態 | 主な参照箇所 | 変更する代表的な構文 |
|---|---|---|
| executor | `@s`、権限判定、一部の結果帰属 | `execute as` |
| position | `~ ~ ~`、距離、block判定 | `execute at`, `positioned` |
| rotation | `^ ^ ^`、facing | `rotated`, `facing` |
| dimension | 座標・block・entity探索のworld | `execute in`, `at` |
| anchor | `eyes`/`feet`からのlocal座標・facing | `anchored` |
| permission/source | 実行可能なcommand、feedback | 呼出元で決まる |

`execute` のsubcommandは左から右へコンテキストを変換します。

```mcfunction
execute as @a at @s positioned ~ ~1 ~ run particle minecraft:happy_villager ~ ~ ~ 0 0 0 0 1
```

この例ではplayerごとに分岐し、そのplayerをexecutorにし、そのplayerのdimension・位置・回転へ移動してから、位置を1block上げます。

重要な区別:

- `as <targets>` はexecutorだけを変え、位置を変えない
- `at <targets>` は位置・回転・dimensionを対象へ合わせるが、executorを変えない
- playerごとの位置で処理する定型は `execute as @a at @s run ...`
- `positioned as` は位置をentityへ合わせるが、`at`と同一ではない。必要なrotation/dimensionも対象バージョンのcommand treeで確認する
- `anchored eyes` は以後のlocal座標やfacingの基準を変える。独立した次のfunction行へ変更を持ち越さない

## 分岐と実行回数

複数対象を取るsubcommandは、1本の処理を複数の実行コンテキストへ分岐させます。

```mcfunction
execute as @a at @s if entity @e[type=minecraft:zombie,distance=..8,limit=1] run function example:near_zombie
```

- 最初の `as @a` でplayer数だけ分岐する
- 各分岐の `@s` はそのplayer
- 条件を満たした分岐だけがfunctionへ到達する
- selectorが0件なら、その分岐から先は実行されない
- 複数分岐が同じstorageやfake player scoreへ書く場合、最後の1件へ依存する設計にしない

entityの反復順序や、複数分岐したcommandのresult集計をビジネスロジックの順序として利用しないでください。順序が必要なら、scoreで明示的に優先度を付け、1件ずつ選びます。

1.20.3では `maxCommandForkCount` が追加され、分岐数にも上限があります。大量entityへ多段の `as`/`at` を重ねると積の数だけ処理が増えるため、selectorを早い段階で絞ります。

## function

通常のfunction呼出しは呼出元のコンテキストを引き継ぎます。

```mcfunction
execute as @a at @s run function example:player/tick
```

`example:player/tick` 内では `@s` がplayer、`~ ~ ~` がそのplayerの位置です。ただし、function内のある行で行った `execute` の変更は、次の独立した行へ持ち越されません。

```mcfunction
# 1行目だけpositionが変わる
execute positioned ~ ~10 ~ run particle minecraft:cloud ~ ~ ~ 0 0 0 0 1
# 2行目はfunction呼出元のposition
particle minecraft:flame ~ ~ ~ 0 0 0 0 1
```

function tagはJSONの `values` 順にentryを持ちます。初期化順に依存する場合は、複数packが同じ `#minecraft:load` tagへ追加することを前提に、他namespaceとの暗黙の順序へ依存しないでください。

### macro

1.20.2以降のmacro行は、引数を置換した後で実行時にparseされます。

```mcfunction
$data modify storage example:state current set value $(value)
```

- 通常行はreload時に事前parseされる
- macro行は置換値ごとにparse負荷が発生する
- 同じ引数集合はcacheされるが、通常行より高コスト
- 置換値はcommand文字列であり型安全ではない
- 外部入力をcommand名、selector、resource locationへ直接挿入しない

固定分岐が少数なら、macroより複数の通常functionへ分けた方が検証しやすくなります。

## `return` とfunction結果

バージョン境界:

- 1.20: `return <value>`
- 1.20.2: 正式リリースでは `return run` と `execute if function` を利用不可
- 1.20.3: `return run`, `return fail`, `execute if|unless function` を再導入し、function resultを変更

```mcfunction
# example:check
execute unless score @s example.ready matches 1 run return 0
return 1
```

```mcfunction
execute if function example:check run say ready
execute store result score #result example.tmp run function example:check
```

1.20.3以降、通常のfunctionは明示的にreturnしなければresultを返しません。`execute store ... run function` がfunction内の各command結果を順次保存する旧挙動を前提にしないでください。

`return run <command>` はcommandのsuccess/resultと、対象が0件になる分岐の扱いが1.20.3開発中に調整されています。1.20.3以降でも対象正式リリースのプロファイルと実ゲームtestを優先します。

## load、tick、schedule

### load

`#minecraft:load` はworld/server loadまたは `/reload` 後に実行されます。初回world作成だけのhookではありません。

load functionは必ず再実行可能にします。

```mcfunction
scoreboard objectives add example.state dummy
execute unless score #schema example.state matches 3 run function example:migrate
scoreboard players set #schema example.state 3
```

objectiveが既に存在すると `scoreboard objectives add` は失敗しますが、後続行は続きます。失敗feedbackを避けることより、loadを何度実行しても状態を壊さないことを優先します。

### tick

`#minecraft:tick` は毎game tickの入口です。20 TPSなら目標上は1秒20回ですが、lag時に実時間20回を保証しません。

- 実時間ではなくgame tick基準の処理に使う
- 全entity走査を入口に置かず、tag/score/predicateで対象を絞る
- 低頻度処理はscore counterまたはscheduleへ分離する
- loadで作るobjectiveやstorageがtickより先に必要なら、対象バージョンでload/tick順を検証する

### schedule

`schedule function` は呼出元のexecutor・位置を保存しません。期限時はserver由来のコンテキストで実行されるため、後で必要なentityや座標をscoreboard/storageへ明示的に保存します。

```mcfunction
data modify storage example:task pending set value {dimension:"minecraft:overworld",x:0,y:64,z:0}
schedule function example:task/run 20t replace
```

```mcfunction
# example:task/run
execute in minecraft:overworld positioned 0 64 0 run function example:task/body
```

- `replace` は同じfunction IDの既存予定を置換する
- `append` は同じIDの予定を追加できるバージョンで使う
- scheduleはworldの時刻queueに保存されるが、pack更新でfunction IDを消すと期限時に解決できない
- exact tick、同時刻順、再起動後の動作が要件なら、空worldで再起動を含めてtestする
- entity単位の大量timerは、1件ずつscheduleするよりscoreboardでまとめて減算する方が管理しやすい

## success、result、失敗

| 状態 | 意味 |
|---|---|
| parse error | command treeに一致せずfunctionをloadできない |
| runtime failure | 構文は正しいが対象なし、pathなし、変更なし等 |
| success | `execute store success` が保存する成否 |
| result | command固有の整数値 |
| void | 保存できる結果を返さない |

```mcfunction
execute store success score #ok example.tmp run data get storage example:state value
execute store result score #value example.tmp run data get storage example:state value 1
```

successとresultは交換可能ではありません。`data get`、`clear`、`advancement`、複数対象commandなどが返すresultの意味は個別に確認します。

`execute store result storage <id> <path> <type> <scale>` では、resultへscaleを掛けて指定NBT数値型へ変換します。境界値、負数、小数、overflowへ依存する場合は、対象バージョンで期待値をassertしてください。

## 権限、chunk、world状態

- functionから実行できるcommandはcommand sourceとserver設定のpermission levelに影響される
- 専用serverでは `function-permission-level` を確認する
- 対象chunkが未loadのcommandは失敗する場合がある
- `forceload` は永続的なworld変更なので、追加と解除を対にする
- client表示、entity AI、block updateはcommand実行と同tickに最終状態へ到達するとは限らない

「commandがsuccessを返した」と「playerから見える結果が同tickに確定した」を同一視しないでください。視覚・AI・physicsを含むtestは数tick待つ設計にします。

## 上級実装の確認項目

```text
[ ] @s、position、dimensionを各entry pointで特定した
[ ] 複数selectorによる分岐数を見積もった
[ ] 反復順序や最後の分岐へ依存していない
[ ] functionがresultを返さない経路を扱った
[ ] loadが何度実行されても安全
[ ] scheduleへ呼出元contextが保存されると仮定していない
[ ] 未load chunkと対象0件を正常系・異常系に分類した
[ ] command chain/fork上限を超える入力を制限した
[ ] reload、server再起動、低TPSでもtestした
```

## 参照

- [Mojang: Java Edition 1.20.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-2)
- [Mojang: Java Edition 1.20.3](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-3)
- [Minecraft Wiki: Command context](https://minecraft.wiki/w/Command_context)
- [Minecraft Wiki: `/execute`](https://minecraft.wiki/w/Commands/execute)
- [Minecraft Wiki: `/function`](https://minecraft.wiki/w/Commands/function)
- [Minecraft Wiki: `/schedule`](https://minecraft.wiki/w/Commands/schedule)
