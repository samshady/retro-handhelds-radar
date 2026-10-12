#!/usr/bin/env python3
"""
Retro Handhelds Radar Static Site Generator
Assembles modular HTML templates with verified data into dist/index.html and index.html
"""
import json
import os
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "handhelds.json")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
DIST_DIR = os.path.join(BASE_DIR, "dist")
OUTPUT_HTML_DIST = os.path.join(DIST_DIR, "index.html")
OUTPUT_HTML_ROOT = os.path.join(BASE_DIR, "index.html")

def build():
    print(f"Reading dataset: {DATA_FILE}")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        handhelds = json.load(f)
    print(f"Loaded {len(handhelds)} handheld models.")

    head_path = os.path.join(SCRIPTS_DIR, "template_head.html")
    body_path = os.path.join(SCRIPTS_DIR, "template_body.html")
    scripts_path = os.path.join(SCRIPTS_DIR, "template_scripts.html")

    with open(head_path, "r", encoding="utf-8") as f:
        head_html = f.read()
    with open(body_path, "r", encoding="utf-8") as f:
        body_html = f.read()
    with open(scripts_path, "r", encoding="utf-8") as f:
        scripts_html = f.read()

    combined_html = f"{head_html}\n{body_html}\n{scripts_html}"
    
    # Inject json data
    json_data_str = json.dumps(handhelds, ensure_ascii=False, indent=2)
    final_html = combined_html.replace("__JSON_DATA__", json_data_str)
    
    # Strip trailing whitespace
    final_html = "\n".join(line.rstrip() for line in final_html.splitlines()) + "\n"

    os.makedirs(DIST_DIR, exist_ok=True)
    with open(OUTPUT_HTML_DIST, "w", encoding="utf-8") as f:
        f.write(final_html)
    print(f"Generated: {OUTPUT_HTML_DIST} ({len(final_html):,} bytes)")

    with open(OUTPUT_HTML_ROOT, "w", encoding="utf-8") as f:
        f.write(final_html)
    print(f"Generated: {OUTPUT_HTML_ROOT} ({len(final_html):,} bytes)")

    # Copy favicon to dist
    favicon_src = os.path.join(BASE_DIR, "favicon.svg")
    favicon_dist = os.path.join(DIST_DIR, "favicon.svg")
    if os.path.exists(favicon_src):
        shutil.copyfile(favicon_src, favicon_dist)
        print(f"Copied favicon to: {favicon_dist}")

    # Copy assets if present
    assets_src = os.path.join(BASE_DIR, "assets")
    assets_dist = os.path.join(DIST_DIR, "assets")
    if os.path.exists(assets_src):
        if os.path.exists(assets_dist):
            shutil.rmtree(assets_dist)
        shutil.copytree(assets_src, assets_dist)
        print(f"Copied assets to: {assets_dist}")

    print("Site build completed successfully!")

if __name__ == "__main__":
    build()
