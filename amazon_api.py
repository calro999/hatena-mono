import os
import json
import hmac
import hashlib
import datetime
import urllib.request
from typing import List, Dict, Any

class AmazonPAAPI:
    def __init__(self, access_key: str, secret_key: str, associate_tag: str, host: str = "webservices.amazon.co.jp", region: str = "us-west-2"):
        self.access_key = access_key
        self.secret_key = secret_key
        self.associate_tag = associate_tag
        self.host = host
        self.region = region
        self.service = "ProductAdvertisingAPI"
        self.path = "/paapi5/searchitems"

    def _sign(self, key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def _get_signature_key(self, key: str, date_stamp: str, region_name: str, service_name: str) -> bytes:
        k_date = self._sign(("AWS4" + key).encode("utf-8"), date_stamp)
        k_region = self._sign(k_date, region_name)
        k_service = self._sign(k_region, service_name)
        k_signing = self._sign(k_service, "aws4_request")
        return k_signing

    def search_items(self, keywords: str, search_index: str = "All", item_count: int = 5) -> List[Dict[str, Any]]:
        # Check if dummy/mock mode is enabled or credentials are missing
        if not self.access_key or not self.secret_key or not self.associate_tag or self.access_key.startswith("DUMMY"):
            print("Amazon PA-API: Credentials not set or dummy mode. Returning mock data.")
            return self._get_mock_items(keywords)

        now = datetime.datetime.utcnow()
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")

        payload = {
            "Keywords": keywords,
            "SearchIndex": search_index,
            "ItemCount": item_count,
            "Resources": [
                "Images.Primary.Large",
                "ItemInfo.Title",
                "ItemInfo.Features",
                "Offers.Listings.Price"
            ],
            "PartnerTag": self.associate_tag,
            "PartnerType": "Associates"
        }
        
        request_parameters = json.dumps(payload)
        
        # HTTP headers
        content_type = "application/json; charset=utf-8"
        target = "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems"
        
        # Create canonical request
        canonical_uri = self.path
        canonical_querystring = ""
        canonical_headers = f"content-type:{content_type}\nhost:{self.host}\nx-amz-target:{target}\n"
        signed_headers = "content-type;host;x-amz-target"
        payload_hash = hashlib.sha256(request_parameters.encode("utf-8")).hexdigest()
        
        canonical_request = f"POST\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
        
        # Create string to sign
        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{self.region}/{self.service}/aws4_request"
        string_to_sign = f"{algorithm}\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        
        # Calculate signature
        signing_key = self._get_signature_key(self.secret_key, date_stamp, self.region, self.service)
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        
        # Authorization header
        authorization_header = f"{algorithm} Credential={self.access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
        
        headers = {
            "Content-Type": content_type,
            "X-Amz-Date": amz_date,
            "X-Amz-Target": target,
            "Authorization": authorization_header,
            "Host": self.host
        }
        
        url = f"https://{self.host}{self.path}"
        req = urllib.request.Request(url, data=request_parameters.encode("utf-8"), headers=headers, method="POST")
        
        try:
            with urllib.request.urlopen(req) as response:
                res_data = response.read().decode("utf-8")
                data = json.loads(res_data)
                return self._parse_items(data)
        except Exception as e:
            print(f"Error calling Amazon PA-API: {e}. Falling back to mock data.")
            return self._get_mock_items(keywords)

    def _parse_items(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        parsed_items = []
        if "SearchResult" in data and "Items" in data["SearchResult"]:
            for item in data["SearchResult"]["Items"]:
                item_info = item.get("ItemInfo", {})
                title = item_info.get("Title", {}).get("DisplayValue", "商品タイトルなし")
                features = item_info.get("Features", {}).get("DisplayValues", [])
                
                images = item.get("Images", {})
                img_url = images.get("Primary", {}).get("Large", {}).get("URL", "")
                
                offers = item.get("Offers", {})
                price = "価格情報なし"
                if offers and "Listings" in offers:
                    listings = offers["Listings"]
                    if listings:
                        price_info = listings[0].get("Price", {})
                        price = price_info.get("DisplayAmount", "価格情報なし")
                
                detail_url = item.get("DetailPageURL", "")
                asin = item.get("ASIN", "")
                
                parsed_items.append({
                    "asin": asin,
                    "title": title,
                    "features": features,
                    "image_url": img_url,
                    "price": price,
                    "url": detail_url
                })
        return parsed_items

    def _get_mock_items(self, keywords: str) -> List[Dict[str, Any]]:
        # Return elegant mock data if API credentials are not provided or error occurs.
        return [
            {
                "asin": "B0C78F7Y1M",
                "title": f"【Amazon.co.jp限定】最新スマートウォッチ Pro (2026モデル) - {keywords}特集商品",
                "features": [
                    "高精度心拍数＆睡眠トラッキング機能搭載",
                    "常時表示対応の高品質AMOLEDディスプレイ",
                    "最大14日間のロングライフバッテリー"
                ],
                "image_url": "https://images-na.ssl-images-amazon.com/images/I/71u0A8sS8LL._AC_SL1500_.jpg",
                "price": "￥12,800",
                "url": f"https://www.amazon.co.jp/dp/B0C78F7Y1M?tag={self.associate_tag}"
            },
            {
                "asin": "B0B8G4R9XY",
                "title": "ノイズキャンセリング搭載 ワイヤレスヘッドホン SoundAir-II",
                "features": [
                    "ハイレゾ対応＆圧倒的な低音響設計",
                    "業界最高クラスのノイズキャンセリング性能",
                    "急速充電対応（10分の充電で3時間再生可能）"
                ],
                "image_url": "https://images-na.ssl-images-amazon.com/images/I/61t54LwU8sL._AC_SL1500_.jpg",
                "price": "￥8,980",
                "url": f"https://www.amazon.co.jp/dp/B0B8G4R9XY?tag={self.associate_tag}"
            }
        ]
