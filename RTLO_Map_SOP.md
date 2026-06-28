# RTLO Operations Command Center — Team SOP

**Link:** [https://map.inhousekru.com](https://map.inhousekru.com)  
**Updated:** Automatically every 30 minutes during business hours, and every 3 hours overnight. No login required — just open the link.

---

## What This Is

The Operations Command Center is a live map of the Phoenix Metro that shows every active job in JobTread, every lead in the GoHighLevel sales pipeline, all nine service zones, every supplier location we use, and live crew locations — all in one place.

---

## Reading the Map

### Job & Lead Pins

| Symbol | Color | Meaning |
|---|---|---|
| ● Circle | Green | JobTread — **Active Production Phase** (job underway) |
| ● Circle | Purple | JobTread — **Sold \| Project Intake Phase** (sold, not yet active) |
| ◆ Diamond | Orange | GHL — **Appt Booked** |
| ◆ Diamond | Pink | GHL — **Consultation** |
| ◆ Diamond | Blue | GHL — **Proposal** |
| ◆ Diamond | Red | GHL — **Permitting** |

**Click** any pin to open a popup with the full details — name, address, service zone, status, and a direct link to open that record in JobTread or GoHighLevel.

### Service Zones

The shaded polygons across the map represent our nine service zones (Z1 through Z5B). Every job and lead popup tells you which zone that address falls in.

### Crew Locations

When crew members have their iOS tracking Shortcut enabled, their live locations appear on the map as colored dots with their names. You can toggle the crew layer on or off from the left sidebar. 

**Note on Crew Setup:** 
All crew members must use the exact API key `rtlo-crew-2026` in their iOS Shortcut. If this key is ever rotated in the system, every crew member must update their Shortcut before the system redeploys, or their location tracking will break.

---

## Filtering the Map

Use the **filter chips** along the top toolbar to show or hide specific categories:
- **JT ▾** — toggles all JobTread jobs on/off. Click individual chips to filter by status.
- **GHL ▾** — toggles all GHL pipeline leads on/off. Click individual chips to filter by stage.
- **Zone chips (Z1, Z2A, etc.)** — click any zone chip to show only pins within that zone.

---

## Using the Search Bar

Type any of the following into the search bar at the top of the map:
- **A supplier name** (e.g., "SiteOne", "Floor & Decor", "Aquatec") — the map flies to that pin and highlights it.
- **A job name or client name** — flies to that job or lead pin.
- **A street address** — geocodes the address, drops a pin, and tells you which service zone it falls in. Use this to quickly zone-check any address a customer or subcontractor gives you.

---

## Left Sidebar: Dashboard & Controls

The left sidebar contains your main operational controls and data:

1. **Live Dashboard:** Shows a real-time count of jobs and leads by category.
2. **Weather Risks Today:** Alerts you to any active NWS weather warnings or high precipitation risks for the day.
3. **Weather Overlay:** Toggle the live precipitation radar ON/OFF.
4. **Live Data Refresh:** Click the 🔄 button to force an immediate fetch of the latest jobs and leads from JobTread and GHL.
5. **Crew Layer:** Toggle live crew locations ON/OFF.
6. **Map Legend:** A quick reference for what each pin color and zone means.

---

## Right Sidebar: Supplier Layers

The right-hand panel lists all supplier categories. Each is **OFF by default** to keep the map clean. Toggle any layer ON to show those locations as pins.

| Icon | Meaning |
|---|---|
| ★ Gold Star | **Showroom** — walk-in, client-facing, product displays |
| ◆ Diamond | **Supply / Distribution** — contractor pickup, not a showroom |
| 💧 Water Drop | **Pool & Fountain supplier** |
| 🌿 Leaf | **Nursery** |
| 🔥 Fire | **BBQ / Outdoor Living** |
| ⚡ Bolt | **Tesla Superchargers** |

**All ON / All OFF** buttons at the top of the panel toggle every supplier layer at once.

---

## System Architecture & Maintenance 

For administrators handling the backend infrastructure:

- **Repository:** The code lives at `eruss-oss/rtlo-operations-map`. The repository is set to public to ensure free and unlimited GitHub Actions minutes.
- **Data Refresh:** Handled by `map-refresh.yml` GitHub Actions workflow.
- **Server Health:** The map is hosted on a Render server. A keep-alive GitHub Actions workflow pings the `/healthz` endpoint every 14 minutes to prevent the free tier server from sleeping.
- **Environment Variables:** Secrets like `JT_GRANT_KEY`, `GHL_PIT`, and `OWM_API_KEY` are stored securely in Render environment variables and GitHub Secrets, not in the codebase.

---
*Questions? Contact Eric Russell — eruss@rtloaz.com*
