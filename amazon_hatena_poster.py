from external_links import find_best_external_link, generate_external_link_html
import os
if os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ.setdefault(k, v)
import sys
import time
import random
from typing import Set, Dict, Any, Optional
from rakuten_api import RakutenAPI
from yahoo_api import YahooShoppingAPI
from toggle_mode import get_next_platform, save_current_platform
from article_generator import ArticleGenerator
from image_generator import ImageGenerator
from hatena_api import HatenaAPI
from bluesky_api import BlueskyAPI

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

def post_single_article(
    post_index: int,
    total_posts: int,
    posted_cache: Set[str],
    hatena_client: HatenaAPI,
    article_gen: ArticleGenerator,
    img_gen: ImageGenerator,
    rakuten_client: RakutenAPI,
    yahoo_client: Optional[YahooShoppingAPI],
    search_keywords: str,
    forced_platform: str
) -> bool:
    print(f"\n==================================================")
    print(f"=== Starting Post Batch [{post_index}/{total_posts}] ===")
    print(f"==================================================")

    # 1. Determine platform
    platform = get_next_platform(forced_platform)
    print(f"Selected Platform for Post #{post_index}: {platform.upper()}")

    recent_titles = hatena_client.get_recent_titles()
    recent_titles_str = " ".join(recent_titles).lower()

    # 2. Fetch Item from Selected Platform
    target_item = None
    max_retries = 10

    if platform == "yahoo" and yahoo_client:
        print("--- Fetching items from Yahoo! Shopping API ---")
        for attempt in range(max_retries):
            current_keyword = search_keywords if (search_keywords and attempt == 0) else yahoo_client.generate_random_keyword()
            print(f"--- Attempt {attempt + 1}/{max_retries} (Yahoo Keyword: '{current_keyword}') ---")
            items = yahoo_client.search_items(query=current_keyword, hits=30)
            if not items:
                continue
            random.shuffle(items)
            for item in items:
                item_code = item.get("itemCode", "")
                clean_name = item.get("clean_title", "").lower()
                if item_code and item_code in posted_cache:
                    continue
                if clean_name and clean_name in recent_titles_str:
                    continue
                target_item = item
                break
            if target_item:
                break
    else:
        if platform == "yahoo" and not yahoo_client:
            print("YAHOO_CLIENT_ID not found. Falling back to Rakuten.")
            platform = "rakuten"
        print("--- Fetching items from Rakuten API ---")
        for attempt in range(max_retries):
            current_keyword = search_keywords if (search_keywords and attempt == 0) else rakuten_client.generate_random_keyword()
            print(f"--- Attempt {attempt + 1}/{max_retries} (Rakuten Keyword: '{current_keyword}') ---")
            items = rakuten_client.search_items(keyword=current_keyword, hits=30)
            if not items:
                continue
            random.shuffle(items)
            for item in items:
                item_code = item.get("itemCode", "")
                clean_name = item.get("clean_title", "").lower()
                if item_code and item_code in posted_cache:
                    continue
                if clean_name and clean_name in recent_titles_str:
                    continue
                target_item = item
                break
            if target_item:
                break

    if not target_item:
        print(f"Warning: Could not find any unique unposted items for Post #{post_index}.")
        return False
        
    print(f"Selected Item to Post: [{platform.upper()}] {target_item['clean_title']} ({target_item['price']}) - Code: {target_item.get('itemCode')}")

    # 3. Generate Eyecatch Image
    eyecatch_path = f"eyecatch_{post_index}.png"
    img_gen.generate_eyecatch(
        prompt=target_item['clean_title'], 
        output_path=eyecatch_path,
        image_url=target_item.get('image_url'),
        category=target_item.get('category')
    )

    # 4. Generate Review Article & Title using LLM
    clean_title = target_item.get("clean_title") or target_item["title"]
    gen_title, desc_html, body_html = article_gen.generate_review_article(target_item)
    title = gen_title
    print(f"Generated Article Title: {title}")

    # Determine image to insert
    uploaded_image_url = hatena_client.upload_image_to_fotolife(eyecatch_path)
    if not uploaded_image_url:
        print("Fotolife upload skipped/failed. Using product image URL directly.")
        uploaded_image_url = target_item.get('image_url') or img_gen._select_unsplash_image_url(clean_title, target_item.get('category'))

    affiliate_link = target_item.get("url", "")

    # Platform design & wording
    if platform == "yahoo":
        platform_name = "Yahoo!ショッピング"
        sub_badge = "Yahoo!ショッピング 公式・優良配送ストア"
        btn_gradient = "linear-gradient(135deg, #ff0033 0%, #ff334b 100%)"
        btn_shadow = "rgba(255,0,51,0.25)"
        notice_text = "※PayPayポイント還元率、現在のセール・クーポン情報、配送予定日は上記Yahoo!ショッピングリンク先からご確認いただけます。"
    else:
        platform_name = "楽天市場"
        sub_badge = "楽天市場 公式ショップ・優良店"
        btn_gradient = "linear-gradient(135deg, #bf0000 0%, #e60000 100%)"
        btn_shadow = "rgba(191,0,0,0.25)"
        notice_text = "※現在のセール状況、お買い物マラソン等の楽天ポイント倍率や即日配送状況は上記リンク先からご確認いただけます。"

    # Product image
    img_html = ""
    if uploaded_image_url:
        img_html = f'''
<div style="text-align: center; margin: 25px 0 20px 0;">
    <a href="{affiliate_link}" target="_blank" rel="noopener noreferrer" style="display: inline-block; text-decoration: none;">
        <img src="{uploaded_image_url}" alt="{clean_title}" style="width: 100%; max-width: 680px; height: auto; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.12); display: block; margin: 0 auto; transition: transform 0.2s ease;">
    </a>
    <p style="font-size: 11px; color: #999; margin-top: 8px;">（※画像クリックで{platform_name}の商品ページへ移動できます）</p>
</div>
'''

    # First CTA
    early_cta_html = ""
    if affiliate_link:
        early_cta_html = f'''
<div style="margin: 20px 0 35px 0; padding: 16px 20px; background: #fff8f8; border: 1px solid #ffd8d8; border-radius: 12px; text-align: center;">
    <p style="font-size: 13px; color: #bf0000; font-weight: bold; margin: 0 0 10px 0;">＼ セール情報・リアルタイム最安値をチェック ／</p>
    <a href="{affiliate_link}" target="_blank" rel="noopener noreferrer" style="display: inline-block; background: {btn_gradient}; color: #ffffff; padding: 13px 28px; font-size: 15px; font-weight: bold; text-decoration: none; border-radius: 25px; box-shadow: 0 4px 12px {btn_shadow};">
        {platform_name}で「{clean_title}」の価格・在庫を見る 🛒
    </a>
</div>
'''

    # Closing CTA
    closing_cta_html = ""
    if affiliate_link:
        closing_cta_html = f'''
<div style="margin: 45px 0 25px 0; padding: 26px 22px; background: #fdfbfb; border: 2px solid #f0e6e6; border-radius: 18px; text-align: center; box-shadow: 0 6px 18px rgba(0,0,0,0.04);">
    <span style="display: inline-block; background: #333333; color: #fff; font-size: 12px; font-weight: bold; padding: 4px 12px; border-radius: 20px; margin-bottom: 12px;">{sub_badge}</span>
    <div style="font-size: 18px; font-weight: bold; color: #222; margin-bottom: 8px; line-height: 1.4;">{clean_title}</div>
    <div style="font-size: 20px; font-weight: bold; color: #bf0000; margin-bottom: 18px;">{target_item.get('price', '')}</div>
    <a href="{affiliate_link}" target="_blank" rel="noopener noreferrer" style="display: inline-block; background: {btn_gradient}; color: #ffffff; padding: 16px 38px; font-size: 17px; font-weight: bold; text-decoration: none; border-radius: 35px; box-shadow: 0 6px 16px {btn_shadow}; text-align: center;">
        {platform_name}で詳細・ユーザー口コミを見る 🛒
    </a>
    <p style="font-size: 12px; color: #888; margin-top: 14px; margin-bottom: 0;">{notice_text}</p>
</div>
'''

    ext_target = find_best_external_link(target_item.get('title', ''), target_item.get('itemCaption', '') or target_item.get('caption', ''))
    ext_link_html = generate_external_link_html(ext_target)
    if ext_link_html:
        print(f"[EXTERNAL-LINK] Added affinity link to {ext_target['domain']}")
    article_content = f"{desc_html}\n{img_html}\n{early_cta_html}\n{body_html}\n{ext_link_html}\n{closing_cta_html}"

    # Post Entry
    published_entry_url = hatena_client.post_entry(
        title=title,
        html_content=article_content,
        is_draft=False
    )
    
    if published_entry_url:
        item_code = target_item.get("itemCode", "")
        if item_code:
            save_posted_cache(item_code)
            posted_cache.add(item_code)
            print(f"Saved {item_code} to {CACHE_FILE}")

        save_current_platform(platform)
        print(f"Rotated platform state: last was {platform}")

        # Post to Bluesky
        try:
            print("Preparing to post to Bluesky (@mikke-hobby.bsky.social)...")
            bsky = BlueskyAPI()
            bsky_text = bsky.generate_post_text(
                item=target_item,
                blog_url=published_entry_url,
                genre="gadget"
            )
            print(f"Generated Bluesky Post Text:\n---\n{bsky_text}\n---")
            bsky.post(bsky_text)
        except Exception as bsky_e:
            print(f"Warning: Failed to post to Bluesky: {bsky_e}")

        # Cleanup eyecatch
        if os.path.exists(eyecatch_path):
            try:
                os.remove(eyecatch_path)
            except Exception:
                pass

        print(f"=== Post #{post_index} Completed Successfully! ===")
        return True
    else:
        print(f"=== Post #{post_index} Failed at Posting Stage. ===")
        return False

def main():
    print("=== Starting Gadget Hatena Blog Auto Poster (Rakuten & Yahoo Hybrid) ===")
    
    # 1. Load Configurations from environment variables
    rakuten_app_id = os.environ.get("RAKUTEN_APP_ID", "")
    rakuten_access_key = os.environ.get("RAKUTEN_ACCESS_KEY", "")
    rakuten_affiliate_id = os.environ.get("RAKUTEN_AFFILIATE_ID", "")

    yahoo_client_id = os.environ.get("YAHOO_CLIENT_ID", "")
    yahoo_affiliate_id = os.environ.get("YAHOO_AFFILIATE_ID", "")
    
    hatena_id = os.environ.get("HATENA_ID", "")
    blog_id = os.environ.get("HATENA_BLOG_ID", "")
    api_key = os.environ.get("HATENA_API_KEY", "")

    search_keywords = os.environ.get("SEARCH_KEYWORDS", "").strip()
    forced_platform = os.environ.get("POST_PLATFORM", "").strip().lower()

    # Load posted cache
    posted_cache = load_posted_cache()
    print(f"Loaded {len(posted_cache)} items from {CACHE_FILE}.")

    if not api_key:
        print("Warning: HATENA_API_KEY is not set. Running in DRY-RUN/DEMO mode.")

    # Initialize Clients
    hatena_client = HatenaAPI(
        hatena_id=hatena_id,
        blog_id=blog_id,
        api_key=api_key
    )

    rakuten_client = RakutenAPI(
        app_id=rakuten_app_id,
        access_key=rakuten_access_key,
        affiliate_id=rakuten_affiliate_id
    )

    yahoo_client = None
    if yahoo_client_id:
        yahoo_client = YahooShoppingAPI(client_id=yahoo_client_id, affiliate_id=yahoo_affiliate_id)

    img_gen = ImageGenerator()
    article_gen = ArticleGenerator()
    article_gen.load_model()

    # 1回の実行で確実に2記事を連続投稿
    posts_per_run = int(os.environ.get("POSTS_PER_RUN", "2"))
    successful_posts = 0

    for idx in range(1, posts_per_run + 1):
        success = post_single_article(
            post_index=idx,
            total_posts=posts_per_run,
            posted_cache=posted_cache,
            hatena_client=hatena_client,
            article_gen=article_gen,
            img_gen=img_gen,
            rakuten_client=rakuten_client,
            yahoo_client=yahoo_client,
            search_keywords=search_keywords,
            forced_platform=forced_platform
        )
        if success:
            successful_posts += 1
        
        # 連続投稿時の安全なインターバル（15秒）
        if idx < posts_per_run:
            print(f"Waiting 15 seconds before next post...")
            time.sleep(15)

    print(f"\n=== Auto Post Process Completed: {successful_posts}/{posts_per_run} posts published successfully ===")
    if successful_posts == 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
