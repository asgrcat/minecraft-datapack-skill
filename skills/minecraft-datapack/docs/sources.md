# 資料と検証方針

## 優先順位

1. **Mojang 公式リリースノート／スナップショット記事**: 対象バージョンの technical changes、data pack version、移行事項の一次資料
2. **Mojang 公式 version manifest / server JAR**: 正式リリース／スナップショット ID、公開時刻、実際の command graph、registry、vanilla data の機械可読な正本
3. **Minecraft Wiki**: 複数スナップショットに分散した変更履歴、構文表、pack format 対応表の照合

資料間に食い違いがあるときは、対象IDの server JAR の挙動を優先します。Wiki だけにある記述には、可能な限りバージョンページまたはコマンド/JSON 個別ページを併記します。

## 共通資料

- [Minecraft Java Edition release notes](https://www.minecraft.net/en-us/articles?category=news)
- [公式 version manifest v2](https://piston-meta.mojang.com/mc/game/version_manifest_v2.json)
- [Minecraft Wiki: Data pack](https://minecraft.wiki/w/Data_pack)
- [Minecraft Wiki: Pack format](https://minecraft.wiki/w/Pack_format)
- [Minecraft Wiki: `pack.mcmeta`](https://minecraft.wiki/w/Pack.mcmeta)
- [Minecraft Wiki: Function](https://minecraft.wiki/w/Function_(Java_Edition))
- [Minecraft Wiki: Commands](https://minecraft.wiki/w/Commands)
- [Minecraft Wiki: Advancement](https://minecraft.wiki/w/Advancement)
- [Minecraft Wiki: Scoreboard](https://minecraft.wiki/w/Scoreboard)
- [Minecraft Wiki: NBT path](https://minecraft.wiki/w/NBT_path_format)
- [Minecraft Wiki: Creating a data pack](https://minecraft.wiki/w/Tutorial:Creating_a_data_pack)
- [Minecraft Wiki: Running the data generator](https://minecraft.wiki/w/Tutorial:Running_the_data_generator)

詳細書式リファレンスで特に使う一次資料:

- [Mojang: Java Edition 1.18.2](https://feedback.minecraft.net/hc/en-us/articles/4531177623437-Minecraft-Java-Edition-1-18-2): universal registry tag、density function、configured structure
- [Mojang: Java Edition 1.20.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-5): item stack component、loot、predicate、recipe result
- [Mojang: Java Edition 1.21](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21): enchantment、painting、jukebox song、単数形ディレクトリ
- [Mojang: Java Edition 1.21.5](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-5): text／SNBT、entity component、GameTest、mob variant／spawn condition
- [Mojang: Java Edition 1.21.11](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-11): environment attributes、timeline、modifier、補間
- [Mojang: Java Edition 26.1](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-1): world clock、time marker、trade、sound variant
- [Mojang: Java Edition 26.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-2): entity predicate、worldgen、dimension type、Sulfur Cube
- [Mojang: 26.3 Snapshot 1](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-1): slot source、pottery、configured feature／material rule再編
- [Mojang: 26.3 Snapshot 2](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-2): block transformer、feature／carver再編
- [Mojang: 26.3 Snapshot 3](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-3): post effect、number provider、brewing recipe
- [Mojang: 26.3 Snapshot 4](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-4): registry参照、loot／predicate／advancement再編
- [Mojang: 26.3 Snapshot 5](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-5): inline値と参照の混在list
- [Mojang: 26.3 Snapshot 6](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-6): fuel inline数値、noise／density function再編
- [Mojang: 26.3 Snapshot 7](https://www.minecraft.net/en-us/article/minecraft-26-3-snapshot-7): block state、item animation、exploration map、density function精度

26.2以降のdata generatorが出力する`reports/datapack.json`は、data packから要素を定義できるregistry、tag対応、安定性を列挙します。`registries.json`だけでは「IDが存在すること」と「data packから新規entryを追加できること」を区別できないため、両方を照合します。

## gameplay要素

block、entity、itemの追加情報は、対象正式リリースのMojang release noteを一次資料にします。データパックから利用できる入口は次の順で確定します。

1. 対象バージョンのserver JARのregistry/block/item reportでIDとstateを確認
2. vanilla advancement、loot table、tag、worldgenから公式の利用例を確認
3. release noteのvanilla挙動とdata pack technical changesを結び付ける
4. Minecraft Wikiの個別block/entity/commandページで挙動を横断照合
5. selector、predicate、command、GameTestを対象バージョンで実行

vanilla gameplayに存在することと、データパック用callbackが公開されていることは別です。専用advancement triggerやpredicateがないinteractionを、推測したevent名で記述しません。

## データ駆動JSONパラメータ

item component、dimension/worldgen、enchantment、variant、predicate、advancement、loot table、recipe、item modifierは次の証拠を分けて記録します。

1. `registries.json`と`datapack.json`でregistry/type IDとdata packから追加できるelementを確定
2. `generated/data/minecraft/`とitem default component reportでvanillaが実際に使うfield pathと型を確認
3. Mojang正式リリースノートでfieldの意味、default、値域、rename、削除を確認
4. Minecraft Wikiのdata format個別ページでsnapshot間の変更とgameplay上の説明をcross-check
5. exact release serverのreloadと機能testでcodecと動作を分けて検査

`json-catalog`のregistry ID一覧はreportに公開されたentry集合、`observed_shapes`はvanilla使用例の集計です。`registry_sources: unknown`や`source.datapack: null`はreportから判定できない状態であり、機能非対応を意味しません。観測fieldを完全なJSON Schemaまたはcodecの全分岐として扱いません。保証ラベルとfamily別の出典は[`json-parameters/README.md`](json-parameters/README.md)および各子文書に記載します。

## バージョンページの URL

各バージョンファイルは次を参照します。

- 公式: `https://www.minecraft.net/en-us/article/minecraft-java-edition-<version>`。古い記事でこの slug が存在しない場合は、そのバージョンファイルに実在する公式記事 URL を記す
- Wiki: `https://minecraft.wiki/w/Java_Edition_<version>`

Minecraft Wiki はコミュニティ運営であり Mojang 公式ではありません。変更の発見と横断表には有用ですが、`data_pack_format` と構文は公式 JAR でも再検証してください。

## `release_date` の定義

正式リリースプロファイルの `release_date` は、Mojangが一般利用者向けに正式リリースを公開したcalendar dateです。スナップショットプロファイルでは、そのスナップショットの公開日を表します。地域表示による日付差がある場合は、バージョンページと公式告知で採用した日付を記録します。

公式version manifestの `releaseTime` はartifact metadataのtimestampであり、`release_date` と一致することを要求しません。JAR取得、対象IDの完全一致、並び順の機械処理には `release_date` を使わず、manifestのID、type、`releaseTime`、download URL、SHA-1を使います。

Wiki の `Pack format` 本文や一覧には更新遅れの注意書きが出る場合があります。本リポジトリでは安定リリースの値を各公式 release note、公式 version manifest、Wiki のバージョン別ページおよび `Template:Data_pack_format` と照合しました。26.3の開発値は安定リリース一覧から除外し、[`snapshots/README.md`](snapshots/README.md) へ分離しています。

## 更新日

最終照合日: 2026-08-05（JST）

対象となる最新正式リリース: Java Edition 26.2（2026-06-16、data pack format 107.1）

対象となる最新収録スナップショット: Java Edition 26.3 Snapshot 7（2026-08-04、data pack format 115.0）
