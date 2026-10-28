# -*- coding: utf-8 -*-
"""Design review capture: scroll through sections, open modal, log console + a11y issues."""
import sys, json, time
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
URL = "https://wus311125-cmd.github.io/"
OUT = r"C:\Users\NHP\personal-site"

results = {"console_errors": [], "notes": []}

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
    page = ctx.new_page()
    page.on("console", lambda m: results["console_errors"].append(f"[{m.type}] {m.text}") if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: results["console_errors"].append(f"[pageerror] {e}"))

    page.goto(URL, wait_until="networkidle", timeout=45000)
    page.wait_for_timeout(2500)  # let boot + hero animations run
    page.screenshot(path=f"{OUT}\\pw_desktop_hero.png")

    # counts
    results["notes"].append(f"posts rendered: {page.locator('.post').count()}")
    results["notes"].append(f"columns rendered: {page.locator('.col').count()}")
    results["notes"].append(f"filter buttons: {page.locator('#writebar .f').count()}")

    # scroll: columns
    page.locator("#columns").scroll_into_view_if_needed()
    page.wait_for_timeout(1200)
    page.screenshot(path=f"{OUT}\\pw_desktop_columns.png")

    # scroll: writing
    page.locator("#writing").scroll_into_view_if_needed()
    page.wait_for_timeout(1200)
    page.screenshot(path=f"{OUT}\\pw_desktop_writing.png")

    # filter interaction: click 記憶系統
    page.locator("#writebar .f", has_text="記憶系統").first.click()
    page.wait_for_timeout(800)
    results["notes"].append(f"after filter '記憶系統': posts visible = {page.locator('.post:not(.hide)').count()}")
    page.screenshot(path=f"{OUT}\\pw_desktop_filtered.png")
    # reset to 全部
    page.locator("#writebar .f", has_text="全部").first.click()
    page.wait_for_timeout(500)

    # open reader modal (first post)
    page.locator(".post").first.click()
    page.wait_for_timeout(900)
    page.screenshot(path=f"{OUT}\\pw_desktop_reader.png")
    results["notes"].append(f"reader open: {page.locator('#reader.open').count() == 1}")
    results["notes"].append(f"reader title: {page.locator('.rtitle').inner_text()[:40]}")
    # check focus management
    ae = page.evaluate("document.activeElement ? document.activeElement.tagName + '.' + document.activeElement.className : 'body'")
    results["notes"].append("activeElement after open: %s" % ae)
    # ESC close
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    results["notes"].append(f"reader closed on ESC: {page.locator('#reader.open').count() == 0}")

    # footer
    page.locator("#contact").scroll_into_view_if_needed()
    page.wait_for_timeout(1000)
    page.screenshot(path=f"{OUT}\\pw_desktop_footer.png")

    # ---- mobile ----
    mctx = browser.new_context(**p.devices["iPhone 13"])  # 390x844, dpr 3
    mp = mctx.new_page()
    mp.on("console", lambda m: results["console_errors"].append(f"[m:{m.type}] {m.text}") if m.type in ("error", "warning") else None)
    mp.on("pageerror", lambda e: results["console_errors"].append(f"[m:pageerror] {e}"))
    mp.goto(URL, wait_until="networkidle", timeout=45000)
    mp.wait_for_timeout(2500)
    mp.screenshot(path=f"{OUT}\\pw_mobile_hero.png")
    mp.locator("#writing").scroll_into_view_if_needed()
    mp.wait_for_timeout(1000)
    mp.screenshot(path=f"{OUT}\\pw_mobile_writing.png")
    # post tap area check: bounding box of a post row
    box = mp.locator(".post").first.bounding_box()
    results["notes"].append(f"mobile first post row bbox: {json.dumps(box)}")
    # open post on mobile
    mp.locator(".post").first.click()
    mp.wait_for_timeout(900)
    mp.screenshot(path=f"{OUT}\\pw_mobile_reader.png")
    results["notes"].append(f"mobile reader open: {mp.locator('#reader.open').count() == 1}")
    # horizontal overflow check
    results["notes"].append(f"mobile body scrollWidth={mp.evaluate('document.body.scrollWidth')} vs innerWidth={mp.evaluate('window.innerWidth')}")
    # tap target of filter buttons on mobile
    fbox = mp.locator("#writebar .f").first.bounding_box()
    results["notes"].append(f"mobile filter btn bbox: {json.dumps(fbox)}")
    mctx.close()

    # contrast checks via computed styles
    def cstyle(sel, prop):
        return page.evaluate(f"getComputedStyle(document.querySelector('{sel}')).{prop}")
    results["notes"].append(f"hero h1 color={cstyle('#hero h1','color')} bg(hero)= {cstyle('#hero','backgroundColor')}")
    date_col = cstyle('.post .date', 'color'); date_sz = cstyle('.post .date', 'fontSize')
    tt_sz = cstyle('.post .tt', 'fontSize'); sub_col = cstyle('#hero .sub', 'color')
    results["notes"].append("post date color=%s size=%s" % (date_col, date_sz))
    results["notes"].append("post title size=%s" % tt_sz)
    results["notes"].append("sub color=%s" % sub_col)
    faint = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--ink-faint')")
    results["notes"].append("ink-faint rgb check: %s" % faint)
    browser.close()

print(json.dumps(results, ensure_ascii=False, indent=1))
