# 現行GTFS-JP解析

対象: 大東市公式「令和8年度用GTFSデータ」  
配布URL: https://www.city.daito.lg.jp/uploaded/attachment/41955.zip  
取得・確認日: 2026-08-28  
SHA-256: `5b01bb8343b6f797af62ed23196a4a3b2c360fdbe20180a696481be209cd8503`

## 要約

現行データは、運行情報だけでなくFares v1で改定後の成人片道運賃をかなり詳細に収録している。7つの価格と1,990件のroute/O-Dルールがあり、コミュニティバス、南部地域コミュニティバス、東部地域乗合タクシーを網羅する。一方、小児、65歳以上、障害者等、媒体差、乗継券、定期券は機械可読運賃として入っていない。

## ファイル一覧と件数

| ファイル | データ行 | 内容 |
|---|---:|---|
| agency.txt | 1 | 大東市コミュニティ |
| routes.txt | 17 | 3種の交通サービスをrouteとして収録 |
| trips.txt | 158 | 各routeの便 |
| stops.txt | 238 | stationとplatformを含む |
| stop_times.txt | 1,893 | 各便の停車時刻 |
| calendar.txt | 7 | 2026-04-01〜2027-03-31の基本運行日 |
| calendar_dates.txt | 59 | 祝日等の運休例外 |
| fare_attributes.txt | 7 | Fares v1価格 |
| fare_rules.txt | 1,990 | route・乗車地・降車地別のFares v1規則 |
| feed_info.txt | 1 | 発行者と有効期間 |
| routes_jp.txt | 4 | GTFS-JP拡張の系統グループ |
| office_jp.txt | 1 | 営業所情報 |
| translations.txt | 238 | 読み仮名等 |

## agency

- agency_id: `6000020272183`
- agency_name: `大東市コミュニティ`
- timezone: `Asia/Tokyo`
- language: `ja`

## routes / trips

| route | 名称 | trips | PoCでの分類 |
|---|---|---:|---|
| R1,R2 | 三箇方面コース | 48 / 25 | コミュニティバス |
| R3,R4 | 野崎・寺川コース：東部地域乗合タクシー | 3 / 3 | 東部乗合タクシー |
| R5,R6 | 西部方面コース | 16 / 16 | コミュニティバス |
| R7,R8 | 中垣内コース：東部地域乗合タクシー | 3 / 3 | 東部乗合タクシー |
| R9 | 中垣内コース：南部地域コミュニティバス | 7 | 南部コミュニティバス |
| R10,R11 | 南新田・朋来コース：特定区間 | 1 / 1 | コミュニティバス |
| R12,R13 | 南新田方面コース | 11 / 11 | コミュニティバス |
| R14 | 朋来コース：南部地域コミュニティバス | 3 | 南部コミュニティバス |
| R15 | 朋来方面コース | 1 | コミュニティバス |
| R16,R17 | 北条コース：東部地域乗合タクシー | 3 / 3 | 東部乗合タクシー |

全routeの `route_type` は3（Bus）。予約制乗合タクシーもGTFS上はBusとして収録される。

## stops / stop_times

- stopsは238行で、station (`location_type=1`) とplatform (`location_type=0`) の親子構造を持つ。
- fare_rulesはplatform IDをorigin/destinationとして使用する。
- stop_timesのtrip参照・stop参照に欠落はない。
- fare_rulesが参照するplatformは144件。
- 住道駅周辺は `住道駅前［北］(S11_1)`、`住道駅中央(S26_1)`、`住道駅南(S54_1/S54_2)` 等に分かれている。乗継設計では「住道駅」という名称だけで一括せず、公式案内と実際のroute順序を照合する必要がある。

## calendar / calendar_dates

- 7 service_idがあり、基本期間はすべて2026-04-01〜2027-03-31。
- 平日、土日、月水金、毎日等のserviceが分離されている。
- calendar_datesは59行で、主に祝日・年始の運休を表す。
- tripsの全service_idはcalendarまたはcalendar_datesから参照できる。

## 現行Fares v1

### fare_attributes.txt

| fare_id | 円 | 主な用途 |
|---|---:|---|
| Fare120yen_00 | 120 | コミュニティバス特定区間 |
| Fare240yen_00 | 240 | コミュニティバス基本区間 |
| Fare270yen_00 | 270 | コミュニティバス基本区間 |
| Fare300yen_00 | 300 | 南部均一・東部2km未満 |
| Fare330yen_00 | 330 | 東部4km未満 |
| Fare350yen_00 | 350 | 東部6km未満 |
| Fare390yen_00 | 390 | 東部8km未満 |

すべてJPY、`payment_method=0`（車内支払）、`transfers=0`（Fares v1上は乗継なし）である。

### fare_rules.txt

- 1,990行、重複なし。
- route_id、origin_id、destination_idの参照欠落なし。
- 価格別件数: 120円 35、240円 300、270円 154、300円 850、330円 418、350円 207、390円 26。
- route別に方向を含むO-D組合せを列挙しており、成人区間運賃の重要な原典として利用できる。

## 現在表現できていること

- 2026-04-01以後の成人片道運賃。
- routeごとの乗車platform・降車platformの組合せ。
- コミュニティバスの120/240/270円。
- 南部の300円。
- 東部の300/330/350/390円。
- Fares v1を読むconsumerに対する基本的な運賃提示。

## 現在表現できていないこと

- 小児、65歳以上、障害者等、障害のある小児の価格。
- 同じ価格でも対象者が異なること。
- 現金、交通系IC、PiTaPa除外、現金限定という媒体条件。
- 紙の乗継券と2乗車目の割引。
- 120円区間同士の特別な乗継扱い。
- 幼児無料の同伴人数条件。
- 定期券の券種、通勤/通学、期間、媒体、適用範囲。
- 予約制であることを運賃規則として表すこと。

## データ品質上の発見

1. `trips.txt` だけがCP932/Shift_JIS系で、他の日本語ファイルはUTF-8。GTFSはUTF-8を要求するため、原本は文字コードエラーになり得る。
2. `fare_attributes.txt` と `stop_times.txt` の末尾に空の列名がある。内容は壊していないが不要なヘッダである。
3. shapes.txtがない。仕様上はroute-based serviceに推奨されるためValidator警告候補だが、本PoCは運賃が主対象であり、根拠のない経路形状は生成しない。
4. route_colorが白でroute_text_color省略のため、表示上のコントラスト警告候補。

PoC出力では1と2を正規化する。3と4は原本由来の非運賃課題として残し、検証結果に記録する。
