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
4. 商品リンクは、文末付近に自然な形で `[Amazonで「{clean_title}」の価格やクチコミをチェックする]({url})` のようにMarkdownのリンク記法で埋め込んでください。
"""

        # Trial order of Free LLM APIs
        generators = [
            ("Gemini API (Free Tier)", self._generate_with_gemini),
            ("GitHub Models API (Free for Actions/PAT)", self._generate_with_github_models),
            ("OpenRouter Free API", self._generate_with_openrouter),
            ("Hugging Face API (Free Tier)", self._generate_with_huggingface),
            ("Pollinations AI Free (No Key Required)", self._generate_with_pollinations),
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
                raw_article = f"""## 1. はじめに：なぜ今この商品が注目されているのか？
これはローカル開発環境でのドライラン検証用のテスト記事です。現在、すべてのオンライン無料LLM APIがレート制限またはキー未設定のため利用できませんでした。

## 2. デザインと携帯性：洗練されたスタイルと使いやすさ
この製品は優れたデザインとコンパクトさを兼ね備えています。

## 3. 実力検証：使ってわかった圧倒的なパフォーマンス
テスト特徴1、特徴2、特徴3により、非常に高いレベルの実用性を誇ります。

## 4. 本音でレビュー：メリットと購入前に知っておきたい注意点
デメリットとしては、オンラインLLM接続が切れている場合に自動投稿ができない点が挙げられます。

## 5. まとめ：どんな人におすすめ？
この検証テキストはローカルでのアイキャッチ画像や投稿プロセスの疎通確認用です。
[Amazonで「{clean_title}」の価格やクチコミをチェックする]({url})
ぜひチェックしてみてください！"""

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

        # Convert Markdown to HTML for Hatena Blog compatibility
        import markdown
        html_output = markdown.markdown(raw_article, extensions=['nl2br'])
        return html_output

    def _generate_with_gemini(self, prompt: str) -> Optional[str]:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return None
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{
                    "text": "あなたはプロのモノ系ブロガー・レビューライターです。読者に寄り添った自然で魅力的な日本語を使い、指示された厳格なルールと章構成を完全に守り、余計な挨拶や解説を一切含まないブログ本文のみを出力します。\n\n" + prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2000
            }
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            try:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            except KeyError:
                return None
        else:
            print(f"Gemini API returned status {resp.status_code}: {resp.text}")
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
                {"role": "system", "content": "あなたはプロのモノ系ブロガー・レビューライターです。指示されたルールを厳格に守り、日本語で前置き・後書きなしでブログ本文のみを出力してください。"},
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
                {"role": "system", "content": "あなたはプロのモノ系ブロガー・レビューライターです。指示された厳格なルールを守り、余計な解説を一切含まない日本語ブログ本文のみを出力します。"},
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
            "inputs": f"<|im_start|>system\nあなたはプロのモノ系ブロガー・レビューライターです。日本語で余計な前置きや後書きなしに、本文のみを出力します。<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n",
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

    def _generate_with_pollinations(self, prompt: str) -> Optional[str]:
        """Pollinations AIのテキスト生成。異なるモデルでPOSTリトライして429を回避します。"""
        url = "https://text.pollinations.ai/"
        
        # Try different free models on Pollinations to spread load and avoid 429
        models = ["openai", "qwen", "mistral"]
        
        for attempt, model in enumerate(models):
            payload = {
                "messages": [
                    {"role": "system", "content": "あなたはプロのモノ系ブロガー・レビューライターです。日本語で前置き・後書きなしでブログ本文のみを出力してください。"},
                    {"role": "user", "content": prompt}
                ],
                "model": model
            }
            try:
                print(f"Trying Pollinations AI POST (model: {model}, attempt: {attempt+1})...")
                resp = requests.post(url, json=payload, timeout=25)
                if resp.status_code == 200 and len(resp.text.strip()) > 300:
                    return resp.text
                elif resp.status_code == 429:
                    print(f"Pollinations AI {model} returned 429. Waiting {attempt+2}s before trying next model...")
                    time.sleep(attempt+2)
                else:
                    print(f"Pollinations AI {model} returned status {resp.status_code}")
            except Exception as e:
                print(f"Pollinations POST attempt for {model} failed: {e}")
            
        return None
