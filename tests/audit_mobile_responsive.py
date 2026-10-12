#!/usr/bin/env python3
"""
Automated Responsive & Mobile Usability Auditor
Checks touch targets, horizontal overflow, sub-12px micro-text, and mobile layout constraints.
"""
import os
import sys
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

async def run_audit():
    port = find_free_port()
    server = StaticServer(DIST_DIR, port)
    server.start()
    base_url = f"http://localhost:{port}"

    viewports = [
        ("iphone_se", 320, 568),
        ("iphone_mini", 360, 640),
        ("iphone_standard", 390, 844),
        ("android_large", 412, 915),
        ("ipad_mini", 768, 1024),
    ]

    findings = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for name, width, height in viewports:
            print(f"\n--- Checking Viewport: {name} ({width}x{height}) ---")
            await page.set_viewport_size({"width": width, "height": height})
            await page.goto(base_url)
            await page.wait_for_load_state("networkidle")

            # 1. Horizontal Overflow Check
            overflow = await page.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
            if overflow > 1:
                findings.append({
                    "severity": "Serious",
                    "issue": f"Horizontal scroll overflow of {overflow:.1f}px detected at {width}px width",
                    "viewport": name
                })
                print(f"  [!] OVERFLOW: {overflow:.1f}px at {width}px")
            else:
                print(f"  [OK] No horizontal overflow at {width}px")

            # 2. Header Height Check (Must be <= 25% viewport height)
            header_height = await page.evaluate("() => document.querySelector('header').offsetHeight")
            header_ratio = header_height / height
            if header_ratio > 0.25:
                findings.append({
                    "severity": "Moderate",
                    "issue": f"Header consumes {header_ratio*100:.1f}% of vertical viewport (max 25%)",
                    "viewport": name
                })
                print(f"  [!] Header height: {header_height}px ({header_ratio*100:.1f}% of {height}px)")
            else:
                print(f"  [OK] Header height: {header_height}px ({header_ratio*100:.1f}%)")

            # Capture screenshot
            shot_path = os.path.join(SCREENSHOTS_DIR, f"audit_{name}_{width}.png")
            await page.screenshot(path=shot_path, full_page=False)

        # 3. Micro-text audit (< 12px)
        print("\n--- Auditing Font Sizes (Micro-Text < 12px) ---")
        await page.set_viewport_size({"width": 390, "height": 844})
        await page.goto(base_url)
        small_texts = await page.evaluate('''() => {
            const elements = Array.from(document.querySelectorAll('*'));
            const violations = [];
            for (const el of elements) {
                if (el.children.length === 0 && el.textContent.trim().length > 0) {
                    const style = window.getComputedStyle(el);
                    const size = parseFloat(style.fontSize);
                    if (size < 11.5) {
                        violations.push({
                            tag: el.tagName,
                            text: el.textContent.trim().substring(0, 30),
                            fontSize: size,
                            classes: el.className
                        });
                    }
                }
            }
            return violations;
        }''')
        if small_texts:
            print(f"  Found {len(small_texts)} micro-text instances (<12px):")
            for item in small_texts[:8]:
                print(f"    - [{item['fontSize']}px] <{item['tag']}> \"{item['text']}\" (class: {item['classes']})")
            findings.append({
                "severity": "Moderate",
                "issue": f"Found {len(small_texts)} elements with computed font-size < 12px",
                "details": small_texts
            })
        else:
            print("  [OK] Zero elements with font size < 12px")

        # 4. Touch Target Audit (< 44px height or width on interactive elements)
        print("\n--- Auditing Interactive Touch Targets (< 44px) ---")
        touch_violations = await page.evaluate('''() => {
            const interactives = Array.from(document.querySelectorAll('button, a, input, select'));
            const violations = [];
            for (const el of interactives) {
                if (el.offsetParent !== null) { // visible
                    const rect = el.getBoundingClientRect();
                    const text = el.innerText || el.getAttribute('aria-label') || el.title || '';
                    if (rect.height < 43.5 || rect.width < 43.5) {
                        violations.push({
                            tag: el.tagName,
                            text: text.trim().substring(0, 25),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            classes: el.className
                        });
                    }
                }
            }
            return violations;
        }''')
        if touch_violations:
            print(f"  Found {len(touch_violations)} touch targets below 44px:")
            for item in touch_violations:
                print(f"    - [{item['width']}x{item['height']}px] <{item['tag']}> \"{item['text']}\"")
            findings.append({
                "severity": "Moderate",
                "issue": f"Found {len(touch_violations)} interactive elements below 44px touch target",
                "details": touch_violations
            })
        else:
            print("  [OK] All visible interactive elements meet 44px touch target!")

        # 5. Detail Modal mobile check
        print("\n--- Auditing Detail Modal on Mobile (390px) ---")
        await page.click("#handheldGrid article:first-child button")
        await page.wait_for_timeout(350)
        modal_rect = await page.evaluate('''() => {
            const drawer = document.getElementById('modalContent');
            const rect = drawer.getBoundingClientRect();
            return {
                width: rect.width,
                windowWidth: window.innerWidth,
                overflowY: drawer.scrollHeight > drawer.clientHeight
            };
        }''')
        print(f"  Modal width: {modal_rect['width']}px (window: {modal_rect['windowWidth']}px), scrollable: {modal_rect['overflowY']}")
        await page.screenshot(path=os.path.join(SCREENSHOTS_DIR, "audit_modal_mobile_390.png"))

        await browser.close()

    server.stop()

    print("\n================ AUDIT SUMMARY ================")
    print(f"Total Findings: {len(findings)}")
    for f in findings:
        print(f"[{f['severity']}] {f['issue']}")

    return findings

if __name__ == "__main__":
    asyncio.run(run_audit())
