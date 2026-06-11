import os
from PIL import Image, ImageDraw, ImageFont
import random
from typing import Tuple

class ImageGenerator:
    def __init__(self, model_id: str = "Ondy/tiny-sd"):
        self.model_id = model_id
        self.cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        self.pipe = None

    def load_model(self):
        try:
            print(f"Loading Stable Diffusion model: {self.model_id}...")
            import torch
            from diffusers import StableDiffusionPipeline
            # Load with float32 for CPU
            self.pipe = StableDiffusionPipeline.from_pretrained(
                self.model_id,
                cache_dir=self.cache_dir,
                torch_dtype=torch.float32
            )
            self.pipe.to("cpu")
            # Enable attention slicing for CPU memory optimization
            self.pipe.enable_attention_slicing()
            print("Stable Diffusion model loaded successfully.")
        except Exception as e:
            print(f"Failed to load image generation model: {e}. Fallback generator will be used.")

    def generate_eyecatch(self, prompt: str, output_path: str = "eyecatch.png") -> str:
        # Prompt translation/cleanup for better SD performance (SD works best with English prompts)
        english_prompt = f"Product banner, high quality, professional product photography, 4k, trending on artstation, {prompt}"
        
        if self.pipe is None:
            return self._generate_fallback_image(prompt, output_path)

        try:
            print(f"Generating image with prompt: {english_prompt}")
            # SD Turbo / Tiny-SD can generate decent images in 4-8 steps
            image = self.pipe(
                english_prompt, 
                num_inference_steps=6, 
                guidance_scale=2.0
            ).images[0]
            
            image.save(output_path)
            print(f"Image saved to {output_path}")
            return output_path
        except Exception as e:
            print(f"Error during image generation: {e}. Falling back to gradient banner generation.")
            return self._generate_fallback_image(prompt, output_path)

    def _generate_fallback_image(self, text: str, output_path: str, size: Tuple[int, int] = (800, 450)) -> str:
        print("Generating a premium gradient fallback image with Pillow...")
        width, height = size
        image = Image.new("RGB", size)
        draw = ImageDraw.Draw(image)

        # Generate a premium gradient (e.g. deep blues to purples)
        color_start = (random.randint(10, 40), random.randint(20, 60), random.randint(80, 150))
        color_end = (random.randint(80, 160), random.randint(10, 50), random.randint(120, 200))

        for y in range(height):
            # Interpolate colors
            r = int(color_start[0] + (color_end[0] - color_start[0]) * (y / height))
            g = int(color_start[1] + (color_end[1] - color_start[1]) * (y / height))
            b = int(color_start[2] + (color_end[2] - color_start[2]) * (y / height))
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Draw abstract geometric overlay for high quality look
        for _ in range(5):
            x1, y1 = random.randint(0, width), random.randint(0, height)
            x2, y2 = x1 + random.randint(50, 200), y1 + random.randint(50, 200)
            draw.ellipse([x1, y1, x2, y2], fill=(255, 255, 255, 10), outline=(255, 255, 255, 30))

        # Add Title text
        # Since standard fonts might not be installed on Github Actions runner,
        # we draw a stylish card overlay and simple text
        card_margin = 40
        draw.rounded_rectangle(
            [card_margin, card_margin, width - card_margin, height - card_margin],
            radius=15,
            fill=None,
            outline=(255, 255, 255, 120),
            width=2
        )
        
        # Simple text representation using default font if TrueType is unavailable
        try:
            # Try to load default sans font
            font = ImageFont.load_default()
        except:
            font = None

        # Draw a beautiful badge text "HOT ITEM"
        draw.rectangle([60, 60, 200, 95], fill="#FF9900", outline=None)
        draw.text((75, 70), "HOT ITEM", fill=(255, 255, 255), font=font)

        # Draw the title (truncted if too long)
        display_text = text[:35] + "..." if len(text) > 35 else text
        draw.text((60, 120), display_text, fill=(255, 255, 255), font=font)
        draw.text((60, 160), "Amazon Special Review & Features", fill=(200, 200, 250), font=font)

        # Draw Amazon style cart button graphic
        draw.rounded_rectangle([60, 320, 280, 370], radius=8, fill="#FF9900")
        draw.text((80, 335), "CHECK ON AMAZON", fill=(255, 255, 255), font=font)

        image.save(output_path)
        print(f"Fallback image saved to {output_path}")
        return output_path
