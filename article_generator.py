import os
import re
import requests
import json
import time
import random
from typing import Dict, Any, Optional, Tuple

class ArticleGenerator:
    def __init__(self, model_id: str = ""):
        pass

    def load_model(self):
        print("ArticleGenerator: Initialized using online free API router.")
        pass

    def generate_review_article(self, item: Dict[str, Any]) -> Tuple[str, str, str]:
        """
        Gemini などの LLM を用いて、
        (title, description_html, content_html) を生成して返す。
        """
        title = item.get("title", "")
        clean_title = item.get("clean_title", title)
        features = "\n".join([f"- {f}" for f in item.get("features", [])])
        price = item.get("price", "")
        caption = item.get("caption", "")

        prompt = f"""あなたは月間数百万PVを集める超人気商品レビューメディアのプロ編集長です。
以下の商品情報を元に、読者が検索結果・SNSから流入した瞬間に心を掴まれ、思わず購入したくなる記事を作成してください。

【対象商品情報】
正式商品名: {title}
製品名略称: {clean_title}
価格: {price}
特徴・詳細:
{caption}
{features}

【★極めて重要なセールス・執筆戦略（購入心理の先回りカバー）】
購入を検討する顧客が心の中で抱く「買わない理由（迷いや懸念・不安など）を10個」あらかじめ深く想定してください。
（例：価格に見合うか、使いこなせるか、手入れや保管が面倒ではないか、耐久性や品質は大丈夫か、サイズ感や置き場所、類似品で十分ではないか、自分に本当に必要か、後悔しないか、初期設定や扱いが難しくないか、家族や周囲の反応など）
そして、それら10個の不安や迷いを、先回りして綺麗に解消・カバーする魅力的な文章を本文の中にさりげなく織り込んでください。

※※【厳格な禁止事項】※※
記事内に「買わない理由」「顧客が躊躇する理由」「デメリット10選」「買わない理由を解消」といった直接的な言葉や見出し、ネガティブな箇条書きは【絶対に書かないでください】。
あくまで読者にとって「自然で魅力的なメリットやベネフィット、安心できる使い心地」として美しく昇華し、読者が疑問を抱く前に自然と不安が晴れて欲しくなる、エレガントで説得力のあるセールス文章に仕上げてください。AI臭い定型文や使い回しテンプレートは一切排除してください。

【プロセールス・反論処理（買わない理由の先回り解消）の極意（最重要）】
購入を検討する顧客が「買わない理由・躊躇する心理」を必ず水面下で10個（価格への躊躇、サイズ・置き場所、使いこなせるか、耐久性・手入れの手間、類似品・代替品との違い、今買う理由の不足、失敗したくない不安など）想定してください。
そして、それらの懸念・不安をすべて覆して解消する魅力や根拠、安心材料を、本文の自然な流れの中にさりげなく散りばめてください。
※注意（厳格厳守）：
- 記事内に「買わない理由」「デメリット10選」「購入をためらう理由」などのネガティブな直接的表現・見出し・項目立てをすることは【絶対に禁止】です。
- あくまで「魅力・メリット・使うことで得られる至福の体験・使い勝手の良さ」として美しく昇華し、読者が疑問を抱く前にスッと納得して背中を押される上品で洗練されたセールス文章を構築してください。

【★アプリ再検索・離脱防止のリンク誘導戦略（最重要ルール）】
読者が「なるほど、あとでいつものショッピングアプリ（Amazon/楽天/Yahoo!等）で検索して買おう」と離脱するスキを一切与えないでください。
- 記事本文や小見出しで、フル商品名や確定価格（〇〇円）、具体的なセール値引き額・特典内容を【すべて書ききってネタバレさせることは厳禁】です。
- 製品の具体的な型番・品番（例: 「型番: ABC-123」や「モデル〇〇」等）は記載しても構いませんが、正式名称や価格はあえて伏せ、「このクラスの逸品」「今注目を集める最新モデル」のように製品の圧倒的魅力やベネフィットのみを情熱的に伝えてください。
- 「現在の在庫状況・最新のタイムセール価格・限定特典やクーポンの有無は、下記の公式商品ページにてリアルタイムで確認できます」のように、読者が【今すぐリンク先を確認しなければならない理由】を自然に残し、リンク先へとスムーズに誘導してください。

【---TITLE---の生成ルール（最重要・厳格遵守）】
商品名（ブランド名やメーカー名、製品名、ポケットカイロ等の一般名詞の羅列）をそのままタイトルに並べるのは【厳禁】です。
「読者が日常で得られる圧倒的なベネフィット・感情を揺さぶる体験・劇的な変化」に焦点を当てた、思わずクリックして読みたくなる魅力的なタイトルを作成してください。
※「スヌーピー」「ハローキティ」等の超有名キャラクターや「書籍・漫画の作品名」以外は、一般的なブランド名（Coolean等）や型番・製品名はタイトルに入れず、手に入る体験や価値を主役にしてください。
（悪い例：10秒で包み込む極上の温もり Coolean POMI ポケットカイロ）
（良い例：かじかむ指先が10秒でとろける。冬の通勤が劇的に変わる手のひらサイズの極上温もり）
※「【本音レビュー】」「【正直レビュー】」「【話題】」「【速報】」「まとめ」などの使い回しテンプレート接頭辞は【絶対に使用禁止】です。
※30〜40文字程度の、自然で洗練された日本語のタイトルを1つだけ出力してください。

【必須の出力フォーマット（厳格遵守）】
必ず以下のセクション区切り記号を使って出力してください。

---TITLE---
読者の感情を動かし、日常が劇的に変わるベネフィットがひと目で突き刺さる【完全独自のブログ記事タイトル】を出力。
ブランド名や型番をただ並べるのではなく、そのアイテムがもたらす最高の体験を言葉にしてください。

---DESCRIPTION---
検索エンジンやブログ一覧の「ディスクリプション（抜粋）」として表示される、記事冒頭のリード文（3行・約100〜130文字）。
※記号の羅列やアフィリエイト定型文は一切書かず、誰のどんな悩みを解決するのか、商品の最大の見どころは何かを最初の3行で魅力的に伝えてください。

---CONTENT---
読者が引き込まれる本文HTML（800〜1400文字程度）。
見出し（<h3>）、段落（<p>）、箇条書き（<ul><li>）、太字（<b>）を使って美しく整形してください。
読者の共感・リアルな使い心地・日常が劇的に良くなるベネフィット・購入時の迷いを払拭する安心感・背中を押す購入推奨を感情豊かに執筆してください。
前置きや挨拶、解説文は一切不要です。
"""

        generators = [
            ("Gemini API (Free Tier)", self._generate_with_gemini),
            ("Groq API (Llama 3.3 70B)", self._generate_with_groq),
            ("GitHub Models API", self._generate_with_github_models),
            ("OpenRouter Free API", self._generate_with_openrouter),
        ]

        raw_text = None
        for name, gen_fn in generators:
            try:
                print(f"Attempting article generation with {name}...")
                res = gen_fn(prompt)
                if res and len(res.strip()) > 300:
                    raw_text = res.strip()
                    print(f"Successfully generated article using {name}!")
                    break
            except Exception as e:
                print(f"Error calling {name}: {e}. Trying next fallback...")

        parsed_title, parsed_desc, parsed_content = self._parse_generated_output(raw_text, clean_title, title, price)
        return parsed_title, parsed_desc, parsed_content

    def _parse_generated_output(self, raw_text: Optional[str], clean_title: str, title: str, price: str) -> Tuple[str, str, str]:
        """LLMの出力を (title, description, content) にパース。万一パース失敗時のフォールバックも完備。"""
        if raw_text and "---TITLE---" in raw_text and "---DESCRIPTION---" in raw_text and "---CONTENT---" in raw_text:
            try:
                parts = raw_text.split("---TITLE---")[1].split("---DESCRIPTION---")
                gen_title = parts[0].strip().replace("\n", " ")
                gen_title = re.sub(r'^(TITLE:|タイトル[:：]|【.*?】)\s*', '', gen_title).strip()
                gen_title = re.sub(r'\s+', ' ', gen_title)

                subparts = parts[1].split("---CONTENT---")
                gen_desc = subparts[0].strip()
                gen_desc = re.sub(r'^(DESCRIPTION:|ディスクリプション[:：])\s*', '', gen_desc).strip()

                gen_content = subparts[1].strip()
                gen_content = re.sub(r'^(CONTENT:|本文[:：])\s*', '', gen_content).strip()

                # タイトルのクレンジング（途切れ防止: 単純スライスによる中途半端な切断を禁止）
                if len(gen_title) > 42:
                    # 句読点やスペースなど意味の区切りがある場合のみ適切にトリム、なければそのまま活かす
                    for sep in ['！', '!', '？', '?', ' ', '　', '。']:
                        if sep in gen_title[:38]:
                            idx = gen_title[:38].rfind(sep)
                            if idx > 15:
                                gen_title = gen_title[:idx+1].strip()
                                break
                if not gen_title:
                    gen_title = "日常のストレスが消える！一度使うと手放せない感動の体験を徹底解説"

                # ディスクリプションのHTML整形（改行を反映）
                desc_html = f'<p class="entry-lead" style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 24px;">{gen_desc}</p>'

                return gen_title, desc_html, gen_content
            except Exception as e:
                print(f"Error parsing LLM output: {e}. Falling back to default layout.")

        # フォールバック生成（手動テンプレートでも商品名ベタ貼りを排除し魅力・ベネフィット訴求）
        fallback_title = "日々の暮らしが劇的に快適になる！使って実感した極上の使い心地"
        fallback_desc = f'<p class="entry-lead" style="font-size: 16px; line-height: 1.8; color: #333; margin-bottom: 24px;">実際に使ってわかったリアルな魅力と感動の理由をお届け。日々の暮らしのストレスを減らし、QOLを劇的に上げてくれる今注目の逸品です。</p>'
        fallback_content = f"""<h3>実際に使って感動した「{clean_title}」の圧倒的な使い心地</h3>
<p>日々の生活や作業のなかで、「もっと使いやすいものはないか」と探している方にぜひ試していただきたいのがこのアイテムです。細部まで使い勝手が計算されており、手に取るたびに満足感を味わえます。</p>

<h3>購入前にチェックしておきたいポイントと魅力</h3>
<ul>
  <li><b>直感的な使いやすさ</b>：余計な手間がかからず、届いたその日からすぐに快適さを実感できます。</li>
  <li><b>洗練されたデザイン</b>：どんなお部屋やデスクにも自然に馴染むスマートな外観。</li>
  <li><b>抜群のコストパフォーマンス</b>：価格以上のクオリティで、長く愛用できる仕上がりです。</li>
</ul>

<h3>今すぐチェックして損はないイチオシ商品</h3>
<p>セール期間やポイントアップ期間は特に注文が集中し、在庫が薄くなることも珍しくありません。気になっている方は、ぜひ楽天市場の公式取扱店で最新の価格と在庫をチェックしてみてください！</p>"""
        return fallback_title, fallback_desc, fallback_content

    def _generate_with_gemini(self, prompt: str) -> Optional[str]:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        
        models = [
            "gemini-3.5-flash-lite",
            "gemini-3.5-flash",
            "gemini-3.1-flash-lite",
            "gemini-3-flash",
            "gemini-3.6-flash",
            "gemini-3.7-flash",
            "gemini-2.5-pro",
            "gemini-3.1-pro"
        ]
        headers = {"Content-Type": "application/json"}
        for model_name in models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": "あなたはプロの商品レビュー編集者です。指示された厳格な出力フォーマットを守り、日本語で指定セクションのみを出力してください。\n\n" + prompt
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.8,
                        "maxOutputTokens": 3000
                    }
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=20)
                if resp.status_code == 200:
                    data = resp.json()
                    candidate = data.get("candidates", [{}])[0]
                    parts = candidate.get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts if p.get("text")).strip()
                    if text and len(text) > 200 and "---TITLE---" in text:
                        print(f"Successfully generated article via Gemini API ({model_name}).")
                        return text
            except Exception as e:
                print(f"Gemini API ({model_name}) error: {e}")
        return None

    def _generate_with_groq(self, prompt: str) -> Optional[str]:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return None
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
        for model in models:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "あなたはプロの商品レビュー編集者です。指示されたフォーマット（---TITLE---, ---DESCRIPTION---, ---CONTENT---）を厳格に守り日本語で出力してください。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.8
            }
            try:
                res = requests.post(url, headers=headers, json=payload, timeout=20)
                if res.status_code == 200:
                    text = res.json()["choices"][0]["message"]["content"]
                    if text and len(text.strip()) > 200 and "---TITLE---" in text:
                        return text.strip()
            except Exception as e:
                print(f"Groq ({model}) error: {e}")
        return None

    def _generate_with_github_models(self, prompt: str) -> Optional[str]:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not token:
            return None
        url = "https://models.inference.ai.azure.com/chat/completions"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "あなたはプロの商品レビュー編集者です。---TITLE---, ---DESCRIPTION---, ---CONTENT---の区切りを守り日本語で出力してください。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.8
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception:
            pass
        return None

    def _generate_with_openrouter(self, prompt: str) -> Optional[str]:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            return None
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "google/gemma-2-9b-it:free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception:
            pass
        return None
