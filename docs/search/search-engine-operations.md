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
4. IndexNowを利用する場合は、下記の準備手順を実行する。

## IndexNow準備

IndexNowキーは8〜128文字の英数字またはハイフンで作成し、公開サイト配下のUTF-8テキストファイルとして配置する。キーはこのリポジトリへ事前生成していない。

キー取得後のローカル準備例:

```bash
python3 scripts/prepare_indexnow.py --key YOUR_INDEXNOW_KEY --write
```

この操作で次を生成する。

- `YOUR_INDEXNOW_KEY.txt`：公開確認用キーファイル
- `docs/search/indexnow-payload.json`：本番sitemap掲載URLだけを含む通知ペイロード

送信前チェック:

- キーファイルが本番URLでHTTP 200になること
- `host`が`bellflower1209.github.io`であること
- `keyLocation`が本番プロジェクト配下であること
- `urlList`がHTTPSかつ`/suzuka-official-music/`配下だけであること
- 前回から追加・更新・削除されたURLだけを通知し、同じURLを短時間に連続送信しないこと

送信先候補はIndexNow公式エンドポイント`https://api.indexnow.org/indexnow`。このプロジェクトのスクリプトは安全のため送信を実行しない。
