import base64
import os
import urllib.request
import xml.etree.ElementTree as ET
import datetime
import hashlib
import random
from typing import Optional, Dict

class HatenaAPI:
    def __init__(self, hatena_id: str, blog_id: str, api_key: str):
        self.hatena_id = hatena_id.strip()
        
        # Clean blog_id (remove http://, https://, and trailing slashes/paths)
        cleaned_blog_id = blog_id.replace("https://", "").replace("http://", "").split("/")[0].strip()
        self.blog_id = cleaned_blog_id
        
        self.api_key = api_key.strip()

    def _get_wsse_headers(self) -> Dict[str, str]:
        """Generates WSSE authentication headers for Hatena API."""
        created = datetime.datetime.utcnow().isoformat() + "Z"
        
        # Generate 20-byte random nonce
        nonce_bytes = os.urandom(20)
        
        # Calculate digest: SHA1(Nonce + Created + API_KEY)
        sha = hashlib.sha1()
        sha.update(nonce_bytes + created.encode("utf-8") + self.api_key.encode("utf-8"))
        digest = sha.digest()
        
        # Base64 encode nonce and digest
        nonce_b64 = base64.b64encode(nonce_bytes).decode("utf-8")
        digest_b64 = base64.b64encode(digest).decode("utf-8")
        
        wsse_header = (
            f'UsernameToken Username="{self.hatena_id}", '
            f'PasswordDigest="{digest_b64}", '
            f'Nonce="{nonce_b64}", '
            f'Created="{created}"'
        )
        
        return {
            "X-WSSE": wsse_header,
            "Authorization": "WSSE profile=\"UsernameToken\""
        }

    def upload_image_to_fotolife(self, image_path: str) -> Optional[str]:
        """Uploads an image to Hatena Fotolife and returns its URL."""
        if not self.hatena_id or not self.api_key or self.hatena_id.startswith("DUMMY"):
            print("Hatena API (Fotolife): Credentials not set. Skipping image upload.")
            return None

        if not os.path.exists(image_path):
            print(f"Image file not found: {image_path}")
            return None

        try:
            with open(image_path, "rb") as f:
                img_base64 = base64.b64encode(f.read()).decode("utf-8")

            url = "https://f.hatena.ne.jp/atom/post"
            xml_payload = f"""<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom">
  <title>eyecatch</title>
  <content mode="base64" type="image/png">{img_base64}</content>
</entry>
"""
            headers = self._get_wsse_headers()
            headers["Content-Type"] = "application/xml"

            req = urllib.request.Request(
                url, 
                data=xml_payload.encode("utf-8"), 
                headers=headers, 
                method="POST"
            )

            print("Uploading image to Hatena Fotolife...")
            with urllib.request.urlopen(req) as response:
                res_xml = response.read()
                root = ET.fromstring(res_xml)
                
                namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
                
                content_el = root.find('atom:content', namespaces)
                if content_el is not None:
                    img_url = content_el.get('src')
                    if img_url:
                        print(f"Image uploaded successfully. URL: {img_url}")
                        return img_url
                        
                for link in root.findall('atom:link', namespaces):
                    if 'image' in (link.get('type') or ''):
                        img_url = link.get('href')
                        print(f"Image uploaded successfully. URL: {img_url}")
                        return img_url
            
            print("Warning: Could not parse image URL from Fotolife response.")
            return None
        except Exception as e:
            print(f"Failed to upload image to Hatena Fotolife: {e}")
            return None

    def post_entry(self, title: str, html_content: str, is_draft: bool = False) -> bool:
        """Posts an entry to Hatena Blog using AtomPub API."""
        if not self.hatena_id or not self.blog_id or not self.api_key or self.hatena_id.startswith("DUMMY"):
            print("Hatena API: Credentials not set or dummy mode. Skipping post.")
            print(f"--- DUMMY API POST ---")
            print(f"Blog ID: {self.blog_id}")
            print(f"Title: {title}")
            print(f"Content:\n{html_content[:500]}...")
            print(f"----------------------")
            return True

        draft_val = "yes" if is_draft else "no"
        url = f"https://blog.hatena.ne.jp/{self.hatena_id}/{self.blog_id}/atom/entry"
        
        # Escape XML entities in HTML content to prevent XML parsing error on post
        escaped_html = html_content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        xml_payload = f"""<?xml version="1.0" encoding="utf-8"?>
<entry xmlns="http://www.w3.org/2005/Atom"
       xmlns:app="http://www.w3.org/2007/app">
  <title>{title}</title>
  <author><name>{self.hatena_id}</name></author>
  <content type="text/html">
    {escaped_html}
  </content>
  <app:control>
    <app:draft>{draft_val}</app:draft>
  </app:control>
</entry>
"""
        headers = self._get_wsse_headers()
        headers["Content-Type"] = "application/xml"

        req = urllib.request.Request(
            url, 
            data=xml_payload.encode("utf-8"), 
            headers=headers, 
            method="POST"
        )

        try:
            print(f"Posting entry to Hatena Blog ({self.blog_id})...")
            with urllib.request.urlopen(req) as response:
                if response.status in (201, 200):
                    print("Entry posted successfully via AtomPub API!")
                    return True
                else:
                    print(f"Failed to post. Status code: {response.status}")
                    return False
        except Exception as e:
            print(f"Failed to post entry to Hatena Blog: {e}")
            return False
