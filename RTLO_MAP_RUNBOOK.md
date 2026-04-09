# RTLO Operations Command Center: Map Architecture & Runbook

This document outlines the architecture, data pipeline, and known pitfalls of the RTLO Operations Command Center map. It serves as a technical reference to ensure future modifications can be made safely without breaking the map's rendering or functionality.

## 1. System Architecture

The RTLO map is a static HTML file (`map.html`) generated daily by a Python script (`daily_refresh.py`). It is entirely self-contained, meaning it requires no external database or server-side processing at runtime.

### Core Components

| Component | File Path | Purpose |
|---|---|---|
| **Build Script** | `/home/ubuntu/rtlo-map/daily_refresh.py` | Fetches live data from APIs, geocodes addresses, injects data into the HTML template, and outputs the final map. |
| **HTML Template** | `/home/ubuntu/rtlo-map/index_new.html` | The structural skeleton of the map, containing Mapbox GL JS initialization, UI layout, and placeholder markers. |
| **Zone Source** | `/home/ubuntu/rtlo-map/index.html` | The original working map file, now used strictly as the source of truth for the complex geographical zone polygons. |
| **Final Output** | `/home/ubuntu/rtlo-map/map.html` | The fully built, self-contained map ready for deployment to the Manus CDN. |

## 2. Data Pipeline & Logic

The `daily_refresh.py` script executes the following sequence:

### A. Data Ingestion
- **JobTread (JT):** Fetches all jobs via the JobTread GraphQL API. Extracts the custom field `Job Status` (not the native system status). Filters to include only jobs in the "Sold | Project Intake Phase" or "Active Production Phase". Pre-sale "Opportunity" jobs are strictly excluded.
- **GoHighLevel (GHL):** Fetches all opportunities via the GHL REST API. Excludes any opportunities in "Closed Won" or "Closed Lost" stages.
- **Suppliers:** Loads static JSON files containing pre-geocoded supplier locations (Home Depot, SiteOne, Ace, Turf, Rock, Tile, Slab, RWC).
- **Weather:** Fetches live weather alerts from the National Weather Service API for the Phoenix Metro area.

### B. Deduplication Logic
To prevent stacked pins for the same project, GHL opportunities are suppressed if they match an active JobTread job. The matching criteria are:
1. **Linked ID:** GHL `ghlId` matches JT `id`.
2. **Name Match:** Normalized names (lowercase, alphanumeric only) match exactly (e.g., "Dan Schultz" != "Schultz").
3. **Address Match:** Normalized addresses (lowercase, alphanumeric only) match exactly. This catches cases where the names differ but the location is identical.

### C. Template Injection
The script reads `index_new.html` and replaces specific string placeholders with JSON-serialized data arrays.

**CRITICAL PITFALL: Zone Injection**
The service zones (Z1, Z2A, etc.) are injected from `index.html` using a strict brace-matching algorithm to extract exactly the `const ZONES = {...};` object.
- **Do not** use simple regex or string splitting (`split('};')`) to extract the zones, as this will accidentally capture the `const ZONE_CHIP_MAP` declaration that follows it in the source file.
- **Do not** declare `const ZONE_CHIP_MAP` twice in the final HTML. Duplicate `const` declarations in JavaScript throw a fatal `SyntaxError` that halts all script execution, resulting in a blank map and a spinning loading wheel.

## 3. Modifying the Map Safely

When adding new features, layers, or UI elements, follow these strict guidelines:

### Modifying the UI or Map Logic
1. **Edit the Template:** Make all HTML/CSS/JS changes in `index_new.html`.
2. **Never Hardcode Data:** Use placeholders (e.g., `NEW_DATA_PLACEHOLDER`) in the template, and update `daily_refresh.py` to inject the actual data.
3. **Script Placement:** Ensure the Mapbox GL JS library (`<script src="https://api.mapbox.com/mapbox-gl-js/v3.2.0/mapbox-gl.js"></script>`) is loaded *before* the main inline script.
4. **Token Handling:** The Mapbox token (`mapboxgl.accessToken`) must be a string literal in the injected script, not dependent on external `config.js` files, to ensure CDN compatibility.

### Adding New Data Sources
1. **Fetch Script:** Create a standalone Python script (e.g., `fetch_new_data.py`) to handle API pagination, error handling, and geocoding.
2. **Save to JSON:** Save the processed data to a local JSON file (e.g., `new_data.json`).
3. **Update Pipeline:** Add the JSON loading and placeholder injection to `daily_refresh.py`.

## 4. Deployment Workflow

The map is hosted on the Manus CDN. To deploy updates:

1. Run the build script:
   ```bash
   python3.11 /home/ubuntu/rtlo-map/daily_refresh.py
   ```
2. Verify the output syntax (crucial step to prevent spinning wheels):
   ```bash
   node --check /tmp/extracted_inline_script.js
   ```
   *(Note: The build pipeline should automate this extraction and check.)*
3. Upload to the CDN:
   ```bash
   manus-upload-file /home/ubuntu/rtlo-map/map.html
   ```
4. The command will return a direct `files.manuscdn.com` URL. This is the new live link.

## 5. Troubleshooting Guide

| Symptom | Root Cause | Solution |
|---|---|---|
| **Spinning Loading Wheel** | Fatal JavaScript `SyntaxError` halting execution. | Check the browser console. Usually caused by duplicate `const` declarations (e.g., `ZONE_CHIP_MAP`) or unreplaced placeholders breaking JSON parsing. |
| **Map Loads but No Pins** | `mapboxgl.accessToken` is missing or invalid. | Ensure the token is injected directly into the HTML and not relying on a missing `config.js`. |
| **Stacked Pins (JT + GHL)** | Deduplication failure. | The GHL opportunity and JT job have different names and addresses. Update the address in either system to match exactly. |
| **Missing JobTread Jobs** | Status filter exclusion. | The job's custom `Job Status` field is not set to "Sold \| Project Intake Phase" or "Active Production Phase". |
