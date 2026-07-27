# -*- coding: utf-8 -*-

import os
from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_URL = os.environ.get("SITE_URL", "http://127.0.0.1:4173/alternatives/")
SITE_DIR = Path(__file__).resolve().parents[1]
PREVIEW_DIR = SITE_DIR / "previews" / "alternatives"
PREVIEW_DIR.mkdir(parents=True, exist_ok=True)


def assert_alternative_page(page, viewport_name):
    errors = []
    page.on(
        "console",
        lambda message: errors.append(f"console:{message.type}:{message.text}")
        if message.type == "error"
        else None,
    )
    page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
    page.goto(BASE_URL, wait_until="networkidle")

    assert "東へ、足を伸ばす？" in page.locator("h1").inner_text().replace("\n", "")
    assert page.locator(".destination").count() == 2
    assert page.locator(".route-plan").count() == 2
    assert page.locator(".comparison-row").count() == 6
    assert page.get_by_text("2026年8月8日は運休日").count() == 1
    assert page.get_by_text("OUR PICK · おすすめ").count() == 1
    assert page.get_by_text("こだま951号。15:07着。").count() == 1

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

    page.screenshot(
        path=str(PREVIEW_DIR / f"{viewport_name}-hero.png"),
    )
    page.locator("#tomonoura .route-plan").scroll_into_view_if_needed()
    page.wait_for_timeout(250)
    page.screenshot(
        path=str(PREVIEW_DIR / f"{viewport_name}-tomonoura-route.png"),
    )
    page.locator("#onomichi .route-plan").scroll_into_view_if_needed()
    page.wait_for_timeout(250)
    page.screenshot(
        path=str(PREVIEW_DIR / f"{viewport_name}-onomichi-route.png"),
    )
    page.locator("#compare").scroll_into_view_if_needed()
    page.wait_for_timeout(250)
    page.screenshot(
        path=str(PREVIEW_DIR / f"{viewport_name}-compare.png"),
    )
    page.screenshot(
        path=str(PREVIEW_DIR / f"{viewport_name}-full.png"),
        full_page=True,
    )

    assert not errors, "\n".join(errors)


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)

    desktop = browser.new_context(
        viewport={"width": 1440, "height": 1000},
        device_scale_factor=1,
    )
    assert_alternative_page(desktop.new_page(), "desktop")
    desktop.close()

    mobile = browser.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=1,
        is_mobile=True,
        has_touch=True,
    )
    assert_alternative_page(mobile.new_page(), "mobile")
    mobile.close()

    browser.close()

print("Alternatives smoke test: OK")
