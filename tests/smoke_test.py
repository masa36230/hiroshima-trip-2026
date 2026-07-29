# -*- coding: utf-8 -*-

import io
import os
import platform
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

# Windowsでも日本語のテスト結果を安全に表示できるようにする。
if platform.system() == "Windows":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_URL = os.environ.get("SITE_URL", "http://127.0.0.1:4173")
SITE_DIR = Path(__file__).resolve().parents[1]
PREVIEW_DIR = SITE_DIR / "previews"
PREVIEW_DIR.mkdir(exist_ok=True)


def assert_page(page, viewport_name):
    errors = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto(BASE_URL, wait_until="networkidle")

    assert page.locator("h1").inner_text().replace("\n", "") == "海と祈り、おいしい広島。"
    assert page.locator(".day-story").count() == 4
    assert page.locator(".timeline").count() == 4
    assert page.locator(".reservation-badge").count() == 5
    assert page.locator('#day3 .timeline li:has-text("かき船かなわ") time').inner_text() == "19:00"
    assert page.locator(".meal-special span").nth(1).inner_text() == "19:00"
    assert "19:00" in page.locator('[data-booking="kanawa"] + .custom-check + .check-rank + .check-copy small').inner_text()
    assert page.locator("[data-booking]").count() == 7
    confirmed_bookings = page.locator('[data-confirmed="true"]')
    assert confirmed_bookings.count() == 5
    assert all(confirmed_bookings.nth(index).is_checked() for index in range(5))
    assert all(confirmed_bookings.nth(index).is_disabled() for index in range(5))
    page.screenshot(path=str(PREVIEW_DIR / f"{viewport_name}-hero.png"))
    page.locator("#overview").scroll_into_view_if_needed()
    page.wait_for_timeout(250)
    page.screenshot(path=str(PREVIEW_DIR / f"{viewport_name}-overview.png"))

    for image in page.locator("img").all():
        image.scroll_into_view_if_needed()
        image.evaluate(
            """async (img) => {
              if (img.complete && img.naturalWidth > 0) return;
              await new Promise((resolve) => {
                img.addEventListener("load", resolve, {once: true});
                img.addEventListener("error", resolve, {once: true});
                });
            }"""
        )
    page.locator("#dining").scroll_into_view_if_needed()
    page.wait_for_timeout(250)
    page.screenshot(path=str(PREVIEW_DIR / f"{viewport_name}-dining.png"))
    page.evaluate("window.scrollTo(0, 0)")

    image_results = page.locator("img").evaluate_all(
        "(images) => images.map((img) => ({src: img.src, ok: img.complete && img.naturalWidth > 0}))"
    )
    failed_images = [image["src"] for image in image_results if not image["ok"]]
    assert not failed_images, f"Images failed: {failed_images}"

    dimensions = page.evaluate(
        """() => ({
          scrollWidth: document.documentElement.scrollWidth,
          viewportWidth: window.innerWidth
        })"""
    )
    assert (
        dimensions["scrollWidth"] <= dimensions["viewportWidth"] + 1
    ), f"Horizontal overflow in {viewport_name}: {dimensions}"

    optional_booking = page.locator('[data-booking="riho"]')
    optional_booking.uncheck(force=True)
    optional_booking.check(force=True)
    assert "6 / 7" in page.locator("#booking-count").inner_text()
    page.reload(wait_until="networkidle")
    assert page.locator('[data-booking="riho"]').is_checked()

    first_details = page.locator(".accordion details").first
    first_details.locator("summary").click()
    assert first_details.evaluate("(element) => element.open")

    page.screenshot(
        path=str(PREVIEW_DIR / f"{viewport_name}-full.png"),
        full_page=True,
    )
    page.locator("#day2").scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    page.screenshot(path=str(PREVIEW_DIR / f"{viewport_name}-day2.png"))
    page.locator("#day3").scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    page.screenshot(path=str(PREVIEW_DIR / f"{viewport_name}-day3.png"))
    page.locator('#day3 .timeline li:has-text("かき船かなわ")').scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    page.screenshot(path=str(PREVIEW_DIR / f"{viewport_name}-day3-dinner.png"))
    assert not errors, "\n".join(errors)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)

    desktop = browser.new_context(
        viewport={"width": 1440, "height": 1000},
        device_scale_factor=1,
    )
    desktop.grant_permissions(["clipboard-read", "clipboard-write"], origin=BASE_URL)
    assert_page(desktop.new_page(), "desktop")
    desktop.close()

    mobile = browser.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=1,
        is_mobile=True,
        has_touch=True,
    )
    mobile.grant_permissions(["clipboard-read", "clipboard-write"], origin=BASE_URL)
    mobile_page = mobile.new_page()
    assert_page(mobile_page, "mobile")
    assert mobile_page.locator(".mobile-dock").is_visible()
    mobile.close()

    browser.close()

print("Smoke test: OK")
