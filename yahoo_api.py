import os
import re
import random
import requests
from typing import List, Dict, Any, Optional

def clean_yahoo_product_title(title: str) -> str:
    """Yahoo!ショッピング特有のSEOキーワード詰め込みやPRタグを除去し、スマートで短い商品名に整形"""
    if not title:
        return "注目アイテム"

    cleaned = title
    # 1. ブラケット・括弧とその中身を削除（【...】, ［...］, [...], （...）, (...), {...}）
    cleaned = re.sub(r'\{[^}]*\}', ' ', cleaned)
    cleaned = re.sub(r'【[^】]*】', ' ', cleaned)
    cleaned = re.sub(r'［[^］]*］', ' ', cleaned)
    cleaned = re.sub(r'\[[^\]]*\]', ' ', cleaned)
    cleaned = re.sub(r'（[^）]*）', ' ', cleaned)
    cleaned = re.sub(r'\([^)]*\)', ' ', cleaned)
    cleaned = re.sub(r'〈[^〉]*〉', ' ', cleaned)
    cleaned = re.sub(r'《[^》]*》', ' ', cleaned)

    # 2. Yahoo!プロモーション記号・装飾文字の削除
    cleaned = re.sub(r'[★☆◆◇■□▲▼◎○〇♪!！?？※★☆・]+', ' ', cleaned)

    # 3. Yahoo!特有のプロモーション・SEOワードの削除
    promo_words = [
        r'送料無料.*', r'あすつく', r'即納', r'ランキング\s*\d*位', r'第?\d+冠',
        r'クーポン(で|\s*利用で)?\d+%?OFF?', r'ポイント\s*\d+倍', r'PayPay\s*\d+倍',
        r'超PayPay祭', r'お買い物マラソン', r'セール', r'限定', r'正規品',
        r'公式', r'メーカー保証', r'ギフト', r'プレゼント', r'母の日', r'父の日',
        r'敬老の日', r'お祝い', r'新生活', r'防災グッズ', r'PSE認証(済)?',
        r'202[4-7]年?(最新|新型)?', r'最新(版|型)?', r'新型', r'超軽量', r'大容量'
    ]
    for pw in promo_words:
        cleaned = re.sub(pw, ' ', cleaned, flags=re.IGNORECASE)

    # 4. 区切り文字で分割し、意味のある先頭部分を採用
    delimiters = [r'\s*\|\s*', r'\s*｜\s*', r'\s*／\s*', r'\s*/\s*', r'\s*－\s*', r'\s*:\s*', r'\s*：\s*']
    for delim in delimiters:
        parts = re.split(delim, cleaned)
        if parts and len(parts[0].strip()) >= 4:
            cleaned = parts[0]
            break

    # 5. 連続スペースを1つに統合
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # 6. スペース区切りで単語を抽出し、長すぎるSEOワードの連なりを短縮（最大30文字程度）
    words = cleaned.split()
    if words:
        filtered_words = []
        for w in words:
            if w in ["用", "対応", "向け", "おすすめ", "人気", "ランキング"]:
                continue
            filtered_words.append(w)
            if len(" ".join(filtered_words)) >= 26:
                break
        if filtered_words:
            cleaned = " ".join(filtered_words)

    return cleaned[:35].strip() or "注目ガジェット"

class YahooShoppingAPI:
    """Yahoo!ショッピング API (v3) クライアント"""
    
    BASE_URL = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"
    
    # ガジェット特化の厳選キーワード
    GADGET_KEYWORDS = [
        "ワイヤレスイヤホン ノイズキャンセリング",
        "モバイルバッテリー 急速充電",
        "スマートウォッチ 心拍計",
        "Anker USB急速充電器",
        "Bluetooth スピーカー 高音質",
        "ワイヤレス充電器 Qi2",
        "メカニカルキーボード 静音",
        "エルゴノミクス マウス",
        "USBハブ ドッキングステーション Type-C",
        "スマート家電 スマートリモコン",
        "骨伝導イヤホン 防水",
        "SSD ポータブル 高速 外付け",
        "ハンディファン 冷却プレート 静音",
        "卓上加湿器 超音波",
        "デスクライト LED 調光調色",
        "忘れ物防止タグ トラッカー",
        "WEBカメラ フルHD マイク内蔵"
    ]

    def __init__(self, client_id: str = "", affiliate_id: str = ""):
        self.client_id = client_id or os.environ.get("YAHOO_CLIENT_ID", "")
        self.affiliate_id = affiliate_id or os.environ.get("YAHOO_AFFILIATE_ID", "")

    def generate_random_keyword(self) -> str:
        return random.choice(self.GADGET_KEYWORDS)

    def search_items(self, query: str = "", hits: int = 30, sort: str = "-score") -> List[Dict[str, Any]]:
        """Yahoo!ショッピングAPI v3で商品検索を実行"""
        if not self.client_id:
            print("Warning: YAHOO_CLIENT_ID is not configured.")
            return []

        if not query:
            query = self.generate_random_keyword()

        params = {
            "appid": self.client_id,
            "query": query,
            "results": min(hits, 30),
            "sort": sort,
            "in_stock": "true",
            "image_size": 600
        }

        # アフィリエイト設定（バリューコマース等）
        if self.affiliate_id:
            params["affiliate_type"] = "vc"
            params["affiliate_id"] = self.affiliate_id

        try:
            resp = requests.get(
                self.BASE_URL,
                params=params,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                raw_items = data.get("hits", [])
                items = []
                
                for raw in raw_items:
                    title = raw.get("name", "")
                    clean_title = clean_yahoo_product_title(title)
                    price_val = raw.get("price", 0)
                    price_str = f"{price_val:,}円" if isinstance(price_val, (int, float)) else str(price_val)
                    
                    # 画像URLの取得 (exImage優先、なければmedium)
                    image_url = ""
                    ex_img = raw.get("exImage")
                    if isinstance(ex_img, dict) and ex_img.get("url"):
                        image_url = ex_img.get("url")
                    elif isinstance(raw.get("image"), dict):
                        image_url = raw.get("image", {}).get("medium") or raw.get("image", {}).get("small", "")

                    item_url = raw.get("url", "")
                    item_code = raw.get("code") or raw.get("id") or item_url

                    items.append({
                        "title": title,
                        "clean_title": clean_title,
                        "price": price_str,
                        "url": item_url,
                        "image_url": image_url,
                        "itemCode": f"yahoo_{item_code}",
                        "platform": "yahoo",
                        "seller": raw.get("seller", {}).get("name", "Yahoo!ショッピング"),
                        "description": raw.get("description", ""),
                        "category": "ガジェット"
                    })
                return items
            else:
                print(f"Yahoo API Error: HTTP {resp.status_code}: {resp.text[:150]}")
                return []
        except Exception as e:
            print(f"Yahoo API request failed: {e}")
            return []
