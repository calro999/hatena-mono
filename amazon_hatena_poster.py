import os
if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)
import sys
import random
from typing import Set
from rakuten_api import RakutenAPI, clean_product_title
from article_generator import ArticleGenerator
from image_generator import ImageGenerator
from hatena_api import HatenaAPI

CACHE_FILE = "posted_cache.txt"

def load_posted_cache() -> Set[str]:
    """過去に投稿した商品の itemCode / ID をキャッシュから読み込む"""
    if not os.path.exists(CACHE_FILE):
        return set()
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_posted_cache(item_code: str):
    """投稿した商品の itemCode をキャッシュに保存"""
    if not item_code:
        return
    with open(CACHE_FILE, "a", encoding="utf-8") as f:
        f.write(f"{item_code}\n")

def main():
    print("=== Starting Rakuten Gadget Hatena Blog Auto Poster ===")
    
    # 1. Load Configurations from environment variables
    # Rakuten API settings
    rakuten_app_id = os.environ.get("RAKUTEN_APP_ID", "")
    rakuten_access_key = os.environ.get("RAKUTEN_ACCESS_KEY", "")
    rakuten_affiliate_id = os.environ.get("RAKUTEN_AFFILIATE_ID", "")
    
    # Hatena API Settings
    hatena_id = os.environ.get("HATENA_ID", "")
    blog_id = os.environ.get("HATENA_BLOG_ID", "")
    api_key = os.environ.get("HATENA_API_KEY", "")

    # Content Settings
    search_keywords = os.environ.get("SEARCH_KEYWORDS", "").strip()

    # Load posted cache
    posted_cache = load_posted_cache()
    print(f"Loaded {len(posted_cache)} items from {CACHE_FILE}.")

    # Check Hatena API configuration
    if not api_key:
        print("Warning: HATENA_API_KEY is not set. Running in DRY-RUN/DEMO mode.")
        dry_run = True
    else:
        dry_run = False

    # Initialize Hatena API Client first to check recent entries for duplication
    print("Initializing Hatena API Client...")
    hatena_client = HatenaAPI(
        hatena_id=hatena_id,
        blog_id=blog_id,
        api_key=api_key
    )
    
    recent_titles = hatena_client.get_recent_titles()
    recent_titles_str = " ".join(recent_titles).lower()

    # 2. Fetch Items from Rakuten API with Retry for New Items
    rakuten_client = RakutenAPI(
        app_id=rakuten_app_id,
        access_key=rakuten_access_key,
        affiliate_id=rakuten_affiliate_id
    )

    target_item = None
    max_retries = 10
    
    for attempt in range(max_retries):
        if search_keywords and attempt == 0:
            current_keyword = search_keywords
        else:
            current_keyword = rakuten_client.generate_random_keyword()
            
        print(f"--- Attempt {attempt + 1}/{max_retries} (Keyword: '{current_keyword}') ---")
        items = rakuten_client.search_items(keyword=current_keyword, hits=30)
        
        if not items:
            print(f"No items found for keyword '{current_keyword}'. Trying next keyword...")
            continue

        # Shuffle items to avoid always picking the first item from top rankings
        random.shuffle(items)

        for item in items:
            item_code = item.get("itemCode", "")
            clean_name = item.get("clean_title", "").lower()
            
            # Check against local cache
            if item_code and item_code in posted_cache:
                continue
                
            # Check against Hatena recent blog post titles
            if clean_name and clean_name in recent_titles_str:
                continue

            target_item = item
            break
            
        if target_item:
            print(f"Found new unique item: {target_item['title']}")
            break

    if not target_item:
        print("Error: Could not find any unique unposted items after multiple attempts.")
        sys.exit(1)
        
    print(f"Selected Item to Post: {target_item['clean_title']} ({target_item['price']}) - Code: {target_item.get('itemCode')}")

    # 3. Generate Eyecatch Image
    print("Initializing Image Generator...")
    img_gen = ImageGenerator()
    
    eyecatch_path = "eyecatch.png"
    img_gen.generate_eyecatch(
        prompt=target_item['clean_title'], 
        output_path=eyecatch_path,
        image_url=target_item.get('image_url'),
        category=target_item.get('category')
    )

    # 4. Generate Review Article
    print("Initializing LLM Article Generator...")
    article_gen = ArticleGenerator()
    article_gen.load_model()
    
    article_content = article_gen.generate_review_article(target_item)
    
    clean_title = target_item.get("clean_title") or target_item["title"]
    title = f"【徹底レビュー】本当に買い？「{clean_title}」の実力を徹底検証！"

    # Determine image to insert
    uploaded_image_url = hatena_client.upload_image_to_fotolife(eyecatch_path)
    if not uploaded_image_url:
        print("Fotolife upload skipped/failed. Using product image URL directly.")
        uploaded_image_url = target_item.get('image_url') or img_gen._select_unsplash_image_url(clean_title, target_item.get('category'))

    # Insert image to the beginning of the article
    if uploaded_image_url:
        img_html = f'<div style="text-align: center; margin: 20px 0;"><img src="{uploaded_image_url}" alt="{target_item["clean_title"]}" style="max-width: 100%; height: auto; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.08);"></div>'
        article_content = img_html + article_content

    # Ensure Affiliate CTA button exists in the article
    if target_item.get("url"):
        cta_html = f"""
        <div style="text-align: center; margin: 40px 0 20px 0;">
            <a href="{target_item['url']}" target="_blank" rel="noopener noreferrer" style="display: inline-block; background: #BF0000; color: #fff; padding: 16px 32px; font-size: 18px; font-weight: bold; text-decoration: none; border-radius: 30px; box-shadow: 0 4px 15px rgba(191,0,0,0.3); text-align: center;">
                楽天市場で「{clean_title}」の詳細・クチコミを見る 🛒
            </a>
            <p style="font-size: 12px; color: #666; margin-top: 10px;">※現在の価格や在庫状況、実際のユーザー評価・ポイント還元は上記リンク先から確認できます。</p>
        </div>
        """
        article_content += cta_html

    # Post Entry
    success = hatena_client.post_entry(
        title=title,
        html_content=article_content,
        is_draft=False
    )
    
    if success:
        # Save to cache only when posting succeeds
        item_code = target_item.get("itemCode", "")
        if item_code:
            save_posted_cache(item_code)
            print(f"Saved {item_code} to {CACHE_FILE}")
        print("=== Auto Post Process Completed Successfully! ===")
    else:
        print("=== Auto Post Process Failed at Posting Stage. ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
