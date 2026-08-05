# 実行ハーネス

`tools/datapack_harness.py` は、正式リリースと収録済みスナップショットのプロファイル解決、公式server JARの取得とSHA-1検証、data generator、pack静的検査、server起動・reload検査を実行します。このCLIを使用する場合だけPython 3.10以降が必要で、追加のPython packageは使用しません。

MinecraftのBrigadierとcodecを再実装しません。静的に確定できない項目は警告します。server検査を行うかはproject設定の要求levelと利用者の判断で決めます。

## 0. project設定

利用者repositoryの `datapack-project.json` に対象バージョン、namespace、pack root、要求検証levelを保存します。schemaとtemplateはrepository rootの `schemas/`、`templates/` にあります。

必須fieldは `schema_version`、`target_version`、`namespace`、`pack_root`、`validation_level` です。対応範囲は省略すると対象バージョンだけ、editionはJava、experimentalは無効、server typeはvanillaになります。cacheは `.cache/minecraft`、reportは `build/minecraft/<target_version>/generated` を使います。配布元のversion/source/commitをprojectにも残す場合は、任意の `harness` objectを追加できます。導入済みのバージョンの正本は `VERSION` です。

収録済みスナップショットを `target_version` にする場合は、意図的な実験利用を示すため `experimental_features: true` が必須です。

```bash
python3 <harness-root>/tools/datapack_harness.py \
  project-check --project datapack-project.json
```

生成済みpackを設定値で静的検査します。

```bash
python3 <harness-root>/tools/datapack_harness.py \
  validate-project --project datapack-project.json
```

pathはproject fileのdirectoryを基準に解決します。`validate-project` は静的検査だけを実行し、要求levelが `server` または `functional` の場合は残っているlevelを表示します。JAR downloadやserver起動へ自動的に進みません。

## 1. プロファイル検査

```bash
python3 tools/datapack_harness.py profiles
```

検査内容:

- 全50正式リリースと収録済みスナップショットの必須front matter
- `compatibility` の基本クラス
- `compatibility_tags` の定義済み値
- filenameとversionの一致
- `inherits` の参照、循環、単一chain
- `AI 生成規則` の存在
- `JSONパラメータ差分` の存在と、item・dimension/worldgen・enchantment・variant・predicate・advancement・loot_table・recipe・item_modifier各1件のlabel付きbullet
- `profile.schema.json` のJSON構文

front matterのschemaは [`versions/profile.schema.json`](versions/profile.schema.json) です。Markdown本文の任意見出しを機械可読な差分fieldとして扱いません。

## 2. 対象バージョンの解決

```bash
python3 tools/datapack_harness.py resolve 1.20.5
```

JSON出力:

- 対象バージョンのprofile
- 1.13から対象バージョンまでのinheritance chain
- 対象バージョンだけの `active_ai_rules`
- 過去バージョンの参考履歴 `rule_history`（対象バージョンへ適用しない）
- 1.13から対象バージョンまでのfamily別追加・変更・削除・互換性 `json_parameter_history`（各バージョンの`changes`は9 familyのobject）
- command/registry/vanilla dataの正本path
- server検査に必要なJava major

versionは完全一致です。[`snapshots/README.md`](snapshots/README.md)にあるID以外のsnapshot、pre-release、Bedrock Edition、近似semverを受け付けません。

`rule_history` は変更理由を追跡するための参考情報です。過去バージョンの禁止規則を対象バージョンへ累積適用しません。`json_parameter_history`はバージョン別プロファイルの差分を時系列で提示しますが、対象バージョンで使用可能なcommand、registry、vanilla resourceは自然言語だけで合成せず、対象バージョンのreport/dataで決定します。

## 3. 公式server JAR

```bash
python3 tools/datapack_harness.py fetch 1.20.5 \
  --cache-dir .cache/minecraft
```

処理:

1. 公式version manifest v2を取得
2. `id`完全一致かつ正式リリースでは`type: release`、スナップショットでは`type: snapshot`を1件選択
3. version metadataからserver URLとSHA-1を取得
4. JARをdownload
5. local JARのSHA-1を検証
6. metadataをcacheへ保存

SHA-1不一致はerrorです。既存cacheも毎回hashを確認し、不一致なら再取得します。

## 4. reportとvanilla data

```bash
python3 tools/datapack_harness.py reports 1.20.5 \
  --cache-dir .cache/minecraft \
  --output build/1.20.5/generated \
  --java /path/to/java
```

バージョンに応じてdata generatorの起動方法を切り替えます。

- 1.13〜1.17.1: classpathから `net.minecraft.data.Main`
- 1.18以降: bundlerのmain classを指定

data generatorは自動削除される一時working directoryで実行します。bundlerが展開する `libraries/`、`versions/`、`logs/` はリポジトリへ残りません。`--output` は起動時のdirectoryを基準に絶対pathへ解決します。

生成成功時にはoutput rootへ `.datapack-harness-report.json` を保存し、対象IDと検証済みserver JARのSHA-1を記録します。`json-catalog`はこのprovenanceを必須とし、CLIのversionと一致しないreportを拒否します。

必要Java major:

| 対象バージョン | Java |
|---|---:|
| 1.13〜1.16.5 | 8 |
| 1.17〜1.17.1 | 16 |
| 1.18〜1.20.4 | 17 |
| 1.20.5〜1.21.11 | 21 |
| 26.1以降 | 25 |

ハーネスは必要majorを表示します。複数JDKがある環境では `--java` へ対象バージョン用の実行ファイルを指定します。

現行のdata generatorでは、`commands.json`、`registries.json`に加えて
`datapack.json`も確認します。`datapack.json`は、各registryについてdata pack
からelementを追加できるか、tagを持てるか、安定した組み込みregistryかを
区別します。itemの既定componentは`reports/minecraft/components/item/`、
実際のJSON例は`data/minecraft/`を使います。

## 5. JSONパラメータカタログ

data generatorの出力から、対象バージョン固有のitem component、enchantment effect、variant、worldgen、predicate、advancement trigger、loot、recipeのtype IDと、vanilla JSONで観測できるfield pathを集計します。

```bash
python3 tools/datapack_harness.py json-catalog 1.21.11 \
  --reports build/1.21.11/generated \
  --output build/1.21.11/json-catalog.json
```

`registry_ids`と`worldgen_dispatchers`は、`registries.json`に公開されたentry IDを列挙します。`registry_sources`は、各`registry_ids` groupの参照元registryを`present`（reportに公開）または`unknown`（このreportでは未公開）で示します。`observed_shapes`は`generated/data/minecraft/`、旧バージョンの`generated/reports/{worldgen/,}minecraft/`、item reportにあるvanilla例を走査し、JSON pathごとに実際に現れた型を出力します。先行する`reports` commandが記録したversionとserver JAR SHA-1も出力へ含めます。

用途:

- source registryが`present`のgroupで、対象バージョンにcomponent/effect/feature/condition/function/trigger/recipe typeが公開されているか確認
- 主要JSON familyのvanilla使用fieldを検索
- 境界バージョン間でregistry IDと観測fieldを機械比較
- 手書き例を作る前に同型のvanilla fileを特定

`registry_ids`が空でも、`registry_sources`が`unknown`なら非対応とは確定できません。`source.datapack`が`null`のバージョンでは、空の`data_driven_registries`も「追加可能なregistryなし」ではなくreport未公開です。`observed_shapes`はcodec schemaではありません。vanillaが使用しない任意field、条件付き必須field、値域、排他的な組合せは出力から確定できないため、[`json-parameters/README.md`](json-parameters/README.md)のfamily別説明とserver検査を併用します。

## 6. pack静的検査

```bash
python3 tools/datapack_harness.py validate-pack 1.20.5 path/to/pack \
  --reports build/1.20.5/generated
```

検査内容:

- `pack.mcmeta` のtop-level object、JSON、対象format包含
- 全 `.json` のUTF-8/JSON構文
- 全 `.mcfunction` のUTF-8。BOMと不正byte列を拒否し、他fileの検査は継続
- namespace/resource pathの文字
- plural/singular data directory
- function tag directory
- `.mcfunction` の先頭 `/`
- macroと行継続の1.20.2境界
- `commands.json` に存在するroot literal
- 自namespaceのfunction参照切れ
- `registries.json` と照合できないvanilla ID候補

制限:

- command引数全体のBrigadier parseは再実装しない
- registryにないserializer IDと、存在しないID候補を完全には区別できない
- Minecraft codecの必須field・loot contextは静的に保証しない
- zip packは静的検査前に展開する

これらはwarningとして残します。要求levelが `static` ならwarningと未検査範囲を報告して完了できます。`server` 以上を要求する場合だけ、次のserver検査を追加します。

consumer CIの最小levelは `static` です。`generated` levelの自動化は整備中であり、生成だけをCI成功の証拠にはしません。

## 7. server起動とreload

```bash
python3 tools/datapack_harness.py server-test 1.20.5 path/to/pack \
  --cache-dir .cache/minecraft \
  --java /path/to/java \
  --accept-eula \
  --expect-log "PACK_TEST_LOAD_OK" \
  --log build/1.20.5/server-test.log
```

`server-test`:

1. 一時server directoryを作る
2. packを新規worldの `datapacks` へcopy
3. exact release serverを起動
4. startup後のenabled一覧に `file/pack-under-test` があることを確認
5. `reload` を送り、開始とadvancement reload完了logを待つ
6. reload後のenabled一覧にもpackがあることを再確認
7. serverを停止
8. exit statusとparse/load/function/JSON errorを検査

`--accept-eula` は、実行者がMinecraft EULAへ同意したことを明示する必須flagです。指定なしではserverを起動しません。

`--expect-log` は任意かつ複数指定可能です。packの `minecraft:load` entry pointから一意な文字列をconsoleへ出すテスト用functionを用意し、その文字列を指定すると、reload区間内での実行も肯定的に確認できます。指定しない場合、ハーネスが保証するのはpackの有効化、reload完了、既知load error不在までであり、任意のentry point実行までは保証しません。

`--log` を指定した場合、pack未有効、reload timeout、load errorなどで検査が失敗しても、終了までに収集したserver出力と `[HARNESS] ERROR` の失敗理由を保存します。一時server directoryが削除された後も診断に利用できます。

server検査は一時worldを使用します。既存worldをupgradeしません。旧world migration testは、利用者が複製した専用worldで別に行います。

### 境界バージョンのintegration matrix

通常CIのunit testでは、旧形式と現行形式の代表的なenabled一覧、reload開始・完了、失敗logをparserへ入力します。これは実serverの起動確認ではありません。

release前には、EULAへ同意できる隔離環境でバージョンごとに正しい最小packとJDKを用意し、次を実行します。

| 正式リリース | Java | 確認する境界 |
|---|---:|---|
| 1.13 | 8 | 最古バージョン、複数形folder |
| 1.17 | 16 | Java 16 |
| 1.18 | 17 | bundler起動 |
| 1.20.5 | 21 | item component |
| 1.21.9 | 21 | minor pack format metadata |
| 26.2 | 25 | 最新正式リリース |
| 26.3-snapshot-7 | 25 | 最新収録スナップショット |

各バージョンで `--expect-log` を指定し、成功logを保存します。実行していないバージョンについて「server-test互換性確認済み」と記録しません。

## 保証レベル

| 段階 | 保証 |
|---|---|
| `profiles` | バージョンのmetadata・継承・互換性schemaの整合 |
| `resolve` | 対象バージョンと適用規則の決定 |
| `fetch` | 公式release／snapshot JARとSHA-1 |
| `reports` | 対象バージョンのcommand graph・registry・vanilla data |
| `validate-pack` | pack構造と一部参照の静的検査 |
| `server-test` | exact serverでpack有効化、reload完了、既知load error不在を検査 |
| GameTest/client E2E | gameplay要件の結果 |

`server-test`に成功しても、player入力、camera、AI、乱数、multiplayer、chunk unloadの要件までは保証しません。[`validation.md`](validation.md) と [`gameplay-requirements.md`](gameplay-requirements.md) の機能testを追加します。

## CI

`.github/workflows/docs-harness.yml` は、外部downloadを行わず次を実行します。

```bash
python3 tools/datapack_harness.py profiles
python3 -m unittest discover -s tests -v
```

公式JARのdownloadとserver起動は容量、Java matrix、EULA同意が必要なため、通常CIへ暗黙には含めません。release前の明示jobまたはlocal検査として実行します。

## 終了code

- `0`: 検査成功。warningが残る場合がある
- `1`: profile、download、SHA-1、静的検査、data generator、server検査の失敗

CIでは標準出力の文言ではなく終了codeを使用します。
