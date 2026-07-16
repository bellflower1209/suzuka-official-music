# SUZUKA 公式音楽サイト — GitHub Pages版

音楽レーベルSUZUKAの公式サイトを、GitHub Pagesでそのまま公開できる静的HTMLへ変換したパッケージです。SEO上の正式な本家はGitHub Pages版です。旧 `chatgpt.site` 版はコンテンツ取得元としてのみ使用し、公開時のcanonical・OGP・構造化データ・sitemapはGitHub Pages版へ正規化します。Node.jsやビルド作業は不要です。

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

## 正本サイトとの同期

正本サイトの公開内容をGitHub Pages版へ同期するときは、リポジトリ直下で次を実行します。

```bash
python3 scripts/sync_from_canonical.py
```

同期処理は、コンテンツ取得元のNext/Vinext固有スクリプトを除外し、内部リンクと画像参照をGitHub Pages向けの相対パスへ変換します。既存の固定ミュージックプレイヤーに加え、トップページの視聴CTA、YouTube登録導線、リリースカードの視聴導線、各アーティストページ末尾の回遊導線も自動で再適用されます。

GitHub Pagesで先行追加した「好きが、今日も増えていく。」はローカル専用リリースとして管理し、同期時にも個別ページ、トップページの最新カード、榎本魅愛の楽曲一覧、sitemapへの登録を保持します。

「もしも明日、はじめましてになっても。」も同じローカル専用リリースとして管理し、同期時に個別ページ、トップページ、榎本魅愛の代表曲・楽曲一覧、sitemapへの登録を保持します。正式ジャケットは `images/mv-moshimo-ashita-hajimemashite-ni-natte-mo.png` です。

### 「好きが、今日も増えていく。」正式ジャケットの差し替え

正式ジャケットは `images/mv-suki-ga-kyou-mo-fueteiku.jpg` に配置しています。トップページ、榎本魅愛の代表曲・楽曲一覧、個別リリースページ、OGP、Twitter Card、構造化データで同じ画像を参照します。

## 公開・SEO方針

- SEO上の正式な本家：`https://bellflower1209.github.io/suzuka-official-music/`
- 旧 `chatgpt.site` 版：旧サイト兼コンテンツ同期元（SEO上の正本ではありません）
- canonical・`og:url`・サイト内JSON-LD URL：各GitHub Pagesページの自己参照URL
- sitemap：GitHub Pages版の公開URLのみを収録
- Google Search Console：GitHub Pages版のURLプレフィックスを管理対象とします

同期スクリプトでは、取得元を `CONTENT_SOURCE_URL`、公開正規URLを `PUBLIC_CANONICAL_BASE_URL` として分離しています。そのため同期を再実行しても、SEO上の正本が旧サイトへ戻ることはありません。

Search Consoleへ追加するURLプレフィックスは `https://bellflower1209.github.io/suzuka-official-music/`、送信するサイトマップは `https://bellflower1209.github.io/suzuka-official-music/sitemap.xml` です。
