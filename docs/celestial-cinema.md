# CELESTIAL GATE Cinema V2 — 素材・実装・運用

本番未公開のローカル改装です。正本は引き続き `assets/data/creator-cms.json`。既存のPython生成方式とGitHub Pages構成を維持し、HTMLに写真背景の表示層を生成します。人物・顔・衣装は生成していません。参考画像内の人物・名称・UIは転用していません。

## 制作・採用素材

built-in image_genで人物のいない装飾背景13点、物理扉のテクスチャ2点、透過建築フレーム2点を制作しました。全プロンプト、生成日、元ファイル名、元画像SHA-256、実寸、用途、派生ファイルのSHA-256は `assets/data/celestial-cinema-assets.json` に記録しています。

| 用途 | 素材ID | 内容 |
|---|---|---|
| ホーム・共通ページ | `hero` | 雲海、巨大な白大理石宮殿、柱、自然光、反射する床 |
| 朝霧しのぶ | `asagiri-shinobu` | 記憶・和の歌に合わせた白石庭園、紅葉、水面 |
| ASTERIA | `asteria` | 五つのアーチ、星空、真鍮の天球儀 |
| ECLYPSE | `eclypse` | 白石・ガラス・金属の近未来観測所 |
| 榎本魅愛 | `enomoto-mia` | 薔薇のテラス、夜明けの淡い光 |
| 神代煌牙 | `koga-kamishiro` | 白石と青灰色の聖堂、盾と剣 |
| 妃みちる | `michiru` | 花と本を置いた静かな温室 |
| NOX | `nox` | 黒曜石の城、深紅の月、濃霧、赤い反射 |
| RANGILI | `rangili` | 白石の透かし彫り、暖色の祝祭庭園 |
| RE:VIVE | `revive` | 雨上がりの白い円形劇場、新しい朝 |
| VEILFANG | `veilfang` | 月明かりと森の白石の神殿 |
| 鉄髭 - TETSUHIGE - | `tetsuhige` | 白石の天空工房、鉄床と道具 |
| LEON VAIL | `leon-vail` | 無人の白石劇場、青い幕、マイク |
| 天界の扉面 | `door-celestial` | 重い白大理石・真鍮・彫刻・外側の蝶番 |
| 魔界の扉面 | `door-infernal` | 黒曜石・黒鉄・外側の蝶番 |
| 天界の門構造 | `frame-celestial` | 白石の柱・アーチ、開口部と周囲が透過 |
| 魔界の門構造 | `frame-infernal` | 黒石の巨大な尖頭アーチ、開口部と周囲が透過 |

音楽性の根拠は既存のArtistのworld・プロフィール・作品です。背景は今回の美術設計であり、公式の人物設定を追記するものではありません。各背景は対応Artistのページと扉の奥に表示します。Artistページでは背景を最初に見せ、既存の配信・JOYSOUND告知は内容とリンクを保持したまま入口の後へ配置します。

保存先は `assets/cinema/`。背景はAVIF/WebP各768・1280・1600px、スマートフォン用縦構図約627×941px。生成元は1672×941px（妃みちるのみ高さ940px）、扉・フレームは1024×1536px。4K素材とは扱っていません。アップスケールせず、門の透過を保ちました。背景17点の派生と公式サムネイルを合わせて132ファイル、16,987,024 bytesです。閲覧時は該当サイズだけを読みます。

公式画像10組は元画像を残し、全構図を保持した比例縮小WebP480/960pxを `assets/cinema/official/` に追加しました。人物の切り抜き・顔の修正・衣装変更はありません。LEON VAILと鉄髭は正式画像がないためIMAGE PENDINGを維持します。

生成原本と制作記録はリポジトリ外の `/Users/enomotojunichi/Documents/SUZUKA公式サイト/CELESTIAL_CINEMA_QA/originals/`、`generation-sources.json` に保存しています。原本を今後も保管してください。通常ビルドは配布済みAVIF/WebPを使い、画像生成やPillowを必要としません。

## 使用条件と出典

生成画像はこの依頼で許可された装飾用途に使用しています。[OpenAI利用規約](https://openai.com/policies/terms-of-use/)が適用される生成物として出典を記録しました。他社ストック画像のライセンスや排他的権利は主張していません。公式画像の出典・権利は既存の正本を引き継ぎます。

## 扉とアクセス

WebGLを追加せず、写真の門構造とCSS 3Dを組み合わせました。左右の面を外側の蝶番位置から回転させ、厚み・陰影と緩急を付けて、固有の風景を露出します。NOXのみ黒曜石の扉と城に接続します。スキップ・Escape・キャンセル・戻る・短縮・キーボード操作・focus復帰・prefers-reduced-motionを維持しました。

正式 `door-heavy-v2.wav` は未取得で、扉は無音です。音声初期OFF・ユーザー操作による再生・500ms取得タイムアウト・楽曲再生時の抑制を保持しています。接続方法と原音SHAの登録手順は `docs/celestial-gate.md` を参照。モック検証は実音の品質・同期確認ではありません。

画像エラーがスクリプト実行前に発生したケースも検出し、AVIFからWebP、公式縮小画像から既存原画像へ再試行します。装飾が全て読めない場合も本文・リンク・スキップを維持します。JavaScript無効時は従来のArtist URLへ直接移動します。

## 変更する場所

| 変更内容 | 編集元 |
|---|---|
| 公式情報・画像・作品・MV・歌詞・配信状態 | `assets/data/creator-cms.json` |
| 背景の対応・領域・色・速度・正式音源 | `assets/data/celestial-gate.json` |
| 構図・余白・字体・門の3D・スマホ表示 | `assets/celestial-gate.css` |
| 開閉・音声・画像失敗・メニュー操作 | `assets/celestial-gate.js` |
| 全ページへの生成・picture・preload | `scripts/build_celestial_gate.py` |
| 素材の出典と派生ファイル | `assets/data/celestial-cinema-assets.json` |
| 素材準備用の任意ツール | `scripts/prepare_celestial_cinema_assets.py` |
| 新しい写真・門・公式原画像の整合性監査 | `scripts/audit_celestial_cinema.py` |

旧 `celestial-palace.svg` / `nox-citadel.svg` は保管のみでメイン背景には使用しません。小さな紋章のSVGは維持します。新しいArtistを追加する場合は正本・テーマ・同slugの背景素材とmanifestを整合させます。生成HTMLは直接編集しません。

```bash
cd '/Users/enomotojunichi/Documents/SUZUKA公式サイト/suzuka-celestial-gate'
python3 scripts/build_changed_content.py --root . --dry-run
python3 scripts/build_changed_content.py --root .
python3 scripts/build_changed_content.py --root . --dry-run
python3 scripts/audit_sync.py
python3 scripts/audit_celestial_gate.py
python3 scripts/audit_celestial_cinema.py
node --check assets/celestial-gate.js
```

2回目はchangedCount=0、deletedCount=0を確認します。番号付きのiCloud重複HTMLなど未追跡ファイルが混ざる場合は、そのファイルを触らず、Git管理ファイルと今回の素材だけを別のローカル検証コピーに移して生成します。今回の検証はこの方法で行い、`CELESTIAL_CINEMA_QA/validation-stage.json` と `generated-apply.json` に対象ファイルと削除0件を記録しています。

素材を再エンコードする場合だけ、AVIF対応Pillowを用意し、原本を指す制作記録を `--sources`、原本保管先を `--archive`、サイトを `--root` に指定します。通常ビルドでの再生成は不要です。

## 公開前の確認

- 正式Ver.2原音を受領し、登録後に実際の音質・音量・発光と開閉の同期を試聴する。
- iPhone Safari・Android Chrome実機で、縦横・戻る・短縮・全門・低速通信を確認する。WebKit検査は実機確認の代わりではない。
- LEON VAIL・鉄髭の正式画像、またはIMAGE PENDINGでの公開可否を判断する。
- 背景の実寸は最大1672px。大画面/高DPIでの追加素材制作が必要か最終レビューする。
- 既存4監査課題は今回修正しない。全61ローカル検査の結果と公開workflowの検証結果はリポジトリ外の最終報告に記載する。
- Core Web Vitalsは本番の利用者データで未検証。低速通信を模擬したローカル測定値は最終報告を参照する。
- 明示的な公開承認後のみ、対象コミットをレビューし、mainへの反映と既存Pages公開手順を実施する。今回はpush・merge・deploy・IndexNow送信を実施しない。

プレビューは親フォルダーで `python3 -m http.server 8818 --bind 127.0.0.1` を実行し、`http://127.0.0.1:8818/suzuka-celestial-gate/` を開きます。Windowsの具体例と停止方法は `docs/celestial-gate.md` を参照してください。
