# SUZUKA 最新化・環境整理 更新候補 2026-10-26

調査・未公開候補の準備を実施。mainマージ、本番公開、既存ファイル削除は未実施。

## 1. 現行バージョン

- 本番はCELESTIAL V6・12世界 + MUSIC PRODUCTION。main: `934a63b79a7bdda85f4839aa77d3576a2987ee0a`。
- 公開パッケージ784ファイル。登録12組・99作品・Shorts 92本・正本NEWS 81件。
- 作品数は登録数であり、全主動画の現時点の一般視聴を意味しない。

## 2. GitHub・本番・ローカルの差分

- GitHub保存public-releaseと本番はHTTP/SHAで784/784一致。Pages/Actions成功。現在Actions ZIPは再取得不可（一覧0）。
- 管理用mainはb355cf4のまま、origin/mainより2コミット古い。既存4環境のHEAD/statusは維持。
- 未マージPR 0、リモートブランチ9。古い2ブランチに各1独自コミットあり。削除・統合なし。
- 作業場所: `/Users/enomotojunichi/Developer/SUZUKA/worktrees/latest-audit-20261026` / `chore/official-latest-audit-20261026`。未コミット・未push・PRなし。
- Terminal作業は未コミット36件。今回と重なる5ファイルは別途内容比較が必要。

## 3. 更新情報

- ユーザーの追加指示によりBABA NOVAを登録。公式画像は未確認のため画像確認中表示。既存12世界・12保護音源を保持。
- 新規音源5曲、Shorts6本、公式note NEWS3件。「天照」の配信状態を一次情報でpublishedに修正。
- 候補の登録数: 13組・104作品・Shorts98本・正本NEWS84件。YouTube公開と10月31日配信予定は分離。

| アーティスト | 新規登録曲 | 公式公開日時 JST |
|---|---|---|
| 妃みちる | あなたはあなたでいい ～明るい未来へ～ | 2026-10-21T20:00:08+09:00 |
| 榎本魅愛 | あなただけに送るHappy Birthday | 2026-10-25T20:09:18+09:00 |
| BABA NOVA | サラダチキン婆 | 2026-10-18T20:00:06+09:00 |
| BABA NOVA | ばぁーれすく | 2026-10-20T20:00:07+09:00 |
| NOX | 幾千の夜を越えて | 2026-10-26T20:00:06+09:00 |

## 4. 品質と課題

- ローカル検証65項目PASS。Chrome/WebKit × 390/1440pxで未公開候補を確認。内部参照欠損0。
- 候補800ファイル、既存784保持・16追加・158変更・626バイト一致・削除0。既存画像/JS/CSS/制作依頼等の保護対象158件は全件一致。
- 候補sitemap369 URL。本番355 URL。世界設定と公開ランタイムに変更なし。
- Chrome/WebKitで135秒再生・1 Audio・同一仮想src・OFF後src除去を確認。WebKitは再生開始操作を要する場合あり。実音・iPhone実機・今回のネイティブSafariは未検証。
- 既存の主YouTube動画36件は一次応答が「非公開動画」。作品データは保持。登録済み別動画情報26件・配信情報13件があり、確認済み代替なしでURLを置換していない。
- BABA NOVAの公式プロフィール画像/専用世界、新曲の正式ジャケット/歌詞は確認待ち。妃みちるの10月27日配信候補は公開済みにせず保留。
- 新規セッションでは音声OFFでも認証challengeが1件発生する現行仕様を記録。保存済みOFFの閲覧は音源API 0件。

## 5. Mac容量

- 採取範囲: 145,476ファイル、論理39.643 GB、割当21.004 GB。完全なMac全体走査ではない。
- Developer/SUZUKA: 割当18.826 GB。うちTerminal `.p0-work` は17.293 GBで作業/復元資料として保護。
- Documents/SUZUKA公式サイト: 論理18.043 GB / 割当約0.012 GB。iCloudの見かけのサイズを削減見込みに加算しない。
- 未走査/タイムアウト等129件と探索拒否2件あり。APFSの実解放量は割当合計から確定できない。

## 6. 削除候補

- A: 正本・環境・Git作業コピー。B: 634のSHA一致グループはA/E保護を優先。D: 不要と確定したバックアップ0。
- C条件付き候補: キャッシュ581件8.62 MB + main一致QA展開物784件121.56 MB = 1,365ファイル / 130.17 MB。
- E: `.git`、公式素材、音源、未コミット、復元要否不明、確認不能。即削除可能と断定した容量0 GB。実削除0。
- 本調査の新規worktree/証跡/展開物も約0.819 GBある。採取量と一部重複するので二重加算しない。

## 7. 実施計画

1. ローカル候補と本報告をレビュー。既存Terminalと重なる5ファイルを個別比較する。
2. 非公開36主動画の既存別動画/配信先を個別検証し、代替がない物の表示方法を決める。
3. 許可された次工程で明示ファイル指定のcommit/PR。mainマージ・Pages公開は別途明示承認後のみ。
4. 公開後は実Actions成果物、本番ハッシュ、スマホ実機、Safari、実音を確認。
5. 容量削減は130.17 MBの条件付き候補から参照/復元/使用中確認をやり直し、承認パスだけ別工程で実施。

## 修正箇所と検証コマンド

正本: `assets/data/creator-cms.json`。動画日時: `assets/data/youtube-publish-dates.json`。今回の根拠: `docs/official-sync-20261026.json`。
生成: `scripts/build_official_sync_20261026.py`。BABA NOVAは`presentationStatus=catalog-only`で、未登録の13番目の世界を作らない。
過去の20261018監査は保存した99作品のスナップショットへ実行し、現行の全99作品保護と新規登録は20261026監査で別途検証する。旧検査を単に弱めてはいない。

```sh
git status --short --branch
/Users/enomotojunichi/Developer/SUZUKA/dev-environments/python312/venv/bin/python -B scripts/audit_official_sync_20261026.py
/Users/enomotojunichi/Developer/SUZUKA/dev-environments/python312/venv/bin/python -B scripts/build_changed_content.py --dry-run
/Users/enomotojunichi/Developer/SUZUKA/dev-environments/python312/venv/bin/python -B scripts/build_official_sync_20261026.py --check
/Users/enomotojunichi/Developer/SUZUKA/dev-environments/python312/venv/bin/python -B scripts/verify_public_release.py
```

候補artifactDigest: `c537edf7780acfef5025c33895dffde25c0a48d53f4ea3b773a4bebd3380ff4b`。
本番artifactDigest: `f04e74f41c742321aec555e06c990a05efa96ec9781529624755841f87956fa1`。

詳細明細はMacローカルの `/Users/enomotojunichi/Documents/Codex/2026-10-26/suzuka-modernization/reports/SUZUKA_最新化・環境整理_報告書_20261026.html` および隣接evidence/を参照。生のストレージ明細や取得HTMLは公開パッケージへ含めない。
