import os
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

BASE = os.environ.get("APP_URL", "http://localhost:8501")
OUT = Path(__file__).resolve().parent.parent / "public" / "landing"
OUT.mkdir(parents=True, exist_ok=True)

CLIMB_JS = """
(el) => {
  let cur = el;
  for (let i = 0; i < 15 && cur; i++) {
    const r = cur.getBoundingClientRect();
    if (r.width >= 300 && r.height >= 200) return cur;
    cur = cur.parentElement;
  }
  return el;
}
"""


def panel_shot(page, title, fname, settle=2.0):
    """Element-screenshot the panel whose header contains `title`."""
    loc = page.get_by_text(title, exact=False).first
    handle = loc.element_handle()
    root = handle.evaluate_handle(CLIMB_JS)
    time.sleep(settle)
    root.as_element().screenshot(path=str(OUT / fname))
    print("saved", fname)


def add_panel(page, name):
    page.get_by_role("button", name="+ 新增面板").click()
    time.sleep(0.4)
    btn = page.locator("button", has_text=name).last
    btn.click()
    time.sleep(0.8)


def main():
    if sync_playwright is None:
        return
    try:
        with sync_playwright() as p:
            chrome_path = "/usr/bin/chromium" if os.path.exists("/usr/bin/chromium") else None
            browser = p.chromium.launch(
                headless=True,
                executable_path=chrome_path,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            ctx = browser.new_context(
                viewport={"width": 1600, "height": 1000},
                device_scale_factor=2,
                color_scheme="dark",
                locale="zh-TW",
                timezone_id="Asia/Taipei",
            )
            page = ctx.new_page()
            page.goto(BASE)
            print("waiting for live data...")
            time.sleep(16)

            # 1. hero - default dark terminal
            page.screenshot(path=str(OUT / "terminal-dark.png"))
            print("saved terminal-dark.png")

            # link TXFR1 so flash/orders target futures
            try:
                page.get_by_text("TXFR1", exact=True).first.click()
                time.sleep(2)
            except Exception as e:
                print("link TXFR1 failed:", e)

            # 2. AI Agent panel - skills tab then settings
            try:
                add_panel(page, "AI Agent")
                time.sleep(1)
                try:
                    page.get_by_role("button", name="技能", exact=True).click()
                except Exception:
                    pass
                time.sleep(0.6)
                panel_shot(page, "AI Agent", "agent-skills.png")
                page.get_by_role("button", name="設定", exact=True).click()
                time.sleep(0.6)
                panel_shot(page, "AI Agent", "agent-settings.png")
                page.get_by_role("button", name="對話", exact=True).click()
                time.sleep(0.6)
                panel_shot(page, "AI Agent", "agent-chat.png")
            except Exception as e:
                print("agent shots failed:", e)

            # 3. flash order ladder
            try:
                add_panel(page, "閃電下單")
                time.sleep(1)
                en = page.get_by_role("button", name="啟用閃電下單")
                if en.count() > 0:
                    en.first.click()
                    time.sleep(2)
                panel_shot(page, "閃電下單", "flash.png", settle=3)
            except Exception as e:
                print("flash shot failed:", e)

            # 4. grid orders (網格)
            try:
                add_panel(page, "網格")
                time.sleep(1)
                panel_shot(page, "網格", "grid.png")
            except Exception as e:
                print("grid shot failed:", e)

            # 5. sector heatmap
            try:
                add_panel(page, "類股熱力圖")
                time.sleep(1)
                panel_shot(page, "類股熱力圖", "heatmap.png")
            except Exception as e:
                print("heatmap shot failed:", e)

            # 6. option payoff
            try:
                add_panel(page, "選擇權損益圖")
                time.sleep(2)
                panel_shot(page, "選擇權損益圖", "payoff.png")
            except Exception as e:
                print("payoff shot failed:", e)

            # full layout with extras
            page.screenshot(path=str(OUT / "terminal-extras.png"))

            ctx.close()

            # 7. light theme - fresh context
            ctx2 = browser.new_context(
                viewport={"width": 1600, "height": 1000},
                device_scale_factor=2,
                color_scheme="light",
                locale="zh-TW",
                timezone_id="Asia/Taipei",
            )
            page2 = ctx2.new_page()
            page2.goto(BASE)
            page2.evaluate(
                "localStorage.setItem('sj-pro-theme', JSON.stringify({mode:'light'}))"
            )
            page2.reload()
            time.sleep(14)
            page2.screenshot(path=str(OUT / "terminal-light.png"))
            print("saved terminal-light.png")
            ctx2.close()
            browser.close()
    finally:
        pass


if __name__ == "__main__":
    sys.exit(main())
