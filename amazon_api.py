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
    """Extracts a clean, short product name suitable for blog titles and search links."""
    cleaned = title
    # Remove bracketed/parenthesized specifications (both half-width and full-width)
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
    
    # Fallback to truncated original title if empty
    if not cleaned:
        cleaned = title[:30].strip()
        
    return cleaned

class AmazonPAAPI:
    def __init__(self, access_key: str = "", secret_key: str = "", associate_tag: str = "mattan0290c-22", host: str = "", region: str = ""):
        self.associate_tag = associate_tag or "mattan0290c-22"

    def search_items(self, keywords: str, search_index: str = "All", item_count: int = 5) -> List[Dict[str, Any]]:
        print("Amazon PA-API: Completely deprecated. Discovering trending items via Free LLM API...")
        
        items = self._discover_trending_items_via_llm()
        
        if not items:
            print("LLM item discovery failed. Using local trend pool.")
            items = self._get_mock_items(keywords)

        results = []
        for item in items:
            clean = clean_product_title(item["title"])
            search_url = f"https://www.amazon.co.jp/s?k={urllib.parse.quote(clean)}&tag={self.associate_tag}"
            
            results.append({
                "asin": item.get("asin", "B000000000"),
                "title": item["title"],
                "clean_title": clean,
                "features": item.get("features", ["優れたデザイン", "高いコストパフォーマンス", "最新のテクノロジー搭載"]),
                "image_url": item.get("image_url", ""),
                "price": item.get("price", "価格情報なし"),
                "url": search_url,
                "category": item.get("category", "gadget")
            })
            
        return results

    def _discover_trending_items_via_llm(self) -> Optional[List[Dict[str, Any]]]:
        prompt = """現在、日本国内のAmazonや主要家電量販店、SNS等で「非常に評価が高く、売れ筋で大人気」の最新ガジェット、PC周辺機器、スマート家電、ゲーム、美容家電などから、実際に存在するリアルな商品候補を5つ挙げてください。
必ず実在するモデル名、メーカー名を使用してください。
出力は以下のJSON配列形式のみにし、マークダウンブロック（```json ... ```）等で包んで、他の説明や挨拶文は一切含めないでください。

[
  {
    "asin": "実在またはダミーの10桁ASINコード",
    "title": "正式な商品名（例：Anker Nano II 45W）",
    "features": [
      "特徴1：〜〜〜",
      "特徴2：〜〜〜",
      "特徴3：〜〜〜"
    ],
    "price": "市場想定価格（例：￥3,990）",
    "category": "カテゴリ（gadget, pc, kitchen, beauty, gameのいずれか）"
  }
]
"""
        generators = [
            ("Gemini API", self._call_gemini),
            ("GitHub Models API", self._call_github_models),
            ("Pollinations AI Free", self._call_pollinations),
        ]

        for name, fn in generators:
            try:
                print(f"Requesting trending items from {name}...")
                raw_res = fn(prompt)
                if raw_res:
                    json_str = raw_res.strip()
                    if "```json" in json_str:
                        json_str = json_str.split("```json")[-1].split("```")[0].strip()
                    elif "```" in json_str:
                        json_str = json_str.split("```")[-1].split("```")[0].strip()
                    
                    items = json.loads(json_str)
                    if isinstance(items, list) and len(items) > 0 and "title" in items[0]:
                        return items
            except Exception as e:
                print(f"Failed to fetch trends from {name}: {e}")
        return None

    def _call_gemini(self, prompt: str) -> Optional[str]:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        resp = requests.post(url, json=payload, timeout=25)
        if resp.status_code == 200:
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return None

    def _call_github_models(self, prompt: str) -> Optional[str]:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not token:
            return None
        url = "https://models.inference.ai.azure.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a helpful JSON generator. Output only valid JSON arrays. Do not talk."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=25)
        if resp.status_code == 200:
            try:
                return resp.json()["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                return None
        return None

    def _call_pollinations(self, prompt: str) -> Optional[str]:
        url = "https://text.pollinations.ai/"
        payload = {
            "messages": [
                {"role": "system", "content": "You are a helpful JSON generator. Output only valid JSON arrays. Do not talk."},
                {"role": "user", "content": prompt}
            ],
            "model": "openai"
        }
        for attempt in range(3):
            resp = requests.post(url, json=payload, timeout=25)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 429:
                print(f"Pollinations AI returned 429. Waiting {attempt+2}s...")
                time.sleep(attempt+2)
            else:
                break
        return None

    def _get_mock_items(self, keywords: str) -> List[Dict[str, Any]]:
        pool = [
            {
                "asin": "B09Y2MYLMC",
                "title": "Sony WH-1000XM5 ワイヤレスノイズキャンセリングヘッドホン",
                "features": [
                    "業界最高クラスのノイズキャンセリング: 圧倒的な静寂感とクリアな音楽空間を提供。",
                    "ハイレゾ音源対応: 高音質コーデックLDACに対応し、繊細な音も忠実に再現。",
                    "スマート機能: 会話を開始すると自動で外音取り込みに切り替わるSpeak-to-Chat搭載。"
                ],
                "price": "￥48,500",
                "category": "gadget"
            },
            {
                "asin": "B0CGDJ4Y8X",
                "title": "Shokz OpenRun Pro 2 骨伝導イヤホン",
                "features": [
                    "第2世代デュアルピッチテクノロジー: 骨伝導と空気伝導を組み合わせ、豊かな重低音とクリアな中高音を両立。",
                    "オープンイヤーデザイン: 耳を塞がないため、周囲の音を聴きながら安全にトレーニングや通話が可能。",
                    "最大12時間の音楽再生: 急速充電にも対応し、わずか5分の充電で約2.5時間使用可能。"
                ],
                "price": "￥27,880",
                "category": "gadget"
            },
            {
                "asin": "B0D1A45Y8Z",
                "title": "Anker Prime Wall Charger (100W, 3 Ports, GaN)",
                "features": [
                    "最大100Wの超高出力: MacBook Proを含むノートPCからスマートフォンまで3台同時に急速充電可能。",
                    "極限のコンパクト設計: 一般的な96W以上の充電器と比較し、約45%の小型化を実現。",
                    "独自のActiveShield 2.0搭載: 優れた温度管理と保護システムで、接続された機器を24時間保護。"
                ],
                "price": "￥9,990",
                "category": "gadget"
            },
            {
                "asin": "B0B1D4Y7S3",
                "title": "ロジクール MX MASTER 3S アドバンスド ワイヤレス マウス",
                "features": [
                    "静音クリック: 従来モデルよりクリック音を約90%軽減し、静かな作業環境を提供。",
                    "8000DPI高精度トラッキング: ガラス面を含むあらゆる材質の表面で極めてスムーズな操作が可能。",
                    "人間工学デザイン: 手のひらに自然にフィットする美しいシェイプで長時間の使用でも疲れにくい。"
                ],
                "price": "￥16,800",
                "category": "pc"
            },
            {
                "asin": "B082TTR5C1",
                "title": "HHKB Professional HYBRID Type-S 日本語配列／墨",
                "features": [
                    "極上の打鍵感: 静電容量無接点方式による滑らかで心地よい打鍵感と耐久性。",
                    "Type-S静音仕様: タイピング音を大幅に低減した静音モデル。",
                    "ハイブリッド接続: Bluetooth接続とUSB接続（Type-C）の両方に対応。"
                ],
                "price": "￥36,850",
                "category": "pc"
            },
            {
                "asin": "B0C77G172F",
                "title": "SwitchBot ロボット掃除機 K10+ (世界最小級モデル)",
                "features": [
                    "直径わずか24.8cmの超小型: 家具の隙間や椅子の脚の間もしっかり入り込んで徹底清掃。",
                    "自動ゴミ収集ステーション付き: 最大70日間ゴミ捨て不要で、清掃からゴミ収集まで全自動化。",
                    "静音設計と強力な吸引力: 2500Paの強力な吸引力を持ちながら、図書館並みの静音運転が可能。"
                ],
                "price": "￥59,800",
                "category": "kitchen"
            },
            {
                "asin": "B0B7H8MC5M",
                "title": "バルミューダ The Toaster スチームトースター",
                "features": [
                    "スチームテクノロジー: 独自のスチーム技術と細やかな温度制御で、窯から出したてのようなトーストを再現。",
                    "5つの調理モード: トースト、チーズトースト、フランスパン、クロワッサン、クラシックの各モード搭載。",
                    "洗練されたデザイン: キッチンをおしゃれに彩るモダンで美しい外観。"
                ],
                "price": "￥27,900",
                "category": "kitchen"
            },
            {
                "asin": "B0B5F4KV4B",
                "title": "パナソニック ヘアドライヤー ナノケア EH-NA0J",
                "features": [
                    "高浸透ナノイー: 水分発生量が従来の18倍。髪の内側までしっかりうるおい、しっとりまとまる髪へ。",
                    "スマート温冷モード: 温風と冷風を自動で交互に切り替え、毛先までツヤのある仕上がりに。",
                    "コンパクト＆軽量: 風量アップと本体の軽量設計を両立し、乾かしやすさが大幅に向上。"
                ],
                "price": "￥38,000",
                "category": "beauty"
            }
        ]
        return random.sample(pool, min(len(pool), 5))
