# SUZUKA OFFICIAL SYNC — 2026-10-12 / 10-13再確認

最終確認基準: 2026-10-13T20:13:57+09:00（Asia/Tokyo）。出典ごとのUTC/JST確認時刻は [JSON記録](official-sync-20261012.json) に保存。ブランチ `project-a/official-sync-20261012`、起点 `386d6b0`、正本 `assets/data/creator-cms.json`。

公開情報で確認できた変更のみ反映。作品数82→89、公表済みの配信予定2件。12アーティストと既存82作品の作品ID・作品名・主公開日・主動画URL・歌詞・正式画像を保持。既存6作品の副次配信フィールドだけを、出典付きの承認差分として記録した。

## サービス確認結果

| サービス | 確認結果 | 未確認・制約 |
|---|---|---|
| YouTube / Shorts | 公式4チャンネルの同一性、対象77本のwatchメタデータを10/13再取得。73既掲載候補は前回と同一。前回プレミア待ち2本が実際に公開済みへ変化。50Shortsを追加。 | LOGIN_REQUIREDの1Shortsは追加しない。チャンネル継続ページの全件網羅は未確認。 |
| TuneCore Japan公開アーティスト / LinkCore | 正本の既存20リンクと公式アーティストページから得た新12リンク、計32作品を再確認。実在するApple Music / Spotifyの公式redirect53件がHTTP 200。 | ストア未記載を配信停止・未配信と推定しない。地域別再生・契約期間・全ストア継続配信は未確認。 |
| TuneCore管理画面 | 前回Safariの正規セッションはログインへ転送しhCAPTCHA表示。 | 認証情報取得・入力・CAPTCHA操作は未実施。非公開管理状態は未確認のまま。 |
| Instagram | 正本の `suzuka12090511` の公開プロフィールはHTTP 200、SUZUKA MUSIC確認。 | 投稿本文と投稿日一覧は取得できず、最新告知は未確認。既存導線を保持。 |
| note | 正本 `1209bellflower` の公開18記事を再確認。10/12調査後の新規記事はなし。新しい6記事へのNEWS導線を追加。 | 本文転載や推測による記事要約なし。 |

## チャンネル同一性

| アーティスト | 公式handle / チャンネルID |
|---|---|
| SUZUKA | [@suzuka1209](https://www.youtube.com/@suzuka1209) / `UCVde75yhByGQMu3SkO-fzrA` |
| 榎本魅愛 | [@enomotomia](https://www.youtube.com/@enomotomia) / `UCRwW7smDoEB-UOHMQJJ1Jyg` |
| 神代煌牙 | [@KOGAKAMISHIRO](https://www.youtube.com/@KOGAKAMISHIRO) / `UCtRwFzemyx508t7yXnpCVKA` |
| 妃みちる | [@michirukisaki](https://www.youtube.com/@michirukisaki) / `UCDqoQCLOp0lWb1bZ6vWEM3g` |

`@KOGAKAMISHIRO` は神代煌牙。妃みちると混同していない。アーティスト設定は変更していない。

## 新規登録7作品

| 作品 | アーティスト | 公開根拠・日付 | 配信状態 |
|---|---|---|---|
| [未完成の革命](https://www.youtube.com/watch?v=ee787y2wjNs) | RE:VIVE | 2026-10-12T20:00:07+09:00 | 未確認 |
| [午前0時のシンデレラ](https://www.youtube.com/watch?v=blXPDEriTyE) | ASTERIA | 2026-09-01T21:25:40+09:00 | 未確認 |
| [一護一逢〜再開の約束〜](https://www.youtube.com/watch?v=-ru6EtMyKAk) | 神代煌牙 | 2026-10-10T20:40:36+09:00 | published / 2026-10-13 |
| [ゆっくり休んで](https://linkco.re/28YfhcNX?lang=ja) | 妃みちる | 2026-10-11 | published / 2026-10-11 |
| [誰かのために](https://linkco.re/V5tf40p0?lang=ja) | 妃みちる | 2026-10-12 | published / 2026-10-12 |
| [恋の途中](https://linkco.re/fTcQ4px9?lang=ja) | 榎本魅愛 | 2026-10-05 | published / 2026-10-05 |
| [雨のち貴方](https://www.youtube.com/watch?v=LMg--k5FbrU) | 妃みちる | 2026-10-13T20:00:09+09:00 | upcoming / 2026-10-14 |

「一護一逢〜再開の約束〜」は公式YouTube原表記を保持。配信ページでは「一護一逢 (〜再開の約束〜)」だが、既存作品名へ推測修正していない。「恋の途中」は公式LinkCoreに6曲が掲載されたアルバムとして独立登録。「雨のち貴方」は10/13 20:00:09 JST、398秒、playability=OK / isUnlisted=false / 妃みちるのチャンネルID一致を実測し、YouTube公開済み作品として登録。配信日は10/14予定のまま分離している。ストリーミングだけの3作品の公開日は日精度で記録し、時刻を推測していない。

## 既存作品の副次配信情報

| 作品 | 状態・配信日 | 公式出典 |
|---|---|---|
| Without Worrying | published / 2026-10-05 | [LinkCore](https://linkco.re/F1979f3c?lang=ja) |
| Without worrying - Reimagined - | published / 2026-10-05 | [LinkCore](https://linkco.re/ef1DD6B3?lang=ja) |
| あなたを想う、それだけで | published / 2026-10-10 | [LinkCore](https://linkco.re/MDZzMupn?lang=ja) |
| 神様は留守 | published / 2026-10-10 | [LinkCore](https://linkco.re/VNy0eVS4?lang=ja) |
| 天照 | upcoming / 2026-10-17 | [LinkCore](https://linkco.re/uh3MSXtm?lang=ja) |
| 魔法が解けても ― Pumpkin Carriage ― | published / 2026-10-03 | [LinkCore](https://linkco.re/tSpMyUFE?lang=ja) |

一護一逢の配信情報は新規作品内へ登録。新規ゆっくり休んで・誰かのために・一護一逢はApple Musicリンクを確認し、未掲載Spotifyを推定追加していない。

## 公表済みの配信予定2作品

| 作品 | アーティスト | 予定日（JST・日精度） | 公式出典 |
|---|---|---|---|
| 天上天下唯我独尊 | 榎本魅愛 | 2026-10-15 | [LinkCore](https://linkco.re/9U1eCaGv?lang=ja) |
| 私の選んだ道 (あなたに届けたい8つの歌) | 妃みちる | 2026-10-14 | [LinkCore](https://linkco.re/Rq5BFPrU?lang=ja) |

未公開音源リンクや作り話の時刻・カウントダウンは作らない。予定ページはnoindex、配信時刻未確認を明示。予定日の到来だけで公開済みに変更しない。既存公開作品「天照」の配信予定10/17は副次配信フィールドに分離する。

## 追加した21動画バージョン

主動画URLと主公開日を保持し `videoVersions` へ追加。作品を重複登録していない。確認済みVideoObjectのみ生成。

| 既存作品 | 区分 | 動画公開日時（JST） | 出典 |
|---|---|---|---|
| 百万告 | 撮影映像 / 1番 | 2026-07-28T20:00:09+09:00 | [公式動画](https://www.youtube.com/watch?v=tFQPag-rSno) |
| 花言葉 | ORIGINAL VERSION | 2026-10-09T20:00:09+09:00 | [公式動画](https://www.youtube.com/watch?v=0xNqwMg_i5E) |
| もしも明日、はじめましてになっても | OFFICIAL LYRIC VIDEO | 2026-10-07T20:00:13+09:00 | [公式動画](https://www.youtube.com/watch?v=Mr3qtg9d1S0) |
| SMILE AND SAY GOODBYE ― 大好きだから、笑ってさようなら。― | OFFICIAL MV | 2026-10-06T20:00:19+09:00 | [公式動画](https://www.youtube.com/watch?v=8ZGpEiIo4sU) |
| また、君に恋をする。 | OFFICIAL VIDEO | 2026-10-04T20:00:19+09:00 | [公式動画](https://www.youtube.com/watch?v=PvX4zU7CpdE) |
| 夢と、介護と、私たち。 | OFFICIAL MV | 2026-10-03T20:31:04+09:00 | [公式動画](https://www.youtube.com/watch?v=UgA5YsSgN70) |
| 天照 | OFFICIAL AUDIO | 2026-10-03T19:00:06+09:00 | [公式動画](https://www.youtube.com/watch?v=A7c2GmZH7sw) |
| Without Worrying | OFFICIAL VIDEO | 2026-10-03T09:16:55+09:00 | [公式動画](https://www.youtube.com/watch?v=MlbqKSCi4U8) |
| 君は負けない | OFFICIAL VIDEO | 2026-10-02T20:00:02+09:00 | [公式動画](https://www.youtube.com/watch?v=TeZOrOs1Qnw) |
| 明日は、きっと。 | OFFICIAL VIDEO | 2026-09-24T22:29:30+09:00 | [公式動画](https://www.youtube.com/watch?v=P8nDdk8A85E) |
| Hello Hello Halloween | OFFICIAL AUDIO | 2026-09-13T20:00:06+09:00 | [公式動画](https://www.youtube.com/watch?v=vw1bP_5kZuM) |
| 花言葉 | OFFICIAL MV | 2026-09-12T20:40:39+09:00 | [公式動画](https://www.youtube.com/watch?v=rZhp5O3YTw8) |
| Echoes of You | OFFICIAL MV | 2026-10-09T20:00:16+09:00 | [公式動画](https://www.youtube.com/watch?v=v1rY03gArRk) |
| My Queen, My Oath | OFFICIAL MV | 2026-10-08T20:00:17+09:00 | [公式動画](https://www.youtube.com/watch?v=FUwxYpxVRcM) |
| 忘却の生き物 | OFFICIAL MV | 2026-10-07T20:00:13+09:00 | [公式動画](https://www.youtube.com/watch?v=sGG9Slgp7Rc) |
| One More Kiss | OFFICIAL VIDEO | 2026-10-06T20:00:35+09:00 | [公式動画](https://www.youtube.com/watch?v=Q9eeq3EMUYE) |
| マーメイドの下僕 | OFFICIAL VIDEO | 2026-10-05T20:00:29+09:00 | [公式動画](https://www.youtube.com/watch?v=wH6aAAxPqw4) |
| 悪役でいい | OFFICIAL MV | 2026-10-04T20:00:23+09:00 | [公式動画](https://www.youtube.com/watch?v=xNc2PSfp4aM) |
| 魔法が解けても ― Pumpkin Carriage ― | OFFICIAL MV | 2026-10-03T20:00:23+09:00 | [公式動画](https://www.youtube.com/watch?v=xGORQvmcZJ4) |
| たった1人の君へ | OFFICIAL VIDEO | 2026-10-06T20:00:19+09:00 | [公式動画](https://www.youtube.com/watch?v=DPUQyibGcbA) |
| はじめまして、奇跡 | OFFICIAL VIDEO | 2026-10-13T20:00:08+09:00 | [公式動画](https://www.youtube.com/watch?v=nplXdPAD9QU) |

「はじめまして、奇跡」の新動画は10/13 20:00:08 JST / 211秒の実公開を確認し、既存作品の21件目の追加動画として扱う。前回のプレミア待ち情報は過去の確認履歴であり、今回の公開判定を置き換えない。

## noteの6新規導線

| 記事 | 公開日時（JST） |
|---|---|
| [【本日20:00解禁】RE:VIVE『未完成の革命』――未完成のままでいい。何度でも、立ち上がれ。](https://note.com/1209bellflower/n/n3c62926d29e0) | 2026-10-12T15:52:18+09:00 |
| [SUZUKAと3人のアーティスト、それぞれの世界をもっと深く。](https://note.com/1209bellflower/n/nd4ccc92d086c) | 2026-10-03T16:49:06+09:00 |
| [榎本魅愛、新曲『天照 -アマテラス-』10月3日19:00 音源先行公開](https://note.com/1209bellflower/n/n00f345878afe) | 2026-10-03T13:39:51+09:00 |
| [「Without worrying」が、新しく生まれ変わりました。](https://note.com/1209bellflower/n/n2e08265c5c5b) | 2026-10-02T22:40:34+09:00 |
| [「あなたはひとりじゃない」——榎本魅愛『Without worrying』](https://note.com/1209bellflower/n/n3e1b02345551) | 2026-10-02T22:36:43+09:00 |
| [🚫忘れたい恋ほど、心は規制無視。榎本魅愛「恋禁区。」FULL MV解禁](https://note.com/1209bellflower/n/n561715644520) | 2026-10-01T00:59:00+09:00 |

## 正式画像と未確認事項

- 追加7画像は、公開LinkCoreに実表示されたジャケットを元のPNGバイトのまま取得。10/13再取得のSHA-256と既存7ファイルがすべて一致。400×400の公開画像を拡大・加工・生成していない。出典ページ・元画像パス・寸法・SHA-256をJSONに記録。
- 一護一逢は確認済み公開ジャケットへ更新。未完成の革命・午前0時のシンデレラは正式ジャケット未確認を保持し、公式YouTubeサムネイルとして明示。
- 既存の正式画像、歌詞、クレジットは保持。新規作品の歌詞を外部から推測転載しない。
- 「ウチら最強じゃね！」は予定日だけで配信済みと認定せず、直接一致する公開配信作品の確認待ち。
- [MIA MATES Shorts](https://www.youtube.com/shorts/roImlU6PSpA) は10/13もLOGIN_REQUIRED。未認証で追加しない。
- Instagramの最新告知、TuneCoreの非公開管理状態、地域別再生は未確認。

## 検証と公開ゲート

- 変更前生成差分0。新規差分の生成は削除0を確認して適用。
- `audit_official_sync_20261012.py` は12アーティスト・既存82作品の原情報保持、許可された副次配信6フィールドだけの変更、ソースの公開状態・チャンネル・日付・タイトル・原画像SHA・未来予定と公開済みの分離を監査する。
- 新50Shortsと21動画の構造化データは公式公開日時証拠を登録して生成。監査を弱めて不明なVideoObjectを公開していない。
- 「夢と、介護と、私たち。」の正式作品名と歌詞を保持。公式動画原題の「わたしたち」だけを一致するカード・Shorts検索文書・VideoObject.nameに限定して扱い、それ以外の本文・作品名・歌詞誤記は引き続き失敗する。
- 既存失敗2件は9/24固定件数監査 `audit_20260924_sync.py` と9/24固定配信状態 `audit_linkcore_releases.py`。`audit_homepage_upgrade.py` は10/2時点の「魔法が解けても」配信予定状態を要求する固定前提であり、日付だけ進めた隔離原本でも同一失敗が再現する。期待値を書き換えず最新公開ソース専用監査と区別する。
- 最終再生成0差分・同期監査・既存Pages CI・Chrome/WebKit・リンク検証・公開結果は親担当の最終QAで確定。結果未確認の段階で公開済みと報告しない。
- V6はこのAコミットの正本を安全に取り込み、デザイン開発ブランチで生成する。V6の本番公開は行わない。

## 運用

正本の確認済みフィールドだけを修正し、`scripts/build_changed_content.py --root . --dry-run` →削除0確認→適用→再度dry-run→ `scripts/audit_sync.py --root .` の順に検証する。歌詞や正式画像を置き換える前に正式素材の出典を確認する。動画の公開とストリーミング開始を別々に記録し、配信開始日は公式確認が取れてから状態を更新する。
