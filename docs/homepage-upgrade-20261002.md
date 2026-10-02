# 2026年10月2日更新の運用手順

このフォルダーは、元の `suzuka-official-music` に手を加えずに作成した確認用サイトです。Gitの履歴・認証情報はコピーしていません。本番公開は実行していません。

## 編集する場所

| 内容 | 編集する正本 |
|---|---|
| Artist、作品、News、作品と配信の状態 | `assets/data/creator-cms.json` |
| 公式チャンネル | Artistの `officialYoutubeUrl` / `officialYoutubeChannelId` / 出典・確認日時 |
| HERO | 対象Releaseの `homeHero`。設定は1作品だけに付与 |
| トップ掲載数・主要Artist | `homepage` |
| MIA meets | `seriesDefinitions` の `mia-meets` |
| 動画の別バージョン | Releaseの `videoVersions` |
| JSON-LDに使う公開日時の検証台帳 | `assets/data/youtube-publish-dates.json` |
| ブランド紹介 | `assets/data/brand.json` とCMSの `site.description` |
| 新セクションの構成 | `scripts/build_homepage_upgrade.py` |
| 新セクションの見た目 | `assets/homepage-upgrade.css` |

生成済みHTMLを直接変更すると再生成で失われます。

MIA meetsの `episodes` は現在空です。正式確認後、各話に `number`（1、2、3…）、`releaseSlug`（既存の公開Release）、`status: published`、`verifiedAt` を登録すると掲載できます。公開済み作品への参照と確認日時が必須です。相手・作品・公開日は確認前に追加しないでください。

作品公開日、MV公開日、ストリーミング配信日は別々に保持します。正式MVではない先行音源や短い告知動画には、その内容が伝わる `videoLabel` / `videoVersions.label` を付けます。旧MV・旧公開版のURLは残します。

## Macでの確認

ターミナルで実行します。

```bash
cd '/Users/enomotojunichi/Documents/SUZUKA公式サイト/suzuka-update-20261002'
python3 scripts/build_explore_catalog.py --root .
python3 scripts/audit_sync.py --root .
python3 scripts/audit_homepage_upgrade.py
python3 scripts/audit_seo.py
python3 -m http.server 8765
```

ブラウザーで `http://127.0.0.1:8765/` を開きます。すでに確認用サーバーが起動中なら最後のコマンドは不要です。サーバーを停止するときは起動したターミナルでControl+Cを押します。

## Windowsでの確認

確認用フォルダーを、例として `C:\SUZUKA\suzuka-update-20261002` にコピーします。Python 3とNode.jsが利用できる環境でPowerShellから実行します。

```powershell
Set-Location 'C:\SUZUKA\suzuka-update-20261002'
py -3 scripts/build_explore_catalog.py --root .
py -3 scripts/audit_sync.py --root .
py -3 scripts/audit_homepage_upgrade.py
py -3 scripts/audit_seo.py
py -3 -m http.server 8765
```

## 日付の運用

`updatedAt` にAsia/Tokyo基準の確認日時を登録します。静的生成はこの明示された日時を使うため、再生成の結果が実行時刻によって揺れません。過去の日付になった未確認予定はトップのUpcomingから除外し、Scheduleでは公開状況確認中として扱います。ブラウザーのSchedule分類もJST基準です。

予定日を迎えただけで公開済みに昇格させません。ストリーミングは公式LinkCoreの作品名・Artist・日付と、ストア導線の応答を確認してから `status: published` と `verifiedAt` を更新します。未確認配信の予定日を過ぎた場合は、ブラウザー表示も「配信状況確認中」とします。

この監査の `audit_homepage_upgrade.py` は10月2日時点の固定確認を含みます。後日10月3日作品の配信を正式確認した場合は、その検証台帳と監査の期待値を一緒に更新してください。過去の確認条件は固定fixtureに残します。

## 公開の扱い

既存運用は `main` へのpushからGitHub Actionsの検証・GitHub Pagesデプロイへ進む構成です。今回はpush・デプロイ・IndexNow送信を行っていません。元の作業フォルダーの未公開変更を確認したうえで、承認されたファイルだけを反映する必要があります。
