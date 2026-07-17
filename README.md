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
- `assets/styles.css`：正本サイトから同期する基本CSS
- `assets/engagement.css`：YouTube視聴・チャンネル登録・楽曲回遊CTAの追加CSS
- `assets/main.js` / `assets/player.css`：共通固定ミュージックプレイヤー
- `images/`：ジャケット画像・チャンネル画像
- `scripts/sync_from_canonical.py`：正本サイトから静的ページを同期するスクリプト
- `scripts/check_static_site.py`：内部リンクとアセットを検査するスクリプト
- `robots.txt` / `sitemap.xml`：検索エンジン向けファイル
- `.nojekyll`：GitHub Pages用設定

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
```

`sitemap.xml` はHTMLの自己参照canonicalから自動生成します。公開ページの追加・削除後は `python3 scripts/validate_sitemap.py --write` を実行してください。候補XML、重複、絶対URL、canonical、noindex、未公開ページ、robots.txtの検証に合格した場合だけ更新されます。GitHub Pagesへの公開後は `python3 scripts/validate_sitemap.py --remote` で、Googlebot User-Agentによる本番取得、Content-Type、リダイレクト、全URLのHTTP 200も確認できます。

XML名前空間はGoogle Search CentralとSitemaps.orgの標準例に合わせて `http://www.sitemaps.org/schemas/sitemap/0.9` を使用します。これは名前空間識別子であり、`loc`および公開サイトのURLはすべてHTTPSです。

## 公開済みサイトとの同期

公開済みのGitHub Pages版から静的ページと共有アセットを再取得するときは、リポジトリ直下で次を実行します。ローカルの未公開変更を上書きするため、実行前に必ずコミットまたはバックアップを作成してください。

```bash
python3 scripts/sync_from_canonical.py
```

同期処理は、公開済みページから不要な実行時スクリプトを除外し、内部リンクと画像参照をGitHub Pages向けの相対パスへ変換します。既存の固定ミュージックプレイヤーに加え、トップページの視聴CTA、YouTube登録導線、リリースカードの視聴導線、各アーティストページ末尾の回遊導線も自動で再適用されます。

GitHub Pagesで先行追加した「好きが、今日も増えていく。」はローカル専用リリースとして管理し、同期時にも個別ページ、トップページの最新カード、榎本魅愛の楽曲一覧、sitemapへの登録を保持します。

「もしも明日、はじめましてになっても」も同じローカル専用リリースとして管理し、同期時に個別ページ、トップページ、榎本魅愛の代表曲・楽曲一覧、sitemapへの登録を保持します。ジャケット上では末尾に句点があるため、表記差は楽曲台帳に記録しています。正式ジャケットは `images/mv-moshimo-ashita-hajimemashite-ni-natte-mo.png` です。

榎本魅愛の公開済み楽曲は `assets/data/enomoto-mia-releases.json` を正本として管理します。プロフィールの公式MV一覧、構造化データ、固定プレイヤー、監査スクリプトは、曲数をHTMLへ直接記載せず、この台帳の `status: published` から対象曲を取得します。未公開曲は `status: unpublished` とし、公開一覧やプレイヤーへ表示しません。

### 「好きが、今日も増えていく。」正式ジャケットの差し替え

正式ジャケットは `images/mv-suki-ga-kyou-mo-fueteiku.jpg` に配置しています。トップページ、榎本魅愛の代表曲・楽曲一覧、個別リリースページ、OGP、Twitter Card、構造化データで同じ画像を参照します。

## 公開・SEO方針

- SEO上の正式な本家：`https://bellflower1209.github.io/suzuka-official-music/`
- コンテンツ同期元：上記GitHub Pages版
- canonical・`og:url`・サイト内JSON-LD URL：各GitHub Pagesページの自己参照URL
- sitemap：GitHub Pages版の公開URLのみを収録
- Google Search Console：GitHub Pages版のURLプレフィックスを管理対象とします

同期スクリプトでは、取得元と公開正規URLの両方をGitHub Pages版へ固定しています。同期を再実行しても、canonical・OGP・構造化データが別オリジンへ切り替わることはありません。

Search Consoleへ追加するURLプレフィックスは `https://bellflower1209.github.io/suzuka-official-music/`、送信するサイトマップは `https://bellflower1209.github.io/suzuka-official-music/sitemap.xml` です。
