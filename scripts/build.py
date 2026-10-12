#!/usr/bin/env python3
"""
Retro Handhelds Radar Static Site Generator
Assembles modular HTML templates with verified data into dist/index.html and index.html
"""
import json
import os
import shutil
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data", "handhelds.json")
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DIST_DIR = os.path.join(BASE_DIR, "dist")
OUTPUT_HTML_DIST = os.path.join(DIST_DIR, "index.html")
OUTPUT_HTML_ROOT = os.path.join(BASE_DIR, "index.html")

FORBIDDEN_PHRASES = [
    "\u2014",  # Unicode em-dash
    "&mdash;",
    "&#8212;",
    "Clean standalone HTML",
    "No bloated JavaScript",
    "Sam built this",
    "personal sweet spot",
    "friend gift",
]

def run_pre_build_validation(handhelds):
    print("Running Pre-Build Quality Gates...")
    errors = []

    # Gate 1: Dataset size & price checks
    if len(handhelds) == 0:
        errors.append("Dataset is empty.")
    for h in handhelds:
        model = h.get("model_name", "Unknown")
        price_eur = h.get("price_eur", 0)
        price_usd = h.get("price_usd", 0)
        if price_eur > 100 or price_usd > 100:
            errors.append(f"Model {model} exceeds sub-100 threshold (EUR: {price_eur}, USD: {price_usd}).")
        
        # Check image existence
        img_rel = h.get("image", "")
        img_full = os.path.join(BASE_DIR, img_rel)
        if not os.path.exists(img_full):
            errors.append(f"Model {model} image missing: {img_full}")
        elif os.path.getsize(img_full) < 10000:
            errors.append(f"Model {model} image suspiciously small (<10KB): {img_full}")

    # Gate 2: Copy hygiene & Zero Em-Dash in templates
    templates = [
        os.path.join(SCRIPTS_DIR, "template_head.html"),
        os.path.join(SCRIPTS_DIR, "template_body.html"),
        os.path.join(SCRIPTS_DIR, "template_scripts.html"),
        DATA_FILE,
    ]
    for tmpl in templates:
        with open(tmpl, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in content:
                errors.append(f"Forbidden phrase/character '{phrase}' found in {os.path.basename(tmpl)}")

    if errors:
        print("FAIL: Pre-build validation gates rejected the build:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    print("PASS: Pre-build quality gates cleared cleanly.")

def run_post_build_validation():
    print("Running Post-Build Quality Gates...")
    errors = []
    
    # Check built files exist
    for out_file in [OUTPUT_HTML_DIST, OUTPUT_HTML_ROOT]:
        if not os.path.exists(out_file):
            errors.append(f"Output file missing: {out_file}")
            continue
        with open(out_file, "r", encoding="utf-8") as f:
            content = f.read()
        if "\u2014" in content:
            errors.append(f"Forbidden em-dash found in {out_file}")
        if "&mdash;" in content or "&#8212;" in content:
            errors.append(f"Forbidden html em-dash found in {out_file}")
        if "crt-mode" not in content:
            errors.append(f"Retro styling (crt-mode) missing from default body in {out_file}")

    if errors:
        print("FAIL: Post-build validation gates failed:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    print("PASS: Post-build quality gates cleared cleanly.")

def build():
    print(f"Reading dataset: {DATA_FILE}")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        handhelds = json.load(f)
    print(f"Loaded {len(handhelds)} handheld models.")

    # 1. Run Pre-Build Gates
    run_pre_build_validation(handhelds)

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

    # 2. Run Post-Build Gates
    run_post_build_validation()

    print("Site build and all automated quality gates passed successfully!")

if __name__ == "__main__":
    build()
