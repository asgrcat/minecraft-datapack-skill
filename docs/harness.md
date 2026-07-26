# 実行ハーネス

`tools/datapack_harness.py` は、正式版プロファイルの解決、公式server JARの取得とSHA-1検証、data generator、pack静的検査、server起動・reload検査を実行します。Python標準ライブラリだけを使用します。

MinecraftのBrigadierとcodecを再実装しません。静的に確定できない項目は警告し、対象版serverでの検査へ送ります。

## 1. プロファイル検査

```bash
python3 tools/datapack_harness.py profiles
```

検査内容:

- 全50版の必須front matter
- `compatibility` の基本クラス
- `compatibility_tags` の定義済み値
- filenameとversionの一致
- `inherits` の参照、循環、単一chain
- `AI 生成規則` の存在
- `profile.schema.json` のJSON構文

front matterのschemaは [`versions/profile.schema.json`](versions/profile.schema.json) です。Markdown本文の任意見出しを機械可読な差分fieldとして扱いません。

## 2. 対象版の解決

```bash
python3 tools/datapack_harness.py resolve 1.20.5
```

JSON出力:

- 対象版profile
- 1.13から対象版までのinheritance chain
- 各版の `AI 生成規則`
- command/registry/vanilla dataの正本path
- server検査に必要なJava major

versionは完全一致です。一覧にないsnapshot、pre-release、Bedrock版、近似semverを受け付けません。

## 3. 公式server JAR

```bash
python3 tools/datapack_harness.py fetch 1.20.5 \
  --cache-dir .cache/minecraft
```

処理:

1. 公式version manifest v2を取得
2. `id`完全一致かつ `type: release` を1件選択
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

版に応じてdata generatorの起動方法を切り替えます。

- 1.13〜1.17.1: classpathから `net.minecraft.data.Main`
- 1.18以降: bundlerのmain classを指定

必要Java major:

| 正式版 | Java |
|---|---:|
| 1.13〜1.16.5 | 8 |
| 1.17〜1.17.1 | 16 |
| 1.18〜1.20.4 | 17 |
| 1.20.5〜1.21.11 | 21 |
| 26.1以降 | 25 |

ハーネスは必要majorを表示します。複数JDKがある環境では `--java` へ対象版用の実行ファイルを指定します。

## 5. pack静的検査

```bash
python3 tools/datapack_harness.py validate-pack 1.20.5 path/to/pack \
  --reports build/1.20.5/generated
```

検査内容:

- `pack.mcmeta` のJSONと対象format包含
- 全 `.json` のUTF-8/JSON構文
- namespace/resource pathの文字
- plural/singular data directory
- function tag directory
- `.mcfunction` の先頭 `/`
- macroの1.20.2境界
- `commands.json` に存在するroot literal
- 自namespaceのfunction参照切れ
- `registries.json` と照合できないvanilla ID候補

制限:

- command引数全体のBrigadier parseは再実装しない
- registryにないserializer IDと、存在しないID候補を完全には区別できない
- Minecraft codecの必須field・loot contextは静的に保証しない
- zip packは静的検査前に展開する

これらはwarningとして残し、server検査を完了条件にします。

## 6. server起動とreload

```bash
python3 tools/datapack_harness.py server-test 1.20.5 path/to/pack \
  --cache-dir .cache/minecraft \
  --java /path/to/java \
  --accept-eula \
  --log build/1.20.5/server-test.log
```

`server-test`:

1. 一時server directoryを作る
2. packを新規worldの `datapacks` へcopy
3. exact release serverを起動
4. startup完了後に `reload` を送る
5. serverを停止
6. exit statusとparse/load/JSON errorを検査

`--accept-eula` は、実行者がMinecraft EULAへ同意したことを明示する必須flagです。指定なしではserverを起動しません。

server検査は一時worldを使用します。既存worldをupgradeしません。旧world migration testは、利用者が複製した専用worldで別に行います。

## 保証レベル

| 段階 | 保証 |
|---|---|
| `profiles` | 版metadata・継承・互換性schemaの整合 |
| `resolve` | 対象版と適用規則の決定 |
| `fetch` | 公式release JARとSHA-1 |
| `reports` | 対象版のcommand graph・registry・vanilla data |
| `validate-pack` | pack構造と一部参照の静的検査 |
| `server-test` | exact serverでstartup/reload時のload検査 |
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
