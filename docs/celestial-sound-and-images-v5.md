# V5 効果音UIと停止画像の復旧

2026-10-10。公開基準 a61e59d23dba3a31f7689934022cdf5fab499581。

## 効果音の運用

公開操作は「効果音 ON / OFF」。初期OFF、選択は suzuka.cg.sound に保存。
ゲインは0.24固定（上限0.24）。旧音量設定が保存されていても反映しない。
内部の短縮設定 suzuka.cg.short、reduced-motion、saveDataは維持。
正式 assets/audio/door-heavy-v2.wav は未登録。doorAudio=null、
doorAudioStatus=missing-formal-door-heavy-v2 を維持。
現在の候補は assets/audio/door-heavy-candidate-v4.wav。
candidateAudioStatus=new-candidate-not-adopted であり正式Ver.2の採用を意味しない。
読み込み・再生失敗時は無音遷移し、楽曲再生中は効果音を抑える。

## 公式画像とチャンネル

12組の正式プロフィールは登録済み。今回プロフィール・既存ジャケットの画素は変更していない。
「公式画像確認中」は停止した旧YouTubeサムネイルの代替表示（生成307ページ中85ページ・213箇所。旧補助HTMLを含む86ページ・225箇所）。
正本にある同じ作品の正式画像を復旧し、画像がなかった7作品には確認した公式動画のサムネイルを登録。
停止URLの履歴と旧MVリンクは保持。別作品の画像や人物は借用しない。
元画像が停止した告知・Shortsで同じ作品の画像がない場合は、紐付いたアーティストの登録済み公式画像を使用。altに「公式アーティスト画像（元の動画画像は配信停止）」と明記し、作品ジャケット・動画サムネイルの登録済み状態と混同しない。

公開チャンネルの表示名、externalId、ownerUrlsを2026-10-10に照合。

| アーティスト | 確認した公開チャンネル |
|---|---|
| 榎本魅愛 | https://www.youtube.com/channel/UCRwW7smDoEB-UOHMQJJ1Jyg / @enomotomia |
| 神代煌牙 | https://www.youtube.com/channel/UCtRwFzemyx508t7yXnpCVKA / @KOGAKAMISHIRO |
| 妃みちる | https://www.youtube.com/channel/UCDqoQCLOp0lWb1bZ6vWEM3g / @michirukisaki |

妃みちるとして指定された @KOGAKAMISHIRO は神代煌牙だった。
正本の妃みちるのチャンネルは本人名・IDとも一致したため、その正本を維持する。
YouTube Studio管理画面のログインや設定変更は行っていない。

7作品：UPdown、分かれた道、タイパなんて知らなかった、夏が終わるまで、そばにいて。、キャラメ〜ル、神様は留守、君にかかった魔法。
動画oEmbedの作品名、author_name、author_urlを公開チャンネルと照合。
「君にかかった魔法」は公式チャンネル内検索とoEmbedを照合し、画像のみ登録（既存MVリンクは保持）。
出典・元画像・寸法・SHA-256は assets/data/official-image-restorations.json。
元JPEGは images/official-originals/*-youtube.jpg、WebPは images/*-official-youtube.webp。
縦横比と全構図を維持し、人物の生成・加工を行っていない。

## 検証と残存事項

scripts/test_official_image_restoration.py は出典ID、両画像のSHA・寸法、正本との対応、
未知URLや実ファイルのない画像の登録拒否を検証する。
扉テストは初期OFF、保存、固定ゲイン、ミュート、失敗、NOX専用音響、短縮・reduced-motion・saveDataを検証する。
9月固定監査 audit_20260924_sync.py と audit_linkcore_releases.py の条件は変更しない。
正式Ver.2の提供とiPhone/Android実機確認は別途必要。Chrome・WebKitエミュレーションは実機確認ではない。
