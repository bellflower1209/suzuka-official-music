# SUZUKA 公式音楽サイト — GitHub Pages版

音楽レーベルSUZUKAの公式サイトを、GitHub Pagesでそのまま公開できる静的HTMLへ変換したパッケージです。正本は `chatgpt.site` 版で、GitHub Pages版はその公開HTML・CSS・画像を静的サイト向けに同期しています。Node.jsやビルド作業は不要です。

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

同期処理は、正本のNext/Vinext固有スクリプトを除外し、内部リンクと画像参照をGitHub Pages向けの相対パスへ変換します。既存の固定ミュージックプレイヤーに加え、トップページの視聴CTA、YouTube登録導線、リリースカードの視聴導線、各アーティストページ末尾の回遊導線も自動で再適用されます。

## SEOに関する注意

各HTMLのcanonical・OGP・JSON-LDは、正本である次のサイトを指しています。

https://suzuka-official-music.ria20210815.chatgpt.site

`robots.txt` と `sitemap.xml` はGitHub Pages版の公開URLを使用しています。GitHub Pages版を正本へ変更する場合は、HTML内のcanonical・OGP・JSON-LDもGitHub Pages URLへ統一してください。
