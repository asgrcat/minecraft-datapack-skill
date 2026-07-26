# 資料と検証方針

## 優先順位

1. **Mojang 公式リリースノート**: 正式リリースの technical changes、data pack version、移行事項の一次資料
2. **Mojang 公式 version manifest / server JAR**: 正式リリース ID、公開時刻、実際の command graph、registry、vanilla data の機械可読な正本
3. **Minecraft Wiki**: 複数スナップショットに分散した変更履歴、構文表、pack format 対応表の照合

資料間に食い違いがあるときは、対象正式リリースの server JAR の挙動を優先します。Wiki だけにある記述には、可能な限りバージョンページまたはコマンド/JSON 個別ページを併記します。

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

## gameplay要素

block、entity、itemの追加情報は、対象正式リリースのMojang release noteを一次資料にします。データパックから利用できる入口は次の順で確定します。

1. 対象バージョンのserver JARのregistry/block/item reportでIDとstateを確認
2. vanilla advancement、loot table、tag、worldgenから公式の利用例を確認
3. release noteのvanilla挙動とdata pack technical changesを結び付ける
4. Minecraft Wikiの個別block/entity/commandページで挙動を横断照合
5. selector、predicate、command、GameTestを対象バージョンで実行

vanilla gameplayに存在することと、データパック用callbackが公開されていることは別です。専用advancement triggerやpredicateがないinteractionを、推測したevent名で記述しません。

## バージョンページの URL

各バージョンファイルは次を参照します。

- 公式: `https://www.minecraft.net/en-us/article/minecraft-java-edition-<version>`。古い記事でこの slug が存在しない場合は、そのバージョンファイルに実在する公式記事 URL を記す
- Wiki: `https://minecraft.wiki/w/Java_Edition_<version>`

Minecraft Wiki はコミュニティ運営であり Mojang 公式ではありません。変更の発見と横断表には有用ですが、`data_pack_format` と構文は公式 JAR でも再検証してください。

## `release_date` の定義

バージョンプロファイルの `release_date` は、Mojangが一般利用者向けに正式リリースを公開したcalendar dateです。地域表示による日付差がある場合は、バージョンページと公式告知で採用した日付を記録します。

公式version manifestの `releaseTime` はartifact metadataのtimestampであり、`release_date` と一致することを要求しません。JAR取得、正式リリースの完全一致、並び順の機械処理には `release_date` を使わず、manifestのrelease ID、`releaseTime`、download URL、SHA-1を使います。

Wiki の `Pack format` 本文や一覧には更新遅れの注意書きが出る場合があります。本リポジトリでは安定リリースの値を各公式 release note、公式 version manifest、Wiki のバージョン別ページおよび `Template:Data_pack_format` と照合しました。また、Wiki の現行 folder一覧に表示される `upcoming`（現在は26.3 snapshot）項目は、26.2の安定リリース一覧から除外しています。

## 更新日

最終照合日: 2026-07-26（JST）

対象となる最新正式リリース: Java Edition 26.2（2026-06-16、data pack format 107.1）
