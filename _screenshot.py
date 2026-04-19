"""
Screenshot the live AIIM frontend for the public showcase README.

Pages captured:
  browse.png        — landing page with creator grid
  browse_filters.png — same page, filter panel opened
  influencer.png    — a single-creator detail view
  recommend.png     — the AI recommend page
"""

import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE = "https://aiim-frontend-559416574965.asia-northeast3.run.app"
OUT = os.path.dirname(os.path.abspath(__file__)) + "/screenshots"


def build_driver(width=1440, height=900):
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument(f"--window-size={width},{height}")
    drv = webdriver.Chrome(options=opts)
    drv.set_window_size(width, height)
    return drv


def wait_for_network_idle(drv, timeout=6):
    """Poor-man's network-idle: wait for document.readyState then a short settle."""
    WebDriverWait(drv, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )
    time.sleep(2.0)


def full_page_height(drv) -> int:
    return int(drv.execute_script(
        "return Math.max("
        "document.body.scrollHeight, document.documentElement.scrollHeight,"
        "document.body.offsetHeight, document.documentElement.offsetHeight)"
    ))


def snap(drv, path, fullpage=False):
    if fullpage:
        h = full_page_height(drv)
        drv.set_window_size(1440, min(h, 3500))  # cap at 3500 to keep PNGs sane
        time.sleep(0.8)
    drv.save_screenshot(path)
    print(f"  saved {path}")


def main():
    drv = build_driver()
    try:
        # 1. Landing / browse
        print("[1/4] /  (browse)")
        drv.get(BASE + "/")
        wait_for_network_idle(drv)
        # wait for any card-like element
        try:
            WebDriverWait(drv, 10).until(
                EC.presence_of_any_elements_located  # noqa: E501
                if False else
                lambda d: len(d.find_elements(By.CSS_SELECTOR,
                    "a[href^='/influencer/'], article, [class*=card], [class*=Card]")) > 0
            )
        except Exception:
            pass
        snap(drv, OUT + "/browse.png", fullpage=False)

        # full-page version
        snap(drv, OUT + "/browse_full.png", fullpage=True)
        drv.set_window_size(1440, 900)

        # 2. Pick first influencer card and follow it
        print("[2/4] /influencer/<id>")
        drv.get(BASE + "/")
        wait_for_network_idle(drv)
        links = drv.find_elements(By.CSS_SELECTOR, "a[href^='/influencer/']")
        if links:
            href = links[0].get_attribute("href")
            print(f"  following {href}")
            drv.get(href)
            wait_for_network_idle(drv)
            snap(drv, OUT + "/influencer.png", fullpage=False)
            snap(drv, OUT + "/influencer_full.png", fullpage=True)
            drv.set_window_size(1440, 900)
        else:
            print("  [warn] no /influencer/ links found on home — skipping detail screenshot")

        # 3. Recommend page
        print("[3/4] /recommend")
        drv.get(BASE + "/recommend")
        wait_for_network_idle(drv)
        snap(drv, OUT + "/recommend.png", fullpage=False)
        snap(drv, OUT + "/recommend_full.png", fullpage=True)
        drv.set_window_size(1440, 900)

        # 4. Browse with filter panel visible (try to click anything labeled "Filter")
        print("[4/4] /  (filters if present)")
        drv.get(BASE + "/")
        wait_for_network_idle(drv)
        try:
            btn = drv.find_element(By.XPATH, "//*[contains(translate(text(),"
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'filter')]")
            btn.click()
            time.sleep(1.0)
            snap(drv, OUT + "/browse_filters.png", fullpage=False)
        except Exception as e:
            print(f"  [info] filter toggle not found: {type(e).__name__}")

    finally:
        drv.quit()


if __name__ == "__main__":
    main()
