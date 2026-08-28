# 大東市 GTFS Fares v2 PoC 実施計画

確認日: 2026-08-28

## 目的と完了条件

大東市が公開する令和8年度GTFS-JPを入力として、公開情報で確認できる運賃だけをGTFS Fares v2に変換・追加し、同じ入力から何度でも再生成できるPoCを作る。完了条件は次のとおり。

1. 公式ZIPを再取得でき、原本のハッシュを記録できる。
2. 現行GTFSの構成、Fares v1の表現範囲、品質上の注意点を説明できる。
3. Fares v2の各行が元のFares v1の区間ルールまたは大東市の公式運賃制度に追跡できる。
4. 小児、65歳以上、障害者等、支払媒体、コミュニティバスの乗継を、仕様で安全に表せる範囲で収録する。
5. 独自検査とMobilityData GTFS Validatorの結果を隠さず残す。
6. Before / Afterを3例以上で人が読める形にし、非技術者向け説明・30問の理解度チェック・営業デモ台本を用意する。

## Phase 0: 調査

- 大東市公式「令和8年度用GTFSデータ」を最新版として取得する。
- 2026年4月1日改定後の、コミュニティバス、南部地域コミュニティバス、東部地域乗合タクシーの運賃・割引・支払方法・乗継・定期券を確認する。
- GTFS仕様は `gtfs.org` のSchedule Referenceを根拠にする。
- 確認済み事実、設計上の解釈、未確定事項を分けて `docs/RESEARCH.md` に記録する。

## Phase 1: 現行GTFS解析

- ZIP内の全ファイル、文字コード、行数、主キー、参照整合性を確認する。
- agency / routes / trips / stops / stop_times / calendar / calendar_datesを集計する。
- `fare_attributes.txt` と `fare_rules.txt` が表す成人運賃と、表していない割引等を整理する。
- `docs/CURRENT_GTFS.md` に結果を残す。

## Phase 2: Fares v2設計案

- 現行Fares v1の1,990区間ルールを正とし、停留所をFares v2のareaへ機械変換する。
- routesへ `network_id` を追加し、コミュニティバス、南部、東部乗合タクシーを分ける。
- `fare_products.txt`、`fare_leg_rules.txt`、`rider_categories.txt`、`fare_media.txt`、`areas.txt`、`stop_areas.txt` を生成する。
- 乗継は、公式に限定された「市役所と他コースを住道駅でつなぐ」区間だけにleg groupを付け、`fare_transfer_rules.txt` で表す。
- 定期券は価格体系・有効範囲・媒体差が複雑で、現行Schedule Referenceの運賃商品だけでは有効期間を十分に記述できないため、今回の機械可読運賃計算には含めない。
- 判断理由を `docs/FARES_V2_DESIGN.md`、未確定事項を `ASSUMPTIONS.md` に残す。

## 計画の自己レビュー

### 妥当性

- 新しい区間運賃を推測せず、現行Fares v1の区間表を再利用するため、成人運賃の過剰な再解釈を避けられる。
- rider categoryとfare mediaを分けることで、同じ区間でも現金・IC・資格条件が異なる制度を表現できる。
- 全路線一律の乗継ルールにはせず、公式ページで案内される接続だけを対象にする。

### 主要リスクと対策

- **consumer対応差**: Fares v2を読まないアプリがある。Fares v1を削除せず併存させ、説明資料で保証しない。
- **乗継券の時間制限不明**: `duration_limit` は空欄にし、発券・提示という運用条件を文書に残す。
- **幼児無料の同伴人数条件**: 同伴者との関係を標準ファイルだけで安全に計算できないため、商品化せず説明に残す。
- **定期券**: 価格だけ登録すると適用範囲を誤解させるため、PoC本体から除外する。
- **原本の文字コード**: `trips.txt` がCP932である。rawを変更せず、processed/distのみUTF-8へ変換する。

自己レビューの結論: 成人区間運賃を現行Fares v1から変換し、公開情報で明確な割引だけを追加する方針は、安全性と再現性のバランスが取れている。実装へ進む。

## Phase 3: 実装

- `src/download.py`: URL、取得日時、SHA-256を記録してダウンロード。
- `src/inspect_gtfs.py`: ファイル構造・件数・文字コード・参照をJSON/Markdown出力。
- `src/build_fares_v2.py`: 原本をUTF-8正規化し、Fares v2を生成してZIP化。
- `src/validate.py`: 構造、必須値、外部キー、金額、日付、UTF-8、ZIPを検査。
- `src/demo.py`: 具体的な乗車例をFares v2ルールから逆引きしてJSONを生成。
- `demo/index.html`: 静的なBefore / Afterビューア。
- `tests/`: 生成件数、参照、代表運賃、乗継限定、再現性をテスト。

## Phase 4: 検証

- 独自検査でFares v2特有の参照とUTF-8を確認する。
- MobilityData GTFS Validator v8.0.1を使用し、原本と生成後を比較する。
- error / warning / infoの件数と、PoCで直したもの・残したものを `docs/VALIDATION.md` に記録する。

## Phase 5-8: デモ・教材

- 代表例を最低3つ選び、元のroute/area/rule/product/category/mediaまで追跡する。
- `docs/EXPLAINER.md` に30秒説明、v1/v2比較、実例、限界、想定Q&A 20問以上を作る。
- `docs/QUIZ.md` に初級10問、中級10問、商談10問と解説を作る。
- `docs/SALES_DEMO.md` に5〜10分の説明台本を作る。
- README冒頭に「このプロジェクトを5分で理解する」を置く。

## Git運用

1. 調査・計画
2. 解析・設計
3. 生成実装・テスト
4. 検証・デモ
5. 教材・最終整備

の小さい単位でコミットする。raw ZIPは公式配布物として由来とハッシュを記録し、生成物は再生成可能にする。
