import os
import re
from typing import Dict, Any

class ArticleGenerator:
    def __init__(self, model_id: str = "Qwen/Qwen2.5-1.5B-Instruct", use_hf_cache: bool = True):
        self.model_id = model_id
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

        prompt = f"""以下のAmazonの商品情報を元に、ブログ「はてなブログ」に投稿するための、高品質で自然な商品紹介記事を執筆してください。

【商品名】: {title}
【価格】: {price}
【主な特徴】:
{features}
【商品ページURL】: {url}

【執筆の厳格なルール（最優先）】:
1. ブログ記事の**本文のみ**を出力してください。挨拶文（「承知しました」「以下が記事です」など）や、記事の解説、まとめのアドバイス（「以上のように、自然な言葉遣い〜」「購入につなげることができます」など）は**絶対に1文字も出力しないでください**。記事の最後は「ぜひチェックしてみてください！」などの読者へのメッセージで終了させてください。
2. 「アフィリエイト」「アフィリンク」「誘導」「広告」といった、読者に商業的な意図を直接感じさせる言葉は**見出し・本文含め、絶対に記事内に出力しないでください**。
3. 記事はMarkdown（マークダウン）形式で執筆してください。見出しは「## 」「### 」を使用し、箇条書きは「- 」を使用してください。
4. 商品リンクは、文末付近に自然な形で `[詳細はこちら]({url})` や `[Amazonで「{title}」をチェックする]({url})` のようにMarkdownのリンク記法で埋め込んでください。
"""

        if self.model is None or self.tokenizer is None:
            return self._generate_fallback_article(item)

        try:
            messages = [
                {
                    "role": "system", 
                    "content": "あなたは優秀なブログライターです。指示されたルールを厳格に守り、挨拶文や解説、余計なメタ発言を一切含まない、ブログの本文のみを出力します。"
                },
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
                temperature=0.6,
                top_p=0.9,
                do_sample=True
            )
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]

            response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # --- Robust Post-Processing to remove meta-explanations ---
            # Remove common starting chat prefixes
            response = re.sub(r"^(はい、|承知いたしました。|以下が商品紹介記事です。|以下に記事を出力します。|以下が執筆した記事です。)\s*", "", response)
            
            # Truncate at common AI metadata/explanation footers
            meta_markers = [
                "以上のように",
                "このように、",
                "自然な言葉遣いと",
                "アフィリエイトリンクへの",
                "読者は商品の魅力を理解し",
                "購入につなげることができます"
            ]
            for marker in meta_markers:
                if marker in response:
                    print(f"Truncating AI meta-explanation found at marker: '{marker}'")
                    response = response.split(marker)[0].rstrip()

            # Convert Markdown to HTML using the python-markdown library
            import markdown
            # Enable linebreaks extension to preserve formatting
            html_output = markdown.markdown(response, extensions=['nl2br'])
            
            return html_output

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
