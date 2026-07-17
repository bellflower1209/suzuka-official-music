# SUZUKA 内部リンク監査レポート

監査日: 2026-07-17  
公開URL: https://bellflower1209.github.io/suzuka-official-music/

## 結果概要

- 検索対象ページ: 24ページ（修正前20ページ）
- sitemap.xml登録URL: 24 URL
- トップページから到達可能: 24 / 24ページ
- 内部リンク切れ: 0件
- 空リンク: 0件
- 孤立ページ: 0件
- 重複リリースカード: 0件
- 旧URL `suzuka-official-music.ria20210815.chatgpt.site`: 0件
- canonical不一致: 0件
- 空の画像alt: 0件
- 確認したYouTube URL: 18 URL、HTTPエラー0件

## 主な修正

1. `/releases/` を新設し、トップに掲載されている16作品を重複なく一覧化した。
2. `/news/` と、トップ掲載内容に対応する2件の記事ページを新設した。
3. トップのNewsカードを、プロフィール内アンカーではなく各News記事へ変更した。
4. 全検索対象ページに Home / Artists / Releases / News / YouTube の共通フッター導線を追加した。
5. ヘッダーの Releases / News を、トップ内アンカーから独立した一覧URLへ統一した。
6. 榎本魅愛プロフィールに、監査時点の公開済み楽曲すべての専用ページ導線に加えて公式MVへの直接リンクを追加した。
7. すべての楽曲詳細ページから、Home、プロフィール、Releases一覧、公式MV、関連曲3曲以上へ移動できる状態にした。
8. 関連曲が2件だった新曲2ページへ3件目の関連曲を追加した。
9. 空だったジャケット画像のaltを、楽曲名とアーティストが分かる文言へ修正した。
10. sitemap.xmlへ Releases一覧、News一覧、News記事2件を追加した。

## ページと導線

### トップページ

- Artists一覧、全アーティスト、Releases一覧、榎本魅愛を含む全14楽曲詳細、News一覧、News記事2件へ到達可能。
- YouTubeチャンネルと公開MVへの外部リンクを確認済み。

### 榎本魅愛プロフィール

- 楽曲台帳で公開済みと確認した楽曲すべての専用ページへリンク済み。
- 同楽曲の公式MVへ直接リンク済み。
- Home、Artists、Releases、News、YouTubeへ移動可能。

### 楽曲詳細

- 14ページを確認。
- 各ページにHome、アーティストプロフィール、Releases一覧、MV、パンくず、関連曲3曲以上を確認。
- 旧綴り `/releases/toriatsukai-chuui/` は検索対象外のnoindexリダイレクトとして維持し、正規URLへ転送する。

### Releases

- 16作品を掲載、重複0件。
- 専用ページが存在する14作品は詳細ページへリンク。
- 専用ページ未作成の `SHADOW//CODE` と `My Queen, My Oath` は、確定済みの公式MVまたはアーティスト内楽曲情報へリンク。

### News

- 一覧から2記事へ移動可能。
- 各記事から関連アーティストまたは関連楽曲、News一覧、トップへ戻れる。

## canonical / sitemap / robots

- 24ページすべてのcanonicalと実際の公開URLが一致。
- sitemap.xmlの24 URLと検索対象24ページが完全一致。
- robots.txtは通常クローラーをブロックせず、GitHub Pagesのサブディレクトリを許可し、絶対URLのsitemapを指定している。

```text
User-agent: *
Allow: /suzuka-official-music/

Sitemap: https://bellflower1209.github.io/suzuka-official-music/sitemap.xml
```

## 検証

- `python3 scripts/audit_seo.py`: 合格（24ページ、24 sitemap URL、24到達可能ページ、35 JSON-LDブロック）
- `python3 scripts/check_static_site.py`: 合格（内部URL 47件、404なし）
- `node scripts/browser_qa.mjs`: 合格
  - 390px: 24ページすべて
  - 768px / 1280px: トップ、プロフィール、Releases、News、楽曲詳細の主要テンプレート
  - 横スクロールなし
  - JavaScript例外、console error、HTTP 4xx/5xxなし
  - 固定ミュージックプレイヤーの存在とfixed配置を確認
- JavaScript構文: 合格
- Python構文: 合格
- JSON-LD構文: 合格

## 残課題

- `SHADOW//CODE` と `My Queen, My Oath` の専用リリースページは今回の内部リンク監査の範囲では新規作成していない。
- Newsの日付は確定した月日がないため、年表記のみを維持した。
- YouTube動画の説明欄更新やYouTube Studio上の設定変更は行っていない。

## SEO改善効果

- 一覧ページと共通ナビゲーションにより、検索エンジンがページ階層と作品群を理解しやすくなった。
- 孤立を防ぐ複数導線により、ユーザーが楽曲・プロフィール・News間を回遊しやすくなった。
- canonical、sitemap、内部リンク先が一致し、クロールの重複や分散を抑えられる構成になった。
- 固有のNews URLが生まれ、アーティスト情報とリリース情報を検索結果へ提示できる基盤が整った。
