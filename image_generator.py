import os
import requests
import io
import re
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Optional

class ImageGenerator:
    def __init__(self, model_id: str = ""):
        # Diffusers model is no longer needed. We keep the constructor signature for compatibility.
        self.model_id = model_id
        print("ImageGenerator: Using lightweight Pillow composition engine instead of Stable Diffusion.")

    def load_model(self):
        # NOP. Kept for compatibility with existing scripts.
        pass

    def generate_eyecatch(self, prompt: str, output_path: str = "eyecatch.png", image_url: Optional[str] = None) -> str:
        from amazon_api import clean_product_title
        clean_title = clean_product_title(prompt)
        
        # 1. Try to download the product image if URL is provided
        product_img = None
        if image_url:
            try:
                print(f"Downloading product image from: {image_url}")
                resp = requests.get(image_url, timeout=10)
                if resp.status_code == 200:
                    product_img = Image.open(io.BytesIO(resp.content))
                    print("Product image downloaded successfully.")
            except Exception as e:
                print(f"Failed to download product image: {e}. Generating banner without product photo.")

        return self._generate_composite_image(clean_title, product_img, output_path)

    def _load_font(self, size: int):
        font_paths = [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf"
        ]
        for path in font_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    def _draw_wrapped_text(self, draw: ImageDraw.ImageDraw, text: str, position: Tuple[int, int], font, max_width: int, fill: Tuple[int, int, int, int]):
        lines = []
        current_line = ""
        
        # Character-by-character wrap to natively support both Japanese and English without spaces
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

        # Draw up to 3 lines to prevent layout break
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
            draw.text((x + 2, y + 2), line, fill=(10, 10, 15, 120), font=font)
            # Main text
            draw.text((x, y), line, fill=fill, font=font)
            y += line_height

    def _generate_composite_image(self, clean_title: str, product_img: Optional[Image.Image], output_path: str, size: Tuple[int, int] = (800, 450)) -> str:
        print("Generating composite premium eyecatch...")
        width, height = size
        
        # Create canvas with alpha channel
        image = Image.new("RGBA", size)
        draw = ImageDraw.Draw(image)

        # 1. Premium Gradient Background (Deep Blue-Grey to rich Slate)
        color_start = (20, 24, 33)
        color_end = (41, 55, 91)
        for y in range(height):
            ratio = y / height
            r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
            g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
            b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

        # 2. Add abstract glowing ambient elements
        draw.ellipse([width - 320, -120, width + 80, 280], fill=(99, 102, 241, 45))  # Indigo glow on top right
        draw.ellipse([-120, height - 280, 280, height + 120], fill=(236, 72, 153, 30))  # Pink glow on bottom left

        # 3. Outer Premium Frame / Card Border
        card_margin = 30
        draw.rounded_rectangle(
            [card_margin, card_margin, width - card_margin, height - card_margin],
            radius=24,
            fill=(255, 255, 255, 6),
            outline=(255, 255, 255, 25),
            width=2
        )

        # 4. Fonts
        font_large = self._load_font(32)
        font_medium = self._load_font(20)
        font_small = self._load_font(13)

        # 5. Left Column Content (Product Info)
        # Badge: "RECOMMENDED"
        badge_x1, badge_y1 = 65, 65
        badge_x2, badge_y2 = 210, 95
        draw.rounded_rectangle([badge_x1, badge_y1, badge_x2, badge_y2], radius=6, fill="#FF9900")
        draw.text((badge_x1 + 18, badge_y1 + 5), "RECOMMENDED", fill=(255, 255, 255, 255), font=font_small)

        # Title (wrapped)
        title_x, title_y = 65, 125
        max_title_width = 380
        self._draw_wrapped_text(draw, clean_title, (title_x, title_y), font_large, max_title_width, (255, 255, 255, 255))

        # Subtitle / Footer
        sub_text = "Amazon Hot Selling Gadget Review"
        draw.text((65, 270), sub_text, fill=(200, 205, 215, 180), font=font_medium)

        # Amazon CTA Button
        btn_x1, btn_y1 = 65, 335
        btn_x2, btn_y2 = 310, 385
        draw.rounded_rectangle([btn_x1, btn_y1, btn_x2, btn_y2], radius=25, fill="#FF9900")
        draw.text((btn_x1 + 25, btn_y1 + 14), "Amazonで詳細を見る ➔", fill=(255, 255, 255, 255), font=font_medium)

        # 6. Right Column Content (Product Photo Card)
        photo_box_size = 280
        photo_x1 = width - card_margin - photo_box_size - 30
        photo_y1 = (height - photo_box_size) // 2
        photo_x2 = photo_x1 + photo_box_size
        photo_y2 = photo_y1 + photo_box_size

        # Soft Card Shadow (drawn using dark gray rectangle with rounded edges)
        draw.rounded_rectangle(
            [photo_x1 + 4, photo_y1 + 4, photo_x2 + 4, photo_y2 + 4],
            radius=16,
            fill=(10, 12, 18, 120),
            outline=None
        )

        # White Rounded Card for Product
        draw.rounded_rectangle(
            [photo_x1, photo_y1, photo_x2, photo_y2],
            radius=16,
            fill=(255, 255, 255, 255),
            outline=(255, 255, 255, 40),
            width=1
        )

        if product_img:
            # Resize image to fit neatly within the card padding
            padding = 20
            fit_size = photo_box_size - (padding * 2)
            
            # Maintain aspect ratio
            product_img.thumbnail((fit_size, fit_size), Image.Resampling.LANCZOS)
            
            # Create a transparent overlay to paste
            img_w, img_h = product_img.size
            paste_x = photo_x1 + padding + (fit_size - img_w) // 2
            paste_y = photo_y1 + padding + (fit_size - img_h) // 2
            
            # If the downloaded image has alpha, use it as mask, otherwise paste directly
            if product_img.mode in ('RGBA', 'LA') or (product_img.mode == 'P' and 'transparency' in product_img.info):
                image.paste(product_img, (paste_x, paste_y), product_img.convert("RGBA"))
            else:
                image.paste(product_img, (paste_x, paste_y))
        else:
            # Draw beautiful geometric placeholders since product photo was not available
            inner_padding = 40
            placeholder_draw = ImageDraw.Draw(image)
            # Ambient geometric circle inside the white card
            circle_x1 = photo_x1 + inner_padding
            circle_y1 = photo_y1 + inner_padding
            circle_x2 = photo_x2 - inner_padding
            circle_y2 = photo_y2 - inner_padding
            placeholder_draw.ellipse([circle_x1, circle_y1, circle_x2, circle_y2], fill=(240, 244, 253), outline=(220, 225, 235), width=2)
            
            # Draw a cart icon or shopping box representation
            cart_center_x = (photo_x1 + photo_x2) // 2
            cart_center_y = (photo_y1 + photo_y2) // 2
            placeholder_draw.rectangle([cart_center_x - 30, cart_center_y - 20, cart_center_x + 30, cart_center_y + 20], fill=None, outline="#FF9900", width=4)
            placeholder_draw.line([(cart_center_x - 20, cart_center_y - 35), (cart_center_x - 30, cart_center_y - 20)], fill="#FF9900", width=4)
            placeholder_draw.line([(cart_center_x + 20, cart_center_y - 35), (cart_center_x + 30, cart_center_y - 20)], fill="#FF9900", width=4)

        # Convert to RGB to discard alpha, save as PNG/JPEG
        rgb_image = image.convert("RGB")
        rgb_image.save(output_path, "PNG")
        print(f"Composite eyecatch saved successfully to: {output_path}")
        return output_path
