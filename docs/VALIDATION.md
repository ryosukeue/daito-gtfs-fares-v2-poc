# 検証結果

最終実行日: 2026-08-29  
検証対象: `dist/daito_gtfs_fares_v2.zip`  
SHA-256: `379524e2be56659a91a53d88623b81668e29ede5604addad2bff5b7fedf86a85`

## 結論

- プロジェクト独自検査: **error 0 / warning 0**
- MobilityData GTFS Validator v8.0.1: **error 0 / warning 35 / info 15**
- 自動テスト: **8件すべて成功**
- 公式原本に対する同Validator結果: **error 167 / warning 35 / info 3**

生成後にerrorは残っていない。warning/infoは元データ由来の命名・推奨項目・GTFS-JP拡張等で、運賃計算を壊すものではない。隠さず以下に記録する。

## 使用したValidator

### MobilityData GTFS Validator

- 名称: MobilityData Canonical GTFS Validator
- バージョン: 8.0.1
- 公開日: 2026-05-12
- 取得元: https://github.com/MobilityData/gtfs-validator/releases/tag/v8.0.1
- CLI JAR SHA-256: `19293ddd9b6f954f216d4f12054bd8a3232921751c4484339e339764a91000e2`
- 実行環境: Eclipse Temurin JRE 21.0.12.1
- 検証日引数: `2026-08-28`（feed有効期間内）
- 国コード: `jp`

実行例:

```bash
java -jar gtfs-validator-8.0.1-cli.jar \
  -i dist/daito_gtfs_fares_v2.zip \
  -o reports/validator/final \
  -d 2026-08-28 -c jp -svu -p -r report.html
```

### プロジェクト独自検査

`python3 src/validate.py` で次を検査した。

- ZIP直下配置と重複ファイル
- CSVヘッダ、空列、必須フィールド、必須値
- UTF-8
- route / trip / stop / service参照
- fare product / rider category / fare media参照
- area / stop_area参照
- fare leg ruleのnetwork/area/product参照
- transfer ruleのleg group/product参照
- Fares v2主要主キー重複
- 金額が数値であること、通貨がJPYであること
- calendar / calendar_dates / feed_infoの日付形式

## 原本のValidator結果

| severity | 件数 | 主な内容 |
|---|---:|---|
| ERROR | 167 | 空列名6、行長不一致161 |
| WARNING | 35 | route名重複6、連絡先/推奨field不足2、日本語に対するmixed case判定27 |
| INFO | 3 | GTFS-JP独自column/file |

原本の主要error:

1. `fare_attributes.txt` と `stop_times.txt` の末尾に空列名。
2. `trips.txt` 全158行がヘッダ7列に対し5列で、末尾空値が省略。
3. `stops.txt` の総合文化センター3行が10列に分裂。
4. 原本の `trips.txt` はCP932で、UTF-8前提のValidatorで正常解釈できない。

## 生成後のValidator結果

### ERROR: 0

Fares v2を含む全対象ファイルが読み込まれ、Validatorのsummaryには次のfeatureが認識された。

- Fares V1
- Fare Products
- Fare Transfers
- Fare Media
- Rider Categories
- Route-Based Fares
- Zone-Based Fares

### WARNING: 35

| code | 件数 | 判断 |
|---|---:|---|
| `duplicate_route_name` | 6 | 方向違いのrouteが同じ旅客向け名称を持つ原本設計。route_id/tripは分離済みで、名称を勝手に変えない。 |
| `mixed_case_recommended_field` | 27 | 日本語名の全角数字・記号等に対する推奨警告。日本語の正式名称を変更しない。 |
| `stop_without_stop_time` | 2 | `S84_2`、`S88_2`。原本にある未使用platform。削除すると将来ダイヤや案内との整合を損なうため残す。 |

### INFO: 15

| code | 件数 | 判断 |
|---|---:|---|
| `trip_headsign_matches_intermediate_stop` | 12 | headsignが途中停留所名と一致する案内上の情報。原本を維持。 |
| `unknown_column` | 1 | `jp_parent_route_id`。GTFS-JP拡張なので標準GTFS Validatorには未知。意図どおり残す。 |
| `unknown_file` | 2 | `routes_jp.txt`、`office_jp.txt`。GTFS-JP拡張なので残す。 |

## 修正したもの

1. 全テキストをUTF-8（BOMなし）・CRLFへ正規化。
2. 空のCSVヘッダを除去し、末尾空フィールドを明示。
3. 総合文化センター3行の分裂した緯度経度を、元の数値断片から `34.704536, 135.6238244` に復元。
4. R4のstop_timesがparent stationを参照していた25停留所を、既存の方向別platformへ付け替え。
5. `fare_attributes.agency_id` を単一agency IDで補完。
6. `feed_info.feed_version` と `feed_contact_url` をPoC出力として追加。
7. Fares v2の全主キー・外部キーを整合させた。

raw ZIPは一切変更していない。修正は生成時に毎回適用される。

## 乗継商品で行った互換性対応

2026-04-27改訂の公式GTFS Schedule Referenceは `fare_products.amount` の負額を乗継割引に使用できると明記する。一方、Validator v8.0.1は負額を `number_out_of_range` として扱った。

初期案の「A + 負の割引 + B (`fare_transfer_type=1`)」を、最終版では「A + 割引後の2乗車目追加支払額 (`fare_transfer_type=0`)」へ変更した。例:

- 240円乗車 → 120円乗車、大人120円引き
- 初期算式: 240 + (-120) + 120 = 240
- 最終算式: 240 + 0 = 240

最終金額と公式制度は同じで、商品amountはすべて非負となりValidatorを通過する。

## 修正しなかったもの

- route名重複: 往復・方向違いのデータ設計を勝手に変えないため。
- 日本語mixed case警告: 正式な日本語表記を英語向け規則に合わせて改変しないため。
- 未使用platform 2件: 公開GTFSのstop資産を削除しないため。
- GTFS-JP独自file/column: GTFS-JPとして必要な情報を維持するため。
- shapes.txt欠如: 実走形状を推測生成しないため。

## 自動テスト

`python3 -m unittest discover -s tests -v`

検査項目:

1. 生成件数
2. コミュニティバス270円と65歳以上140円
3. 特定区間で小児も120円
4. 南部の対象障害小児80円
5. 東部390円区間の65歳以上200円
6. 市役所乗継の総額と無関係な乗継への非適用
7. 65歳以上に一般IC商品が存在しないこと
8. ZIPのバイト単位再現性
9. 独自Validator error 0（同じtest内で確認）

## 検証の限界

- Validator合格は、大東市が制度解釈を正式承認したことを意味しない。
- 幼児同伴、介護者同行、手帳提示、声掛け等の運用条件は自動検証できない。
- 個別consumerがFares v2の全機能を実装しているかは検証対象外。
- 実証公開前には市担当者・運行事業者による区間表と乗継条件の業務レビューが必要。
