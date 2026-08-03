# SUZUKA 検索エンジン公開運用

更新基準: 2026-08-03T00:45:42+09:00

## Google Search Console

対象プロパティ:

`https://bellflower1209.github.io/suzuka-official-music/`

公開後に人が行う操作:

1. `sitemap.xml`、`image-sitemap.xml`、`video-sitemap.xml`をサイトマップ画面から送信する。
2. URL検査でトップ、新規作品3ページ、新規News 3ページを確認し、インデックス登録をリクエストする。
3. 動画の構造化データに残っている旧`uploadDate`警告で「修正を検証」を開始する。

`/admin/`と`/admin/dashboard/`はnoindexであり、登録リクエストを行わない。UpcomingのYouTube URLはサイトの公開作品ページではないため、公開日までMusicRecording・VideoObjectとして登録しない。

## Bing Webmaster Tools

1. GitHub Pagesの公開URLをサイトとして追加する。
2. 所有権確認はBingの案内に従い、Google Search Consoleからのインポートまたは指定メタタグを使う。
3. `sitemap.xml`を送信する。必要に応じて画像・動画サイトマップも個別送信する。
4. GitHub Actionsの「IndexNow after GitHub Pages」で送信結果を確認する。

## IndexNow運用

IndexNowキーは32文字の16進乱数で生成し、GitHub Pagesのプロジェクト配下へUTF-8テキストとして配置している。`keyLocation`は`assets/data/indexnow.json`で明示する。

ローカルdry-runと手動送信:

```bash
python3 scripts/submit_indexnow.py --dry-run
python3 scripts/submit_indexnow.py --submit
python3 scripts/submit_indexnow.py --urls https://bellflower1209.github.io/suzuka-official-music/
```

`--urls`だけを指定した場合は送信せず、dry-runとしてペイロードを表示する。通常送信は直前の成功PagesデプロイSHAと現在のsitemap・公開HTMLハッシュを比較し、追加・更新・削除URLだけを送る。

送信前チェック:

- キーファイルが本番URLでHTTP 200になること
- `host`が`bellflower1209.github.io`であること
- `keyLocation`が本番プロジェクト配下であること
- `urlList`がHTTPSかつ`/suzuka-official-music/`配下だけであること
- 前回から追加・更新・削除されたURLだけを通知し、同じURLを短時間に連続送信しないこと

送信先はIndexNow公式エンドポイント`https://api.indexnow.org/indexnow`。HTTP 200または202だけを成功とし、それ以外はActions上で失敗として記録する。IndexNowは検索結果へのインデックス登録を保証しない。
