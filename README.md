# 大東市 GTFS Fares v2 PoC

## このプロジェクトを5分で理解する

### 何を作ったか

大東市が公式公開する令和8年度GTFS-JPを入力に、GTFS Fares v2の運賃データを自動生成し、既存データへ追加した試作品です。完成ZIPは `dist/daito_gtfs_fares_v2.zip` です。

追加した主な情報は次のとおりです。

- コミュニティバスの120 / 240 / 270円
- 南部地域コミュニティバスの300円
- 東部地域乗合タクシーの300 / 330 / 350 / 390円
- 小児、65歳以上、障害者等、対象障害小児の価格
- 現金、交通系IC、子どもICOCA、PiTaPa除外IC、紙の乗継券
- 市役所来庁として公式案内される限定乗継

### なぜ作ったか

元GTFSにはFares v1で成人運賃が入っていますが、「誰が」「何で支払い」「乗継時にいくらになるか」を十分に分けられません。Fares v2を使うと、実際の運賃制度を標準的な表の関係として詳しく渡せる可能性があります。

### 何が変わったか

例として、住道駅前［北］から三箇西までは、元データでは成人270円だけが機械可読でした。追加後は、65歳以上・現金なら140円、小児・子どもICOCAなら140円、対象障害小児なら70円、という候補を区別できます。

原本でValidator errorとなった文字コード、空列、総合文化センターの壊れた緯度経度、R4のstation/platform参照も、rawを変更せず生成時に正規化しました。

### まだできないこと

- Google Maps等がFares v2を表示・計算する保証
- 幼児無料の「同伴者1人につき1人」を自動判定
- 介護者1人まで、手帳提示、年齢申告、運転士への声掛けを自動判定
- 乗継券の未公表の時間条件を補完
- 定期券の期間・用途・適用範囲を安全に完全表現
- 大東市や運行事業者による正式承認の代替

### デモの動かし方

```bash
python3 src/build_fares_v2.py
python3 src/demo.py
python3 -m http.server 8000 -d demo
```

ブラウザで `http://localhost:8000` を開くと、4つのBefore / After例を切り替えて見られます。終了はターミナルで `Ctrl+C` です。

## 最短の再生成手順

Python 3.9以上だけで生成・独自検査・テストを実行できます。外部Pythonパッケージは不要です。

```bash
python3 src/download.py
python3 src/inspect_gtfs.py data/raw/daito_gtfs_2026.zip --output reports/source_inspection.json
python3 src/build_fares_v2.py
python3 src/validate.py
python3 -m unittest discover -s tests -v
python3 src/demo.py
```

`download.py` は取得日時・URL・SHA-256を `data/raw/daito_gtfs_2026.metadata.json` に記録します。市が将来route IDや制度を変えた場合、分類不能なrouteを黙って処理せず停止します。

## 成果物

| 場所 | 内容 |
|---|---|
| `dist/daito_gtfs_fares_v2.zip` | Fares v1を残しFares v2を追加した完成GTFS |
| `demo/index.html` | Before / Afterデモ |
| `docs/RESEARCH.md` | 公式情報と仕様調査 |
| `docs/CURRENT_GTFS.md` | 元GTFS解析 |
| `docs/FARES_V2_DESIGN.md` | 設計判断と各fileの役割 |
| `docs/VALIDATION.md` | Validator結果と未修正warning |
| `docs/EXPLAINER.md` | 非技術者向け教材・想定Q&A |
| `docs/QUIZ.md` | 30問の理解度チェック |
| `docs/SALES_DEMO.md` | 5〜10分の自治体向け説明台本 |
| `ASSUMPTIONS.md` | 未確定事項・実証前確認事項 |
| `PLAN.md` | 調査から実装までの計画と自己レビュー |

## 生成したFares v2

| file | 行数 | 役割 |
|---|---:|---|
| rider_categories.txt | 7 | 利用者区分 |
| fare_media.txt | 5 | 現金・IC・乗継券 |
| fare_products.txt | 63 | 区分・媒体別の商品価格 |
| areas.txt | 144 | 運賃判定用の乗降area |
| stop_areas.txt | 144 | stopとareaの対応 |
| fare_leg_rules.txt | 1,879 | O-Dと商品の対応 |
| fare_transfer_rules.txt | 8 | 市役所関連の限定乗継 |

さらに `routes.txt` に3つのnetwork_idを追加しています。

## 検証結果

- 自動テスト: 8件成功
- 独自Validator: error 0 / warning 0
- MobilityData GTFS Validator v8.0.1: error 0 / warning 35 / info 15
- 完成ZIP SHA-256: `379524e2be56659a91a53d88623b81668e29ede5604addad2bff5b7fedf86a85`

warningは、往復routeの同名、日本語へのmixed case推奨、未使用platform 2件です。GTFS-JP独自file/columnはinfoとして残ります。詳細は `docs/VALIDATION.md` を参照してください。

## 重要な設計上の制約

定期券、幼児同伴、介護者同行等を無理に商品へ押し込んでいません。情報を増やすことより、誤った運賃候補を出さないことを優先しました。Fares v2仕様で表現できることと、consumerが実際に利用することは別です。

## ディレクトリ構成

```text
.
├── README.md / PLAN.md / ASSUMPTIONS.md
├── src/                 # 取得・解析・生成・検証・デモ生成
├── tests/               # 標準ライブラリunittest
├── data/raw/            # 公式原本（直接編集しない）
├── data/processed/      # 再生成される展開済み出力
├── dist/                # 完成ZIP
├── demo/                # Before / After UIと生成JSON
├── docs/                # 調査・設計・検証・説明資料
└── reports/             # 機械検査のJSON等
```

## ライセンスと出典

元データは大東市公式オープンデータを利用しています。公式ページはCC BY 4.0に基づく利用条件と、大東市データを利用した旨の表示を求めています。

- 公式ページ: https://www.city.daito.lg.jp/site/kokyokotsu/68741.html
- GTFS公式仕様: https://gtfs.org/documentation/schedule/reference/

本リポジトリはPoCであり、大東市の公式GTFS配信物ではありません。
