# 調査記録

確認日: 2026-08-28（日本時間）

## 調査方針

運賃制度は大東市公式サイトを一次情報とした。GTFS Fares v2はGTFS公式Schedule Referenceを仕様根拠とした。画像にしかない表は、同じ公式ページの本文、令和8年改定案・ニュースレター、配布GTFSのFares v1を相互確認した。以下の「確認済み」は出典に直接記載または配布データに収録された内容、「設計上の解釈」はPoCでの写像、「不明」は公開情報だけでは確定しない内容である。

## 1. 最新GTFS-JP

- **内容（確認済み）**: 「（令和8年度）大東市コミュニティバス等のGTFS-JPデータ」が2026-03-16に更新され、「令和8年度用GTFSデータ」として公開されている。利用・改変と二次的著作物作成が可能で、市データを利用した旨の表示が必要。
- **出典URL**: https://www.city.daito.lg.jp/site/kokyokotsu/68741.html
- **配布ZIP**: https://www.city.daito.lg.jp/uploaded/attachment/41955.zip
- **確認日**: 2026-08-28
- **GTFS上で表現可能か**: 時刻・停留所・路線・Fares v1成人運賃が収録済み。
- **Fares v2案**: 元ZIPを唯一の生成入力とし、Fares v1を残してFares v2を併記する。
- **不明点**: 市がFares v2を正式配信する予定やconsumer別対応状況は確認できない。

## 2. 交通サービスとコース

### 大東市コミュニティバス

- **内容（確認済み）**: 市内3コース。南新田・朋来方面、三箇方面、西部方面。基本運賃は240円・270円、特定区間は120円。
- **出典URL**: https://www.city.daito.lg.jp/site/kokyokotsu/69161.html
- **確認日**: 2026-08-28
- **表現可能性**: route/networkと乗降areaの組合せで表現できる。
- **Fares v2案**: route `R1,R2,R5,R6,R10,R11,R12,R13,R15` をコミュニティバスnetworkとする。
- **不明点**: なし。区間別価格は配布GTFSのFares v1を使用する。

### 南部地域コミュニティバス

- **内容（確認済み）**: 中垣内コース・朋来コースの2コース、月・水・金（祝日と1月1〜3日は運休）、大人300円均一。65歳以上・小人は150円。現金のみで、クレジットカード・ICカード不可。
- **出典URL**: https://www.city.daito.lg.jp/site/kokyokotsu/69163.html
- **確認日**: 2026-08-28
- **表現可能性**: network別300円商品とcash媒体で表現できる。
- **Fares v2案**: route `R9,R14` を南部networkとする。
- **不明点**: 公式ページにある運行日記述とGTFS calendarの整合はValidatorと目視で確認するが、運休日の業務判断は行わない。

### 東部地域乗合タクシー

- **内容（確認済み）**: 北条、野崎・寺川、中垣内の3コース。予約制、現金のみ、ICカード不可。2026-04-01以後の大人運賃は距離帯により300/330/350/390円。
- **出典URL**: https://www.city.daito.lg.jp/site/kokyokotsu/index.html
- **補助出典**: https://www.city.daito.lg.jp/uploaded/attachment/41820.pdf
- **確認日**: 2026-08-28
- **表現可能性**: GTFSに収録済みのO-D運賃表をarea間ルールへ変換できる。
- **Fares v2案**: route `R3,R4,R7,R8,R16,R17` を東部乗合タクシーnetworkとする。
- **不明点**: Fares v2は予約そのものを運賃ファイルで表す仕様ではない。予約条件は運賃計算と分離する。

## 3. 2026年4月1日運賃改定

- **内容（確認済み）**: コミュニティバスは200→240円、230→270円、特定100→120円。東部乗合タクシーは200/230/250/290→300/330/350/390円。南部は200→300円。近鉄バス阪奈生駒線も改定されたが区間別で、65歳以上の市独自割引はない。
- **出典URL**: https://www.city.daito.lg.jp/site/kokyokotsu/67602.html
- **確認日**: 2026-08-28
- **表現可能性**: 改定後価格はFares v2 amountで表現可能。旧価格との時期切替を同一feedで表す必要はない（feed期間が2026-04-01以後）。
- **Fares v2案**: 配布GTFSに入った改定後Fares v1を変換元にする。
- **不明点**: 近鉄バス阪奈生駒線は今回の市配布GTFSの17 routesには収録されておらず、PoC対象外。

## 4. 小児・幼児・乳児

- **内容（確認済み）**: コミュニティバスでは小児（小学生以下）は大人の半額、1円単位を切り上げる。幼児（1歳以上〜小学生未満）は同伴者1人につき1人無料、2人目以上は小児料金。乳児（1歳未満）は無料。120円特定区間は割引なし。南部・東部にも同伴条件と無料条件があり、障害のある小児はさらに半額（例: 南部300円に対し80円）。
- **出典URL**: https://www.city.daito.lg.jp/site/kokyokotsu/67602.html
- **南部の明記**: https://www.city.daito.lg.jp/site/kokyokotsu/69163.html
- **確認日**: 2026-08-28
- **表現可能性**: 単独の小児価格はrider categoryで表現可能。同伴人数に依存する幼児無料は標準Fares v2だけでは確実に計算できない。
- **Fares v2案**: `child` と `disabled_child` は収録する。幼児・乳児は過剰適用を避けるため商品化せず、eligibility URLと文書に残す。
- **不明点**: 「小学生以下」と「幼児」の重なりは公式の同伴条件が優先するが、単独利用など全ケースは公開文だけで補完しない。

## 5. 65歳以上

- **内容（確認済み）**: コミュニティバスは240円区間120円、270円区間140円、120円区間は割引なし。65歳以上の割引は現金のみで、降車時に乗務員へ声掛けが必要。南部は300円→150円。東部は300/330/350/390→150/170/180/200円。
- **出典URL**: https://www.city.daito.lg.jp/site/kokyokotsu/69161.html
- **南部出典**: https://www.city.daito.lg.jp/site/kokyokotsu/69163.html
- **東部補助出典**: https://www.city.daito.lg.jp/uploaded/attachment/41820.pdf
- **確認日**: 2026-08-28
- **表現可能性**: rider categoryとcash媒体で表現可能。声掛けという手続は価格データだけでは強制できない。
- **Fares v2案**: `senior_65_plus`、cashのみ。
- **不明点**: 年齢確認書類の要否は公式ページから一律には確定しない。

## 6. 障害者割引・介護者

- **内容（確認済み）**: コミュニティバスは身体障害者手帳・療育手帳保有者等が対象。南部・東部は身体・精神・療育手帳保有者等が対象。第一種身体障害者手帳保有者の介護者1人まで対象。小児の対象者はさらに半額。コミュニティバスではPiTaPa以外のICカードでも手帳提示により割引可。
- **出典URL**: https://www.city.daito.lg.jp/site/kokyokotsu/67602.html
- **IC条件**: https://www.city.daito.lg.jp/site/kokyokotsu/69161.html
- **南部詳細**: https://www.city.daito.lg.jp/site/kokyokotsu/69163.html
- **確認日**: 2026-08-28
- **表現可能性**: rider categoryとfare mediaで価格は表現可能。手帳種別、介護者人数、本人との同行関係はconsumerが自動判定できない。
- **Fares v2案**: 対象範囲が違うため `disability_community` と `disability_south_taxi` を分け、介護者を名称・eligibility URLに含める。
- **不明点**: 精神障害者割引がコミュニティバス本体には記載されていないため、南部・東部と同じ対象とは推測しない。

## 7. 特定区間120円

- **内容（確認済み）**: 住道駅周辺〜市役所等の一部区間が120円。特定区間は割引なし。
- **出典URL**: https://www.city.daito.lg.jp/site/kokyokotsu/69161.html
- **確認日**: 2026-08-28
- **表現可能性**: area間のfare leg ruleで表現可能。
- **Fares v2案**: 現行Fares v1の `Fare120yen_00` の35ルールをそのままarea間へ変換し、category空欄（全利用者同額）とする。
- **不明点**: なし。対象組合せはFares v1を根拠とする。

## 8. 乗継券・乗継割引

- **内容（確認済み）**: コミュニティバス路線のみ。市役所と南新田・朋来/西部方面を住道駅で乗り継ぐ際に、最初のバスで乗継券を受け取る。2台目から大人120円、小児60円、対象障害者大人60円、対象障害者小児30円、65歳以上60円を割引。120円区間同士は全員120円引き。
- **出典URL**: https://www.city.daito.lg.jp/site/kokyokotsu/69160.html
- **確認日**: 2026-08-28
- **表現可能性**: leg groupとtransfer fare productで算術を表現可能。公式仕様は負額も認めるが、使用Validatorとの互換性を高めるため「2乗車目で追加支払いする額」を非負で持たせる方式を採用した。
- **Fares v2案**: GTFS内の住道駅各停留所と市役所を結ぶ実際のO-Dだけにleg groupを付与し、`fare_transfer_type=0` で1乗車目と乗継後追加支払額を合算する。紙の乗継券をfare media type 1とする。
- **不明点**: 有効時間は公式ページに明記がないため `duration_limit` を設定しない。consumerが紙券発行条件まで扱う保証はない。

## 9. 定期券

- **内容（確認済み）**: 2026-04-01にコミュニティバス定期料金が改定。紙式、バスもり！スマホ定期、PiTaPaカード登録型割引サービスが案内されている。
- **出典URL**: https://www.city.daito.lg.jp/site/kokyokotsu/69152.html
- **確認日**: 2026-08-28
- **表現可能性**: fare productとして価格・媒体は置けるが、現行Schedule Referenceのfare_products自体に通用期間・回数・通勤/通学の適用条件を完結して記述するフィールドがない。
- **Fares v2案**: 誤解を避けPoC ZIPには含めない。将来、仕様・consumer対応と商品台帳を確認して別フェーズとする。
- **不明点**: 全券種の正確な価格・有効範囲・払戻条件を機械可読化するための確定情報が不足。

## 10. 支払方法

- **内容（確認済み）**: コミュニティバスは現金、ICOCA/PiTaPa等のIC、定期券。65歳以上割引は現金のみ。障害者割引はPiTaPa以外のIC可。南部・東部は現金のみ。
- **出典URL**: https://www.city.daito.lg.jp/site/kokyokotsu/69161.html
- **南部・東部**: https://www.city.daito.lg.jp/site/kokyokotsu/index.html
- **確認日**: 2026-08-28
- **表現可能性**: fare_mediaで現金、交通系IC、PiTaPa除外IC、紙乗継券を区別できる。
- **Fares v2案**: 媒体名に条件を明示する。Fares v2がカードの個別ブランド規則を機械判定するわけではない点を明記。
- **不明点**: 全対応ICブランドの網羅一覧は今回の価格計算に不要なため固定しない。

## 11. GTFS Fares v2公式仕様

- **内容（確認済み）**: 公式Schedule ReferenceはFares v1とv2を別方式として併存可能としている。Fares v2にはrider_categories、fare_media、fare_products、fare_leg_rules、fare_transfer_rules、areas、stop_areas、network関連等がある。fare_productsの主キーはfare_product_id/rider_category_id/fare_media_idの組合せで、同じ商品IDに利用者区分・媒体別の価格を持てる。transfer productは負額を許容する。
- **出典URL**: https://gtfs.org/documentation/schedule/reference/
- **機能ガイド**: https://gtfs.org/resources/gtfs-schedule-feature-guides/fares/intro/
- **確認日**: 2026-08-28
- **表現可能性**: 今回の成人O-D運賃、利用者区分、媒体、限定乗継の価格計算を表現できる。
- **Fares v2案**: 採用済みSchedule Referenceのフィールドだけを使う。議論中機能を根拠にしない。
- **不明点**: consumer別採用状況はGTFS仕様の適合性とは別問題。Google Maps等での表示を保証しない。

## 12. Validator

- **内容（確認済み）**: MobilityDataのCanonical GTFS Validator最新安定版はv8.0.1（2026-05-12公開）。
- **出典URL**: https://github.com/MobilityData/gtfs-validator/releases/tag/v8.0.1
- **確認日**: 2026-08-28
- **Fares v2案**: CLI JARで原本と生成後を検証し、JSON/HTMLを保存する。
- **不明点**: Validatorが仕様の全意味論を網羅するとは限らないため、独自参照検査も併用する。

## 明確に除外した推測

- 近鉄バス阪奈生駒線の区間運賃を市GTFSへ勝手に追加しない。
- 幼児無料を「全幼児無料」として商品化しない。
- 乗継券に根拠のない時間制限を付けない。
- 定期券を単純な片道商品として扱わない。
- Fares v2を追加すれば特定アプリで必ず表示されるとは書かない。
