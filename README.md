# Retro Handhelds Radar (2026)

A curated European buyer's guide, live price radar, and specification matrix for retro gaming handhelds, custom firmwares (muOS, OnionOS, CrossMix), and PortMaster support.

## Project Structure

```
retro-handhelds-radar/
├── data/
│   └── handhelds.json      # Master database of 16 curated handhelds (specs, EU pricing, pros/cons)
├── scripts/
│   ├── build.py            # Static site compiler that builds templates into dist/index.html
│   ├── generate_data.py    # Dataset generator
│   ├── template_head.html  # Head markup, Catppuccin Mocha tokens, and Google Fonts pairing
│   ├── template_body.html  # Bento grid layout, filters, comparison table, and modal drawer
│   └── template_scripts.html # Filter, search, and modal interactions
├── tests/
│   └── test_no_em_dashes.py # Strict automated test asserting zero em-dashes
├── dist/
│   ├── index.html          # Standalone, compiled single-page application
│   └── favicon.svg         # Tactile retro console icon
├── favicon.svg
├── index.html              # GitHub Pages root deployment entry point
└── README.md
```

## How to Update the Database

Whenever new handhelds launch or AliExpress Choice / 11.11 prices change:
1. Open `data/handhelds.json`.
2. Add or update entries.
3. Re-build the dashboard:
   ```bash
   python3 scripts/build.py
   ```
4. Verify tests pass:
   ```bash
   python3 tests/test_no_em_dashes.py
   ```
5. Open `dist/index.html` in your browser.

## Core Features & Design System
- **Curated Personas**: Instant filtering for Friend Gifts (<€50), Sam's Sweet Spot (<€70), GBA Clamshell, PICO-8 & 1:1 Square, PSP Widescreen, and OLED Powerhouses.
- **European Street Pricing**: Compares typical AliExpress Choice Days, 11.11 Singles Day promos, and German/EU retail pricing.
- **Custom Firmware Matrix**: Deep-dive breakdowns for muOS (H700), OnionOS (Miyoo), and CrossMix/NextUI (TrimUI).
- **Zero Em-Dash Rule**: Strictly enforces zero em-dashes across all copy and UI.
- **Catppuccin Mocha Palette**: Dark mode styling paired with Bricolage Grotesque and Inter typography.
