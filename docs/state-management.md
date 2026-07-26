# 状態管理

この文書は、scoreboard、command storage、entity tag、advancementを状態として使い分け、reload・再起動・更新に耐える設計を扱います。構文のバージョン境界は [`commands.md`](commands.md)、進捗固有の挙動は [`advancements.md`](advancements.md) を参照してください。

## 状態の選択

| 手段 | 値 | 主な所有者 | 向く用途 | 主な弱点 |
|---|---|---|---|---|
| scoreboard | 32-bit整数 | player/entity/fake player | counter、timer、列挙状態、比較・演算 | compound/list/stringを持てない |
| storage | 任意のSNBT | world全体のnamespaced ID | 設定、queue、構造化状態、macro引数 | selectorから直接検索できない |
| entity tag | 文字列集合 | entity/player | 一時的な分類、selector絞り込み | 値や構造を持てない |
| advancement | criteriaの真偽 | player | event検出、達成状態、報酬 | player以外に使えずtrigger依存 |
| entity/item component・NBT | 対象固有 | entity/item/block entity | 対象自身へ属する状態 | バージョン差分が大きくplayer NBTは直接変更不可 |

選択の基準:

- 毎tick比較する整数はscoreboard
- 階層化した設定、list、文字列、queueはstorage
- selectorで高速に絞るbooleanはentity tag
- player eventをtick走査せず拾うならadvancement
- 同じ情報を複数手段へ複製するときは、正本を1つ決める

## scoreboard

### score holder

score holderはplayer名だけではありません。entity、UUID、`#timer` のようなfake playerも値を持てます。

```mcfunction
scoreboard objectives add example.state dummy
scoreboard players set #phase example.state 1
scoreboard players add @s example.state 1
```

- objective名はresource locationではない
- fake playerはログインplayerと衝突しにくい接頭辞を付ける
- selector対象のscoreが未設定の場合、`scores={...}` の条件には一致しない
- `scoreboard players add <holder> <objective> 0` は未設定scoreの初期化に使える
- `reset` はscore holderの値を未設定へ戻す。0を代入するのとは異なる

### 演算

```mcfunction
scoreboard players operation #out example.tmp = #in example.tmp
scoreboard players operation #out example.tmp += #delta example.tmp
scoreboard players operation #out example.tmp >< #other example.tmp
```

代表operation:

| operation | 意味 |
|---|---|
| `=` | 代入 |
| `+=`, `-=`, `*=`, `/=`, `%=` | 整数演算 |
| `<`, `>` | 小さい方／大きい方を代入 |
| `><` | swap |

除算・剰余の負数、0除算、32-bit境界を利用する設計は対象バージョンでtestします。command失敗時に処理全体がrollbackされることはありません。

### player単位の状態

```mcfunction
scoreboard players add @a example.cooldown 0
execute as @a[scores={example.cooldown=1..}] run scoreboard players remove @s example.cooldown 1
execute as @a[scores={example.cooldown=0}] at @s run function example:ready
```

offline playerのscoreもworldに残ります。player名変更、cleanup、pack uninstallまで含めるなら、保持期間と削除手順を決めます。

## command storage

storageは1.15以降で利用でき、worldに保存されるnamespacedなSNBT compoundです。

```mcfunction
data modify storage example:state config set value {schema:3,enabled:true}
data modify storage example:state players set value []
data get storage example:state
```

storage IDとroot compoundを分けて設計します。

```text
example:state
├── config
├── runtime
├── queue
└── migration
```

packごとに1個へ詰め込む必要はありません。更新頻度や責務が異なる状態は `example:config`, `example:runtime` のように分けられます。

### NBT path

代表的なpath:

```text
config.schema
queue[0]
queue[-1]
queue[]
players[{uuid:[I;1,2,3,4]}]
"key.with.dot"
```

- `.` はcompoundの子へ進む
- `[n]` はlist index。負数は末尾側から数える
- `[]` はlistの全要素へmatchする
- `[{...}]` はpatternに一致するlist要素へmatchする
- `.`や空白などを含むkeyはquoted keyを使う
- pathが0件、1件、複数件になる場合を分けてtestする

macroでpath自体を組み立てる設計は入力検証が難しくなります。可能なら固定pathとlist filterを使います。

### 変更操作

```mcfunction
data modify storage example:state config merge value {enabled:true}
data modify storage example:state queue append value {type:"example:job",ticks:20}
data modify storage example:state queue prepend from storage example:incoming job
data modify storage example:state queue insert 1 value {type:"example:priority"}
data remove storage example:state queue[0]
```

使い分け:

- `set`: 対象値を置換
- `merge`: compoundを再帰的にmerge
- `append`/`prepend`/`insert`: listへ追加
- `remove`: pathに一致する値を削除
- `from`: entity/block/storageの既存値をcopy
- `value`: commandに書いたSNBTを使用
- `string`: source stringのsubstringを使用できるバージョンがある

型不一致やsource path欠損はruntime failureです。複数の変更を1command transactionとして扱う仕組みはないため、途中失敗しても先行変更は残ります。

### scoreboardとの変換

```mcfunction
execute store result storage example:state runtime.score int 1 run scoreboard players get @s example.value
execute store result score #value example.tmp run data get storage example:state runtime.score 1
```

- storageへ保存できるのはcommandの数値result
- `success` を保存すれば通常は成否の1/0
- `type` と `scale` によりNBT数値型へ変換される
- 文字列、compound、listは `data modify ... from` で移す

## entity tag

```mcfunction
tag @s add example.active
execute as @e[tag=example.active] at @s run function example:active
tag @s remove example.active
```

tagはselectorで直接絞れるため、毎tick対象を限定する索引として有効です。

- tag名はresource locationではないがnamespace風のprefixを付ける
- entityが破棄されれば状態も失われる
- entityの再召喚や変換をまたぐ識別子として使わない
- 数値状態を複数tag名へ展開しない。数値はscoreboardへ置く

## 永続性と所有権

状態ごとに次を決めます。

| 項目 | 例 |
|---|---|
| owner | world、player、entity、一時task |
| lifetime | 1tick、session、world永続、pack更新後も維持 |
| source of truth | scoreboardまたはstorage |
| initialization | load、初参加advancement、entity生成時 |
| cleanup | 完了時、entity消滅時、uninstall時 |
| migration | schema 2から3へ |

「reloadで初期化」と「world作成時だけ初期化」を混同しないでください。`#minecraft:load` は何度も走るため、保存済みplayer進捗を無条件に消してはいけません。

## schema versionとmigration

storageまたはfake playerへpack内部schema versionを保存します。

```mcfunction
# load
scoreboard objectives add example.meta dummy
scoreboard players add #schema example.meta 0
execute if score #schema example.meta matches ..1 run function example:migrate/1_to_2
execute if score #schema example.meta matches 2 run function example:migrate/2_to_3
execute unless score #schema example.meta matches 3 run function example:error/unsupported_schema
```

各migration:

- 1段階だけ進める
- 再実行しても二重加算や二重配布を起こさない
- 変換完了後にschema versionを更新する
- 旧field削除は新field作成と検証の後に行う
- world backupでupgrade testする

pack versionと内部schema versionは別です。Minecraftのdata pack formatが同じでも、pack自身の保存形式は変わり得ます。

## 複数実行と競合

Minecraft commandは順に状態を変更しますが、transactionやlockを提供しません。

```mcfunction
execute as @a run function example:update_global_counter
```

全playerが同じfake player/storageへ書く場合:

- 加算なら全分岐の累積を意図しているか確認する
- `set`なら最後の分岐へ依存しない
- 読み取り→計算→書き戻しの途中で別functionが同じ値を変更しない構成にする
- tick入口、advancement reward、scheduled functionの責務を分ける

同tick内でもreward functionが別のadvancementをgrantし、さらにrewardを呼ぶような再入経路があります。状態を先に「処理中」へ遷移してから外部effectを実行します。

## uninstallとreset

開発用resetと利用者向けuninstallを分けます。

```mcfunction
# example:admin/reset_player
scoreboard players reset @s example.state
advancement revoke @s from example:root
tag @s remove example.active
```

```mcfunction
# example:admin/uninstall
schedule clear example:task/run
data remove storage example:state runtime
scoreboard objectives remove example.state
```

- uninstallは明示実行された場合だけ破壊的cleanupを行う
- vanillaや他packのobjective/tag/storageを削除しない
- objectiveを削除すると全holderの値が失われる
- storage root全体の削除前に自pack専用IDであることを確認する

## 確認項目

```text
[ ] 各状態のownerとlifetimeを決めた
[ ] source of truthが1つ
[ ] 未設定scoreと0を区別した
[ ] storage pathの0件・複数件をtestした
[ ] loadが保存状態を破壊しない
[ ] migrationを旧world copyでtestした
[ ] 複数entityが同じ値へ書く経路を確認した
[ ] resetとuninstallの対象を自namespaceへ限定した
[ ] server再起動後の永続性を確認した
```

## 参照

- [Minecraft Wiki: Scoreboard](https://minecraft.wiki/w/Scoreboard)
- [Minecraft Wiki: `/scoreboard`](https://minecraft.wiki/w/Commands/scoreboard)
- [Minecraft Wiki: `/data`](https://minecraft.wiki/w/Commands/data)
- [Minecraft Wiki: NBT path](https://minecraft.wiki/w/NBT_path_format)
- [Mojang: Java Edition 1.15](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-15)
- [Mojang: Java Edition 1.20.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-2)
