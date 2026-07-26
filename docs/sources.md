# 資料と検証方針

## 優先順位

1. **Mojang 公式リリースノート**: 正式版の technical changes、data pack version、移行事項の一次資料
2. **Mojang 公式 version manifest / server JAR**: 正式版 ID、公開時刻、実際の command graph、registry、vanilla data の機械可読な正本
3. **Minecraft Wiki**: 複数スナップショットに分散した変更履歴、構文表、pack format 対応表の照合

資料間に食い違いがあるときは、対象正式版の server JAR の挙動を優先します。Wiki だけにある記述には、可能な限り版ページまたはコマンド/JSON 個別ページを併記します。

## 共通資料

- [Minecraft Java Edition release notes](https://www.minecraft.net/en-us/articles?category=news)
- [公式 version manifest v2](https://piston-meta.mojang.com/mc/game/version_manifest_v2.json)
- [Minecraft Wiki: Data pack](https://minecraft.wiki/w/Data_pack)
- [Minecraft Wiki: Pack format](https://minecraft.wiki/w/Pack_format)
- [Minecraft Wiki: `pack.mcmeta`](https://minecraft.wiki/w/Pack.mcmeta)
- [Minecraft Wiki: Function](https://minecraft.wiki/w/Function_(Java_Edition))
- [Minecraft Wiki: Commands](https://minecraft.wiki/w/Commands)
- [Minecraft Wiki: Creating a data pack](https://minecraft.wiki/w/Tutorial:Creating_a_data_pack)
- [Minecraft Wiki: Running the data generator](https://minecraft.wiki/w/Tutorial:Running_the_data_generator)

## 版ページの URL

各版ファイルは次を参照します。

- 公式: `https://www.minecraft.net/en-us/article/minecraft-java-edition-<version>`。古い記事でこの slug が存在しない場合は、その版ファイルに実在する公式記事 URL を記す
- Wiki: `https://minecraft.wiki/w/Java_Edition_<version>`

Minecraft Wiki はコミュニティ運営であり Mojang 公式ではありません。変更の発見と横断表には有用ですが、`data_pack_format` と構文は公式 JAR でも再検証してください。

Wiki の `Pack format` 本文や一覧には更新遅れの注意書きが出る場合があります。本リポジトリでは安定版の値を各公式 release note、公式 version manifest、Wiki の版別ページおよび `Template:Data_pack_format` と照合しました。また、Wiki の現行 folder一覧に表示される `upcoming`（現在は26.3 snapshot）項目は、26.2の安定版一覧から除外しています。

## 更新日

最終照合日: 2026-07-26（JST）

対象となる最新正式版: Java Edition 26.2（2026-06-16、data pack format 107.1）
