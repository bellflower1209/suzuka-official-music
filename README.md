# SUZUKA 公式音楽サイト — GitHub Pages版

現在公開中のSUZUKA公式音楽サイトを、GitHub Pagesでそのまま公開できる静的HTMLへ変換したパッケージです。Node.jsやビルド作業は不要です。

## 収録内容

- `index.html`：トップページ
- `artists/index.html`：アーティスト一覧
- `artists/enomoto-mia/index.html`：榎本魅愛の専用ページ
- `assets/styles.css`：サイト全体のCSS
- `assets/main.js`：モバイルメニュー用JavaScript
- `images/`：ジャケット画像・チャンネル画像
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

このフォルダーをターミナルで開き、次を実行します。

```bash
python3 -m http.server 8000
```

ブラウザで `http://localhost:8000/` を開いてください。終了はターミナルで `Control + C` です。

## SEOに関する注意

canonical、robots.txt、sitemap.xmlは、公式URLである次のサイトを指しています。

https://suzuka-official-music.ria20210815.chatgpt.site

GitHub Pages版を今後の公式URLに変更する場合は、HTML内のcanonical・OGP・JSON-LDと、`robots.txt`・`sitemap.xml`内のURLを、新しいGitHub Pages URLへ置き換えてください。
