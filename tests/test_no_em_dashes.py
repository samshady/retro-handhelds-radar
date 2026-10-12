#!/usr/bin/env python3
"""
Zero Em-Dash Test Suite (sam-web-design)
Asserts that no em-dashes (\\u2014) exist in user-facing HTML, JSON, or template files.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_no_em_dashes():
    em_dash = "\u2014"
    violations = []

    files_to_check = []
    for root, dirs, files in os.walk(BASE_DIR):
        if ".git" in root or "node_modules" in root:
            continue
        for f in files:
            if f.endswith((".html", ".json", ".js", ".py", ".md")):
                files_to_check.append(os.path.join(root, f))

    for filepath in files_to_check:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, 1):
                if em_dash in line:
                    # Skip the test file itself checking for the character
                    if "test_no_em_dashes.py" in filepath and 'em_dash = "\u2014"' in line:
                        continue
                    rel_path = os.path.relpath(filepath, BASE_DIR)
                    violations.append(f"{rel_path}:{line_no} contains em-dash: {line.strip()[:80]}")

    if violations:
        print("FAIL: Found forbidden em-dashes:")
        for v in violations:
            print("  ", v)
        sys.exit(1)
    else:
        print(f"PASS: Zero em-dashes verified across {len(files_to_check)} files.")

if __name__ == "__main__":
    test_no_em_dashes()
