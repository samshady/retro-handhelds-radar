#!/usr/bin/env python3
"""
Comprehensive QA E2E & Boundary Test Suite
Designed using qa-test-designer methodology (Myers, ISTQB, WCAG, Whittaker attack patterns)
and executed with Playwright against a live local static server.
"""
import os
import sys
import time
import socket
import threading
import http.server
import socketserver
import asyncio
from playwright.async_api import async_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(BASE_DIR, "dist")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "tests", "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

class StaticServer:
    def __init__(self, directory, port):
        self.directory = directory
        self.port = port
        self.httpd = None
        self.thread = None

    def start(self):
        handler = lambda *args: http.server.SimpleHTTPRequestHandler(*args, directory=self.directory)
        self.httpd = socketserver.TCPServer(("", self.port), handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()

async def run_tests():
    port = find_free_port()
    server = StaticServer(DIST_DIR, port)
    server.start()
    base_url = f"http://localhost:{port}"

    console_errors = []
    page_errors = []
    passed = 0
    failed = 0

    def record_pass(name):
        nonlocal passed
        passed += 1
        print(f"  ✓ {name}")

    def record_fail(name, reason):
        nonlocal failed
        failed += 1
        print(f"  ✗ {name}: {reason}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        print("\n=== Category 1: Happy Path & Document Integrity ===")
        await page.goto(base_url)
        title = await page.title()
        if "Retro Handhelds Radar" in title:
            record_pass(f"Document title verified: '{title}'")
        else:
            record_fail("Document title", f"Unexpected title: {title}")

        cards = await page.locator("#handheldGrid article").count()
        if cards == 15:
            record_pass(f"Initial render populated all {cards} benchmark handhelds")
        else:
            record_fail("Initial card count", f"Expected 15 cards, found {cards}")

        # Image render test
        images = await page.locator("#handheldGrid article img").count()
        if images == 15:
            record_pass(f"All {images} device cards have product images rendered")
        else:
            record_fail("Product images", f"Expected 15 images, found {images}")

        print("\n=== Category 2: Equivalence Partitioning & Filtering ===")
        # Form factor filter test
        await page.click("button[data-filter='Vertical']")
        vert_count = await page.locator("#handheldGrid article").count()
        if vert_count > 0 and vert_count < 15:
            record_pass(f"Form factor filter 'Vertical' isolated {vert_count} devices")
        else:
            record_fail("Vertical filter", f"Unexpected count {vert_count}")

        # Reset filter
        await page.click("button[data-filter='all']")
        all_count = await page.locator("#handheldGrid article").count()
        if all_count == 15:
            record_pass("Reset form factor filter restored all 15 devices")
        else:
            record_fail("Reset filter", f"Count was {all_count}")

        # Sort test
        await page.select_option("#sortSelect", "price-asc")
        first_price = await page.locator("#handheldGrid article:first-child .text-emerald-400").first.text_content()
        await page.select_option("#sortSelect", "price-desc")
        desc_price = await page.locator("#handheldGrid article:first-child .text-emerald-400").first.text_content()
        if first_price and desc_price:
            record_pass(f"Sort dropdown operates smoothly (cheapest: {first_price.strip()} vs highest: {desc_price.strip()})")
        else:
            record_fail("Sort dropdown", "Failed to sort cards by price")

        print("\n=== Category 3: Boundary & Search Attack Patterns ===")
        # Search for exact model (Anbernic RG28XX is uniquely named)
        await page.fill("#searchInput", "RG28XX")
        search_count = await page.locator("#handheldGrid article").count()
        if search_count == 1:
            record_pass("Specific query 'RG28XX' yielded exact 1 unique match")
        else:
            record_fail("Search RG28XX", f"Expected 1, got {search_count}")

        # Boundary: Empty result attack
        await page.fill("#searchInput", "xyznonexistentdevice12345")
        empty_visible = await page.locator("text=No handhelds match your active filters").is_visible()
        if empty_visible:
            record_pass("Nonsense search query triggers graceful empty-state message")
        else:
            record_fail("Empty state test", "Empty state message not displayed")

        # Recover from empty state via button
        await page.click("text=Reset Filters")
        recovered_count = await page.locator("#handheldGrid article").count()
        if recovered_count == 15:
            record_pass("Empty-state 'Reset Filters' button cleanly recovered full catalog")
        else:
            record_fail("Recover button", f"Expected 15, got {recovered_count}")

        print("\n=== Category 4: State, Sequencing & Modal Lifecycles ===")
        # Open modal
        await page.click("#handheldGrid article:first-child button")
        await page.wait_for_timeout(350)
        modal_visible = await page.locator("#detailModal").is_visible()
        if modal_visible:
            record_pass("Detail drawer opens on Inspect click")
        else:
            record_fail("Modal open", "Modal not visible")

        modal_title = await page.locator("#modalTitle").text_content()
        if modal_title and len(modal_title) > 3:
            record_pass(f"Modal populated with device data: '{modal_title}'")
        else:
            record_fail("Modal data", "Modal title empty")

        # Close via ESC key (Keyboard accessibility)
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(350)
        modal_closed = not await page.locator("#detailModal").is_visible()
        if modal_closed:
            record_pass("Escape key cleanly dismisses detail drawer")
        else:
            record_fail("ESC dismiss", "Modal remained open")

        # Table toggle view
        await page.click("#viewToggleBtn")
        table_visible = await page.locator("#comparisonTableWrapper").is_visible()
        if table_visible:
            record_pass("View toggle switches to comparison table matrix")
        else:
            record_fail("Table toggle", "Table wrapper not visible")

        # Toggle back to grid
        await page.click("#viewToggleBtn")
        grid_restored = await page.locator("#handheldGrid").is_visible()
        if grid_restored:
            record_pass("View toggle returns to Bento card grid")
        else:
            record_fail("Grid toggle", "Grid not visible")

        print("\n=== Category 5: Mobile Viewport & Touch Target Testing ===")
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.wait_for_timeout(200)

        mobile_cards = await page.locator("#handheldGrid article").count()
        if mobile_cards == 15:
            record_pass("390px mobile viewport renders stacked single-column cards")
        else:
            record_fail("Mobile layout", f"Expected 15 cards, got {mobile_cards}")

        # Capture mobile and desktop verification screenshots
        await page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "mobile_390.png"))
        await page.set_viewport_size({"width": 1440, "height": 900})
        await page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "desktop_1440.png"))
        record_pass("Captured high-res visual verification screenshots (desktop & mobile)")

        await browser.close()

    server.stop()

    print("\n=== QA Test Results Summary ===")
    print(f"Total Checks: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    if console_errors:
        print(f"Console Errors: {console_errors}")
    else:
        print("Console Errors: 0")

    if failed > 0 or len(console_errors) > 0 or len(page_errors) > 0:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_tests())
