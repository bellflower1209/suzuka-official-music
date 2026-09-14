# Schedule / Upcoming 運用

- 正本は `assets/data/creator-cms.json`。公開作品は `releases`、日時確定の公開予定は `upcoming`、日付未確認の公開予定は `comingSoon`。
- `comingSoon` に日付・配信URL・画像を推測入力しない。正式日時が確認できたら同じslugのレコードを `upcoming` へ移し、`comingSoon` から除く。作品を重複登録しない。
- 公開済み作品の追加配信は既存レコードの `scheduledStreamingRelease` で管理。`releaseDate` / `publishedAt` / 動画公開日は維持する。
- 百万告は作品公開2026-07-12、ストリーミング配信2026-09-21。Artist・トップの9月枠は `miaReleaseSchedule.activities` の `STREAMING RELEASE` と `officialReleaseDate` で区別する。
- 週は月曜〜日曜、Asia/Tokyo。静的HTMLは正本更新日時のJST日付で再現可能に生成し、閲覧時は `assets/release-schedule.js` がJST当日に再分類する。30秒ごととタブ復帰時にも更新。公開予定時刻を過ぎても自動で公開済みにせず、Awaiting Confirmationへ移す。
- Upcoming詳細は既存仕様どおりnoindex。日付未確認作品にMusicRecording、VideoObject、カウントダウンは生成しない。サイト内Searchからは検索できる。
- 固定プレーヤーは `assets/main.js` が実寸を測り、`assets/player.css` でページ末尾のリンク用余白を確保する。

## 検証

リポジトリ直下で実行：

```sh
python3 scripts/build_changed_content.py
python3 scripts/build_changed_content.py
python3 scripts/audit_sync.py
python3 scripts/audit_postpublication_schedule.py
node scripts/test_schedule_date.cjs
```

2回目の生成はchangedCount/deletedCountとも0。GitHub Pagesでも東京・UTC・米国西海岸の実行環境で週境界テストを行う。ブラウザ監査は既存と同様、ローカルHTTP 8766・Chrome CDP 9223で `node scripts/browser_postpublication_qa.mjs`。390/768/1280px、検索、画像、JS、autoplay、ページ末尾と固定プレーヤー、JST日付境界を検証する。
