# SUZUKA 公式音楽サイト — GitHub Pages版

音楽レーベルSUZUKAの公式サイトを、GitHub Pagesでそのまま公開できる静的HTMLとして管理するパッケージです。SEO上の正式な本家とコンテンツ取得元は、どちらもGitHub Pages版へ統一しています。Node.jsやビルド作業は不要です。

## 収録内容

- `index.html`：トップページ
- `artists/index.html`：アーティスト一覧
- `artists/eclypse/index.html`：ECLYPSE専用ページ
- `artists/koga-kamishiro/index.html`：神代煌牙専用ページ
- `artists/enomoto-mia/index.html`：榎本魅愛の専用ページ
- `about/index.html`：音楽レーベルSUZUKAの紹介ページ
- `releases/`：個別楽曲ページ
- `social/index.html`：YouTube・作品・News・アーティストをまとめる公式SNSハブ
- `assets/styles.css`：正本サイトから同期する基本CSS
- `assets/engagement.css`：YouTube視聴・チャンネル登録・楽曲回遊CTAの追加CSS
- `assets/main.js` / `assets/player.css`：共通固定ミュージックプレイヤー
- `assets/social.js` / `assets/social.css`：共通SNS導線・シェア機能
- `assets/data/social-links.json` / `assets/data/release-links.json`：確認済み公式URLの正本
- `images/`：ジャケット画像・チャンネル画像
- `scripts/sync_from_canonical.py`：正本サイトから静的ページを同期するスクリプト
- `scripts/check_static_site.py`：内部リンクとアセットを検査するスクリプト
- `robots.txt` / `sitemap.xml`：検索エンジン向けファイル
- `assets/data/releases-catalog.json`：検索・ジャンル・年表・Weekly Pickが共通利用する公開作品の正本
- `search/` / `genres/` / `discography/`：作品を探すための静的ページ
- `scripts/build_explore_catalog.py`：正本データと探索ページを再生成するスクリプト
- `scripts/build_explorer_update.py`：ランキング、特集、MVギャラリー、世界観、Wiki、アーティスト強化を正本から再生成
- `assets/data/ranking-source.json`：将来の人気指標を登録するランキング入力正本（CSVも利用可能）
- `rankings/` / `features/` / `gallery/` / `universe/` / `wiki/`：SUZUKA Explorer Update
- `.nojekyll`：GitHub Pages用設定

## Creator Platform Version 3.1

`assets/data/creator-cms.json`を公開情報の正本とし、HTMLを個別に直さず次の順で生成します。公開予定時刻に達しただけでは`published`へ変更せず、公式YouTubeで一般公開を確認してから正本の`status`を更新します。

```bash
python3 scripts/update_20260808_v31.py
python3 scripts/build_explore_catalog.py
python3 scripts/build_explore_catalog.py
python3 scripts/audit_sync.py
```

Version 3.1では`/schedule/`、`/lyrics/`、Solo / Group対応の全Artistプロフィール、4区分の`/rankings/`を正本から生成します。歌詞詳細は`lyricsAvailable`、`lyricsSource`、`lyricsText`がすべて確認済みの作品だけを生成します。GA4・YouTube Analyticsの実測値がない場合は人気順位を作らず、`assets/data/analytics/`に準備中として保持します。

追加監査：

```bash
python3 scripts/audit_artist_v31.py
python3 scripts/audit_schedule.py
python3 scripts/audit_lyrics.py
python3 scripts/audit_v31.py
```

## GitHub Pagesで公開する手順

1. GitHubで新しいリポジトリを作成します。
2. このフォルダー内のファイルとフォルダーを、すべてリポジトリ直下へアップロードします。
3. GitHubの `Settings` → `Pages` を開きます。
4. `Build and deployment` のSourceを `Deploy from a branch` にします。
5. Branchを `main`、フォルダーを `/(root)` に設定して保存します。
6. 数分後に表示されるGitHub PagesのURLを開きます。

内部ページ、CSS、JavaScript、画像はすべて相対パスのため、`https://ユーザー名.github.io/リポジトリ名/`の形式でも動作します。

## ローカル確認

`suzuka-official-music` の親フォルダーで次を実行します。

```bash
python3 -m http.server 8000
```

ブラウザで `http://localhost:8000/suzuka-official-music/` を開いてください。GitHub Pagesと同じベースパスで確認できます。終了はターミナルで `Control + C` です。

内部リンクの一括確認は、別のターミナルで次を実行します。

```bash
python3 scripts/check_static_site.py http://localhost:8000/suzuka-official-music/
```

canonical、OGP、構造化データ、見出し、画像alt、sitemap、robots、孤立ページをまとめて確認する場合は、リポジトリ直下で次を実行します。

```bash
python3 scripts/audit_seo.py
python3 scripts/validate_sitemap.py
python3 scripts/audit_sitemaps.py
python3 scripts/audit_social_links.py
python3 scripts/audit_explorer_update.py
```

`sitemap.xml` はHTMLの自己参照canonicalから自動生成します。公開ページの追加・削除後は `python3 scripts/validate_sitemap.py --write` を実行してください。候補XML、重複、絶対URL、canonical、noindex、未公開ページ、robots.txtの検証に合格した場合だけ更新されます。GitHub Pagesへの公開後は `python3 scripts/validate_sitemap.py --remote` で、Googlebot User-Agentによる本番取得、Content-Type、リダイレクト、全URLのHTTP 200も確認できます。

`sitemap.xml`、`image-sitemap.xml`、`video-sitemap.xml` の3ファイルは `python3 scripts/audit_sitemaps.py` で、UTF-8 XML宣言、Sitemap Protocol名前空間、`url` / `loc` 構造、HTTPS正式ホスト、重複、Googleの上限を一括監査できます。公開後は `python3 scripts/audit_sitemaps.py --remote` を実行すると、Googlebot User-AgentでのHTTP 200、リダイレクトなし、`application/xml`相当、本番XMLとリポジトリのバイト一致まで確認します。

XML名前空間はGoogle Search CentralとSitemaps.orgの標準例に合わせて `http://www.sitemaps.org/schemas/sitemap/0.9` を使用します。これは名前空間識別子であり、`loc`および公開サイトのURLはすべてHTTPSです。

## 公開済みサイトとの同期

公開済みのGitHub Pages版から静的ページと共有アセットを再取得するときは、リポジトリ直下で次を実行します。ローカルの未公開変更を上書きするため、実行前に必ずコミットまたはバックアップを作成してください。

```bash
python3 scripts/sync_from_canonical.py
```

同期処理は、公開済みページから不要な実行時スクリプトを除外し、内部リンクと画像参照をGitHub Pages向けの相対パスへ変換します。既存の固定ミュージックプレイヤーに加え、トップページの視聴CTA、YouTube登録導線、リリースカードの視聴導線、各アーティストページ末尾の回遊導線も自動で再適用されます。

公式SNSハブ `/social/` とSNSリンク正本はローカル専用資産として同期対象から保護します。公式Instagram URLは未確認のため、推測したリンクを公開せず `status: unconfirmed` で管理しています。確認後は `assets/data/social-links.json` の該当項目だけを更新してください。

作品別のYouTube説明欄・固定コメント・Instagram投稿用UTM URLは、次のコマンドで検証・再生成できます。サイト内リンク、canonical、sitemapにはUTMを付けません。

```bash
python3 scripts/audit_social_links.py --write
```

生成先は `docs/social/official-link-plan.md` です。

GitHub Pagesで先行追加した「好きが、今日も増えていく。」はローカル専用リリースとして管理し、同期時にも個別ページ、トップページの最新カード、榎本魅愛の楽曲一覧、sitemapへの登録を保持します。

「もしも明日、はじめましてになっても」も同じローカル専用リリースとして管理し、同期時に個別ページ、トップページ、榎本魅愛の代表曲・楽曲一覧、sitemapへの登録を保持します。ジャケット上では末尾に句点があるため、表記差は楽曲台帳に記録しています。公開ページで使用する確認済み画像は `images/mv-mia.jpg` です。

榎本魅愛の公開済み楽曲は `assets/data/enomoto-mia-releases.json` を正本として管理します。プロフィールの公式MV一覧、構造化データ、固定プレイヤー、監査スクリプトは、曲数をHTMLへ直接記載せず、この台帳の `status: published` から対象曲を取得します。未公開曲は `status: unpublished` とし、公開一覧やプレイヤーへ表示しません。

### 「好きが、今日も増えていく。」正式ジャケットの差し替え

正式ジャケットは `images/mv-suki-ga-kyou-mo-fueteiku.jpg` に配置しています。トップページ、榎本魅愛の代表曲・楽曲一覧、個別リリースページ、OGP、Twitter Card、構造化データで同じ画像を参照します。

## 公開・SEO方針

- SEO上の正式な本家：`https://www.suzukaofficial.com/`
- コンテンツ同期元：上記GitHub Pages版
- canonical・`og:url`・サイト内JSON-LD URL：各GitHub Pagesページの自己参照URL
- sitemap：GitHub Pages版の公開URLのみを収録
- Google Search Console：GitHub Pages版のURLプレフィックスを管理対象とします

`CNAME`には`www.suzukaofficial.com`を保持します。DNSでは`www`のCNAMEを`bellflower1209.github.io`へ向け、GitHub Pagesが証明書を発行した後にHTTPSを強制します。旧`https://bellflower1209.github.io/suzuka-official-music/`は移行元URLであり、canonical・sitemap・IndexNow通知には使用しません。

同期スクリプトでは、取得元と公開正規URLの両方をGitHub Pages版へ固定しています。同期を再実行しても、canonical・OGP・構造化データが別オリジンへ切り替わることはありません。

Search Consoleへ追加するURLプレフィックスは `https://www.suzukaofficial.com/`、送信するサイトマップは `https://www.suzukaofficial.com/sitemap.xml` です。

## IndexNow

本サイトは、新規公開・更新・削除されたindex可能な公開ページだけを、GitHub Pagesのデプロイ成功後にIndexNowへ通知します。IndexNowへの通知は検索エンジンへの更新通知であり、インデックス登録を保証しません。

- 設定：`assets/data/indexnow.json`
- 送信スクリプト：`scripts/submit_indexnow.py`
- 自動送信：`.github/workflows/indexnow.yml`
- 送信記録：`docs/indexnow/submission-log.json`およびGitHub Actionsの実行artifact

手動確認と送信：

```bash
python3 scripts/submit_indexnow.py --dry-run
python3 scripts/submit_indexnow.py --submit
python3 scripts/submit_indexnow.py --urls https://www.suzukaofficial.com/
```

通常は直前の成功Pagesデプロイと現在の`sitemap.xml`・公開HTMLのSHA-256を比較します。`--urls`だけを指定した場合はdry-runとなり、外部送信しません。`/admin/`、noindex、アセット、クエリ・UTM付きURL、予約中ページは送信対象外です。
