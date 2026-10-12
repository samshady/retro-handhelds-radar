#!/usr/bin/env python3
"""
Fetch official, high-quality product images for sub-€100 retro handhelds using Brave Search Images API
Saves them locally to assets/images/<id>.jpg
"""
import os
import sys
import json
import time
import requests
from PIL import Image
import io

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, "assets", "images")
os.makedirs(IMG_DIR, exist_ok=True)

API_KEY = os.environ.get("BRAVE_SEARCH_API_KEY")
if not API_KEY:
    print("Error: BRAVE_SEARCH_API_KEY not found in environment.")
    sys.exit(1)

SEARCH_QUERIES = {
    "trimui-brick": "TrimUI Brick retro handheld console white",
    "anbernic-rg35xx-h": "Anbernic RG35XX H horizontal transparent black retro handheld",
    "anbernic-rg35xx-sp": "Anbernic RG35XX SP clamshell silver retro handheld",
    "miyoo-mini-plus": "Miyoo Mini Plus retro handheld console grey",
    "batlexp-g350": "BatleXP G350 retro handheld gaming console",
    "r36s": "R36S retro handheld console transparent purple",
    "powkiddy-rgb30": "Powkiddy RGB30 retro handheld console blue white",
    "trimui-smart-pro": "TrimUI Smart Pro retro handheld console black",
    "anbernic-rg40xx-h": "Anbernic RG40XX H horizontal retro handheld console",
    "anbernic-rg28xx": "Anbernic RG28XX micro retro handheld console",
    "anbernic-rg35xx-plus": "Anbernic RG35XX Plus vertical retro handheld grey",
    "miyoo-a30": "Miyoo A30 retro handheld console famicom",
    "konkr-pocket-block": "AYANEO KONKR Pocket Block retro handheld",
    "powkiddy-v90": "Powkiddy V90 clamshell retro handheld red",
    "data-frog-sf2000": "Data Frog SF2000 retro handheld console"
}

headers = {
    "Accept": "application/json",
    "X-Subscription-Token": API_KEY
}

download_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_and_save(device_id, query):
    out_path = os.path.join(IMG_DIR, f"{device_id}.jpg")
    if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
        print(f"[{device_id}] Already exists ({os.path.getsize(out_path)} bytes), skipping.")
        return True

    print(f"[{device_id}] Searching for: {query}...")
    try:
        resp = requests.get(
            "https://api.search.brave.com/res/v1/images/search",
            headers=headers,
            params={"q": query, "count": 10},
            timeout=10
        )
        if resp.status_code != 200:
            print(f"[{device_id}] Search API failed with code {resp.status_code}")
            return False

        data = resp.json()
        results = data.get("results", [])
        if not results:
            print(f"[{device_id}] No image results found.")
            return False

        for res in results[:6]:
            img_url = res.get("properties", {}).get("url") or res.get("thumbnail", {}).get("src")
            if not img_url:
                continue

            try:
                img_resp = requests.get(img_url, headers=download_headers, timeout=12)
                if img_resp.status_code == 200 and len(img_resp.content) > 5000:
                    image = Image.open(io.BytesIO(img_resp.content))
                    image = image.convert("RGB")
                    # Resize to clean max 800x800 bounding box
                    image.thumbnail((800, 800), Image.Resampling.LANCZOS)
                    image.save(out_path, "JPEG", quality=88, optimize=True)
                    print(f"[{device_id}] Successfully saved ({os.path.getsize(out_path):,} bytes)")
                    return True
            except Exception as e:
                continue

        print(f"[{device_id}] Could not download valid image from results.")
        return False
    except Exception as e:
        print(f"[{device_id}] Error: {e}")
        return False

def main():
    print(f"Fetching clean images for {len(SEARCH_QUERIES)} sub-€100 retro handhelds...")
    success = 0
    for device_id, query in SEARCH_QUERIES.items():
        if fetch_and_save(device_id, query):
            success += 1
        time.sleep(1.0)
    print(f"\nDone! Successfully acquired {success}/{len(SEARCH_QUERIES)} product images.")

if __name__ == "__main__":
    main()
