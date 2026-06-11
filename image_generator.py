import os
import requests
import io
import re
import urllib.parse
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Optional

class ImageGenerator:
    def __init__(self, model_id: str = ""):
        print("ImageGenerator: Initialized using online Pollinations AI generation + Pillow composition.")

    def load_model(self):
        # NOP. Kept for compatibility.
        pass

    def generate_eyecatch(self, prompt: str, output_path: str = "eyecatch.png", image_url: Optional[str] = None, category: Optional[str] = None) -> str:
        from amazon_api import clean_product_title
        clean_title = clean_product_title(prompt)
        
        # 1. Determine the best AI Image Prompt based on category and title keywords
        ai_prompt = self._select_ai_image_prompt(clean_title, category)
        print(f"Selected AI image generation prompt: '{ai_prompt}'")
        
        # 2. Try to download the AI generated image from Pollinations.ai as base background
        bg_img = None
        try:
            print("Requesting AI image generation from Pollinations.ai...")
            encoded_prompt = urllib.parse.quote(ai_prompt)
            # Use Flux model via pollinations (width=800, height=450)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=450&nologo=true&private=true&seed={os.urandom(4).hex()}"
            resp = requests.get(url, timeout=25)
            if resp.status_code == 200 and len(resp.content) > 5000:
                bg_img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
                print("Successfully downloaded generated AI image for background.")
            else:
                print(f"Pollinations AI returned HTTP {resp.status_code} or too small content. Falling back to gradient background.")
        except Exception as e:
            print(f"Failed to generate background image via AI API: {e}. Falling back to gradient.")

        # 3. Compile the final composite image with typography overlays
        return self._generate_composite_image(clean_title, bg_img, output_path)

    def _select_ai_image_prompt(self, title: str, category: Optional[str]) -> str:
        title_lower = title.lower()
        
        # Match keywords to select specific high-quality visual prompts
        if "ヘッドホン" in title_lower or "イヤホン" in title_lower or "headphone" in title_lower or "earphone" in title_lower:
            return "A stylish modern wireless noise-canceling headphones, warm workspace aesthetic background, close up shot, 3d render, cinematic lighting, 8k, photorealistic"
        
        if "マウス" in title_lower or "キーボード" in title_lower or "mouse" in title_lower or "keyboard" in title_lower:
            return "A sleek high-end mechanical keyboard with glowing RGB keys and ergonomic wireless mouse on a clean workspace desk, close-up, cyberpunk ambient, 8k"
        
        if "掃除機" in title_lower or "ルンバ" in title_lower or "ロボット" in title_lower or "vacuum" in title_lower:
            return "A futuristic smart robotic vacuum cleaner operating on a beautiful hardwood floor of a modern cozy living room, warm afternoon sunlight, 8k"
            
        if "トースター" in title_lower or "ホットクック" in title_lower or "炊飯器" in title_lower or "オーブン" in title_lower or "フライヤー" in title_lower:
            return "A premium minimalist kitchen appliance on a clean white marble countertop, cozy breakfast environment, bright soft morning light, 8k, photorealistic"

        if "ドライヤー" in title_lower or "ヘアアイロン" in title_lower or "ナノケア" in title_lower or "dryer" in title_lower:
            return "A high-end hair dryer placed on a luxury marble bathroom vanity next to elegant cosmetics, soft beauty lighting, 8k, photorealistic"

        if "ゲーム" in title_lower or "コントローラー" in title_lower or "ps5" in title_lower or "switch" in title_lower or "controller" in title_lower:
            return "An immersive gaming setup with custom RGB neon lighting, futuristic game console controller, highly detailed gaming room background, 8k, unreal engine 5 style"

        # Category-based default prompts
        if category == "gadget":
            return "A sleek modern high-tech device on a futuristic display stand, ambient purple and blue neon glowing background, 8k, photorealistic"
        elif category == "pc":
            return "A premium clean PC desk setup, multiple monitors, mechanical keyboard, plant, minimalist workspace, warm studio light, 8k"
        elif category == "kitchen":
            return "A beautiful modern kitchen interior with warm ambient lighting, elegant kitchen gadgets, luxury aesthetic, 8k"
        elif category == "beauty":
            return "A luxury cosmetics and beauty devices display, soft focus, pastel colors, natural daylight, 8k"
        elif category == "game":
            return "A cool gaming setup with colorful lighting, stylish headphone and keyboard, futuristic gaming console, 8k"

        # Universal fallback prompt
        return "A collection of premium modern high-tech gadgets and smart devices on a dark glowing ambient surface, photorealistic, cinematic lighting, 8k"

    def _load_font(self, size: int):
        """日本語表示に対応したフォントをロードする。見つからなければNoto Sans JPを自動DL。"""
        jp_font_paths = [
            # macOS ヒラギノ角ゴシック
            "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc",
            "/System/Library/Fonts/ヒラギノ角ゴシック W9.ttc",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            # Ubuntu / GitHub Actions (apt install fonts-noto-cjk)
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            # ローカルキャッシュ
            os.path.join(os.path.dirname(__file__), "fonts", "NotoSansJP-Bold.ttf"),
            # Windows
            "C:\\Windows\\Fonts\\meiryo.ttc",
            "C:\\Windows\\Fonts\\msgothic.ttc",
        ]
        for path in jp_font_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    pass

        cached = self._download_noto_sans_jp()
        if cached and os.path.exists(cached):
            try:
                return ImageFont.truetype(cached, size)
            except Exception:
                pass

        fallback_paths = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        for path in fallback_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    def _download_noto_sans_jp(self) -> Optional[str]:
        """Google Fonts から Noto Sans JP Bold をダウンロードしてローカルにキャッシュ。"""
        font_dir = os.path.join(os.path.dirname(__file__), "fonts")
        font_path = os.path.join(font_dir, "NotoSansJP-Bold.ttf")
        if os.path.exists(font_path):
            return font_path
        try:
            os.makedirs(font_dir, exist_ok=True)
            url = "https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP-Bold.ttf"
            print("日本語フォントが見つかりません。Noto Sans JP をダウンロード中...")
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                with open(font_path, "wb") as f:
                    f.write(resp.content)
                print(f"フォントを保存しました: {font_path}")
                return font_path
        except Exception as e:
            print(f"フォントのダウンロードに失敗: {e}")
        return None

    def _draw_wrapped_text(self, draw: ImageDraw.ImageDraw, text: str, position: Tuple[int, int], font, max_width: int, fill: Tuple[int, int, int, int]):
        lines = []
        current_line = ""
        for char in text:
            test_line = current_line + char
            try:
                bbox = font.getbbox(test_line)
                w = bbox[2] - bbox[0]
            except Exception:
                w = draw.textlength(test_line, font=font)
                
            if w <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = char
        if current_line:
            lines.append(current_line)

        x, y = position
        try:
            sample_bbox = font.getbbox("A")
            char_height = sample_bbox[3] - sample_bbox[1]
        except Exception:
            char_height = 20
            
        line_spacing = int(char_height * 0.3)
        line_height = char_height + line_spacing
        
        for line in lines[:3]:
            # Drop shadow
            draw.text((x + 2, y + 2), line, fill=(10, 10, 15, 180), font=font)
            # Main text
            draw.text((x, y), line, fill=fill, font=font)
            y += line_height

    def _generate_composite_image(self, clean_title: str, bg_img: Optional[Image.Image], output_path: str, size: Tuple[int, int] = (800, 450)) -> str:
        print("Generating composite premium eyecatch with AI background...")
        width, height = size
        
        # 1. Background Initialization (Use AI-generated image or fallback to premium gradient)
        if bg_img:
            # Scale background image to fit the size perfectly
            image = bg_img.resize(size, Image.Resampling.LANCZOS)
            draw = ImageDraw.Draw(image)
            
            # Draw a dark overlay to make text more readable
            overlay = Image.new("RGBA", size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            
            # Soft black gradient overlay from left to right (heavier on the left side where text sits)
            for x in range(width):
                # Gradient opacity: 200 (left) down to 80 (right)
                alpha = int(210 - (130 * (x / width)))
                overlay_draw.line([(x, 0), (x, height)], fill=(12, 16, 26, alpha))
                
            image = Image.alpha_composite(image, overlay)
            draw = ImageDraw.Draw(image)
        else:
            image = Image.new("RGBA", size)
            draw = ImageDraw.Draw(image)
            # Fallback Premium Gradient Background (Deep Blue-Grey to rich Slate)
            color_start = (20, 24, 33)
            color_end = (41, 55, 91)
            for y in range(height):
                ratio = y / height
                r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
                g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
                b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
                draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

        # 2. Outer Premium Frame / Card Border
        card_margin = 25
        draw.rounded_rectangle(
            [card_margin, card_margin, width - card_margin, height - card_margin],
            radius=20,
            fill=(255, 255, 255, 5),
            outline=(255, 255, 255, 20),
            width=2
        )

        # 3. Fonts Loading
        font_large = self._load_font(32)
        font_medium = self._load_font(20)
        font_small = self._load_font(12)

        # 4. Content Layout (Left-aligned elegant card styling)
        # Badge: "RECOMMENDED"
        badge_x1, badge_y1 = 60, 60
        badge_x2, badge_y2 = 195, 88
        draw.rounded_rectangle([badge_x1, badge_y1, badge_x2, badge_y2], radius=6, fill="#FF9900")
        draw.text((badge_x1 + 16, badge_y1 + 4), "RECOMMENDED", fill=(255, 255, 255, 255), font=font_small)

        # Title (wrapped with high contrast white text)
        title_x, title_y = 60, 115
        max_title_width = 460
        self._draw_wrapped_text(draw, clean_title, (title_x, title_y), font_large, max_title_width, (255, 255, 255, 255))

        # Subtitle / Footer
        sub_text = "Latest Hot Selling Gadget Review & Specs"
        draw.text((60, 265), sub_text, fill=(210, 215, 225, 200), font=font_medium)

        # Amazon CTA Button
        btn_x1, btn_y1 = 60, 325
        btn_x2, btn_y2 = 295, 375
        draw.rounded_rectangle([btn_x1, btn_y1, btn_x2, btn_y2], radius=25, fill="#FF9900")
        draw.text((btn_x1 + 22, btn_y1 + 13), "Amazonで詳細を見る ➔", fill=(255, 255, 255, 255), font=font_medium)

        # Save to output path
        rgb_image = image.convert("RGB")
        rgb_image.save(output_path, "PNG")
        print(f"Premium AI-composed eyecatch saved successfully to: {output_path}")
        return output_path
