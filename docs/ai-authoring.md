# AI データパック生成契約

この文書は、利用者がゲーム版と要件を指定したとき、AI がどの資料をどの順で適用するかを定義します。

## 入力

必須:

```yaml
edition: java
target_version: "1.20.5"
requirements:
  - "初回参加時に名前付きの剣を配る"
```

必要に応じて:

```yaml
namespace: example
supported_versions:
  min: "1.20.5"
  max: "1.21.1"
experimental_features: false
server_type: vanilla
```

- edition未指定時でも、この文書群ではJava Editionと解釈する。ただし出力に明記する
- versionは [`versions/README.md`](versions/README.md) の正式版IDに完全一致させる
- 一覧にないsnapshot/pre-release/Bedrock版を最寄り版へ丸めない
- `26.1` を `1.26.1` に変換しない。文字列の辞書順や単純なsemver比較を使わず、version indexの順序を使う

## 解決アルゴリズム

```text
resolve(target_version):
  profile = versions/<target_version>.md
  if profile does not exist:
    stop as unsupported

  validate profile against versions/profile.schema.json
  chain = resolve_inheritance(profile)
  rules = collect each profile's "AI 生成規則" bullets in chain order

  exact_release = official_manifest.release[target_version]
  reports = generate_reports(exact_release.server_jar)
  capabilities.commands = reports/commands.json
  capabilities.registries = reports/registries.json
  capabilities.vanilla_data = generated/data/minecraft

  state = common rules from commands.md and json-formats.md
  apply target profile's metadata and collected rules
  if requirements mention gameplay content:
    resolve observations and controls from content-hooks.md

  emit using target profile's data_pack_format and directory_schema
  reject commands, IDs and JSON resources absent from capabilities
```

`inherits` はmetadataとAI規則の由来を追跡するために使います。Markdown本文の任意見出しから追加・変更・削除を推測して機能集合を合成しません。command、registry、vanilla JSONの有効集合は、対象版JARから直接得ます。

機械処理では [`versions/profile.schema.json`](versions/profile.schema.json) の基本クラスと `compatibility_tags` を解釈します。本文の「コマンド」「JSON」「変更」などの見出し名は入力スキーマではありません。

## fail-closed

次の場合は推測で出力しません。

- 対象版にcommand branchがあるか不明
- JSONの必須field、`type`固有field、loot contextが不明
- item component、entity predicate、text componentが境界版のどちらか不明
- block/item/entity/registry IDが対象版に存在するか不明
- experimental registryを通常worldで利用できるか不明

代わりに対象版server JARから [`validation.md`](validation.md) のreport/vanilla dataを生成し、確認後に出力します。

## 出力順

1. 対象版、data pack format、namespace
2. 完全なdirectory tree
3. `pack.mcmeta`
4. 全 `.mcfunction`
5. 全 JSON と必要な `.nbt` structure
6. entry pointごとのexecutor、位置、dimension、状態owner
7. install/reload手順
8. 対象版での検証項目
9. 複数版対応なら共通部分とoverlayの対応表

「変更する部分だけ」を依頼された場合を除き、互いに参照するfileは省略しません。

## resource命名

- 利用者指定がなければnamespaceは `generated` のような衝突しにくいlowercase IDを提案し、確定値を全fileで統一
- 自作function/tag/storage/predicate/loot tableは常にnamespaceを明示
- scoreboard objectiveはresource locationではないため、対象版の長さ制約内で短い固有prefixを使う
- fake player/entity tagも他packと衝突しないprefixを持つ
- `minecraft` namespaceは `load`/`tick` tagへのentry追加や、明示されたvanilla overrideだけに使う

## 典型的な境界テスト

### 1.20.4 と1.20.5

要件: 名前付きdiamond swordを配る。

1.20.4:

```mcfunction
give @s minecraft:diamond_sword{display:{Name:'{"text":"Blade"}'}}
```

1.20.5:

```mcfunction
give @s minecraft:diamond_sword[minecraft:custom_name='{"text":"Blade"}']
```

pack formatだけを変更して同じfunctionを共有しません。

### 1.20.6 と1.21

要件: `example:init` function。

```text
# 1.20.6
data/example/functions/init.mcfunction

# 1.21
data/example/function/init.mcfunction
```

resource locationはどちらも `example:init` ですが、物理pathが異なります。

### 1.21.4 と1.21.5

要件: text表示。

1.21.4以前のJSON text文字列例を、1.21.5のSNBT component引数へそのまま二重quoteしません。click/hover field renameも同時に適用します。

### 26.1.2 と26.2

要件: player判定predicate。

26.1.2:

```json
{
  "type": "minecraft:player"
}
```

26.2:

```json
{
  "minecraft:entity_type": "minecraft:player"
}
```

26.2ではunknown fieldを拒否するため、旧 `type` を互換用に併記しません。

## 複数版

1. 最古版の機能集合を基底にする
2. [`compatibility.md`](compatibility.md) の全境界を列挙
3. 同一pathで両立しないfileをoverlayへ
4. 1.20.2未満を含む場合、overlayを利用できないため別pack配布も検討
5. 1.21.9のmetadata境界をまたぐ場合、旧reader用fieldを残す条件を適用
6. 全正式版でtestできない場合、「対応済み」と断定しない

## 完了条件

- 対象版profileの禁止事項が0件
- command graphに全 `.mcfunction` 行が一致
- strict JSON parse成功
- registry/resource reference欠落なし
- `/reload` logにparse/codec/tag errorなし
- load/tick/reward/schedule等のentry pointが実行される
- 永続状態のowner、初期化、migration、cleanupが定義される
- 追加block/entityを使う場合、観測・制御方法とデータパック単独の限界が明記される
- 要件のfunctional testが成功
- experimental利用とworld upgrade不可逆性を利用者へ明示

これらを文書上の自己申告だけで完了扱いにしません。[`harness.md`](harness.md) のprofile解決、対象版report、静的検査、server testの終了codeと、機能test結果を記録します。
