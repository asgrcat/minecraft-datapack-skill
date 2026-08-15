# 追加コンテンツとデータパック活用

この文書は、正式リリースで追加された主要なblock・entity・item・gameplay systemを、データパックから観測・制御する入口へ結び付けます。全registry IDの複製ではなく、「その要素を使って何を作れるか」を探すための索引です。

対象バージョンを決めてから [`versions/README.md`](versions/README.md) のバージョンプロファイルを適用してください。完全なID、block state、entity data/component、tagは対象バージョンのserver JARのreportを正本とします。

## 読み方

コンテンツごとに次の順で調べます。

1. **存在**: `registries.json`、block/item report、vanilla dataでIDを確定
2. **観測**: selector、block predicate、advancement trigger、predicate、loot context
3. **制御**: command、block state、entity/component、recipe、loot、worldgen
4. **入口**: player event、tick、load、schedule、GameTest
5. **限界**: データパックだけで変更できないAI・描画・client挙動を分離

```text
gameplay element
├── eventとして検知できるか
├── 現在状態をqueryできるか
├── commandで状態を変えられるか
├── JSON registry/loot/recipe/worldgenで定義できるか
└── resource packまたはmodが必要か
```

## 共通のフック

### block

| 目的 | 手段 |
|---|---|
| 座標のblockを判定 | `execute if block`, `execute if blocks` |
| block集合を判定 | block tag、block predicate |
| 設置を検知 | advancement `placed_block`, `item_used_on_block` 等 |
| 破壊結果を変更 | loot table |
| 配置・置換 | `setblock`, `fill`, `clone`, `place` |
| block entityを読む | `data get block`, predicate |
| worldへ生成 | configured/placed feature、structure、processor、worldgen |

block IDだけでなくblock stateを確認します。成長段階、向き、waterlogged、powered、oxidation、poseなどがstateなら `execute if block` で判定できます。block entity内のinventory等はNBT/component境界を別に確認します。

### entity

| 目的 | 手段 |
|---|---|
| entity typeで選択 | `@e[type=...]`、entity type tag |
| 距離・tag・scoreで絞る | selector |
| 複雑な状態を判定 | predicate、entity sub-predicate/component |
| 生成・移動・関係変更 | `summon`, `teleport`, `ride`, `execute on` |
| health/effect/attribute | `damage`, `effect`, `attribute` |
| eventを検知 | advancement trigger、damage/loot context |
| dropを変更 | entity loot table |

entityのAI goalを任意に追加することは、通常のデータパックだけではできません。既存AIを利用し、tag/score、attribute、equipment、passenger、predicate、周辺blockを組み合わせてゲームルールを作ります。

### itemとinteraction

- inventoryはadvancement trigger、predicate、`clear ... 0`、item commandで観測・操作
- 1.20.5以降はitem NBTでなくdata componentを使う
- custom itemはvanilla itemへcustom data/model/name等を付け、predicateで識別する
- 左クリック・右クリックの全状況を汎用eventとして直接受け取れるわけではない
- 対応trigger、usable item、consumable/equippable component、interaction entity等を組み合わせる

## 正式リリースごとの主要な着眼点

patch/hotfixだけのバージョンは省略し、gameplay追加の大きい正式リリースを示します。各行は完全な追加一覧ではありません。

| 正式リリース | 主要要素 | データパックでの着眼点 |
|---|---|---|
| [1.13](versions/1.13.md) | 水生mob、Drowned、Phantom、Turtle、Trident、Conduit、coral、kelp、bubble column | 水中arena、trident challenge、turtle保護、conduit領域、bubble elevator判定 |
| [1.14](versions/1.14.md) | Pillager、Ravager、Raid、Fox、Panda、Wandering Trader、village job blocks、Campfire、Scaffolding | raid進行、村人profession、取引・職業quest、campfire料理、scaffolding parkour |
| [1.15](versions/1.15.md) | Bee、Bee Nest/Hive、Honey Block、Honeycomb | 養蜂進捗、hive状態、蜂蜜収穫event、honey/slime movement course |
| [1.16](versions/1.16.md) | Piglin、Hoglin、Strider、Nether biome、Respawn Anchor、Lodestone、Target | bartering loot、Nether faction、strider race、anchor charge、target score |
| [1.17](versions/1.17.md) | Axolotl、Glow Squid、Goat、Copper、Lightning Rod、Powder Snow、Dripstone | lightning event、oxidation時間、goat arena、powder snow hazard、dripstone trap |
| [1.18](versions/1.18.md) | 新terrain/noise、large cave、mountain/cave biome | 高度・biome依存quest、custom worldgen、未生成chunk向けstructure |
| [1.19](versions/1.19.md) | Warden、Allay、Frog/Tadpole、Sculk、Mangrove、Ancient City | vibration stealth、warden追跡、allay sorting、frog variant/生育、ancient city探索 |
| [1.20](versions/1.20.md) | Camel、Sniffer、archaeology、Decorated Pot、Chiseled Bookshelf、Cherry/Bamboo | 騎乗race、sniffer発掘、brush loot、pot loot、bookshelf comparator puzzle |
| [1.20.5](versions/1.20.5.md) | Armadillo、Wolf Armor、wolf variant、item component化 | variant収集、armor耐久・修復、componentベースcustom item |
| [1.21](versions/1.21.md) | Breeze、Bogged、Trial Spawner、Vault、Crafter、Mace、Wind Charge、Trial Chamber | repeatable dungeon、player別reward、wind movement、custom enchantment、crafter automation |
| [1.21.2](versions/1.21.2.md) | Bundleの正式化、item/recipe形式変更 | custom loot kit、容量を使うquest item、component predicate |
| [1.21.4](versions/1.21.4.md) | Pale Garden、Creaking、Creaking Heart、Resin、Eyeblossom | 昼夜horror、heart探索、resin収集、biome侵入event |
| [1.21.5](versions/1.21.5.md) | 温帯/寒帯mob variant、Firefly Bush、Leaf Litter、Wildflowers、fallen tree、GameTest | variant図鑑、spawn条件data、環境quest、pack内自動test |
| [1.21.6](versions/1.21.6.md) | Happy Ghast、Dried Ghast、Harness、Locator Bar | 育成、空中race、複数player mount、hydration timer、waypoint game |
| [1.21.9](versions/1.21.9.md) | Copper Golem、Copper Chest、Golem Statue、Shelf、Mannequin、copper equipment | 自律仕分け、oxidation puzzle、statue pose信号、loadout交換、NPC表現 |
| [1.21.11](versions/1.21.11.md) | Nautilus、Zombie Nautilus、Camel Husk、Parched、Spear | 水中mount、騎乗combat、dash course、variant encounter、速度依存weapon challenge |
| [26.1](versions/26.1.md) | Golden Dandelion、baby model/sound variant、trade data化 | 成長停止collection、baby sanctuary、sound variant図鑑、custom trade progression |
| [26.2](versions/26.2.md) | Sulfur Cube、Sulfur Cave、Cinnabar/Sulfur、Geyser、Potent Sulfur | 吸収item別能力、浮力/爆発puzzle、geyser移動、custom archetype |

## 活用例

### 1.19: Sculk stealth

設計:

1. Ancient Cityまたは独自arenaへの侵入をlocation predicateで検知
2. playerごとの警戒度をscoreboardへ保存
3. vibrationやwarden関連eventを利用できる範囲でadvancement/predicateへ接続
4. 警戒度に応じてsound、darkness、warden配置を制御
5. death/logout/reload時の状態を明示的に処理

Sculk Sensorの全振動をデータパックが汎用callbackとして直接受け取れるとは限りません。取得できないeventは、advancement trigger、block state、scoreboardによる近似のどれを採用したか明記します。

### 1.20: Archaeology quest

利用面:

- suspicious blockのloot tableで発掘品を設計
- brush使用やinventory変化をadvancementで検知
- pottery sherdやcustom data付きitemを収集条件にする
- Decorated Potを納品先・展示物・loot containerとして利用
- structure/worldgenで発掘siteを配置

実装時はblock lootとarchaeology lootのcontextを混同せず、対象バージョンのvanilla JSONから同型を選びます。

### 1.21: Repeatable trial dungeon

利用面:

- Trial Spawner/Vaultのvanilla挙動を利用
- trial spawner configuration、loot table、structureを組み合わせる
- playerごとのclear状態はadvancement/scoreboardへ保存
- Mace/Wind Charge/Breezeをmovement・combat条件へ使う
- GameTestでwave終了、reward、resetを検証

block entity NBTを直接書き換える実装より、対象バージョンで公開されたdata-driven registry/configurationを優先します。

### 1.21.6: Dried Ghast育成

公式挙動では、Dried Ghastはwaterlogged状態で段階的にhydrationが進み、Ghastlingを経てHappy Ghastになります。

作成案:

- hydration stageをblock state reportで確認し、育成UIを表示
- 水から外したときの後退を失敗条件にする
- Ghastling/Happy Ghastをtag付けして所有者・course進捗を管理
- Happy Ghastの複数騎乗を協力raceへ利用
- Locator Bar/waypointで空中探索の目標を示す

blockを壊すとhydrationが保持されないvanilla挙動を、持ち運び可能な育成itemとして誤認しないようにします。

### 1.21.9: Copper Golem物流

Copper GolemはCopper Chestからitemを取り、周辺のChestへ分類する既存AIを持ちます。

作成案:

- 仕分け対象をquest納品として利用
- Copper Chestへの投入をinventory/block dataの差分で観測
- oxidation段階を制限時間や難易度へ使う
- Golem Statueのposeとcomparator出力で暗証puzzleを作る
- Shelfのhotbar交換でclass/loadout stationを作る

Golemの探索順や最後に選ぶChestへ依存する論理は避けます。厳密な配送が必要なら、storage queueとcommand処理を正本にし、Golemは演出・入力役にします。

同バージョンのtechnical entity `minecraft:mannequin` は、player avatarとしてequipment、attribute、effect、damage、pose、profile、descriptionを扱えます。quest NPC、combat dummy、装備展示に向きます。commandでのみspawnされるentityであり、本物のplayerや自由な会話AIとして扱わず、dialog・interaction entity・advancement等を別途接続します。

### 1.21.11: 騎乗combat

利用面:

- Nautilusを水中mountと呼吸制御へ使う
- Zombie Nautilus、Camel Husk、Parchedをbiome encounterへ使う
- Spearの速度依存攻撃をrace/combat scoreへつなぐ
- passenger/vehicle関係を `execute on` やpredicateで照合
- mount armor/equipmentを難易度・報酬にする

damageの原因、direct entity、vehicle/riderのどれをscoreへ帰属させるかをloot/advancement contextごとにtestします。

### 26.1: Golden Dandelionと成長停止

利用面:

- 成長を止めたbaby mobのcollection
- variant・biome・soundを組み合わせた図鑑
- sanctuary内だけ成長停止を許可するルール
- trade_set/villager_tradeで育成用品の解放を段階化

対象外entityはentity type tagやpredicateで除外します。見た目がbabyでも、vanillaのage lock対象かを推測しません。

### 26.2: Sulfur Cube archetype

26.2では `minecraft:sulfur_cube_archetype` registryと `minecraft:sulfur_cube_content` item componentが追加されました。吸収可能item群、浮力、爆発、接触damageをdata-drivenに構成できます。

活用面:

- item tagを「餌」としてarchetypeへ接続
- TNT系、浮力系、接触damage系の役割を分ける
- cave内の運搬・爆破・geyser puzzleへ利用
- 吸収contentをpredicate/componentで判定してscoreへ反映
- advancement、loot、custom archetypeを一連のprogressionにする

unknown entity predicate keyを拒否する26.2の厳格化を適用し、26.1.x形式の `type` fieldを混在させません。

### 26.3スナップショット: Dappled Forestとcamp

26.3 Snapshot 1〜8ではDappled Forest、Poplar、Shelf Mushroom、Red Shrub、Abandoned Camp、Cushion、Straw Bed、Concrete Stairs／Slabs、追加Explorer Mapが開発中です。

活用面:

- Abandoned Campのstructure tagとlootを探索questへ接続
- Dappled Forest／Poplarのworldgenを未生成chunkの探索目標にする
- Cushionの着席をcampの演出へ使い、進行状態はscoreboard／storageで別管理する
- Straw Bedをspawn pointを変えない一時休息として利用する
- data-driven brewing recipeとcamp lootをprogressionへつなぐ
- Abandoned Campのexplorer mapを次の探索目標へつなぎ、map生成失敗時は`minecraft:map_id`なしのitemを除外する
- Concrete Stairs／Slabsのblock／item tagを建築素材の選択や判定へ使う

スナップショットのentity／block interactionを正式仕様として固定せず、専用eventがない挙動を推測したadvancement triggerで実装しません。worldgenは既存worldで検証せず、対象スナップショットごとの実験worldと未生成chunkを使います。

## コンテンツカード

今後、バージョンプロファイルへgameplay要素を追記するときは、次の形式を使います。

```markdown
### minecraft:example

- 種別: block / entity / item / system
- 導入: 1.x
- vanilla挙動: ...
- 観測:
  - selector / block state / advancement / predicate / loot context
- 制御:
  - command / component / registry / loot / recipe / worldgen
- 永続状態: ...
- 作成案:
  - ...
- 限界:
  - ...
- 検証:
  - reports/registries.json
  - vanilla data path
  - functional test
```

追加内容を「できること」と結び付けるには、vanilla説明だけでなく、少なくとも観測・制御・限界の3項目を埋めます。

## 完全なID一覧を生成する

Markdownへ全block/entity IDを固定コピーせず、対象バージョンのJARから生成します。

確認する主なreport:

```text
generated/reports/registries.json
generated/reports/blocks.json
generated/data/minecraft/tags/block/
generated/data/minecraft/tags/entity_type/
generated/data/minecraft/loot_table/
generated/data/minecraft/advancement/
```

古いバージョンでは出力名・複数形directoryが異なる場合があります。

差分抽出の考え方:

```text
target registry IDs - previous release registry IDs = added IDs
previous registry IDs - target registry IDs = removed IDs
common IDs with changed reports/vanilla JSON = behavior candidates
```

ID追加だけでは、AI、drop、interaction、block state、tag membershipの変更を検出できません。公式release noteとvanilla dataのdiffを併用します。

## データパックだけではできないこと

通常、次はresource pack、server plugin、mod等が必要です。

- 完全に新しいentity typeと独自AIの追加
- 完全に新しいblock engine behaviorの追加
- 任意のclient入力を新eventとして受信
- custom GUI screenの自由な実装
- client rendering、animation、shaderの安定した制御

既存entityをtag/component/equipmentで役割化したり、display/interaction entity、dialog、text、particle、soundを組み合わせることはできます。「新しいIDを追加した」のか「vanilla IDを別用途に見せている」のかを利用者へ明示します。

複数playerの参加、進行中の条件変化、死亡・disconnect・chunk unloadをまたぐ複合要件は、構成要素の一覧だけで可否を判定しません。[`gameplay-requirements.md`](gameplay-requirements.md) の判定カード、状態遷移、競合処理、cleanup、機能testを適用します。

## 企画時の確認項目

```text
[ ] 対象バージョンで要素IDが存在する
[ ] block state/entity componentをreportで確認した
[ ] event検知がtick pollingだけになっていない
[ ] vanilla AIの選択順・乱数へ重要状態を依存させていない
[ ] 既存loot/recipe/worldgenの上書き範囲を限定した
[ ] multiplayerでownerとreward帰属を確認した
[ ] chunk unload、death、変換、成長、騎乗解除をtestした
[ ] データパック単独で不可能な部分を明記した
```

## 参照

- [`validation.md`](validation.md)
- [Mojang: Java Edition release notes](https://www.minecraft.net/en-us/articles?category=news)
- [Mojang: Java Edition 1.21.6](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-6)
- [Mojang: Java Edition 1.21.9](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-9)
- [Mojang: Java Edition 1.21.11](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-11)
- [Mojang: Java Edition 26.1](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-1)
- [Mojang: Java Edition 26.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-2)
- [Mojang: Minecraft 26.3 Snapshot 1](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-1)
- [Mojang: Minecraft 26.3 Snapshot 3](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-3)
- [Mojang: Minecraft 26.3 Snapshot 6](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-6)
- [Mojang: Minecraft 26.3 Snapshot 7](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-7)
- [Mojang: Minecraft 26.3 Snapshot 8](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-8)
- [Minecraft Wiki: Data pack](https://minecraft.wiki/w/Data_pack)
- [Minecraft Wiki: Java Edition version history](https://minecraft.wiki/w/Java_Edition_version_history)
