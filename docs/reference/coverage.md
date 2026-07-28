# データ種別カバレッジ

この表は26.2の公式server JARが生成する`reports/datapack.json`を基準に、データパックから要素を定義できる全resource種別を説明先へ対応付けます。正式リリースごとの追加・削除・renameは [`../versions/README.md`](../versions/README.md) と各バージョンファイルを先に適用します。

## registry resource

| 26.2のpath | 最初の主な正式リリース | 説明先 | codecの正本 |
|---|---:|---|---|
| `advancement` | 1.13 | [`../advancements.md`](../advancements.md)、[`components-and-predicates.md`](components-and-predicates.md) | vanilla advancement |
| `banner_pattern` | 1.20.5 | [`registry-formats.md`](registry-formats.md) | vanilla banner pattern |
| `cat_sound_variant` | 26.1 | [`registry-formats.md`](registry-formats.md) | vanilla sound variant |
| `cat_variant` | 1.21.5 | [`registry-formats.md`](registry-formats.md) | vanilla variant |
| `chat_type` | 1.19 | [`registry-formats.md`](registry-formats.md) | vanilla chat type |
| `chicken_sound_variant` | 26.1 | [`registry-formats.md`](registry-formats.md) | vanilla sound variant |
| `chicken_variant` | 1.21.5 | [`registry-formats.md`](registry-formats.md) | vanilla variant |
| `cow_sound_variant` | 26.1 | [`registry-formats.md`](registry-formats.md) | vanilla sound variant |
| `cow_variant` | 1.21.5 | [`registry-formats.md`](registry-formats.md) | vanilla variant |
| `damage_type` | 1.19.4 | [`registry-formats.md`](registry-formats.md) | vanilla damage typeとtag |
| `dialog` | 1.21.6 | [`registry-formats.md`](registry-formats.md) | dialog type registryとvanilla dialog |
| `dimension` | 1.16系 | [`world-and-environment.md`](world-and-environment.md)、[`worldgen.md`](worldgen.md) | 同typeのdimension generator |
| `dimension_type` | 1.16系 | [`world-and-environment.md`](world-and-environment.md) | vanilla dimension type |
| `enchantment` | 1.21 | [`registry-formats.md`](registry-formats.md) | effect component／effect type registry |
| `enchantment_provider` | 1.21 | [`registry-formats.md`](registry-formats.md) | provider type registry |
| `frog_variant` | 1.21.5 | [`registry-formats.md`](registry-formats.md) | vanilla variant |
| `instrument` | 1.21.2 | [`registry-formats.md`](registry-formats.md) | vanilla instrument |
| `item_modifier` | 1.17 | [`recipes-loot-and-tests.md`](recipes-loot-and-tests.md) | loot function type registry |
| `jukebox_song` | 1.21 | [`registry-formats.md`](registry-formats.md) | vanilla jukebox song |
| `loot_table` | 1.13 | [`recipes-loot-and-tests.md`](recipes-loot-and-tests.md) | entry／condition／function type registry |
| `painting_variant` | 1.21 | [`registry-formats.md`](registry-formats.md) | vanilla painting variant |
| `pig_sound_variant` | 26.1 | [`registry-formats.md`](registry-formats.md) | vanilla sound variant |
| `pig_variant` | 1.21.5 | [`registry-formats.md`](registry-formats.md) | vanilla variant |
| `predicate` | 1.15 | [`components-and-predicates.md`](components-and-predicates.md) | loot condition type registry |
| `recipe` | 1.13 | [`recipes-loot-and-tests.md`](recipes-loot-and-tests.md) | recipe serializer registry |
| `sulfur_cube_archetype` | 26.2 | [`registry-formats.md`](registry-formats.md) | vanilla archetype |
| `test_environment` | 1.21.5 | [`recipes-loot-and-tests.md`](recipes-loot-and-tests.md) | environment definition type registry |
| `test_instance` | 1.21.5 | [`recipes-loot-and-tests.md`](recipes-loot-and-tests.md) | test instance type registry |
| `timeline` | 1.21.11 | [`world-and-environment.md`](world-and-environment.md) | environment attribute registryとvanilla timeline |
| `trade_set` | 26.1 | [`registry-formats.md`](registry-formats.md) | vanilla trade set |
| `trial_spawner` | 1.21.2 | [`registry-formats.md`](registry-formats.md) | vanilla trial spawner |
| `trim_material` | 1.20系 | [`registry-formats.md`](registry-formats.md) | vanilla trim material |
| `trim_pattern` | 1.20系 | [`registry-formats.md`](registry-formats.md) | vanilla trim pattern |
| `villager_trade` | 26.1 | [`registry-formats.md`](registry-formats.md) | vanilla trade |
| `wolf_sound_variant` | 1.21.5 | [`registry-formats.md`](registry-formats.md) | vanilla sound variant |
| `wolf_variant` | 1.20.5 | [`registry-formats.md`](registry-formats.md) | vanilla variant |
| `world_clock` | 26.1 | [`world-and-environment.md`](world-and-environment.md) | 26.1 release noteとvanilla `{}` |
| `zombie_nautilus_variant` | 1.21.11 | [`registry-formats.md`](registry-formats.md) | vanilla variant |

## worldgen registry

| 26.2のpath | 説明先 | type固有codecの正本 |
|---|---|---|
| `worldgen/biome` | [`worldgen.md`](worldgen.md)、[`world-and-environment.md`](world-and-environment.md) | vanilla biome |
| `worldgen/configured_carver` | [`worldgen.md`](worldgen.md) | configured carver type |
| `worldgen/configured_feature` | [`worldgen.md`](worldgen.md) | feature type registry |
| `worldgen/density_function` | [`worldgen.md`](worldgen.md) | density function type registry |
| `worldgen/flat_level_generator_preset` | [`worldgen.md`](worldgen.md) | vanilla preset |
| `worldgen/multi_noise_biome_source_parameter_list` | [`worldgen.md`](worldgen.md) | vanilla parameter list |
| `worldgen/noise` | [`worldgen.md`](worldgen.md) | vanilla noise |
| `worldgen/noise_settings` | [`worldgen.md`](worldgen.md) | vanilla noise settings |
| `worldgen/placed_feature` | [`worldgen.md`](worldgen.md) | placement modifier type registry |
| `worldgen/processor_list` | [`worldgen.md`](worldgen.md) | structure processor type registry |
| `worldgen/structure` | [`worldgen.md`](worldgen.md) | structure type registry |
| `worldgen/structure_set` | [`worldgen.md`](worldgen.md) | structure placement type registry |
| `worldgen/template_pool` | [`worldgen.md`](worldgen.md) | pool element type registry |
| `worldgen/world_preset` | [`worldgen.md`](worldgen.md) | vanilla world preset |

## registry以外のresource

| path | 形式 | 説明先 |
|---|---|---|
| `function` | `.mcfunction` | [`../commands.md`](../commands.md)、[`../execution-model.md`](../execution-model.md) |
| `structure` | gzip NBT | [`../json-formats.md`](../json-formats.md)、[`worldgen.md`](worldgen.md) |
| `tags/<registry-path>` | JSON | [`pack-and-paths.md`](pack-and-paths.md)。1.18.2以降は任意registry、1.21で従来6種も単数形化 |
| `pack.mcmeta` | JSON | [`pack-and-paths.md`](pack-and-paths.md)、[`../compatibility.md`](../compatibility.md) |

## 26.2には残っていない歴史的resource path

26.2の一覧だけでは、旧バージョン向けpackの配置を決められません。特に次の
pathは過去の正式リリースで有効でしたが、現在のpathへrenameされたか削除されて
います。

| 歴史的path | 対象範囲 | 現在の扱い |
|---|---|---|
| `advancements` | 1.13〜1.20.6 | 1.21で`advancement`へrename |
| `functions` | 1.13〜1.20.6 | 1.21で`function`へrename |
| `item_modifiers` | 1.17〜1.20.6 | 1.21で`item_modifier`へrename |
| `loot_tables` | 1.13〜1.20.6 | 1.21で`loot_table`へrename |
| `predicates` | 1.15〜1.20.6 | 1.21で`predicate`へrename |
| `recipes` | 1.13〜1.20.6 | 1.21で`recipe`へrename |
| `structures` | 1.13〜1.20.6 | 1.21で`structure`へrename |
| `tags/blocks`、`items`、`fluids`、`entity_types`、`game_events`、`functions` | 各導入時〜1.20.6 | 1.21でregistry pathと同じ単数形へrename |
| `worldgen/configured_surface_builder` | 1.16.2〜1.17.1 | 1.18のsurface rule化で削除 |
| `worldgen/configured_structure_feature` | 1.16.2〜1.18.2 | 1.19で`worldgen/structure`へ移行 |

worldgenの追加・削除順は[`worldgen.md`](worldgen.md)も参照します。同じ
`data_pack_format`を共有する正式リリースでもpathやcodecが同一とは限りません。

## 組み込みtype registry

次はdata packから新しいserializer entryを追加するものではなく、`type`やcomponent keyとして参照する組み込みtype registryです。これはMinecraftの全組み込みregistry一覧ではありません。block、item、entity type、potion、attribute、sound event等も公式registryですが、独自JSON entryを置くフォルダではありません。完全なregistry／ID一覧は対象バージョンのregistry一覧を使います。

```text
command_argument_type
data_component_type
data_component_predicate_type
dialog_action_type
dialog_body_type
dialog_type
enchantment_effect_component_type
enchantment_entity_effect_type
enchantment_level_based_value_type
enchantment_location_based_effect_type
enchantment_provider_type
enchantment_value_effect_type
entity_sub_predicate_type
environment_attribute
loot_condition_type
loot_function_type
loot_pool_entry_type
recipe_serializer
structure_pool_element
structure_processor
test_environment_definition_type
test_instance_type
worldgen/feature
worldgen/placement_modifier_type
```

## カバレッジ判定

新しい正式リリースを追加するときは、次をすべて実施します。

```text
[ ] reports/datapack.jsonのelements:trueを前リリースとdiffした
[ ] 新しいresource pathをこの表へ追加した
[ ] 新しいtype registryを組み込みtype一覧へ追加した
[ ] 追加・削除・renameをversions/<version>.mdへ記録した
[ ] 新規fieldの型、必須性、既定値、値域、consumerを説明した
[ ] 同型vanilla fileまたは公式field listを示した
[ ] 最小resourceを対象serverでreloadした
[ ] 既存worldへの影響と新規world限定かを記録した
```
