import os
from typing import Dict, Any

class ArticleGenerator:
    def __init__(self, model_id: str = "Qwen/Qwen2.5-1.5B-Instruct", use_hf_cache: bool = True):
        self.model_id = model_id
        # Use Hugging Face default cache or workspace specific directory
        self.cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        self.tokenizer = None
        self.model = None

    def load_model(self):
        try:
            print(f"Loading tokenizer & model for {self.model_id}...")
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, cache_dir=self.cache_dir)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                cache_dir=self.cache_dir,
                torch_dtype=torch.float32,  # CPU friendly
                device_map="cpu"
            )
            print("Model loaded successfully.")
        except Exception as e:
            print(f"Failed to load model: {e}. Fallback template will be used.")

    def generate_review_article(self, item: Dict[str, Any]) -> str:
        title = item.get("title", "")
        features = "\n".join([f"- {f}" for f in item.get("features", [])])
        price = item.get("price", "")
        url = item.get("url", "")

        prompt = f"""以下のAmazonの商品情報を元に、ブログ「はてなブログ」に投稿するための高品質で魅力的な商品レビュー記事を日本語で執筆してください。

【商品名】: {title}
【価格】: {price}
【主な特徴】:
{features}
【アフィリエイトリンク】: {url}

【執筆ルール】:
1. 読者の興味を惹くキャッチーな見出し(H2, H3タグを使用)を作成してください。
2. 商品のメリットだけでなく、どのような人におすすめか、どういう生活の変化が期待できるかを具体的に描写してください。
3. 文末には必ずアフィリエイトリンクへのスムーズな誘導を入れてください。
4. HTML形式(見出し、段落 <p>、箇条書き <ul><li> など)で出力してください。MarkdownではなくHTMLタグを使用してください。
"""

        # Fallback implementation if model loading failed
        if self.model is None or self.tokenizer is None:
            return self._generate_fallback_article(item)

        try:
            messages = [
                {"role": "system", "content": "あなたは優秀なブログライター兼アフィリエイターです。"},
                {"role": "user", "content": prompt}
            ]
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            model_inputs = self.tokenizer([text], return_tensors="pt").to("cpu")

            generated_ids = self.model.generate(
                model_inputs.input_ids,
                max_new_tokens=1024,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]

            response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            return response
        except Exception as e:
            print(f"Error during text generation: {e}. Falling back to template-based generation.")
            return self._generate_fallback_article(item)

    def _generate_fallback_article(self, item: Dict[str, Any]) -> str:
        title = item.get("title", "")
        features_html = "".join([f"<li>{f}</li>" for f in item.get("features", [])])
        price = item.get("price", "")
        url = item.get("url", "")
        image_html = f'<div style="text-align: center; margin: 20px 0;"><img src="{item.get("image_url", "")}" alt="{title}" style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"><br><a href="{url}" style="font-size: 14px; color: #555;">(画像出典: Amazon)</a></div>' if item.get("image_url") else ""

        return f"""
<h2>超話題の最新アイテム！「{title}」を徹底レビュー</h2>
<p>こんにちは！今回は、今ネットやSNSで大きな話題を呼んでいる大注目商品「<strong>{title}</strong>」をご紹介します。</p>
<p>日々の暮らしをより豊かに、そして快適にしてくれる機能が満載のこの商品。実際にどのような魅力があるのか、詳細を解説します！</p>

{image_html}

<h3>注目のスペックと主な特徴</h3>
<p>まずは、このアイテムの素晴らしいポイントを整理してみましょう。</p>
<ul>
    {features_html}
</ul>
<p>特筆すべきは、その圧倒的なコストパフォーマンス。これだけの機能が揃って、現在の価格は <strong>{price}</strong> となっています。</p>

<h3>どんな人におすすめ？</h3>
<p>この商品は、以下のような悩みを抱えている方に特におすすめです。</p>
<ul>
    <li>日常のちょっとした不便を解消し、スマートな生活を送りたい方</li>
    <li>機能性とデザイン性を両立したガジェットを探している方</li>
    <li>大切な人へのプレゼントや、自分へのご褒美を探している方</li>
</ul>

<h3>まとめ：今すぐ手に入れて生活をアップグレードしよう！</h3>
<p>「{title}」は、クオリティの高さと実用性を兼ね備えた、今まさに手に入れるべき極上の一品です。</p>
<p>人気商品のため、在庫切れやセール終了になる前にぜひチェックしてみてください！</p>

<div style="text-align: center; margin: 30px 0;">
    <a href="{url}" style="display: inline-block; background: #FF9900; color: #fff; padding: 15px 30px; font-size: 18px; font-weight: bold; text-decoration: none; border-radius: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.15); transition: background 0.3s;">
        Amazonで「{title}」を詳しく見る 🛒
    </a>
</div>
"""
