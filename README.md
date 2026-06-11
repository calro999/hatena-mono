# はてなブログ・アマゾン商品レビュー自動投稿システム

GitHub Actionsを利用して、Amazonで人気・注ements（タイムセールや売れ筋など）の商品情報を自動で取得し、軽量AIモデルによる高品質なレビュー記事とアイキャッチ画像を生成、はてなブログへ直接自動投稿（AtomPub/Fotolife APIを使用）するプロジェクトです。

## システム構成・仕組み

1. **商品情報取得**: Amazon PA-API v5 を使用して、指定されたキーワードに関連する売れ筋・タイムセール商品情報を取得。
2. **アイキャッチ画像生成**: `Ondy/tiny-sd` (超軽量Stable Diffusionモデル) を使用し、商品タイトルに応じたアイキャッチ画像を生成。
3. **はてなフォトライフへのアップロード**: 生成された画像を「はてなフォトライフAPI」経由でアップロードし、画像URLを取得。
4. **レビュー記事生成**: `Qwen/Qwen2.5-1.5B-Instruct` (軽量・高性能日本語LLM) を使用し、HTML形式の高品質レビュー記事を生成（先頭にアップロードされた画像タグを挿入）。
5. **はてなブログ自動投稿**: 「はてなブログ AtomPub API」を使用して、記事を自動的にブログへ投稿。

> [!NOTE]
> GitHub ActionsのCPUリソース制限に配慮し、モデルは自動的にキャッシュされる設定になっています。また、APIのアクセス制限や一時的な環境エラーが発生した場合は、Pillowによる美しいグラデーションバナーと、高品質な記事テンプレートによる自動フォールバックが機能するため、途中でスクリプトがクラッシュして投稿が途絶えることはありません。

## ディレクトリ構成

- `amazon_hatena_poster.py`: 全プロセスを統括するメインスクリプト
- `amazon_api.py`: Amazon PA-APIの署名および商品取得ロジック
- `article_generator.py`: LLMによる日本語レビュー記事生成ロジック
- `image_generator.py`: Stable DiffusionおよびPillowによる画像生成ロジック
- `hatena_api.py`: はてなブログ（AtomPub / フォトライフ）へのAPI連携ロジック
- `.github/workflows/auto_post.yml`: GitHub Actionsで毎日定期実行するワークフロー定義

## セットアップ手順

### 1. GitHub Secrets（アクションシークレット）の設定

リポジトリの `Settings` > `Secrets and variables` > `Actions` に移動し、以下のシークレットを登録してください。

| シークレット名 | 説明 | 例 / 取得方法 |
| :--- | :--- | :--- |
| `AMAZON_ACCESS_KEY` | Amazon PA-APIアクセスキー | アソシエイト開発者画面から取得 |
| `AMAZON_SECRET_KEY` | Amazon PA-APIシークレットキー | アソシエイト開発者画面から取得 |
| `AMAZON_ASSOCIATE_TAG` | AmazonアソシエイトID | `mattan0290c-22` (初期設定済み) |
| `HATENA_ID` | はてなのログインID | はてなブログ右上などに表示されているID |
| `HATENA_BLOG_ID` | あなたのブログURL（ドメイン） | `sample.hatenablog.com` など |
| `HATENA_API_KEY` | はてなブログのAPIキー | 管理画面の「設定」>「詳細設定」の最下部に記載されているAPIキー |

### 2. ローカルでの動作検証（ドライラン）

シークレットを設定せずにローカルで実行すると、自動的に「ドライランモード（ダミーデータ＆モックモデル）」で動作し、ファイルの生成結果をコンソールに出力します。

```bash
# 依存関係のインストール
pip install -r requirements.txt

# テスト実行
python amazon_hatena_poster.py
```
実行後、カレントディレクトリに `eyecatch.png` が生成され、はてなブログに投稿される予定の記事本文がログに表示されます。
