# SUZUKA Official 最新状態同期監査 — 2026-09-24 JST

確認日時：2026-09-24 20:15 JST
状態：ローカル変更・検証対象。本番公開前。

## Phase 1 比較監査

| 項目 | 現在のWeb（監査開始時） | 外部最新情報 | 判定 | 対応 |
| --- | --- | --- | --- | --- |
| 作品 | 公開サイトは60作品。作業ツリーには9月22日分を含む62作品 | TuneCoreで公開済み13件を照合し、「また、君に恋をする。」「恋するすべての瞬間」が未登録 | 不足 | 2作品を正本へ追加し64作品へ再生成 |
| リリース日 | 作品公開日とストリーミング日が混在し得る構造 | LinkCore公開日：9/23（新規2作品・既存3作品）、9/22（2作品）、9/21（3作品） | 要整理 | 作品公開日と配信日を別フィールドのまま保持 |
| 配信状況 | September Blue / Over Driveが9/22予定として残る作業途中状態 | TuneCore管理画面で両作品とも配信中 | 古い | published / NOW STREAMINGへ移動。過去日のUpcomingを解消 |
| MV | Hello Hello HalloweenをHeroに表示 | 9/23の新規2作品は配信公開を確認したが公式MVは未確認 | 正常 | Heroは公開済みMVのHello Hello Halloweenを維持。配信作品へMV表記を付けない |
| Artist | 10組。妃みちるのInstagram URLが旧表記 | 現行公式Instagramは suzuka12090511 | 一部古い | Artistページ・構造化データ・SNSリンクを現行URLへ同期 |
| News | 9/24写真集、9/23配信、9/21発表が未掲載 | Instagram / note / TuneCoreで5件確認 | 不足 | 5件追加し44件へ更新 |
| Instagram告知 | 9/20・9/24告知が未反映 | 3曲同時配信、妃みちる写真集を確認 | 不足 | News、写真集、関連リンクへ反映 |
| note記事 | 妃みちる新記事2件と榎本魅愛配信記事が未反映 | 写真集、Official Channel、3曲同時配信の記事を確認 | 不足 | 3記事をNews等へ反映。未確認のChannel直リンクは追加せず |
| LinkCore | 既存の一部作品のみ | 公開済み13、予定7、審査中1。LinkCore 20件 | 不足 | 公開/予定を分離し、確認済み20 URLを正本・ページへ同期 |

## TuneCore照合結果

- 管理画面集計：全21件（配信開始済み13件、配信予定7件、審査中1件）。
- 配信予定としてサイトへ新規掲載：
  - 2026-09-26 榎本魅愛「Eternity of Flower Words」
  - 2026-09-26 榎本魅愛「恋愛対象外 (仮)」
  - 2026-09-26 神代煌牙「何度生まれ変わっても - RE:BORN OATH -」
  - 2026-09-29 妃みちる「心に残る宝モノ」
- 既存作品に配信予定を追記：10/01「君とならラスボスまで」、10/02「世代を超えてママへ」、10/03「魔法が解けても」。
- 「夢と、介護と、わたしたち」は審査中でリリース日・LinkCore未確定のため、配信予定には掲載しない。
- 管理画面の「配信期間開始日」とLinkCoreの「リリース日」が異なる作品は両者を混同せず、公開日はLinkCoreの確認値を使用した。

## Instagram / note照合結果

- Instagram 2026-09-24告知：妃みちる 1st Digital Photo Book『ありのまま。 — Just As I Am. —』を反映。
- Instagram 2026-09-20告知：榎本魅愛「百万告」「取り扱いチューい」「Hello Hello Halloween」3曲同時配信を反映。
- Instagram 2026-09-19告知：妃みちる「friend like song」「たった1人の君へ」は既存の9/22同期データに保持。
- note 2026-09-24記事：写真集（50 CUT / 300円）をPhotobooksとNewsへ反映。
- note 2026-09-21記事：妃みちる Official ChannelオープンをNewsへ反映。記事からChannelの直接URLを確定できないためリンクは保留。
- note 2026-09-21記事：榎本魅愛3曲同時配信をNewsへ反映。

## 外部側の差異・保留

- noteプロフィールのWebサイト欄は `https://https://www.suzukaofficial.com/` と重複しており、Instagram表記も旧URL。外部サービス側の情報なのでサイトコードからは変更していない。
- 妃みちる Official Channelの専用URLは記事本文から確定できなかったため推測で追加していない。
- TuneCore審査中表記の「夢と、介護と、わたしたち」と、既存の公式MV作品名「夢と、介護と、私たち。」は表記が異なる。審査中登録の正式公開状態が確定していないため、既存作品名は自動変更していない。
- TuneCore審査中作品は公開予定日とLinkCoreが確定するまで、ストリーミング配信予定情報としては非掲載。

## 正本と再生成

- 主正本：`assets/data/creator-cms.json`
- 写真集正本：`assets/data/photobooks.json`
- TuneCore監査スナップショット：`assets/data/tunecore-catalog-20260924.json`
- 更新処理：`scripts/update_20260924_latest.py`
- 回帰監査：`scripts/audit_20260924_sync.py`

生成HTMLを個別編集せず、正本とジェネレーターからTOP、Artists、Releases、News、Discography、Ranking、Features、Gallery、Universe、Wiki、Schedule、Lyrics、Photobooks、Search、個別ページ、サイトマップを再生成する。

## 最終検証

- Build：`build_changed_content.py --dry-run` で差分0。同期監査の2回目生成も差分0。
- Lint / Typecheck相当：本リポジトリに専用のlint/typecheckコマンドはないため、Python全スクリプトのcompileallとJavaScript / MJSの`node --check`を実施し合格。
- Automated test：既存と追加を合わせた51本の監査スクリプトがすべて合格。
- Localhost / 404：392内部URLをクロールし、すべて200。リンク切れ・canonical不整合なし。
- Browser QA：PC 1280px、tablet 768px、mobile 390pxで主要テンプレートを確認。横スクロール、コンソールエラー、通信エラー、プレーヤー回帰なし。
- Player：初期表示でYouTube API / iframeを読み込まず、再生操作後のみAPIとiframeが生成されることを確認。
- Lighthouse（localhost）：Performance 71 / Accessibility 100 / Best Practices 100 / SEO 100。CLS 0、TBT 0ms。Performanceは圧縮・長期キャッシュがない簡易ローカルサーバーの影響を含む。
- 外部リンク：LinkCore 20件、note 3件、Instagram 3件は個別にHTTP 200を確認。HTML内の絶対URL 386件の一括確認で、外部・既存本番URL 369件は到達可能。新規本番URL 16件は未デプロイのため現時点で404（ローカルでは200）。設計上の`/404/`は404応答を確認。

最終状態：**変更済み・テスト済み・本番公開待ち**
