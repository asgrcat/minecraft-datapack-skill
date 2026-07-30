# データ駆動JSONパラメータ索引

この索引は、主要なデータ駆動JSONを「何のための値か」から選び、対象の正式リリースで有効な形へ絞るための入口です。フィールド名だけでなく、表示・保存・ゲーム判定のどれを変えるか、データパックで新しい挙動を追加できる範囲、バージョン境界を扱います。

## 参照順序

family間の参照関係は次の順で確認します。

1. [`items.md`](items.md) でitem ID、item stack、NBT、data componentを区別する
2. [`predicates.md`](predicates.md) で独立predicate、loot condition、入れ子predicateを区別する
3. [`advancements.md`](advancements.md) でcriteria、trigger、requirements、rewardsを区別する
4. [`loot-recipes.md`](loot-recipes.md) でloot table、item modifier、recipeと各contextを区別する
5. [`dimensions-worldgen.md`](dimensions-worldgen.md) でdimension typeと地形generatorを区別する
6. [`enchantments-variants.md`](enchantments-variants.md) で固定されたvanilla要素とdata-driven registryを区別する
7. 下の表と各versionページで対象バージョンの境界を決める
8. 公式server JARから同じバージョンのcatalogとvanilla例を生成する
9. 新規テストworldで読み込みと実際の挙動を確認する

JSONは「Minecraftのあらゆる物を自由に定義できる設定ファイル」ではありません。各保存場所にはcodecという入力規則があり、同じ`type`でも別の場所では別のパラメータを取ることがあります。itemの見た目、dimensionの光、mobのspawn条件のように、似た結果に見えても別のclient表示・registry・gameplay判定へ分かれます。

## この資料の保証ラベル

| ラベル | 確定できること | 確定できないこと |
|---|---|---|
| registry完全一覧 | `registries.json`に公開されたtype/entry ID | 各entryの内部フィールド |
| vanilla観測フィールド | 生成されたvanilla JSONで実際に使用されたkeyとJSON型 | vanillaが使わない任意field、条件付き必須field |
| リリース差分 | Mojangの正式リリースノートに記載された追加・rename・削除 | 記載されなかったcodecの全分岐 |
| gameplay上の役割 | vanilla例とリリースノートから確認した役割 | 未検証の挙動、client mod、shader、他packとの組合せ |

「vanillaに例がない」と「そのcodecで使用できない」は同じではありません。逆に、別バージョンのvanilla例があるだけでは対象バージョンで使用できる証拠になりません。

## バージョン別の選択表

`継承`は、そのfamily固有の破壊的変更がこの索引とバージョン別プロファイルに記録されていないことを表します。同じ完全schemaを保証する記号ではないため、各正式リリースのJARでも確認します。

追加・変更・削除・互換性の履歴は各`versions/<version>.md`の`JSONパラメータ差分`を正本とします。次の表はfamily境界を横断して探すための索引です。

### registry・component・worldgen

| 正式リリース | item | dimension/worldgen | enchantment | variant |
|---|---|---|---|---|
| [1.13](../versions/1.13.md) | legacy item NBT起点 | custom不可 | 固定registry＋item NBT | 固定entity NBT |
| [1.13.1](../versions/1.13.1.md) | 継承 | custom不可 | 継承 | 継承 |
| [1.13.2](../versions/1.13.2.md) | 継承 | custom不可 | 継承 | 継承 |
| [1.14](../versions/1.14.md) | loot/recipe差分 | custom不可 | 継承 | 継承 |
| [1.14.1](../versions/1.14.1.md) | 継承 | custom不可 | 継承 | 継承 |
| [1.14.2](../versions/1.14.2.md) | 継承 | custom不可 | 継承 | 継承 |
| [1.14.3](../versions/1.14.3.md) | 継承 | custom不可 | 継承 | 継承 |
| [1.14.4](../versions/1.14.4.md) | 継承 | custom不可 | 継承 | 継承 |
| [1.15](../versions/1.15.md) | predicate/storage差分 | custom不可 | 継承 | 継承 |
| [1.15.1](../versions/1.15.1.md) | 継承 | custom不可 | 継承 | 継承 |
| [1.15.2](../versions/1.15.2.md) | 継承 | custom不可 | 継承 | 継承 |
| [1.16](../versions/1.16.md) | 継承 | 初期experimental dimension | 継承 | 継承 |
| [1.16.1](../versions/1.16.1.md) | 継承 | 1.16初期形 | 継承 | 継承 |
| [1.16.2](../versions/1.16.2.md) | 継承 | worldgen registry拡大 | 継承 | 継承 |
| [1.16.3](../versions/1.16.3.md) | 継承 | 1.16.2形 | 継承 | 継承 |
| [1.16.4](../versions/1.16.4.md) | 継承 | 1.16.2形 | 継承 | 継承 |
| [1.16.5](../versions/1.16.5.md) | 継承 | 1.16.2形 | 継承 | 継承 |
| [1.17](../versions/1.17.md) | `/item`・item modifier | 継承 | 継承 | 継承 |
| [1.17.1](../versions/1.17.1.md) | 継承 | 継承 | 継承 | 継承 |
| [1.18](../versions/1.18.md) | loot差分 | noise/height全面変更 | 継承 | 継承 |
| [1.18.1](../versions/1.18.1.md) | 継承 | 1.18形 | 継承 | 継承 |
| [1.18.2](../versions/1.18.2.md) | 継承 | density function/noise router | 継承 | 継承 |
| [1.19](../versions/1.19.md) | `set_instrument`追加 | structure rename・seed削除・spawn light | 継承 | predicate variant統合 |
| [1.19.1](../versions/1.19.1.md) | 継承 | 継承 | 継承 | 継承 |
| [1.19.2](../versions/1.19.2.md) | 継承 | 継承 | 継承 | 継承 |
| [1.19.3](../versions/1.19.3.md) | recipe/loot差分 | worldgen schema差分 | 継承 | `type_specific`拡大 |
| [1.19.4](../versions/1.19.4.md) | recipe通知差分 | biome precipitation変更 | 継承 | 継承 |
| [1.20](../versions/1.20.md) | advancement/item predicate差分 | structure processor追加 | 継承 | 継承 |
| [1.20.1](../versions/1.20.1.md) | 継承 | 継承 | 継承 | 継承 |
| [1.20.2](../versions/1.20.2.md) | effect NBT rename | 継承 | 継承 | 継承 |
| [1.20.3](../versions/1.20.3.md) | recipe/item modifier差分 | jigsaw schema差分 | 継承 | 継承 |
| [1.20.4](../versions/1.20.4.md) | legacy最終形 | 継承 | 継承 | 継承 |
| [1.20.5](../versions/1.20.5.md) | structured components起点 | number provider差分 | 固定definition＋表示順tag | `wolf_variant`起点 |
| [1.20.6](../versions/1.20.6.md) | 1.20.5形 | 継承 | 継承 | 継承 |
| [1.21](../versions/1.21.md) | 単数形folder | 継承 | data-driven起点 | `painting_variant`追加 |
| [1.21.1](../versions/1.21.1.md) | 1.21形 | 継承 | 1.21形 | 1.21形 |
| [1.21.2](../versions/1.21.2.md) | ingredient/component再編 | 継承 | effect rename | painting metadata追加 |
| [1.21.3](../versions/1.21.3.md) | 1.21.2形 | 継承 | 1.21.2形 | 1.21.2形 |
| [1.21.4](../versions/1.21.4.md) | component追加・変更 | 継承 | 継承 | 継承 |
| [1.21.5](../versions/1.21.5.md) | component/text再編 | 継承 | predicate/text差分 | animal/sound variant拡大 |
| [1.21.6](../versions/1.21.6.md) | strict JSON | `cloud_height` | 継承 | painting inline禁止 |
| [1.21.7](../versions/1.21.7.md) | 1.21.6形＋差分 | 継承 | 継承 | 継承 |
| [1.21.8](../versions/1.21.8.md) | 1.21.7形 | 継承 | 継承 | 継承 |
| [1.21.9](../versions/1.21.9.md) | `profile`の意味変更・object text追加 | density/noise差分 | effect差分 | 継承 |
| [1.21.10](../versions/1.21.10.md) | 1.21.9形 | 1.21.9形 | 継承 | 継承 |
| [1.21.11](../versions/1.21.11.md) | component差分 | attributes/timeline移行 | effect type追加 | zombie nautilus追加 |
| [26.1](../versions/26.1.md) | recipe result統一 | world clock連携 | loot function差分 | sound wrapper再編 |
| [26.1.1](../versions/26.1.1.md) | 26.1形 | 26.1形 | 継承 | 26.1形 |
| [26.1.2](../versions/26.1.2.md) | 26.1形 | 26.1形 | 継承 | 26.1形 |
| [26.2](../versions/26.2.md) | component type追加 | worldgen追加・rename | predicate互換性変更 | predicate互換性変更 |

### event・条件・生成resource

patchリリースを含む全正式リリースの履歴は各versionページにあります。次はschema選択に直接影響する境界です。

| 正式リリース | predicate | advancement | loot table | recipe | item modifier |
|---|---|---|---|---|---|
| [1.13](../versions/1.13.md) | 埋め込みのみ | data pack起点 | data pack起点 | data pack起点 | 未対応 |
| [1.14](../versions/1.14.md) | loot condition再編 | predicate差分 | context/entry/function再編 | cooking/stonecutting追加 | 未対応 |
| [1.15](../versions/1.15.md) | 独立resource追加 | player条件拡大 | `reference`等 | 継承 | 未対応 |
| [1.16](../versions/1.16.md) | top-level AND配列 | `player` condition共通化 | condition配列差分 | smithing追加 | 未対応 |
| [1.17](../versions/1.17.md) | item/block複数形化 | trigger追加 | provider/function差分 | 継承 | resource追加 |
| [1.18](../versions/1.18.md) | 継承 | travel/fall系差分 | block entity type・`set_potion` | 継承 | loot function差分 |
| [1.18.2](../versions/1.18.2.md) | location feature参照 | 継承 | exploration map参照差分 | 継承 | 継承 |
| [1.19](../versions/1.19.md) | structure・`type_specific` | trigger/condition差分 | `set_instrument` | 継承 | `set_instrument` |
| [1.19.3](../versions/1.19.3.md) | entity sub-predicate拡大 | condition拡大 | 継承 | `category`追加 | 継承 |
| [1.19.4](../versions/1.19.4.md) | damage source tag化 | Interaction対応 | 継承 | `show_notification` | 継承 |
| [1.20](../versions/1.20.md) | `any_of`/`all_of` | location条件・telemetry | `reference`・`random_sequence` | smithing再編 | `reference` |
| [1.20.2](../versions/1.20.2.md) | inline `all_of` | nested codec差分 | `sequence` | 継承 | `sequence` |
| [1.20.5](../versions/1.20.5.md) | item component化 | icon/predicate component化 | component function再編 | result components | component function再編 |
| [1.21](../versions/1.21.md) | 単数形folder | 単数形folder | 単数形folder | 単数形folder | 単数形folder |
| [1.21.2](../versions/1.21.2.md) | item predicate差分 | `killed_by_arrow` | component/enchantment差分 | ingredient簡略化・transmute | component差分 |
| [1.21.5](../versions/1.21.5.md) | entity/block component化 | background/component差分 | text/component差分 | transmute/smithing差分 | component差分 |
| [1.21.6](../versions/1.21.6.md) | strict JSON | strict JSON・trigger追加 | strict JSON | strict JSON | strict JSON |
| [1.21.9](../versions/1.21.9.md) | profile semantics波及 | nested component差分 | interaction context追加 | 継承 | component差分 |
| [1.21.11](../versions/1.21.11.md) | component存在判定 | trigger追加 | `filtered`・`discard`・slots | 継承 | `filtered`差分 |
| [26.1](../versions/26.1.md) | condition・clock・food追加 | reward参照差分 | trade/additional cost差分 | result統一 | enchant function差分 |
| [26.2](../versions/26.2.md) | entity component-map化 | entity condition非互換 | entity condition非互換 | 26.1形 | entity condition非互換 |

この表の`継承`はpack formatが同じという意味ではありません。familyに直接のparameter変更が記録されていない場合でも、folder、text component、predicate、resource IDなど周辺codecが変わることがあります。

## 26.3スナップショット境界

次は開発中の差分です。正式リリース表へ合成せず、各 [`snapshots/<launcher-id>.md`](../snapshots/README.md) の9 family差分を`inherits`順に適用します。

| launcher ID | data pack format | 主要境界 |
|---|---:|---|
| [`26.3-snapshot-1`](../snapshots/26.3-snapshot-1.md) | 108.0 | slot source resource、pot decoration item stack化、configured feature／material rule再編 |
| [`26.3-snapshot-2`](../snapshots/26.3-snapshot-2.md) | 109.0 | `block_transformer`、feature type rename、carver再編 |
| [`26.3-snapshot-3`](../snapshots/26.3-snapshot-3.md) | 110.0 | `compostable`、number provider registry、brewing recipe |
| [`26.3-snapshot-4`](../snapshots/26.3-snapshot-4.md) | 111.0 | loot／predicate／advancementのdiscriminator・参照・condition再編 |
| [`26.3-snapshot-5`](../snapshots/26.3-snapshot-5.md) | 112.0 | inline値とID参照を同じelement listへ混在可能 |
| [`26.3-snapshot-6`](../snapshots/26.3-snapshot-6.md) | 113.0 | fuel／compostableのinline数値、noise／density function再編 |

## 対象バージョンの機械カタログ

ハーネスから公式JARのdata generatorを実行した後、次のコマンドで対象バージョン固有のJSONカタログを作成します。`reports`が記録するversion/SHA-1 provenanceと指定versionが一致しない出力は拒否されます。

```bash
python3 tools/datapack_harness.py reports 1.21.11 \
  --cache-dir .cache/minecraft \
  --output build/minecraft/1.21.11/generated \
  --java /path/to/java

python3 tools/datapack_harness.py json-catalog 1.21.11 \
  --reports build/minecraft/1.21.11/generated \
  --output build/minecraft/1.21.11/json-catalog.json
```

出力には次が含まれます。

| path | 内容 |
|---|---|
| `registry_ids.item_component_types` | 公開されたitem component type ID |
| `registry_ids.item_component_predicate_types` | data component sub-predicate type ID |
| `registry_ids.enchantment_*` | enchantment effect/provider/value type ID |
| `registry_ids.predicate_*` | block/entity/item sub-predicate type ID |
| `registry_ids.loot_*` | loot condition/function/entry/provider type ID |
| `registry_ids.advancement_trigger_types` | advancement trigger type ID |
| `registry_ids.recipe_*` | recipe serializer/type ID |
| `registry_sources` | 各`registry_ids` groupの参照元registryがreportにあるかを`present`/`unknown`で表示 |
| `worldgen_dispatchers` | feature、density function、processor等のtype ID |
| `data_driven_registries` | datapackからelementを追加できるregistry |
| `variant_registries` | registry/datapack reportまたはgenerated dataで確認したvariant registry |
| `data_driven_variant_registries` | そのうちdatapack reportまたはgenerated dataでpack定義可能と確認したvariant registry |
| `observed_shapes` | dimension、dimension type、advancement、predicate、loot table、recipe、item modifier等のvanilla JSONで観測したfield pathとJSON型 |

registry ID一覧はreportに公開された範囲で完全です。空の`registry_ids`は、対応する`registry_sources`がすべて`present`なら「公開entryが0件」、`unknown`なら「このreportからは判定不能」です。`source.datapack`が`null`の場合も、空の`data_driven_registries`だけからpack定義不可とは判定しません。`observed_shapes`はcodec schemaではなくvanilla利用例の集計なので、必須・任意、値域、排他的fieldは各資料と実際のreloadで確定します。
vanilla生成物に独立predicateやitem modifierがないバージョンでは、対応する`file_count`が0になります。resource非対応を意味する値ではないため、type ID、正式リリースノート、独自最小例のreloadも確認します。

## 実装前の確認

```text
[ ] 対象の正式リリースを完全一致で決めた
[ ] 変更したいものがitem stack、registry entry、client resourceのどれか説明できる
[ ] 表示だけの値とgameplay判定を分けた
[ ] 同じtypeの対象バージョンのvanilla JSONを基底にした
[ ] registry/tag参照先が対象バージョンに存在する
[ ] 新規worldまたは未生成chunkが必要な変更を/reloadだけで判定していない
[ ] multiplayer、upgrade、別packとの上書き競合を確認した
[ ] JSON parse成功と、意図したgameplay結果を別々に検査した
```
