# SUZUKA Halloween 2026 編集・運用手順

作業フォルダーは suzuka-halloween-20261004。本番へのpush・デプロイは未実施。
既存のmain（44a2de0）を基準にした独立コピーで作成し、元フォルダーは編集していません。

| 編集対象 | 正本／編集箇所 |
|---|---|
| Artist情報・鉄髭・メンバー | assets/data/creator-cms.json の artists |
| 季節の有効期間・表示文言 | assets/data/site-season.json |
| 色・月・コウモリ・星・ランタン・霧 | assets/halloween-2026.css |
| HTML季節装飾・埋め込み除去・画像確認中表示 | scripts/build_halloween.py |
| 外部公式画像の404記録 | assets/data/image-availability.json |
| メニュー・SNS読み込み | assets/main.js（音楽再生処理は削除済み） |

生成HTMLは直接編集せず、正本とスクリプトを修正後に生成してください。

```sh
cd "/Users/enomotojunichi/Documents/SUZUKA公式サイト/suzuka-halloween-20261004"
python3 scripts/build_changed_content.py --root .
python3 scripts/audit_sync.py --root .
python3 scripts/audit_halloween.py
python3 scripts/audit_artist_v31.py
python3 scripts/audit_images.py
node scripts/test_season_date.cjs
```

ローカル表示は http://127.0.0.1:8766/ 。サーバー停止後の再開コマンド:

```sh
python3 -m http.server 8766 --bind 127.0.0.1
```

別のターミナルで内部リンクを検証:

```sh
python3 scripts/check_static_site.py http://127.0.0.1:8766/
```

ブラウザー検証は scripts/browser_halloween_qa.cjs。PlaywrightとChromeが必要です。このMacの既存Playwrightを使用する例:

```sh
PLAYWRIGHT_PATH="/Users/enomotojunichi/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright" node scripts/browser_halloween_qa.cjs http://127.0.0.1:8766/
```

WindowsではPythonの起動名に応じて python3 を python または py に変更し、作業フォルダーを指定してください。

季節設定は日本時間2026年10月1日から11月1日直前まで有効。11月1日にはバナー・配色が自動終了し、サイト内プレイヤー削除とArtist追加・画像修復は残ります。
JavaScriptが利用できない場合は通常デザインになります。prefers-reduced-motionとスマホでは霧のアニメーションを無効化しています。

画像404の55 URLには、同じ動画の低解像度画像も確認しましたが復旧候補はありませんでした。
別のArtistや作品画像には差し替えず「公式画像確認中」の文字だけの表示にしています。正本の歴史的画像URLは保持し、表示層と生成済みカタログで状態を明示しています。
公式画像が再公開されたら、一次情報と本人・作品の一致を確認し、正本画像とimage-availability.jsonを更新して再生成してください。
妃みちるは既存の公式チャンネルNEWS用画像 images/michiru-official-channel-note.jpg を復旧しています。
鉄髭は画像・未確認の音楽ジャンル・公式チャンネル・作品を推測追加していません。

音楽プレイヤーの再導入は禁止。YouTube埋め込みは外部視聴リンクへ変換されます。
生成前に前回の季節ブロックを除去し、配信告知等の生成後に季節演出を追加する順序を維持してください。
公開するときは既存の GitHub main → Actions → Pages の手順を利用し、本番URLで改めて検証してください。
