# SUZUKA — CELESTIAL GATE 運用・公開前確認

今回の表示名は **SUZUKA — CELESTIAL GATE**、コンセプトは「音楽が導く、十二の世界」。既存のSEO上のブランド実体 `SUZUKA Official`、canonical・OGP・JSON-LD・最新作品HeroとH1を保持しています。データ移行とフレームワーク移行はありません。

## 変更する場所

| 目的 | 正本・ソース |
|---|---|
| Artist / 曲 / MV / 歌詞 / 公開状態 | `assets/data/creator-cms.json` |
| 扉の色・領域名・装飾・速度・音量 | `assets/data/celestial-gate.json` |
| 共通の見た目・スマホ・印刷 | `assets/celestial-gate.css` |
| 扉・音声・スキップ・短縮・戻る処理 | `assets/celestial-gate.js` |
| 各ページへの反映・12扉の生成 | `scripts/build_celestial_gate.py` |
| 写真背景・門・素材台帳 | `assets/cinema/` / `assets/data/celestial-cinema-assets.json` |
| 小さな紋章 | `assets/celestial-emblems.svg` |

写真背景・門・領域名は今回のUIデザインです。旧宮殿・城SVGはメイン背景から退役しました。写真素材・制作原本・使用条件・修正箇所は [Cinema V2運用資料](celestial-cinema.md) を参照してください。公式Artistの顔・衣装・設定画像・作品ジャケットの代替ではありません。Artist画像未登録のLEON VAIL / 鉄髭はIMAGE PENDINGを維持しています。新Artistを正本へ追加するときは、テーマJSONにもそのslugの表示設定を追加してください。魔界はNOXのみです。

生成されたHTMLを直接編集せず、上の正本・ソースを変更して次を実行します。

```bash
python3 scripts/build_changed_content.py --root . --dry-run
# deletedCount が 0 であること、changedFiles が意図した範囲であることを確認
python3 scripts/build_changed_content.py --root .
python3 scripts/build_changed_content.py --root . --dry-run
# 2回目は changedCount=0 / deletedCount=0
python3 scripts/audit_sync.py
python3 scripts/audit_celestial_gate.py
node --check assets/celestial-gate.js
```

通常の `build_explore_catalog.py` の最後にも共通テーマ生成が接続されています。既存監査の期待値は変更していません。

## 正式効果音が未登録

`door-heavy-v2.wav` は未取得です。V4では別管理の新規候補 `door-heavy-candidate-v4.wav` を試聴できます。「候補音声 OFF」が初期値で、正式Ver.2とは明確に区別します。候補の出典・SHA・制作仕様とV4操作は [V4運用資料](celestial-portal-v4.md) を参照してください。

正式原音を受け取った後の手順：

1. 原音を改変せず `assets/audio/door-heavy-v2.wav` に配置します。
2. SHA-256を記録します。
3. `assets/data/celestial-gate.json` の `doorAudio` を `assets/audio/door-heavy-v2.wav`、`doorAudioSha256` を原音のSHA-256、`doorAudioStatus` を `verified-formal-v2` に変更します。
4. 再生成します。ファイル名・サイト内パス・SHAが一致しなければビルドはエラーになります。
5. 実際に音声ONで連続試聴し、重低音の音質・初期音量・紋章発光と開扉の同期を確認します。WAVそのものの試聴は、モックテストでは代替できません。

Macのハッシュ確認：

```bash
shasum -a 256 assets/audio/door-heavy-v2.wav
```

Windows PowerShell：

```powershell
Get-FileHash .\assets\audio\door-heavy-v2.wav -Algorithm SHA256
```

音声の初期値はOFF。音量上限0.5・初期0.24、ON/OFF・音量・短縮設定は端末のlocalStorageに保存します。通常演出は4.0秒、短縮・reduce・データ節約時は250msです。効果音のファイルはArtist選択時だけ取得し、取得・再生の準備が500msを超えた場合は無音で進みます。再生中のaudio/video、または状態不明のYouTube/Vimeo iframeがある場合は重複を避けて無音にします。既存本番はサイト内楽曲プレイヤーを撤去済みの外部視聴方式で、今回もその再生導線を保持しています。

## ローカルプレビュー

作業フォルダー：`/Users/enomotojunichi/Documents/SUZUKA公式サイト/suzuka-celestial-gate`

Macではリポジトリ直下からNodeのローカルサーバーを起動します。

```bash
cd '/Users/enomotojunichi/Documents/SUZUKA公式サイト/suzuka-celestial-gate'
node scripts/preview_celestial_gate.cjs 8821
```

ブラウザ：`http://127.0.0.1:8821/`。確認動画と画像：`http://127.0.0.1:8821/review/review.html`。停止はControl+C。

Windowsではチェックアウトのルートで `node scripts/preview_celestial_gate.cjs 8821` を実行してください。

```bash
python3 scripts/check_static_site.py http://127.0.0.1:8821/
```

## 操作テストの再実行

Playwrightは検証用だけに使用し、公開サイトにNode依存を追加していません。Macの実行例：

```bash
npm install --prefix /private/tmp/cg-browser --cache /private/tmp/cg-npm-cache playwright --no-audit --no-fund
CG_PLAYWRIGHT_MODULE=/private/tmp/cg-browser/node_modules/playwright \
CG_QA_OUTPUT=/private/tmp/celestial-gate-browser \
node scripts/browser_celestial_gate_qa.cjs http://127.0.0.1:8821/
```

Macではインストール済みChromeを使います。WindowsではPlaywrightのChromiumをインストールするか、`CG_CHROME_EXECUTABLE` でChrome実行ファイルを指定します。Windows PowerShellの検証用Chrome指定例：

```powershell
npm install --prefix "$env:TEMP\cg-browser" playwright --no-audit --no-fund
$env:CG_PLAYWRIGHT_MODULE = "$env:TEMP\cg-browser\node_modules\playwright"
$env:CG_CHROME_EXECUTABLE = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
node .\scripts\browser_celestial_gate_qa.cjs http://127.0.0.1:8821/
```

音源エラーのケースは、実音を出さないWeb Audioモックで遷移の安全性だけを確認します。iPhone/Androidの実機と正式音源は別途確認が必要です。

## 公開前の最終手順

1. 正式Ver.2を組み込み、実音と同期を確認する。
2. 未登録のArtist画像2組は、正式画像受領・登録、または現状のIMAGE PENDINGでの公開可否を最終レビューで判断する。
3. iPhone Safari / Android Chrome実機で、音声ON/OFF・戻る・低速回線・短縮・メニュー・全Artistを確認する。
4. 承認対象コミットと差分を確認する。旧チェックアウトの未公開変更や番号付き重複ファイルを含めない。
5. **ユーザーの明示的な公開承認後に限り**、作業ブランチのPR作成・レビュー・mainへの反映・既存Pages workflowによるデプロイを行う。
6. ActionsとPagesの成功に加え、本番のHTML/アセット一致・リンク・画像・3幅表示・console・音声を確認する。

今回の作業ではpush・PR作成・merge・deploy・IndexNow送信は行いません。
