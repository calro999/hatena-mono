import os
import json
import urllib.request
import urllib.parse
import re
import requests
import random
import time
from typing import List, Dict, Any, Optional

def clean_product_title(title: str) -> str:
    """Extracts a clean, readable product name suitable for blog titles and CTA."""
    cleaned = title
    # Remove bracketed/parenthesized tags
    cleaned = re.sub(r'【[^】]*】', '', cleaned)
    cleaned = re.sub(r'［[^］]*］', '', cleaned)
    cleaned = re.sub(r'\[[^\]]*\]', '', cleaned)
    cleaned = re.sub(r'（[^）]*）', '', cleaned)
    cleaned = re.sub(r'\([^)]*\)', '', cleaned)
    
    # Split by common delimiters and take the first portion if it's long enough
    delimiters = [r'\s*\|\s*', r'\s*｜\s*', r'\s*-\s*', r'\s*－\s*', r'\s*:\s*']
    for delim in delimiters:
        parts = re.split(delim, cleaned)
        if parts and len(parts[0].strip()) >= 5:
            cleaned = parts[0]
            break
            
    # Clean up multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    if not cleaned:
        cleaned = title[:35].strip()
        
    return cleaned

# ガジェット・家電・PC・便利グッズの検索キーワードプール
GADGET_BRANDS = [
    "Anker", "Logicool", "Sony", "Audio-Technica", "Shokz", "Sennheiser",
    "Bose", "SwitchBot", "Nature Remo", "CIO", "UGREEN", "Belkin",
    "Keychron", "HHKB", "REALFORCE", "BenQ", "Dell", "ASUS", "MSI",
    "ELECOM", "BUFFALO", "サンワダイレクト", "アイリスオーヤマ",
    "バルミューダ", "Panasonic", "Dyson", "シャープ", "山善"
]

GADGET_CATEGORIES = [
    "ワイヤレスイヤホン", "ノイズキャンセリング ヘッドホン", "骨伝導イヤホン",
    "急速充電器 GaN", "モバイルバッテリー 大容量", "マグネット充電器", "USB-C ハブ",
    "ワイヤレスマウス 静音", "メカニカルキーボード", "トラックボールマウス",
    "スマートリモコン", "スマートプラグ", "ロボット掃除機", "温湿度計 スマート",
    "モニターライト デスクライト", "PCスピーカー", "ウェブカメラ 4K",
    "ポータブル電源", "デスクマット", "ノートパソコンスタンド",
    "スマートウォッチ 防水", "コーヒーメーカー 全自動", "電気ケトル 温度調節",
    "ヘアドライヤー ナノケア", "サーキュレーター 静音", "加湿器 超音波"
]

class RakutenAPI:
    def __init__(self, app_id: str = "", access_key: str = "", affiliate_id: str = ""):
        self.app_id = app_id or os.environ.get("RAKUTEN_APP_ID", "")
        self.access_key = access_key or os.environ.get("RAKUTEN_ACCESS_KEY", "")
        self.affiliate_id = affiliate_id or os.environ.get("RAKUTEN_AFFILIATE_ID", "")

    @staticmethod
    def generate_random_keyword() -> str:
        """ブランド名とカテゴリを組み合わせた多様な検索クエリを生成"""
        mode = random.choice(["brand_category", "brand", "category"])
        if mode == "brand_category":
            return f"{random.choice(GADGET_BRANDS)} {random.choice(GADGET_CATEGORIES)}"
        elif mode == "brand":
            return f"{random.choice(GADGET_BRANDS)} 最新"
        else:
            return f"{random.choice(GADGET_CATEGORIES)} 人気"

    def search_items(self, keyword: str, hits: int = 30) -> List[Dict[str, Any]]:
        """楽天商品検索APIから最新・人気アイテムを取得"""
        if not self.app_id or self.app_id.startswith("DUMMY"):
            print("Rakuten App ID not set. Using local mock items for testing.")
            return self._get_mock_items(keyword)

        print(f"Searching Rakuten Ichiba for keyword: '{keyword}'...")
        base_url = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260401"
        
        # 複数ジャンル（家電・AV・カメラ: 211740, PC・周辺機器: 100026, 家電: 562637）
        genre_id = random.choice(["562637", "100026", "211740", ""])
        
        params = {
            "applicationId": self.app_id,
            "keyword": keyword,
            "sort": random.choice(["standard", "-reviewCount", "-reviewAverage"]),
            "hits": hits,
            "format": "json"
        }
        if self.access_key:
            params["accessKey"] = self.access_key
        if self.affiliate_id:
            params["affiliateId"] = self.affiliate_id
        if genre_id:
            params["genreId"] = genre_id

        url = f"{base_url}?{urllib.parse.urlencode(params)}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
                items = []
                for entry in data.get("Items", []):
                    item_data = entry.get("Item", {})
                    if not item_data:
                        continue

                    # 商品画像URLの取得
                    image_url = ""
                    medium_images = item_data.get("mediumImageUrls", [])
                    if medium_images and isinstance(medium_images, list) and len(medium_images) > 0:
                        image_url = medium_images[0].get("imageUrl", "") if isinstance(medium_images[0], dict) else str(medium_images[0])
                    elif item_data.get("smallImageUrls"):
                        small_images = item_data.get("smallImageUrls", [])
                        if small_images and isinstance(small_images, list) and len(small_images) > 0:
                            image_url = small_images[0].get("imageUrl", "") if isinstance(small_images[0], dict) else str(small_images[0])

                    item_name = item_data.get("itemName", "")
                    clean_name = clean_product_title(item_name)
                    item_caption = item_data.get("itemCaption", "")
                    item_code = item_data.get("itemCode", "")
                    item_price = item_data.get("itemPrice", "")
                    affiliate_url = item_data.get("affiliateUrl", "")
                    
                    if not affiliate_url and item_data.get("itemUrl") and self.affiliate_id:
                        enc_url = urllib.parse.quote(item_data.get("itemUrl"), safe='')
                        affiliate_url = f"https://hb.afl.rakuten.co.jp/hgc/{self.affiliate_id}/?pc={enc_url}&m={enc_url}"
                    elif not affiliate_url:
                        affiliate_url = item_data.get("itemUrl", "")

                    # 特徴抽出（キャプションから箇条書き風に分解）
                    features = []
                    if item_caption:
                        sentences = [s.strip() for s in re.split(r'[。\n\r]+', item_caption) if len(s.strip()) > 10]
                        features = sentences[:3]
                    if not features:
                        features = ["洗練されたデザインと優れた機能性", "日常をアップデートする快適な使い心地", "高い信頼性とコストパフォーマンス"]

                    items.append({
                        "title": item_name,
                        "clean_title": clean_name,
                        "itemCode": item_code,
                        "price": f"￥{item_price:,}" if isinstance(item_price, int) else f"￥{item_price}",
                        "image_url": image_url,
                        "url": affiliate_url,
                        "features": features,
                        "caption": item_caption[:300],
                        "category": self._detect_category(clean_name + " " + item_caption)
                    })
                return items
        except urllib.error.HTTPError as e:
            try:
                error_body = e.read().decode("utf-8")
                print(f"Failed to fetch from Rakuten API (HTTPError {e.code}): {error_body}")
            except Exception:
                print(f"Failed to fetch from Rakuten API: {e}")
            return []
        except Exception as e:
            print(f"Failed to fetch from Rakuten API: {e}")
            return []

    def _detect_category(self, text: str) -> str:
        text_lower = text.lower()
        if any(w in text_lower for w in ["keyboard", "キーボード", "mouse", "マウス", "pc", "パソコン", "usb", "モニター"]):
            return "pc"
        if any(w in text_lower for w in ["トースター", "コーヒー", "ケトル", "掃除機", "ルンバ", "加湿器", "キッチン"]):
            return "kitchen"
        if any(w in text_lower for w in ["ドライヤー", "美顔器", "シェーバー", "ナノケア", "ヘアアイロン"]):
            return "beauty"
        if any(w in text_lower for w in ["ゲーム", "switch", "ps5", "コントローラー"]):
            return "game"
        return "gadget"

    def _get_mock_items(self, keyword: str) -> List[Dict[str, Any]]:
        pool = [
            {
                "title": f"【最新モデル】{keyword} 高機能ワイヤレスモデル",
                "clean_title": f"{keyword} 高機能ワイヤレスモデル",
                "itemCode": f"mock_{abs(hash(keyword)) % 100000}",
                "price": "￥12,800",
                "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop&q=80",
                "url": "https://hb.afl.rakuten.co.jp/mock_gadget",
                "features": [
                    "最新の急速充電・長時間バッテリー駆動に対応",
                    "人間工学に基づいた美しいエルゴノミクスデザイン",
                    "ワンタッチでシームレスに切り替え可能なマルチペアリング機能"
                ],
                "caption": "毎日のデスクワークやライフスタイルをワンランク引き上げる注目の最新アイテム。",
                "category": "gadget"
            }
        ]
        return pool
