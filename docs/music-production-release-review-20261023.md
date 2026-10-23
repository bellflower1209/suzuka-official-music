# SUZUKA MUSIC PRODUCTION — 公開前レビュー

対象は `bellflower1209/suzuka-official-music` の現行公開V6パッケージです。基準コミットは `b355cf47690bf3fe3fdc3c2863fd56108565f3dc`、基準公開パッケージは781ファイル、SHA-256目録のダイジェストは `db92d53a7ccbdee869f41171aa1a1342b2fa28f72f5544939943baf95a2b4184` です。リポジトリ直下の旧HTMLは今回の公開成果物の入力に使用しません。

## 実装と変更理由

`site-content/music-production/page.html.template` にページ本文とSEO・構造化データ、同じフォルダーのCSSとJavaScriptに表示とコピー操作を置きました。`scripts/build_music_production_release.py` は基準コミットの検証済み公開パッケージから毎回生成します。現行のV6トップと12ワールド、内側のページのナビゲーションへリンクを追加し、トップ末尾に独立した案内セクションを置きます。既存の音声制御と演出スクリプトは変更しません。

公開パッケージは784ファイルです。既存781ファイルはすべて残し、変更はHTML 355件のナビゲーション・トップ案内、`sitemap.xml` の1 URL追加、公開目録の更新だけです。残る424ファイルは基準とバイト一致します。新規公開ファイルは `/music-production/index.html`、`/assets/music-production.css`、`/assets/music-production.js` です。サイトマップは既存354 URLを順序・内容ともに保持して355 URLになります。

`scripts/build_official_sync_package.py` は旧コミット `2f6c97b` の760ファイルのパッケージを起点にしていました。現行の781ファイルを起点にしないまま再使用すると、V6音声起動修正や新サービスを巻き戻すため、現行のパッケージダイジェストを検出した時点で停止する条件を追加しました。今回の拡張は専用ビルダーで生成します。公開検証器、承認条件、GitHub Actionsのデプロイ条件は変更していません。

## ローカル検証

以下を2026-10-23に新しい作業ツリーと隔離した展開先で実行しました。

| 検証 | 結果 |
| --- | --- |
| 生成と2回目の再生成比較 | PASS、同一ダイジェスト |
| 公開パッケージ検証 | PASS、784ファイル、公開操作なし |
| 既存781ファイル保持・意図した差分 | PASS、専用6テスト |
| V6非公開音声ゲート | PASS、既存11テスト |
| 公開パッケージの構造化データ | PASS、JSON-LD 375ブロック、VideoObject 241件 |
| 公開パッケージのサイトマップ | PASS、355 URL、重複・canonical不一致なし |
| リポジトリ直下の既存SEO監査 | PASS、既存342 URL。新ページは公開パッケージ側で検査 |
| 既存Celestial Gate監査 | PASS、12アーティスト。正式ドア音声欠落に伴う既存の無音フォールバック表示は継続 |
| Chromium 1440px・390px | PASS、表示、メール本文、コピー、モバイルメニュー、トップ・ワールド・About導線 |
| Safari ローカル表示 | PASS、表示とコピー。レスポンシブデザインモードでも確認 |

ブラウザ検証はローカル候補です。実機iPhoneと、本番ドメインでの変更後の音声再生は公開前には確認できません。V6の音声関連ファイルは基準パッケージとバイト一致し、既存の音声ゲートテストは通過しています。正式ドア音声の欠落表示は今回の変更前からあります。

## 運用・変更箇所

文章は `site-content/music-production/page.html.template`、配色や余白は `music-production.css`、コピー後の表示は `music-production.js` を編集します。問い合わせ先とメール本文の項目は `scripts/build_music_production_release.py` の `mailto()` と `MAIL_FIELDS` が正本です。変更後は、独立作業ツリーで次を実行します。

```sh
python3 -B scripts/build_music_production_release.py --write
python3 -B scripts/build_music_production_release.py --check
python3 -B scripts/test_music_production_release.py
python3 -B scripts/verify_public_release.py --output /private/tmp/新しい空の確認先
```

`--output` は既存ファイルを含まない新しい確認先を指定します。生成後に公開パッケージ用のSEO・サイトマップ監査とブラウザ確認を実施します。

## 公開とロールバック

Draft PRは公開承認ではありません。PRのActionsはビルド検証のみで、Pagesアップロードとデプロイはmain向けの条件に限定されています。SUZUKA代表が公開を承認した後、CI結果と差分を再確認してmainへマージすると、現行ワークフローのPages公開が起動します。公開後は `/music-production/`、トップ・ワールド・内側のページ、355 URLのサイトマップ、音声ON/OFF、アナリティクスを本番ドメインで確認します。

ロールバックが必要な場合は、代表の承認のもとでmain上の追加コミットをrevertし、基準の公開パッケージダイジェストと781ファイルが戻ることを検証してからPagesを再実行します。変更前のブラウザや端末キャッシュによる反映遅延は、公開後の確認時に区別します。
