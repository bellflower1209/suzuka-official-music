# SUZUKA CELESTIAL GATE — V4 Cinematic Portal

ローカルレビュー用。push / PR / mainへのマージ / デプロイは実施しません。

## 実装と変更箇所

- `assets/data/celestial-gate.json`：通常4000ms、短縮250ms、5段階の時刻、到着650ms、正式音源・新規候補の別登録。
- `assets/celestial-gate.js`：requestAnimationFrame共通時計。背景・門・扉・手前の霧の独立した動き。外側蝶番で左右106度回転。画像選択は遷移先のレスポンシブpictureと一致。
- `assets/celestial-gate.css`：24pxの厚み、裏面テクスチャ、陰影、前景門の奥行き、奥の景色の別速度、抑えたブラー、NOX専用の深紅霧・暗転。
- `scripts/build_celestial_gate.py`：正本の末尾で307ページを生成。時刻順・音源SHAと候補区別を検証。到着時の背景色設定はheadで先行し、白いフラッシュを抑止。

|開始–終了|動き|
|---|---|
|0–400ms|門へ接近|
|400–900ms|紋章が発光|
|900–2200ms|重量感のある左右開扉。効果音開始は900ms|
|2200–2800ms|奥の世界が広がる|
|2800–3500ms|三次曲線で加速。門は1170px手前へ、背景は別倍率で動く|
|3500–4000ms|各世界の霧で画面を包み、移動先へ|
|到着650ms|同一背景のオーバーレイからページの同じ景色に接続|

`timeline` を昇順に保ち、`durationMs` は3500–6000ms内で調整できます。画像読み込みは操作を止めません。画像デコード待ちは最大400ms、音声準備は最大500ms。双方を並行して待った後に共通タイムラインを開始します。移動先HTMLを事前取得し、HTTP失敗・HTML以外・タイムアウト時は元ページのスクロールとフォーカスを回復します。成功確認直後に回線が切断してブラウザ自体のエラーページに置き換わる場合は、ブラウザの戻る操作が必要です。

スキップ、Escape、キャンセル、フォーカス閉じ込め、戻る/BFCache、連続クリック抑止、storage拒否、音声OFF/音量変更に対応。演出中も音声OFFと音量を操作できます。演出中のONは次の扉に適用します。reduced-motion・データ節約・短縮・天界へ帰還では250msで進み、長いカメラ移動と効果音を省略します。

## 音源の状態

正式SUZUKA 重低音Ver.2 `assets/audio/door-heavy-v2.wav` は未提供・未登録。`doorAudio` とSHAはnullのままです。リポジトリ、親作業フォルダ、Desktopのファイル名、未追跡ファイル、今回の添付資料を調査しました。無関係な楽曲WAVを扉音に転用していません。

新規試聴候補：`assets/audio/door-heavy-candidate-v4.wav`。**正式採用済みではありません。**

- 48kHz / 16bit / ステレオ / 3.1秒 / 595244bytes。
- SHA-256 `9873405f8cfe15720f74e53db83c9209c7edb02f0a09df807447435151606ebc`。
- 独自の手続き的DSP合成。低周波スイープ、フィルターを通した摩擦音、空間の響きを制作。第三者の音声や楽曲は使用しません。
- 音源開始から約1.3秒までに摩擦・低音が減衰し、その後の奥への進入に合わせて薄い空間音が入ります。波形の立ち上がり・末尾とWeb Audioの別ゲインで急な音量変化を抑えます。
- 初期OFF。音量初期0.24・上限0.5。設定は端末に保存。音声はユーザー操作時のみ取得・再生。音楽再生中や状態不明のYouTube/Vimeo埋め込みがある場合は抑止します。
- 再生成：`python3 scripts/create_portal_audio_candidate.py`。記録：`assets/data/portal-audio-candidate.json`。同じSHAになる決定的合成です。
- 正式音源受領後はWAVを所定パスに置き、SHAを`doorAudioSha256`に設定し、`doorAudio`を登録。正式音源を優先する処理は実装済みですが、実ファイルによる試聴・同期確認は未実施です。

この候補の技術的デコード検証は人間の聴感による採用判断を代替しません。

## 背景・公式素材

V3の背景原本15点と既存エンコードを継続使用。新しい人物画像や背景は生成しません。背景の出典・生成指示・原本/派生SHAは `assets/data/celestial-cinema-assets.json`。採用背景一覧は hero / gallery-hall / asagiri-shinobu / asteria / eclypse / enomoto-mia / koga-kamishiro / michiru / nox / rangili / revive / veilfang / tetsuhige / leon-vail、およびNOX縦版。既存門素材は天界/魔界の扉と門枠4種です。AVIF/WebP、768/1280/1600px、スマホ縦版を保持します。

LEON VAIL公式参照シートVer.1は、正本の登録SHA `15252636c0a59a41c94cbc10cde0ea95f5297650bd3e29d1c950b1900885a0cb` と一致します。参照シートは人物設定用で、公開用の単独プロフィール画像としての登録は空欄です。鉄髭は公式作品ジャケットがありますが、公開プロフィール画像がありません。参照シートやジャケットから顔を切り出さず、両組のIMAGE PENDINGを維持します。

12組・82作品・31公開歌詞、正本JSON、公式原画像、MV・歌詞・配信リンク、URL/canonical/JSON-LD/SEO、既存監査は維持します。

## ローカル起動・検証

```sh
cd '/Users/enomotojunichi/Documents/SUZUKA公式サイト/suzuka-celestial-gate'
node scripts/preview_celestial_gate.cjs 8821
```

サイト `http://127.0.0.1:8821/`。成果物 `http://127.0.0.1:8821/review/review.html`。停止はCtrl+C。localhostのみ。確認動画はブラウザ画面の実録で、音声は録音していません。試聴候補WAVを別掲します。

追加QA：`scripts/browser_celestial_portal_qa.cjs`。PlaywrightのChrome・WebKitと、実際の候補WAVを用います。既存QA：`scripts/browser_celestial_gate_qa.cjs`。こちらの正式音源ケースはモックであり、正式Ver.2試聴済みとは扱いません。

## 公開前に残る確認

- 正式Ver.2の提供と実音による同期・音質・音量確認、または新規候補の採用判断。
- 2組の公開用公式画像の提供・登録、またはIMAGE PENDING継続可否の判断。
- iPhone Safari / Android Chrome実機で戻る・音声・低速回線・操作の確認。エミュレーションは実機確認ではありません。
- 既存4監査課題の別検討（固定スナップショットの件数、features数、旧予定配信状態、旧公開タイトル）。V3との差がない場合は改装の回帰として修正しません。
- 映像・音声候補を含むユーザーの最終レビュー。その後も公開には別の明示許可が必要です。
