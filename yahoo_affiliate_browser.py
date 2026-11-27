import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

# ユーザーデータ（プロファイル）の保存先（共通ディレクトリ）
USER_DATA_DIR = os.path.expanduser("~/.config/yahoo_affiliate_browser")

class YahooAffiliateLinkExtractor:
    """
    Playwrightで保存されたChromeプロファイルを使用し、
    Yahoo!ショッピングの商品ページから公式アフィリエイトリンクを取得するクラス
    """
    def __init__(self, user_data_dir: str = USER_DATA_DIR, headless: bool = True):
        self.user_data_dir = user_data_dir
        self.headless = headless
        Path(self.user_data_dir).mkdir(parents=True, exist_ok=True)

    def login_interactively(self):
        """初回のみ実行：ログイン用ブラウザを可視ウィンドウで立ち上げ、手動ログインを待機"""
        print("\n=======================================================")
        print("【Yahoo!ショッピング ログインセットアップ】")
        print("ブラウザウィンドウが開きます。")
        print("Yahoo! JAPAN IDでログインを完了してください。")
        print("ログイン後、ブラウザを閉じずにターミナルで Enter キーを押してください。")
        print("=======================================================\n")
        
        with sync_playwright() as p:
            # 一般的なChromeのユーザーエージェント
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=False,
                channel="chrome",  # Macにインストールされている実Chromeエンジンを使用
                viewport={"width": 1280, "height": 800},
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.new_pages[0] if context.new_pages else context.new_page()
            page.goto("https://shopping.yahoo.co.jp/")
            
            input("ログインが完了したら、ここに Enter を押してください...")
            
            # 状態保存のために少し待機
            time.sleep(2)
            context.close()
            print("✓ ログインプロファイルを正常に保存しました！")

    def get_affiliate_url(self, item_url: str, timeout_sec: int = 15) -> str:
        """
        商品URLを開いて「共有」→「アフィリエイトリンク取得」を実行してURLを返す。
        万が一取得できなかった場合は元のURLをフォールバックとして返す。
        """
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                channel="chrome",
                viewport={"width": 1280, "height": 800},
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = context.new_pages[0] if context.new_pages else context.new_page()

            # クリップボード読み取り権限の許可
            context.grant_permissions(["clipboard-read", "clipboard-write"])

            try:
                print(f"[Browser] Navigating to: {item_url}")
                page.goto(item_url, wait_until="domcontentloaded", timeout=timeout_sec * 1000)
                page.wait_for_timeout(2000)

                # 1. 「共有」ボタンやアフィリエイトリンクボタンを探す
                # Yahoo!ショッピングのUIパターン:
                # - 「共有」ボタン、シェアアイコン
                # - テキスト「共有」または aria-label に共有を含む要素
                share_btn = None
                selectors = [
                    'button:has-text("共有")',
                    'button[aria-label*="共有"]',
                    'a:has-text("共有")',
                    '[data-test="share-button"]',
                    'button:has-text("シェア")',
                    'button[aria-label*="シェア"]'
                ]
                for sel in selectors:
                    loc = page.locator(sel)
                    if loc.count() > 0 and loc.first.is_visible():
                        share_btn = loc.first
                        break

                if share_btn:
                    print("[Browser] Found share button. Clicking...")
                    share_btn.click()
                    page.wait_for_timeout(1500)

                    # 2. アフィリエイトリンクタブや切り替えの確認
                    aff_tab = page.locator('button:has-text("アフィリエイト"), [role="tab"]:has-text("アフィリエイト")')
                    if aff_tab.count() > 0 and aff_tab.first.is_visible():
                        aff_tab.first.click()
                        page.wait_for_timeout(1000)

                    # 3. 「リンクをコピー」ボタンをクリック
                    copy_btn = page.locator('button:has-text("リンクをコピー"), button:has-text("コピー")')
                    if copy_btn.count() > 0 and copy_btn.first.is_visible():
                        copy_btn.first.click()
                        page.wait_for_timeout(1000)

                        # クリップボードからURLを取得
                        clipboard_text = page.evaluate("navigator.clipboard.readText()")
                        if clipboard_text and "yahoo" in clipboard_text:
                            print(f"[Browser] Successfully obtained affiliate link: {clipboard_text}")
                            context.close()
                            return clipboard_text.strip()

                    # もしモーダル内に直接inputやtextareaでURLが表示されている場合
                    inputs = page.locator('input[value*="yahoo"], textarea[value*="yahoo"]')
                    if inputs.count() > 0:
                        val = inputs.first.get_attribute("value")
                        if val:
                            print(f"[Browser] Extracted URL from input field: {val}")
                            context.close()
                            return val.strip()

                print("[Browser] Share/Affiliate button pattern not matched directly.")
                
            except Exception as e:
                print(f"[Browser] Error extracting affiliate URL: {e}")
            finally:
                context.close()

        print("[Browser] Fallback to original URL.")
        return item_url

if __name__ == "__main__":
    extractor = YahooAffiliateLinkExtractor()
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        extractor.login_interactively()
    else:
        test_url = sys.argv[1] if len(sys.argv) > 1 else "https://store.shopping.yahoo.co.jp/"
        url = extractor.get_affiliate_url(test_url)
        print("Result URL:", url)
