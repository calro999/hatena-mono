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

        prompt = f"""以下のAmazonの商品情報を元に、ブログ「はてなブログ」に投稿するための、読者に役立つ自然で高品質な商品紹介記事を日本語で執筆してください。

【商品名】: {title}
【価格】: {price}
【主な特徴】:
{features}
【商品ページURL】: {url}

【執筆ルール】:
1. 読者の興味を惹くキャッチーな見出し(H2, H3タグを使用)を作成してください。
2. 「アフィリエイト」「アフィリンク」「誘導」「広告」といった、読者に商業的な意図を直接感じさせる言葉は**絶対に記事内（見出し、目次、本文すべて）に出力しないでください**。
3. 商品リンクへ案内する際は、「詳細はこちら」「Amazonでチェックする」「気になった方はこちらから」など、自然な言葉を使用してください。
4. 商品のメリットだけでなく、実際の利用シーンや、導入することで生活がどのように便利になるかを具体的に解説してください。
5. Markdownの記号（#, ##, ###, *, - など）は一切使用せず、**純粋なHTML形式**（<h2>, <h3>, <p>, <ul>, <li> などのタグ）のみで出力してください。
"""

        if self.model is None or self.tokenizer is None:
            return self._generate_fallback_article(item)

        try:
            messages = [
                {"role": "system", "content": "あなたは優秀なブログライターです。読者の役に立つ自然な言葉遣いで、高品質な商品紹介記事をHTML形式で執筆します。"},
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
            
            # Post-processing to clean up any accidental markdown tags the model might output
            clean_response = response.replace("### ", "<h3>").replace("###", "").replace("## ", "<h2>").replace("##", "")
            return clean_response
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
<h2>生活をより豊かに！大注目の人気アイテム「{title}」をご紹介</h2>
<p>こんにちは！今回は、今ネットやSNSでも高い評価を得ている話題の商品「<strong>{title}</strong>」をご紹介します。</p>
<p>日々の暮らしをより便利に、そして快適にしてくれる機能が満載のこの商品。実際の使い勝手やその魅力について分かりやすく解説します！</p>

{image_html}

<h3>注目のスペックと主な特徴</h3>
<p>このアイテムの素晴らしいポイントをいくつか整理してみましょう。</p>
<ul>
    {features_html}
</ul>
<p>クオリティの高さと実用性を兼ね備えており、現在の価格は <strong>{price}</strong> となっています。</p>

<h3>どのような生活の変化が期待できる？</h3>
<p>この商品を導入することで、日常のちょっとした不便が解消され、よりスマートで効率的な毎日を送ることができます。特に、デザイン性と機能性の両方を妥協したくない方にはぴったりです。</p>

<h3>まとめ：気になる方はお早めにチェック！</h3>
<p>「{title}」は、非常に高い完成度を誇るおすすめの一品です。人気商品のため、気になる方はぜひ詳細をチェックしてみてください。</p>

<div style="text-align: center; margin: 30px 0;">
    <a href="{url}" style="display: inline-block; background: #FF9900; color: #fff; padding: 15px 30px; font-size: 18px; font-weight: bold; text-decoration: none; border-radius: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.15); transition: background 0.3s;">
        Amazonで「{title}」の価格と詳細を見る 🛒
    </a>
</div>
"""
