# Minecraft Java Edition Data Pack Harness

Minecraft Java Editionの正式版を完全一致で解決し、AIによるデータパック実装と検証を版ごとに再現可能にする共通ハーネスです。

仕様の入口は [`docs/README.md`](docs/README.md)、AI生成契約は [`docs/ai-authoring.md`](docs/ai-authoring.md) です。

## 前提

- Python 3.10以降
- `profiles`、`resolve`、`project-check`、基本的な静的検査はPython標準ライブラリだけで動作
- `fetch`、`reports` は公式Minecraft server JARのdownloadを明示実行する場合だけnetworkを使用
- `reports` と `server-test` のJava majorは対象版により異なる
- `server-test` は利用者が `--accept-eula` を指定しない限り起動しない

導入確認だけではJARをdownloadせず、JavaやMinecraft serverも起動しません。

## 配布単位

次を同じrevisionからまとめて配置します。

```text
VERSION
LICENSE
CHANGELOG.md
docs/
schemas/
templates/
tools/
tests/
```

一部だけをcopyするとprofile schema、project schema、文書リンク、テストが一致しなくなるため、上記を一つの配布単位として扱います。保守用の `.github/` と `AGENTS.md` は必須配布物ではありません。

## 推奨配置

```text
consumer-repository/
├── AGENTS.md
├── datapack-project.json
├── datapack/
└── tools/
    └── mc-datapack-harness/
        ├── VERSION
        ├── LICENSE
        ├── docs/
        ├── schemas/
        ├── templates/
        ├── tools/
        └── tests/
```

以下では `tools/mc-datapack-harness` を `<harness-root>` とします。`vendor/mc-datapack-harness` 等へ置く場合も、以後のpathを一貫して置換すれば動作します。

## 取得方法

### Git submodule

ハーネスのrevisionを利用者repositoryのgitlinkで固定できます。更新差分を分離したい場合の推奨方法です。

```bash
git submodule add https://github.com/asgrcat/mc-datapack-docs \
  tools/mc-datapack-harness
git -C tools/mc-datapack-harness checkout <tag-or-full-commit>
git add .gitmodules tools/mc-datapack-harness
```

### Git subtree

利用者repository内へ履歴を取り込み、clone時のsubmodule操作を避けたい場合に使います。

```bash
git subtree add \
  --prefix tools/mc-datapack-harness \
  https://github.com/asgrcat/mc-datapack-docs \
  <tag-or-commit> --squash
```

### Release archiveまたはcopy

Git連携を持たせない場合は、同一tagまたはfull commitのarchiveから配布単位をまとめてcopyします。`LICENSE`を削除せず、取得元のtag/full commitを導入記録に残します。

公開release/tagがないrevisionはfull commit SHAで固定します。移動するbranch名だけで導入版を記録しません。

## 初期設定

1. [`templates/datapack-project.json`](templates/datapack-project.json) を利用者repository rootへcopyする
2. `target_version`、`namespace`、`pack_root`、要求する `validation_level` を編集する。配置先が既定と異なる場合は `$schema` も実際の `<harness-root>` に合わせる
3. [`templates/AGENTS.snippet.md`](templates/AGENTS.snippet.md) を利用者側の `AGENTS.md` 等へ追記し、`<harness-root>` を実際のpathへ置換する

project設定の必須fieldは `schema_version`、`target_version`、`namespace`、`pack_root`、`validation_level` の5つです。省略時は次の値を使います。

| field | 既定値 |
|---|---|
| `edition` | `java` |
| `supported_versions.min` / `.max` | `target_version` |
| `experimental_features` | `false` |
| `server_type` | `vanilla` |
| `cache_dir` | `.cache/minecraft` |
| `report_dir` | `build/minecraft/<target_version>/generated` |

導入済みハーネスの版は `<harness-root>/VERSION` で確認します。submoduleは利用者repositoryのgitlink、subtreeは取り込んだ履歴、archive/copyは取得記録でrevisionを固定します。archive情報等をproject fileにも残したい場合だけ、`harness.version`、`harness.source`、`harness.commit` を任意で追加できます。

health check:

```bash
HARNESS_ROOT="tools/mc-datapack-harness"
python3 "$HARNESS_ROOT/tools/datapack_harness.py" --version
python3 "$HARNESS_ROOT/tools/datapack_harness.py" profiles
python3 "$HARNESS_ROOT/tools/datapack_harness.py" \
  project-check --project datapack-project.json
```

いずれもnetwork、Java、EULA同意を必要としません。

## AIへ実装を任せる流れ

```bash
HARNESS_ROOT="tools/mc-datapack-harness"

python3 "$HARNESS_ROOT/tools/datapack_harness.py" \
  project-check --project datapack-project.json

python3 "$HARNESS_ROOT/tools/datapack_harness.py" resolve 1.20.5

python3 "$HARNESS_ROOT/tools/datapack_harness.py" \
  validate-project --project datapack-project.json
```

`resolve` のversionはproject設定の `target_version` と一致させます。AIはproject設定が要求するlevelまで検証し、実行していない上位levelを成功と報告しません。

## 検証level

| level | 必要な証拠 | 主張できること |
|---|---|---|
| `generated` | profile解決とfile生成 | 対象版向けに生成した |
| `static` | `validate-project` 成功 | ハーネスの静的検査に成功した |
| `server` | exact serverでenabled/reload成功 | 対象版serverで読み込めた |
| `functional` | 機能test成功 | 記録した機能testに成功した |

`static` で完了するprojectは正常な利用形態です。`server` と `functional` は利用者が必要性、EULA、本番影響を判断して明示実行します。

`generated` levelの自動化は整備中です。配布するconsumer CI templateの最小保証は `static` とし、生成だけをCI成功条件にはしません。

## CI

[`templates/github/workflows/datapack-harness.yml`](templates/github/workflows/datapack-harness.yml) を利用者repositoryの `.github/workflows/` へcopyします。

`DATAPACK_HARNESS_ROOT` と `DATAPACK_PROJECT` の2値を実際の配置へ合わせます。templateはpull requestで `validate-project` を1回実行し、project設定とpackの静的検査をまとめて行います。JAR downloadやserver起動を暗黙に実行しません。

templateはsubmoduleを前提にしません。ハーネスをsubmoduleで導入したrepositoryだけ、checkout stepへ次を追加します。

```yaml
with:
  submodules: recursive
```

## 更新

更新前に [`CHANGELOG.md`](CHANGELOG.md) と導入先の変更を確認します。

- submodule: ハーネス内で新しいtag/full commitをcheckoutし、利用者repositoryでgitlinkをcommit
- subtree: `git subtree pull --prefix ... <tag-or-commit> --squash`
- archive/copy: 新旧の配布単位を比較し、利用者が加えた変更を退避してから置換

更新後:

1. `<harness-root>/VERSION` と導入方法が固定するtag/full commitを確認する
2. 任意の `harness` metadataを使用している場合はその値も更新する
3. `profiles`、`project-check`、ハーネスのunit testを実行する
4. 生成済みpackへ要求levelの検証を再実行する

## アンインストール

削除してよい範囲は導入した `<harness-root>` 全体です。submoduleの場合はgitlinkと `.gitmodules` の該当entry、subtree/copyの場合は配置directoryを削除します。

利用者側の `datapack-project.json`、`AGENTS.md` の追記、CI workflow、生成したdata packは利用者repositoryの所有物です。自動削除せず、不要か確認して個別に削除します。cache/reportはproject設定のpathを確認してから削除します。

## 保証範囲

ハーネスは既存worldや本番serverを自動更新せず、world backup、配布、本番導入も代行しません。検証levelごとの詳細は [`docs/harness.md`](docs/harness.md) を参照してください。
