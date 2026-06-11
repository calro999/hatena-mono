# はてなブログ・アマゾン商品レビュー自動投稿システム

GitHub Actionsを利用して、Amazonで人気・注目の商品を自動で取得し、軽量AIモデルによるレビュー記事と画像生成（アイキャッチ）を組み合わせた高品質な記事を生成し、はてなブログへ自動投稿（メール投稿機能を使用）するプロジェクトです。

## システム構成・仕組み

1. **商品情報取得**: Amazon PA-API v5 を使用して、指定されたキーワードに関連する売れ筋・タイムセール商品情報を取得。
2. **アイキャッチ画像生成**: `Ondy/tiny-sd` (超軽量Stable Diffusionモデル) を使用し、商品タイトルに応じたアイキャッチ画像を生成。
3. **レビュー記事生成**: `Qwen/Qwen2.5-1.5B-Instruct` (軽量・高性能日本語LLM) を使用し、HTML形式の高品質レビュー記事を生成。
4. **はてなブログ自動投稿**: 生成したHTML記事と画像を添付し、はてなブログの「メール投稿用アドレス」宛にSMTP送信。

> [!NOTE]
> GitHub ActionsのCPUリソース制限に配慮し、モデルは自動的にキャッシュされる設定になっています。また、APIのアクセス制限や一時的な環境エラーが発生した場合は、Pillowによる美しいグラデーションバナーと、高品質な記事テンプレートによる自動フォールバックが機能するため、途中でスクリプトがクラッシュして投稿が途絶えることはありません。

## ディレクトリ構成

- `amazon_hatena_poster.py`: 全プロセスを統括するメインスクリプト
- `amazon_api.py`: Amazon PA-APIの署名および商品取得ロジック
- `article_generator.py`: LLMによる日本語レビュー記事生成ロジック
- `image_generator.py`: Stable DiffusionおよびPillowによる画像生成ロジック
- `email_poster.py`: はてなブログへのメール送信処理
- `.github/workflows/auto_post.yml`: GitHub Actionsで毎日定期実行するワークフロー定義

## セットアップ手順

### 1. GitHub Secrets（アクションシークレット）の設定

リポジトリの `Settings` > `Secrets and variables` > `Actions` に移動し、以下のシークレットを登録してください。

| シークレット名 | 説明 | 例 |
| :--- | :--- | :--- |
| `AMAZON_ACCESS_KEY` | Amazon PA-APIアクセスキー | `AKIAIOSFODNN7EXAMPLE` |
| `AMAZON_SECRET_KEY` | Amazon PA-APIシークレットキー | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AMAZON_ASSOCIATE_TAG` | あなたのAmazonアソシエイトID | `yourtag-22` |
| `SMTP_HOST` | 送信用SMTPサーバーのホスト | `smtp.gmail.com` など |
| `SMTP_PORT` | 送信用SMTPポート | `465` (SSL) または `587` (STARTTLS) |
| `SMTP_USER` | 送信用メールアドレス（Gmail等） | `your-email@gmail.com` |
| `SMTP_PASS` | 送信用メールのアプリパスワード | `abcd efgh ijkl mnop` (Gmailのアプリパスワード等) |
| `HATENA_BLOG_EMAIL` | はてなブログのメール投稿用アドレス | `xxxxxx@b.hatena.ne.jp` |

### 2. ローカルでの動作検証（ドライラン）

シークレットを設定せずにローカルで実行すると、自動的に「ドライランモード（ダミーデータ＆モックモデル）」で動作し、ファイルの生成結果をコンソールに出力します。

```bash
# 依存関係のインストール
pip install -r requirements.txt

# テスト実行
python amazon_hatena_poster.py
```
実行後、カレントディレクトリに `eyecatch.png` が生成され、はてなブログに投稿される予定の記事本文がログに表示されます。
