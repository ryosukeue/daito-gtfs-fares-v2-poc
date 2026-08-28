# GTFS Fares v2設計

確認日: 2026-08-28

## 設計原則

1. 成人O-D運賃は現行Fares v1を正とし、価格表を手入力で作り直さない。
2. 大東市公式ページで確認できた割引だけを追加する。
3. 適用条件を標準仕様で安全に表せない場合は、商品を過剰適用せず文書に残す。
4. Fares v1は削除せず、Fares v2非対応consumer向けに併存させる。
5. Google Maps等の具体的なconsumer対応を仕様適合性と混同しない。

仕様根拠: https://gtfs.org/documentation/schedule/reference/

## 生成するファイル

### routes.txtへのnetwork_id追加

`network_id` は「同じ運賃制度を使うroute群」を区別する。大東市では運賃と支払媒体が異なるため、次の3群にする。

- `daito_community`: R1,R2,R5,R6,R10,R11,R12,R13,R15
- `daito_south`: R9,R14
- `daito_taxi`: R3,R4,R7,R8,R16,R17

routes.txtに直接network_idを持たせるため、networks.txt / route_networks.txtは作らない。ファイルを増やさず、公式仕様の条件に従う。

### areas.txt / stop_areas.txt

Fares v2のfare_leg_rulesはFares v1の `stops.zone_id` ではなくareaを参照する。現行fare_rulesが参照するplatformごとにareaを作り、同じplatformをstop_areasで割り当てる。

- area_id: `area_<stop_id>`
- area_name: 元stop_name

一つのareaに複数platformをまとめると、方向や乗り場が異なる区間へ運賃を過剰適用する恐れがあるため、PoCでは1 platform = 1 areaとする。

### rider_categories.txt

価格差と対象範囲を表すために必要。

- `adult`: 大人（既定カテゴリ）
- `child`: 小児
- `senior_65_plus`: 65歳以上
- `disability_community`: コミュニティバスで公式に案内された手帳保有者等
- `disability_south_taxi`: 南部・東部で公式に案内された手帳保有者等（精神障害者手帳を含む）
- `disabled_child_community`
- `disabled_child_south_taxi`

介護者1人までという同行条件はcategory名とeligibility URLには残せるが、人数関係をGTFS運賃計算だけで強制できない。

### fare_media.txt

同じ区間でも支払い条件が違うため必要。

- `cash` (type 0): 現金、媒体なし
- `transit_ic` (type 2): ICOCA/PiTaPa等の交通系IC
- `child_icoca` (type 2): 子どもICOCA
- `ic_excluding_pitapa` (type 2): 障害者割引で利用できるPiTaPa以外のIC
- `transfer_ticket` (type 1): 車内発行の紙の乗継券

`fare_media` は媒体を記述するもので、声掛け、手帳提示、同行人数を自動執行する仕組みではない。

### fare_products.txt

「売られる/計算に使われる運賃商品」と、その利用者区分・媒体別価格を定義する。

#### コミュニティバス

- `community_120`: 特定区間。全区分120円で割引なし。
- `community_240`: 大人240、小児/65歳以上/対象障害者120、対象障害小児60。
- `community_270`: 大人270、小児/65歳以上/対象障害者140、対象障害小児70。

成人はcashとtransit_ic、小児はcashとchild_icoca、65歳以上はcashのみ、障害者等はcashとic_excluding_pitapaを設定する。

#### 南部地域コミュニティバス

- `south_300`: 大人300、小児/65歳以上/対象障害者150、対象障害小児80。cashのみ。

#### 東部地域乗合タクシー

- `taxi_300`: 300 / 150 / 80
- `taxi_330`: 330 / 170 / 90
- `taxi_350`: 350 / 180 / 90
- `taxi_390`: 390 / 200 / 100

各並びは大人 / 小児・65歳以上・対象障害者 / 対象障害小児。cashのみ。

#### 乗継時の追加支払額

- `transfer_pay_120_full`: 120円区間同士では追加0円。
- `transfer_pay_120_standard`: 2乗車目が120円区間で通常乗継の場合の追加額（大人0、小児等60、対象障害小児90円）。
- `transfer_pay_240_standard`: 2乗車目が240円区間の場合の割引後追加額。
- `transfer_pay_270_standard`: 2乗車目が270円区間の場合の割引後追加額。

公式Schedule Referenceは負額商品も許容するが、MobilityData GTFS Validator v8.0.1は負額をエラーとする。そこで `fare_transfer_type=0`（1乗車目A + 乗継商品AB）を使い、ABを「2乗車目の通常運賃から公式割引額を引いた、追加支払額」として0以上で表す。同じ最終運賃を、より広いconsumer/validator互換性で得るための判断である。

### fare_leg_rules.txt

「どのnetwork・乗車area・降車areaに、どの商品を適用するか」を定義する。現行fare_rulesの各行を1対1で変換する。

| Fares v1 fare_id | route分類 | Fares v2 product |
|---|---|---|
| Fare120yen_00 | community | community_120 |
| Fare240yen_00 | community | community_240 |
| Fare270yen_00 | community | community_270 |
| Fare300yen_00 | south | south_300 |
| Fare300yen_00 | taxi | taxi_300 |
| Fare330yen_00 | taxi | taxi_330 |
| Fare350yen_00 | taxi | taxi_350 |
| Fare390yen_00 | taxi | taxi_390 |

同額300円でも制度・割引・媒体が違うため、南部と東部は別商品にする。

### fare_transfer_rules.txt

公式に案内される市役所来庁の乗継だけを対象にする。全コミュニティバス間へ一般化しない。

対象となる実際の接続は次の系統・areaの組合せを元に作る。

- 西部方面 → 住道駅前［北］ → 三箇方面の市役所区間
- 三箇方面の市役所区間 → 住道駅前［北］ → 西部方面
- 南新田・朋来方面 → 住道駅南 → 市役所特定区間
- 市役所特定区間 → 住道駅南 → 南新田・朋来方面

fare_leg_rulesの該当O-D行だけにleg_group_idを付与する。乗継計算は `fare_transfer_type=0`（1乗車目 + 2乗車目での追加支払額）。公式ページに有効時間の記載がないためduration_limitは空欄。

120/240/270円のどの区間かを判定できるようleg groupを価格帯別に分け、両方が120円なら `transfer_pay_120_full`、それ以外は2乗車目の価格帯に対応するstandard商品を適用する。

## 240円 / 270円 / 120円

- 240円と270円のO-D境界は配布GTFSのFares v1をそのまま引き継ぐ。
- 半額時の1円単位切り上げにより270円の割引運賃は140円。
- 120円特定区間は割引なしのため、categoryを空欄にした全利用者共通商品とする。

## 現金とIC

- コミュニティバス成人は現金・一般ICの両方。
- 子どもICOCAは小児料金。
- 65歳以上割引は現金のみ。
- 障害者割引は現金とPiTaPa以外のIC。
- 南部・東部は現金のみ。

媒体名は人に条件を示せるが、consumerがPiTaPa除外等をどこまでUIや計算へ反映するかは別問題である。

## 定期券を含めない理由

定期券は実在するが、通勤/通学、紙/スマホ/PiTaPa、1/3/6か月等の有効期間と適用範囲を誤りなく結び付ける必要がある。現行fare_productsには金額と媒体はあるが、商品自体の通用期間を完結して記述する欄がない。価格だけ置くと「1乗車の候補商品」と誤読される可能性があるため、本PoCの経路別運賃計算から除外する。

## 完全には表現しない制度

- 幼児無料の「同伴者1人につき1人」条件。
- 介護者が対象本人と同行し、1人までという条件。
- 手帳提示、年齢申告、運転士への声掛け。
- 予約制乗合タクシーの予約手続。
- 定期券の有効期間・用途・払戻等。
- 特定アプリが表示するかどうか。

これらは仕様上の価格表現、運用上の資格確認、consumer実装の境界にある。PoCは「表現できる価格と関係」を提供し、運用判断を置き換えない。
