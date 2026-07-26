# AI データパック生成契約

この文書は、利用者repositoryのproject設定と要件から、AIがどの資料をどの順で適用するかを定義します。

## 入力

永続化するproject設定の正本は、利用者repository rootの `datapack-project.json` です。schemaとtemplateは次にあります。

- `<harness-root>/schemas/datapack-project.schema.json`
- `<harness-root>/templates/datapack-project.json`

実装前に検査します。

```bash
python3 <harness-root>/tools/datapack_harness.py \
  project-check --project datapack-project.json
```

- `target_version`、`namespace`、`pack_root`、対応範囲、experimental許可、server type、要求検証level、cache/report pathを会話だけに保持しない
- 実装要件はproject設定とは別に管理する
- `edition` は `java` だけを受け付ける
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
  active_rules = target profile's "AI 生成規則" bullets
  rule_history = ancestor rules for reference only

  exact_release = official_manifest.release[target_version]
  reports = generate_reports(exact_release.server_jar)
  capabilities.commands = reports/commands.json
  capabilities.registries = reports/registries.json
  capabilities.vanilla_data = generated/data/minecraft

  state = common rules from commands.md and json-formats.md
  apply target profile's metadata and active_rules
  if requirements mention gameplay content:
    resolve observations and controls from content-hooks.md

  emit using target profile's data_pack_format and directory_schema
  reject commands, IDs and JSON resources absent from capabilities
```

`inherits` はmetadataとAI規則の履歴を追跡するために使います。対象版へ適用するのは対象版自身の `active_ai_rules` だけです。祖先版の規則は `rule_history` として出力しますが、後続版で解除された禁止事項を累積適用しません。Markdown本文の任意見出しから追加・変更・削除を推測して機能集合を合成せず、command、registry、vanilla JSONの有効集合は対象版JARから直接得ます。

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

## 検証levelと報告

project設定の `validation_level` を要求levelとします。

| level | 必要な証拠 | AIが報告できること |
|---|---|---|
| `generated` | profile解決と全file生成 | 対象版向けに生成した |
| `static` | `validate-project` 成功 | 静的検査に成功した |
| `server` | exact serverでenabled/reload成功 | 対象版serverで読み込めた |
| `functional` | 機能test成功 | 記録した機能testに成功した |

AIは実行済みlevel、使用した対象版、残っているwarning、未実施の上位levelを明記します。`static` が要求levelなら、server検査を省略してもハーネス利用失敗ではありません。

報告形式:

```text
target_version:
requested_level:
completed_level:
evidence:
warnings:
not_run:
```

levelにかかわらず、永続状態のowner・初期化・migration・cleanup、experimental利用、world upgradeの不可逆性、追加block/entityの観測・制御上の限界は、該当する場合に実装説明へ含めます。

`server` は利用者がEULA同意と実行環境を判断した場合だけ実行します。`functional` は実行した機能test結果だけを証拠にします。
