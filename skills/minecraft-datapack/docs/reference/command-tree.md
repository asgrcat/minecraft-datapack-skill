# コマンド木と引数parser

`.mcfunction`の字句と代表構文は [`../commands.md`](../commands.md)、executor、position、fork、success／resultは [`../execution-model.md`](../execution-model.md) を参照します。この文書は、対象バージョンの`commands.json`を完全な構文リファレンスとして読む方法を説明します。

## node

```json
{
  "type": "argument",
  "parser": "brigadier:integer",
  "properties": {
    "min": 0,
    "max": 15
  },
  "executable": true,
  "children": {}
}
```

| field | 説明 |
|---|---|
| `type` | `root`、固定語の`literal`、引数の`argument` |
| `parser` | argument nodeが使うparser ID |
| `properties` | min/max、単数／複数、resource registry等の追加制約 |
| `executable` | そのnodeでcommandを終了できるか |
| `children` | 続けられるliteral／argument |
| `redirect` | 別nodeへ処理を移すpath |

rootからchildrenを辿り、`executable: true`へ到達するpathだけが完結した構文です。Wikiの角括弧表記を先に解釈してnodeを省略しません。

## Brigadier parser

| parser | properties | 説明 |
|---|---|---|
| `brigadier:bool` | なし | `true`または`false` |
| `brigadier:integer` | 任意の`min`、`max` | 32-bit integer |
| `brigadier:long` | 任意の`min`、`max` | 64-bit integer |
| `brigadier:float` | 任意の`min`、`max` | floating point |
| `brigadier:double` | 任意の`min`、`max` | double |
| `brigadier:string` | `type` | `word`、`phrase`、`greedy`。greedyは残りの行全体 |

## 主なMinecraft parser

実際のparser IDとpropertiesは対象バージョンのreportを優先します。

| 分類 | parserの例 | 説明・確認点 |
|---|---|---|
| entity | `minecraft:entity` | `amount`がsingle／multiple、`type`がplayers／entities |
| game profile | `minecraft:game_profile` | player名またはselector等 |
| position | `minecraft:block_pos`, `vec3`, `vec2`, `column_pos` | absolute、relative、local座標の許可 |
| rotation | `minecraft:rotation` | yaw／pitch |
| range | `minecraft:int_range`, `float_range` | `min..max`の片端省略 |
| block | `minecraft:block_state`, `block_predicate` | block ID、state、NBT、tag許可 |
| item | `minecraft:item_stack`, `item_predicate` | item componentの対象バージョン境界 |
| NBT | `minecraft:nbt_compound_tag`, `nbt_tag`, `nbt_path` | SNBTとNBT pathを区別 |
| text | `minecraft:component`, `message`, `style` | text componentの1.21.5境界 |
| resource | `minecraft:resource`, `resource_key` | propertiesのregistryに属する単一ID |
| resource/tag | `minecraft:resource_or_tag`, `resource_or_tag_key` | `#`tagを許可 |
| objective | `minecraft:objective`, `objective_criteria` | scoreboard objective／criterion |
| score holder | `minecraft:score_holder` | 単数／複数property |
| operation | `minecraft:operation` | scoreboard operation |
| slot | `minecraft:item_slot`, `item_slots`, `slot_source` | slot ID、複数slot、26.2のslot source |
| time | `minecraft:time` | tickとunit suffix、min制約 |
| function | `minecraft:function` | function ID／tag／inline functionのバージョン差 |
| UUID | `minecraft:uuid` | UUID |
| angle | `minecraft:angle` | degree |
| color | `minecraft:color` | 対象バージョンのcolor名制約 |

`resource`と`resource_or_tag`、`entity`のsingleとmultipleを最も注意します。文字列として同じに見えてもargument parserの制約は異なります。

## commandの意味

構文木は次を保証しません。

- command実行に必要なpermission level
- chunkがload済みか
- 対象0件時の成否
- success値とresult値
- forkした各branchの集約
- stateを実際に変更しなかった場合の結果
- consumer固有codecを持つinline JSON／SNBTの妥当性

これらは同じ正式リリースの公式リリースノート、実server、機能テストで確認します。

## バージョン差分を取る

```text
previous commands.json root children
  vs
target commands.json root children
```

root commandの追加だけでなく、同じroot以下のnodeを再帰的に比較します。

```text
[ ] literalの追加・削除
[ ] argument parser IDの変更
[ ] parser propertiesの変更
[ ] executable nodeの移動
[ ] redirect先の変更
[ ] result semanticsのrelease note
```

同じdata pack formatでもcommand treeが変わる正式リリースがあります。format番号だけでcommand構文を共有しません。

## 26.2で特に確認する境界

- team／waypoint colorはlowercase snake_case
- advancement grant／revokeのresult報告
- `execute on owner`のowner関係
- `/unpublish`
- 26.1からのworld clock対応`/time`
- 1.21.11からのnamespaced gamerule、`/stopwatch`
- 1.21.6からの`/dialog`、`/waypoint`
- 1.21.5以降のSNBT text component
- 1.20.5以降のitem component patch

## 検証

```text
[ ] rootからexecutable nodeまでの全pathを辿った
[ ] argument parserのpropertiesを保持した
[ ] resourceとresource-or-tagを区別した
[ ] single targetとmultiple targetを区別した
[ ] inline JSON／SNBTを対象codecで検証した
[ ] success、result、permission、chunk条件を機能テストした
```
