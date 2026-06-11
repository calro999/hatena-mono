import os
import sys
from amazon_api import AmazonPAAPI
from article_generator import ArticleGenerator
from image_generator import ImageGenerator
from hatena_api import HatenaAPI

def main():
    print("=== Starting Amazon Hatena Blog Auto Poster ===")
    
    # 1. Load Configurations from environment variables
    # Amazon API settings
    amz_access_key = os.environ.get("AMAZON_ACCESS_KEY", "DUMMY_ACCESS_KEY")
    amz_secret_key = os.environ.get("AMAZON_SECRET_KEY", "DUMMY_SECRET_KEY")
    amz_associate_tag = os.environ.get("AMAZON_ASSOCIATE_TAG", "mattan0290c-22")
    amz_host = os.environ.get("AMAZON_HOST", "webservices.amazon.co.jp")
    amz_region = os.environ.get("AMAZON_REGION", "us-west-2")
    
    # Hatena API Settings
    hatena_id = os.environ.get("HATENA_ID", "DUMMY_ID")
    blog_id = os.environ.get("HATENA_BLOG_ID", "DUMMY_BLOG_ID")
    api_key = os.environ.get("HATENA_API_KEY", "")

    # Content Settings
    search_keywords = os.environ.get("SEARCH_KEYWORDS", "最新ガジェット")
    
    # Check Hatena API configuration
    if not api_key:
        print("Warning: HATENA_API_KEY is not set. Running in DRY-RUN/DEMO mode.")
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
    
    eyecatch_path = "eyecatch.png"
    img_gen.generate_eyecatch(
        prompt=target_item['title'], 
        output_path=eyecatch_path,
        image_url=target_item.get('image_url')
    )

    # 4. Generate Review Article
    print("Initializing LLM Article Generator...")
    article_gen = ArticleGenerator()
    article_gen.load_model()
    
    article_content = article_gen.generate_review_article(target_item)
    
    clean_title = target_item.get("clean_title") or target_item["title"]
    title = f"【徹底レビュー】本当に買い？「{clean_title}」の実力を徹底検証！"

    # 5. Post to Hatena Blog via API
    print("Initializing Hatena API Client...")
    hatena_client = HatenaAPI(
        hatena_id=hatena_id,
        blog_id=blog_id,
        api_key=api_key
    )

    # Upload eyecatch to Fotolife first
    uploaded_image_url = hatena_client.upload_image_to_fotolife(eyecatch_path)
    if uploaded_image_url:
        print("Inserting uploaded image to the beginning of the article.")
        img_html = f'<div style="text-align: center; margin: 20px 0;"><img src="{uploaded_image_url}" alt="{target_item["title"]}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"></div>'
        article_content = img_html + article_content
    elif target_item.get("image_url"):
        print("Fotolife upload failed or skipped. Inserting Amazon official product image instead.")
        img_html = f'<div style="text-align: center; margin: 20px 0;"><img src="{target_item["image_url"]}" alt="{target_item["title"]}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"></div>'
        article_content = img_html + article_content

    # Post Entry
    success = hatena_client.post_entry(
        title=title,
        html_content=article_content,
        is_draft=False
    )
    
    if success:
        print("=== Auto Post Process Completed Successfully! ===")
    else:
        print("=== Auto Post Process Failed at Posting Stage. ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
