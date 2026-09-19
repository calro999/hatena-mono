import os
import re
import requests
import json
import time
import urllib.parse
from typing import Dict, Any, Optional, List

class ArticleGenerator:
    def __init__(self, model_id: str = ""):
        pass

    def load_model(self):
        print("ArticleGenerator: Initialized using online free API router (No local models loaded).")
        pass

    def generate_review_article(self, item: Dict[str, Any]) -> str:
        title = item.get("title", "")
        clean_title = item.get("clean_title", title)
        features = "\n".join([f"- {f}" for f in item.get("features", [])])
        price = item.get("price", "")
        caption = item.get("caption", "")

        prompt = f"""あなたはモノやガジェットに並々ならぬ偏愛を持つ個人ブロガーです。
以下の商品について、読者が思わず即クリックしたくなるような「熱量とリアリティに満ちた本音レビュー記事」を執筆してください。

【商品名】: {clean_title}（正式名: {title}）
【価格】: {price}
【特徴・スペック概要】:
{caption}
{features}

=======================================================
【記事の3段構成ルール（早期クリック＆SEO特化型）】
=======================================================
以下の3部構成を必ず踏まえて、見出し（##, ###）と本文を執筆してください。

◆ 第1部：前半【結論ファースト＆即クリック促進（ファーストビュー直下）】
- 挨拶や前置きは一切不要。「結論から言うと、これは今年買って一番の当たり」「迷っているなら今すぐチェックして損はない」といったインパクトのある本音からスタートしてください。
- 自分がなぜこれを買うに至ったのかのリアルな日常の悩み・ストーリーと、導入して一瞬で生活が変わった衝撃（ベネフィット）を熱く語ってください。
- 「特に◯◯で悩んでいる人には即効性がある」と結論づけ、前半の段階で読者が「今すぐ楽天市場で詳細を見たい！」と思わせる強烈なフックを作ってください。

◆ 第2部：中盤【購入検討者向け・リアルな使い倒しレビュー（偏愛と本音）】
- スペック表の単なる読み上げは厳禁。実際に数週間〜数ヶ月使い倒したからこそ分かる「ここが圧倒的に良い！」「この使い心地は沼」という独自のこだわりポイントを詳しく解説してください。
- 読者の信頼を勝ち取るため、「正直ここは惜しい」「こういう人には合わないかも」というリアルなデメリット・注意点も包み隠さず本音で明かしてください。
- 「どんな人におすすめか」「日々の生活がどう快適になるか」を具体的に描写してください。

◆ 第3部：後半【検索流入（SEO）特化＆疑問解消】
- 検索ユーザーがGoogleやYahooで検索しそうな疑問に応える見出し（例: 「気になる使い勝手や耐久性は？」「他社製品や旧型と迷ったらどっち？」「失敗しない選び方」など）を2〜3個設けてください。
- 検索キーワード（使い方、評価、口コミ、比較、最安値、ポイント還元など）を自然に含めながら、読者の最後の不安を解消してください。
- 記事の最後は「在庫切れや価格変更の前に、まずは楽天市場で現在の価格やレビューをチェックしてみてください！」といった、読者の背中を自然に押すメッセージで締めくくってください。

=======================================================
【執筆の厳格な禁止・必須ルール（最優先）】
=======================================================
1. **AI臭さの完全排除**:
   - 「〜をご紹介します」「〜と言えるでしょう」「〜はいかがでしょうか」「〜の特徴を持っています」といった機械的な解説口調・テンプレート構文は**絶対に使用禁止**です。
   - 一人称（僕/私）で、友人に「これマジで良いから使ってみて」と熱弁するような、感情と体温のある自然な人間らしい文体で書いてください。
2. **本文のみ出力**:
   - 挨拶文（「承知しました」「以下が記事です」など）やメタ解説、アドバイス等は**1文字も出力しないでください**。
3. **リンク・URLの直接記述禁止**:
   - システム側で最適な位置に大迫力のCTAボタンと商品カードを自動挿入するため、本文中にURLやMarkdownリンク記法（`[text](url)`）は**含めないでください**。
4. **商業用語の排除**:
   - 「アフィリエイト」「誘導」「広告」などの単語は記事内に一切出さないでください。
5. **フォーマット**:
   - Markdown形式（見出しは `## `, `### `、箇条書きは `- `、強調は `**`）で出力してください。
"""

        # Trial order of LLM APIs
        generators = [
            ("Gemini API (Free Tier)", self._generate_with_gemini),
            ("Groq API (Llama 3.3 70B)", self._generate_with_groq),
            ("GitHub Models API (Free for Actions/PAT)", self._generate_with_github_models),
            ("OpenRouter Free API", self._generate_with_openrouter),
            ("Hugging Face API (Free Tier)", self._generate_with_huggingface),
        ]

        raw_article = None
        for name, gen_fn in generators:
            try:
                print(f"Attempting article generation with {name}...")
                res = gen_fn(prompt)
                if res and len(res.strip()) > 300:
                    raw_article = res.strip()
                    print(f"Successfully generated article using {name}!")
                    break
                else:
                    print(f"{name} returned empty or too short response. Trying next fallback...")
            except Exception as e:
                print(f"Error calling {name}: {e}. Trying next fallback...")

        # If all LLM APIs failed
        if not raw_article:
            if os.environ.get("GITHUB_ACTIONS") == "true":
                raise RuntimeError("All free LLM APIs failed to generate a valid review article in GitHub Actions. Cannot proceed to prevent posting spam templates.")
            else:
                print("WARNING: All free LLM APIs failed or are rate-limited. Since this is a local dry-run, generating dummy review text to verify downstream components.")
                raw_article = f"""## 結論：迷っているなら今すぐ手に入れるべき理由
正直、もっと早く買っておけばよかったと後悔するレベルの完成度でした。「{clean_title}」を導入してから、日々のストレスが激減して作業効率が圧倒的に向上しています。

## 実際に1ヶ月使い倒して気づいた「ここが凄い」ポイント
使ってみて一番感動したのは、細部の使い勝手の良さです。スペック上の数値以上に、手に馴染む質感や直感的な操作性が抜群です。

### ここは惜しい！購入前に知っておくべき注意点
あえて気になる点を挙げるなら、最初は設定に少し慣れが必要なところ。ただ、一度自分好みにセッティングしてしまえば全く気になりません。

## 気になる耐久性や実際の口コミ・選び方の疑問
毎日ガシガシ使っていますが、耐久性や安定感に不安は一切ありません。他社製品と比較してもコスパは頭ひとつ抜けています。

気になった方は、セール期間やポイントアップ中にぜひ楽天市場でチェックしてみてください！"""

        # Post-Processing to clean up LLM meta-explanations
        raw_article = re.sub(r"^(はい、|承知いたしました。|以下が商品紹介記事です。|以下に記事を出力します。|以下が執筆した記事です。)\s*", "", raw_article)
        meta_markers = [
            "以上のように",
            "このように、",
            "自然な言葉遣いと",
            "アフィリエイトリンクへの",
            "読者は商品の魅力を理解し",
            "購入につなげることができます"
        ]
        for marker in meta_markers:
            if marker in raw_article:
                print(f"Truncating AI meta-explanation found at marker: '{marker}'")
                raw_article = raw_article.split(marker)[0].rstrip()

        # Remove duplicate markdown links if generated by LLM
        raw_article = re.sub(r'\[([^\]]+)\]\(https?://[^\)]+\)', r'\1', raw_article)

        # Convert Markdown to HTML for Hatena Blog compatibility
        import markdown
        html_output = markdown.markdown(raw_article, extensions=['nl2br'])
        
        # Force all remaining <a> tags to open in a new tab (target="_blank" rel="noopener noreferrer")
        def add_target_blank(match):
            tag = match.group(0)
            if 'target=' not in tag:
                tag = tag.replace('<a ', '<a target="_blank" rel="noopener noreferrer" ')
            return tag
            
        html_output = re.sub(r'<a\s+[^>]*>', add_target_blank, html_output)
        return html_output

    def _generate_with_groq(self, prompt: str) -> Optional[str]:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return None
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama3-8b-8192"]
        sys_msg = "あなたはモノに並々ならぬこだわりを持つ個人ブロガーです。商品のスペック説明は最小限にし、この商品を導入したことで日常がどう劇的に変わったかというライフスタイルへの変化（ベネフィット）を、熱量と独自の視点で語ってください。他人事の解説調ではなく、書き手の顔が見える一人称の熱い語り口で執筆してください。指示されたルールを厳格に守り、日本語で前置き・後書きなしでブログ本文のみを出力してください。"
        
        for model in models:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": sys_msg},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            try:
                res = requests.post(url, headers=headers, json=payload, timeout=30)
                if res.status_code == 200:
                    text = res.json()["choices"][0]["message"]["content"]
                    if text and len(text.strip()) > 200:
                        return text.strip()
                else:
                    print(f"Groq API ({model}) status: {res.status_code}")
            except Exception as e:
                print(f"Groq API ({model}) error: {e}")
        return None

    def _generate_with_gemini(self, prompt: str) -> Optional[str]:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        
        models = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash-lite",
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3-flash",
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
                            "text": "あなたはモノに並々ならぬこだわりを持つ個人ブロガーです。商品のスペック説明は最小限にし、この商品を導入したことで日常がどう劇的に変わったかというライフスタイルへの変化（ベネフィット）を、熱量と独自の視点で語ってください。他人事の解説調ではなく、書き手の顔が見える一人称の熱い語り口で執筆してください。指示された厳格なルールと章構成を完全に守り、余計な挨拶や解説を一切含まないブログ本文のみを出力します。\n\n" + prompt
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 2000
                    }
                }
                if any(v in model_name for v in ["2.5", "3.", "3-"]):
                    payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}
                resp = requests.post(url, headers=headers, json=payload, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    candidate = data.get("candidates", [{}])[0]
                    parts = candidate.get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts if p.get("text")).strip()
                    if text and len(text) > 200:
                        print(f"Successfully generated article via Gemini API ({model_name}).")
                        return text
                else:
                    print(f"Gemini API ({model_name}) returned status {resp.status_code}: {resp.text[:100]}")
            except Exception as e:
                print(f"Gemini API ({model_name}) error: {e}")
        return None

    def _generate_with_github_models(self, prompt: str) -> Optional[str]:
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not token:
            return None
        
        url = "https://models.inference.ai.azure.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "あなたはモノに並々ならぬこだわりを持つ個人ブロガーです。商品のスペック説明は最小限にし、この商品を導入したことで日常がどう劇的に変わったかというライフスタイルへの変化（ベネフィット）を、熱量と独自の視点で語ってください。他人事の解説調ではなく、書き手の顔が見える一人称の熱い語り口で執筆してください。指示されたルールを厳格に守り、日本語で前置き・後書きなしでブログ本文のみを出力してください。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            try:
                return resp.json()["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                return None
        else:
            print(f"GitHub Models API returned status {resp.status_code}: {resp.text}")
        return None

    def _generate_with_openrouter(self, prompt: str) -> Optional[str]:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            return None
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "google/gemma-2-9b-it:free",
            "messages": [
                {"role": "system", "content": "あなたはモノに並々ならぬこだわりを持つ個人ブロガーです。商品のスペック説明は最小限にし、この商品を導入したことで日常がどう劇的に変わったかというライフスタイルへの変化（ベネフィット）を、熱量と独自の視点で語ってください。他人事の解説調ではなく、書き手の顔が見える一人称の熱い語り口で執筆してください。指示された厳格なルールを守り、余計な解説を一切含まない日本語ブログ本文のみを出力します。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            try:
                return data["choices"][0]["message"]["content"]
            except KeyError:
                return None
        else:
            print(f"OpenRouter API returned status {resp.status_code}: {resp.text}")
        return None

    def _generate_with_huggingface(self, prompt: str) -> Optional[str]:
        api_key = os.environ.get("HF_API_KEY") or os.environ.get("HF_TOKEN")
        if not api_key:
            return None
        
        model_id = "Qwen/Qwen2.5-72B-Instruct"
        url = f"https://api-inference.huggingface.co/models/{model_id}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": f"<|im_start|>system\nあなたはモノに並々ならぬこだわりを持つ個人ブロガーです。商品のスペック説明は最小限にし、この商品を導入したことで日常がどう劇的に変わったかというライフスタイルへの変化（ベネフィット）を、熱量と独自の視点で語ってください。他人事の解説調ではなく、書き手の顔が見える一人称の熱い語り口で執筆してください。日本語で余計な前置きや後書きなしに、本文のみを出力します。<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n",
            "parameters": {
                "max_new_tokens": 1500,
                "temperature": 0.7
            }
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=45)
        if resp.status_code == 200:
            data = resp.json()
            try:
                text = data[0]["generated_text"]
                if "assistant\n" in text:
                    return text.split("assistant\n")[-1]
                return text
            except (KeyError, IndexError):
                return None
        else:
            print(f"Hugging Face API returned status {resp.status_code}: {resp.text}")
        return None
