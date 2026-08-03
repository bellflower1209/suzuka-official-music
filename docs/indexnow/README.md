# IndexNow運用記録

SUZUKA公式サイトでは、GitHub Pagesのデプロイ成功後に、直前の成功デプロイと現在の`sitemap.xml`・公開HTMLのSHA-256を比較します。追加・更新・削除されたindex可能URLがある場合だけ、`https://api.indexnow.org/indexnow`へPOSTします。

## 自動送信

`.github/workflows/indexnow.yml`がmainへのpushで起動します。

1. 対象コミットのGitHub Pages deploymentが`succeed`になるまで待機
2. 直前の成功Pages deployment SHAを取得
3. 同一コミットの送信済みcacheを確認
4. `scripts/submit_indexnow.py --submit`を実行
5. `result.json`と`submission-log.json`を90日間artifactへ保存

IndexNow処理が失敗しても、先に完了したGitHub Pages公開は取り消しません。失敗は独立したActions結果として確認します。

## ログ

`submission-log.json`の各記録には、送信日時、コミット、比較元、URL数、対象URL、変更理由、keyLocation、HTTPステータス、応答とエラーを保存します。自動実行の最新版はGitHub Actionsの`indexnow-{commit SHA}` artifactが正本です。

## 手動実行

```bash
python3 scripts/submit_indexnow.py --dry-run
python3 scripts/submit_indexnow.py --submit
python3 scripts/submit_indexnow.py --urls URL1 URL2
```

`--urls`だけを指定した場合はdry-runです。明示URLを実送信する場合は`--submit --urls URL1 URL2`を使用します。

## 応答判定

- 200：送信成功
- 202：受付済み・キー検証待ち
- 400：形式不正
- 403：キー検証失敗
- 422：ホスト・URL・キー不一致
- 429：送信過多

200または202以外は成功として扱いません。IndexNow通知はインデックス登録を保証しません。
