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
        clean_title = item.get("clean_title", title)
        features = "\n".join([f"- {f}" for f in item.get("features", [])])
        price = item.get("price", "")
        url = item.get("url", "")

        prompt = f"""以下のAmazonの商品情報を元に、ブログ「はてなブログ」に投稿するための、高品質で自然かつ詳細なレビュー・紹介記事を執筆してください。
読者が購入のメリット・デメリットを具体的にイメージできるように、各機能の解説を交えて、十分なボリューム（1000文字〜1500文字程度）で書いてください。

【商品名】: {title}
【価格】: {price}
【主な特徴】:
{features}
【商品検索URL】: {url}

【執筆の構成（厳格に以下の章立てにしてください）】:
## 1. はじめに：なぜ今この商品が注目されているのか？
（商品のターゲット層や、現代社会の課題解決について語ってください）

## 2. デザインと携帯性：洗練されたスタイルと使いやすさ
（サイズ感や持ち運びやすさ、見た目のプレミアム感について詳しく説明してください）

## 3. 実力検証：使ってわかった圧倒的なパフォーマンス
（主な特徴に記載されている機能が、日常でどのように役立つかを徹底解説してください）

## 4. 本音でレビュー：メリットと購入前に知っておきたい注意点
（良い点だけでなく、客観的な視点から気になる点も解説してください）

## 5. まとめ：どんな人におすすめ？
（この商品を購入すると最も恩恵を受けるユーザー像を提案してください）

【執筆の厳格なルール（最優先）】:
1. ブログ記事の**本文のみ**を出力してください。挨拶文（「承知しました」「以下が記事です」など）や、記事の解説、まとめのアドバイス（「以上のように、自然な言葉遣い〜」「購入につなげることができます」など）は**絶対に1文字も出力しないでください**。記事の最後は「ぜひチェックしてみてください！」などの読者へのメッセージで終了させてください。
2. 「アフィリエイト」「アフィリンク」「誘導」「広告」といった、読者に商業的な意図を直接感じさせる言葉は**見出し・本文含め、絶対に記事内に出力しないでください**。
3. 記事はMarkdown（マークダウン）形式で執筆してください。見出しは「## 」「### 」を使用し、箇条書きは「- 」を使用してください。
4. 商品リンクは、文末付近に自然な形で `[Amazonで「{clean_title}」の価格やクチコミをチェックする]({url})` のようにMarkdown of the リンク記法で埋め込んでください。
"""

        if self.model is None or self.tokenizer is None:
            return self._generate_fallback_article(item)

        try:
            messages = [
                {
                    "role": "system", 
                    "content": "あなたはプロのモノ系ブロガー・レビューライターです。読者に寄り添った自然で魅力的な日本語を使い、指示された厳格なルールと章構成を完全に守り、余計な挨拶や解説を一切含まないブログ本文のみを出力します。"
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
                max_new_tokens=1500,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]

            response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # --- Robust Post-Processing to remove meta-explanations ---
            response = re.sub(r"^(はい、|承知いたしました。|以下が商品紹介記事です。|以下に記事を出力します。|以下が執筆した記事です。)\s*", "", response)
            
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

            # Convert Markdown to HTML
            import markdown
            html_output = markdown.markdown(response, extensions=['nl2br'])
            return html_output

        except Exception as e:
            print(f"Error during text generation: {e}. Falling back to template-based generation.")
            return self._generate_fallback_article(item)

    def _generate_fallback_article(self, item: Dict[str, Any]) -> str:
        title = item.get("title", "")
        clean_title = item.get("clean_title", title)
        features_list = item.get("features", [])
        
        # Format feature bullet points with premium emojis
        features_html = ""
        for f in features_list:
            parts = f.split(":", 1)
            if len(parts) == 2:
                features_html += f"<li><strong>✨ {parts[0].strip()}:</strong> {parts[1].strip()}</li>"
            else:
                features_html += f"<li><strong>✨ 特徴:</strong> {f}</li>"
                
        price = item.get("price", "")
        url = item.get("url", "")
        
        image_html = ""
        if item.get("image_url"):
            image_html = f"""
            <div style="text-align: center; margin: 30px 0;">
                <img src="{item.get('image_url')}" alt="{clean_title}" style="max-width: 100%; height: auto; border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.08); transition: transform 0.3s ease;">
                <p style="font-size: 13px; color: #888; margin-top: 8px;">(画像出典: Amazon)</p>
            </div>
            """

        # Generate a high-volume, premium quality fallback review article
        return f"""
<div style="font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', sans-serif; line-height: 1.8; color: #333; max-width: 700px; margin: 0 auto;">

    <p>こんにちは！ガジェットと暮らしのモノ選びを楽しむライフスタイルブログへようこそ。</p>
    <p>現代の生活において、私たちの周りは多くのデジタルツールやスマートなガジェットで溢れています。しかし、そのすべてが「本当に私たちの生活を豊かにし、快適にしてくれるか」というと、そうではないこともありますよね。</p>
    <p>今回ピックアップしてご紹介するのは、現在SNSや各種ECサイトで爆発的な支持を集め、レビューでも絶賛の嵐が巻き起こっている大注目のプロダクト、<strong>「{title}」</strong>です！</p>
    <p>このアイテムがなぜこれほどまでに多くの人々を魅了し、暮らしの定番アイテムとなっているのか。その魅力と実力、性能を徹底的に解き明かしていきます。</p>

    {image_html}

    <h2 style="border-left: 5px solid #FF9900; padding-left: 15px; margin-top: 40px; margin-bottom: 20px; font-size: 22px;">1. なぜ今この商品が注目されているのか？</h2>
    <p>日々の暮らしやオフィスワーク、外出先でのアクティビティなど、あらゆるシーンで私たちは小さなストレスに直面しています。重い機材の持ち歩きや、充電切れの心配、操作性の悪さなど、どれも「少しの我慢」で済ませてしまいがちです。</p>
    <p><strong>「{clean_title}」</strong>は、まさにそうした日常の「ちょっとした不便」をスマートに解決するために開発されました。最先端の設計と洗練された使い勝手を両立させることで、単なるツールを超えた「手放せないパートナー」としての地位を確立しています。価格は<strong>{price}</strong>となっており、その実力と体験価値を考えれば、非常に高いコストパフォーマンスを誇っていると言えます。</p>

    <h2 style="border-left: 5px solid #FF9900; padding-left: 15px; margin-top: 40px; margin-bottom: 20px; font-size: 22px;">2. デザインと携帯性：洗練されたスタイル</h2>
    <p>この製品を初めて手にしたときに誰もが驚くのが、無駄を徹底的に削ぎ落としたミニマルな外観デザインです。インテリアや他の持ち物と完璧に調和するスタイリッシュな佇まいは、所有する喜びそのものを満たしてくれます。</p>
    <p>また、軽量かつ極限までコンパクトに設計されているため、バッグの片隅やポケットにも無理なく収まります。「機能性が高い製品は大きくて重い」というこれまでの常識を覆し、必要なときにすぐそばにある手軽さを実現しています。</p>

    <h2 style="border-left: 5px solid #FF9900; padding-left: 15px; margin-top: 40px; margin-bottom: 20px; font-size: 22px;">3. 実力検証：際立つ特徴と圧倒的メリット</h2>
    <p>それでは、具体的にどのような性能を持っているのか、この商品の誇るべき強みを詳しく見ていきましょう。</p>
    
    <ul style="list-style-type: none; padding-left: 0; margin: 20px 0;">
        {features_html}
    </ul>
    
    <p>これらの機能がただスペックシート上に存在するだけでなく、実際の使用感においても見事に調和して機能します。使えば使うほど、メーカーの開発チームがユーザーの実際の行動パターンを研究し尽くして設計したことが伝わってきます。</p>

    <h2 style="border-left: 5px solid #FF9900; padding-left: 15px; margin-top: 40px; margin-bottom: 20px; font-size: 22px;">4. 本音でレビュー：購入前に知っておきたいポイント</h2>
    <p>本音での徹底レビューとして、良い面だけでなく、あえて気になる点や注意すべきポイントについても触れておきます。</p>
    <p>この製品は極めて完成度が高いものの、その高い性能を引き出すためには、適切な接続環境やセットアップが必要です。また、シンプルさを追求した結果、複雑なマニュアル設定を行いたい上級ユーザーにとっては、少々シンプルすぎると感じる部分もあるかもしれません。しかし、これらは「誰もが直感的に、失敗なく快適に使える」という最大のメリットの裏返しでもあります。</p>

    <h2 style="border-left: 5px solid #FF9900; padding-left: 15px; margin-top: 40px; margin-bottom: 20px; font-size: 22px;">5. まとめ：どんな人におすすめ？</h2>
    <p><strong>「{clean_title}」</strong>は、以下のような悩みをお持ちの方に自信を持っておすすめできる製品です。</p>
    <ul style="padding-left: 20px; margin: 15px 0;">
        <li>日々の生活や仕事を効率化し、スマートにアップデートしたい方</li>
        <li>デザインと機能性、どちらも妥協したくないこだわり派の方</li>
        <li>持ち物をできるだけ減らし、ミニマルで快適な移動を行いたい方</li>
    </ul>
    <p>これ一つを取り入れるだけで、あなたの毎日が驚くほど快適に、そして少しだけ特別なものに変わるはずです。</p>
    <p>人気アイテムのため、タイミングによっては在庫が少なくなっていることもあります。気になった方は、ぜひ以下のリンクから詳細やレビューをチェックしてみてください！</p>

    <div style="text-align: center; margin: 40px 0 20px 0;">
        <a href="{url}" style="display: inline-block; background: #FF9900; color: #fff; padding: 16px 32px; font-size: 18px; font-weight: bold; text-decoration: none; border-radius: 30px; box-shadow: 0 4px 15px rgba(255,153,0,0.3); transition: all 0.3s ease; text-align: center;">
            Amazonで「{clean_title}」を見る 🛒
        </a>
        <p style="font-size: 12px; color: #666; margin-top: 10px;">※上記リンク先から現在の販売価格や在庫状況、実際のユーザー評価を確認できます。</p>
    </div>

</div>
"""


