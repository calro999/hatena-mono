import os
import sys
from amazon_api import AmazonPAAPI
from article_generator import ArticleGenerator
from image_generator import ImageGenerator
from email_poster import HatenaEmailPoster

def main():
    print("=== Starting Amazon Hatena Blog Auto Poster ===")
    
    # 1. Load Configurations from environment variables
    # Amazon API settings
    amz_access_key = os.environ.get("AMAZON_ACCESS_KEY", "DUMMY_ACCESS_KEY")
    amz_secret_key = os.environ.get("AMAZON_SECRET_KEY", "DUMMY_SECRET_KEY")
    amz_associate_tag = os.environ.get("AMAZON_ASSOCIATE_TAG", "mattan0290c-22")
    amz_host = os.environ.get("AMAZON_HOST", "webservices.amazon.co.jp")
    amz_region = os.environ.get("AMAZON_REGION", "us-west-2")
    
    # SMTP Settings for Hatena Blog Post
    smtp_host = os.environ.get("SMTP_HOST", "")
    try:
        smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    except ValueError:
        smtp_port = 465
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    target_email = os.environ.get("HATENA_BLOG_EMAIL", "")

    # Content Settings
    search_keywords = os.environ.get("SEARCH_KEYWORDS", "最新ガジェット")
    
    # Check SMTP configuration
    if not smtp_host or not smtp_user or not smtp_pass or not target_email:
        print("Warning: SMTP configuration is incomplete. Running in DRY-RUN/DEMO mode.")
        dry_run = True
    else:
        dry_run = False

    # 2. Fetch Item from Amazon
    print(f"Fetching hot items from Amazon for keywords: '{search_keywords}'...")
    amazon_client = AmazonPAAPI(
        access_key=amz_access_key,
        secret_key=amz_secret_key,
        associate_tag=amz_associate_tag,
        host=amz_host,
        region=amz_region
    )
    
    items = amazon_client.search_items(keywords=search_keywords, item_count=3)
    if not items:
        print("Error: No items fetched from Amazon. Exiting.")
        sys.exit(1)
        
    print(f"Successfully fetched {len(items)} items. Selecting the top item for review.")
    target_item = items[0]
    print(f"Selected item: {target_item['title']} ({target_item['price']})")

    # 3. Generate Eyecatch Image
    print("Initializing Image Generator...")
    img_gen = ImageGenerator()
    img_gen.load_model()
    
    eyecatch_path = "eyecatch.png"
    img_gen.generate_eyecatch(prompt=target_item['title'], output_path=eyecatch_path)

    # 4. Generate Review Article
    print("Initializing LLM Article Generator...")
    article_gen = ArticleGenerator()
    article_gen.load_model()
    
    article_content = article_gen.generate_review_article(target_item)
    
    title = f"【話題の新商品】本当に買い？「{target_item['title']}」徹底レビュー・お得情報まとめ"

    # 5. Post to Hatena Blog
    print("Sending post via Email...")
    poster = HatenaEmailPoster(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_pass=smtp_pass,
        target_email=target_email
    )
    
    success = poster.send_post(
        title=title,
        html_content=article_content,
        image_path=eyecatch_path
    )
    
    if success:
        print("=== Auto Post Process Completed Successfully! ===")
    else:
        print("=== Auto Post Process Failed at Email Sending Stage. ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
