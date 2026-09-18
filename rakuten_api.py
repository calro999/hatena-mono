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
    """楽天特有のSEOキーワード詰め込みやPRタグを除去し、スマートで短い商品名に整形"""
    if not title:
        return "注目アイテム"
    
    cleaned = title
    # 1. ブラケット・括弧とその中身を削除（【...】, ［...］, [...], （...）, (...)）
    cleaned = re.sub(r'【[^】]*】', ' ', cleaned)
    cleaned = re.sub(r'［[^］]*］', ' ', cleaned)
    cleaned = re.sub(r'\[[^\]]*\]', ' ', cleaned)
    cleaned = re.sub(r'（[^）]*）', ' ', cleaned)
    cleaned = re.sub(r'\([^)]*\)', ' ', cleaned)
    cleaned = re.sub(r'〈[^〉]*〉', ' ', cleaned)
    cleaned = re.sub(r'《[^》]*》', ' ', cleaned)
    
    # 2. 楽天プロモーション記号・装飾文字の削除
    cleaned = re.sub(r'[★☆◆◇■□▲▼◎○〇♪!！?？※★☆]+', ' ', cleaned)
    
    # 3. 楽天特有のプロモーション・SEOワードの削除
    promo_words = [
        r'送料無料', r'あす楽', r'即納', r'ランキング\s*\d*位', r'第?\d+冠',
        r'クーポン(で|\s*利用で)?\d+%?OFF?', r'ポイント\s*\d+倍', r'P\d+倍',
        r'スーパーSALE', r'お買い物マラソン', r'セール', r'限定', r'正規品',
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

    # 6. スペース区切りで単語を抽出し、長すぎるSEOワードの連なりを短縮（最大26文字程度、最大4単語）
    words = cleaned.split()
    if words:
        filtered_words = []
        for i, w in enumerate(words):
            # 不要な検索タグ・属性語・否定語のスキップ
            if w in ["テレビ", "両耳", "片耳", "ではない", "用", "対応", "向け", "おすすめ", "人気", "補聴器ではない", "ランキング"]:
                continue
            # ひらがなのみの単語で、直前の単語の読み仮名と思われる場合はスキップ（例: 「集音器 しゅうおんき」）
            if i > 0 and re.fullmatch(r'[ぁ-ん]+', w) and len(w) >= 3:
                continue
            filtered_words.append(w)
        
        words_to_use = filtered_words if filtered_words else words
        shortened = ""
        count = 0
        for w in words_to_use:
            if not shortened:
                shortened = w
                count += 1
            elif count < 4 and len(shortened) + len(w) + 1 <= 28:
                shortened += " " + w
                count += 1
            else:
                break
        cleaned = shortened

    # 7. 万一短すぎる場合のフォールバック
    if len(cleaned) < 3:
        # 元タイトルから記号を取り除いた先頭25文字
        fallback = re.sub(r'[【】［］\[\]（）()★☆◆◇■□▲▼◎!！?？]', ' ', title)
        fallback = re.sub(r'\s+', ' ', fallback).strip()
        cleaned = fallback[:25].strip()

    return cleaned

# 多様なガジェット・家電・PC・デスク環境・スマートホームカテゴリ（60種以上）
GADGET_CATEGORIES = [
    "完全ワイヤレスイヤホン",
    "ノイズキャンセリング ヘッドホン",
    "骨伝導イヤホン",
    "オープンイヤー イヤホン",
    "モバイルバッテリー 大容量",
    "GaN 急速充電器",
    "3in1 ワイヤレス充電スタンド",
    "MagSafe モバイルバッテリー",
    "USB-C ハブ ドッキングステーション",
    "メカニカルキーボード",
    "静音 ワイヤレスマウス",
    "エルゴノミクス トラックボールマウス",
    "デスクマット 大型",
    "モニターライト スクリーンバー",
    "ノートパソコンスタンド アルミ",
    "モバイルモニター ポータブル",
    "PCスピーカー Bluetooth",
    "USB コンデンサーマイク",
    "ウェブカメラ 4K 高画質",
    "ポータブル電源 大容量",
    "ソーラーチャージャー 折りたたみ",
    "スマートウォッチ 防水",
    "スマートリング 健康管理",
    "スマートリモコン",
    "スマートプラグ Wi-Fi",
    "スマートロック 自動施錠",
    "スマート温湿度計",
    "ロボット掃除機 水拭き",
    "ハンディクリーナー コードレス",
    "電動エアダスター 強力",
    "ポータブル スキャナー",
    "ラベルライター スマホ接続",
    "電子ペーパー 電子ノート",
    "電子書籍リーダー",
    "ポータブルプロジェクター 小型",
    "外付けSSD ポータブル 高速",
    "ゲーミングヘッドセット 7.1ch",
    "ゲーミングマウス 超軽量",
    "ケーブルホルダー マグネット 配線整理",
    "デスク下 ケーブルトレー",
    "LEDテープライト デスク 間接照明",
    "サーキュレーター 静音 DCモーター",
    "超音波加湿器 卓上",
    "空気清浄機 小型 卓上",
    "電気ケトル 温度調節",
    "全自動コーヒーメーカー",
    "タンブラー 保温 保冷 デスク",
    "ヘアドライヤー 速乾 大風量",
    "電動歯ブラシ 音波振動",
    "スマホ ジンバル スタビライザー",
    "アクションカメラ 4K",
    "デジタルフォトフレーム Wi-Fi",
    "VRヘッドセット ゴーグル",
    "スマートトラッカー 紛失防止タグ",
    "USB切替器 PC2台用",
    "モニターアーム デュアル シングル",
    "フットレスト デスク下",
    "Bluetooth トランスミッター 受信機",
    "ポータブルDAC ヘッドホンアンプ",
    "骨伝導集音器",
    "デスクヒーター パネルヒーター"
]

class RakutenAPI:
    def __init__(self, app_id: str = "", access_key: str = "", affiliate_id: str = ""):
        self.app_id = app_id or os.environ.get("RAKUTEN_APP_ID", "")
        self.access_key = access_key or os.environ.get("RAKUTEN_ACCESS_KEY", "")
        self.affiliate_id = affiliate_id or os.environ.get("RAKUTEN_AFFILIATE_ID", "")

    @staticmethod
    def generate_random_keyword() -> str:
        """60種以上のガジェットカテゴリから均等・ランダムに選定"""
        return random.choice(GADGET_CATEGORIES)

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
