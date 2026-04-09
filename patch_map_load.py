#!/usr/bin/env python3
"""Patch index_new.html to refactor map.on('load') into separate addJTMarkers/addGHLMarkers functions."""
import re

with open('/home/ubuntu/rtlo-map/index_new.html', 'r') as f:
    html = f.read()

# ── 1. Replace the inline JT/GHL rendering inside map.on('load') ──────────────
# Find the block from "initHoverLabel();" to end of map.on('load') closing "});"
# and replace with: set _mapLoaded flag, call helpers if data ready, call initSupplierLayers

OLD_LOAD_BLOCK = '''  initHoverLabel();

  // Add JobTread pins (only Sold/Active)
  JT_JOBS.forEach(job => {
    if (!job.lat || !job.lon) return;
    const color = getJTColor(job.status);
    const category = getJTCategory(job.status);
    const jobZone = getZoneForCoords(job.lon, job.lat);
    const isActive = category === 'jt-active';

    const el = document.createElement('div');
    el.dataset.category = category;
    el.dataset.zone = jobZone;

    if (isActive && weatherRiskActive) {
      el.style.cssText = `
        width:20px;height:20px;border-radius:50%;
        background:${color};border:2.5px solid rgba(255,255,255,0.9);
        box-shadow:0 0 8px ${color},0 2px 6px rgba(0,0,0,0.5),0 0 0 4px rgba(231,76,60,0.4);
        cursor:pointer;transition:box-shadow 0.15s;
        animation:weatherPulse 1.5s ease-in-out infinite;
      `;
    } else {
      el.style.cssText = `
        width:16px;height:16px;border-radius:50%;
        background:${color};border:2.5px solid rgba(255,255,255,0.9);
        box-shadow:0 0 8px ${color},0 2px 6px rgba(0,0,0,0.5);
        cursor:pointer;transition:box-shadow 0.15s;
      `;
    }

    if (isActive && weatherRiskActive) {
      const badge = document.createElement('div');
      badge.style.cssText = `position:absolute;top:-8px;right:-8px;width:14px;height:14px;background:#e74c3c;border-radius:50%;border:2px solid #fff;font-size:8px;display:flex;align-items:center;justify-content:center;pointer-events:none;`;
      badge.textContent = '!';
      el.style.position = 'relative';
      el.appendChild(badge);
    }

    const displayName = (job.name || 'Job').split(' ').slice(0,2).join(' ');
    el.addEventListener('mouseenter', () => { showLabel(displayName, el); el.style.boxShadow = `0 0 0 3px rgba(255,255,255,0.6), 0 0 16px ${color}, 0 0 6px ${color}`; });
    el.addEventListener('mouseleave', () => { hideLabel(); el.style.boxShadow = `0 0 8px ${color}, 0 2px 6px rgba(0,0,0,0.5)`; });

    const popup = new mapboxgl.Popup({ offset: 14, closeButton: true, maxWidth: '280px' }).setHTML(createJTPopup(job));
    const jtMarker = new mapboxgl.Marker(el).setLngLat([job.lon, job.lat]).setPopup(popup).addTo(map);
    allMarkers.push({ marker: jtMarker, el, category, source: 'jt', zone: jobZone });
  });

  // Add GHL pins (pre-sale only)
  const jtGhlIds = new Set(JT_JOBS.map(j => j.ghlId).filter(Boolean));
  GHL_OPPS.forEach(opp => {
    if (!opp.lat || !opp.lon) return;
    const ghlCat = getGHLCategory(opp.stage_name);
    if (!ghlCat) return;
    const color = getGHLColor(opp.stage_name);
    const oppZone = getZoneForCoords(opp.lon, opp.lat);
    const isAppt = ghlCat === 'ghl-appt';

    const diamond = document.createElement('div');
    diamond.dataset.category = ghlCat;
    diamond.dataset.zone = oppZone;
    diamond.style.cssText = `
      width:14px;height:14px;
      background:${color};border:2px solid rgba(255,255,255,0.85);
      box-shadow:0 0 8px ${color},0 2px 6px rgba(0,0,0,0.5);
      transform:rotate(45deg);border-radius:1px;
      cursor:pointer;transition:box-shadow 0.15s;
    `;

    // For Appt Booked: show name + date on hover
    const displayName = (opp.name || 'Lead').split(' ').slice(0,2).join(' ');
    const apptLabel = isAppt && opp.appt_start
      ? `${displayName} · ${formatApptDate(opp.appt_start)}`
      : displayName;

    diamond.addEventListener('mouseenter', () => { showLabel(apptLabel, diamond); diamond.style.boxShadow = `0 0 0 3px rgba(255,255,255,0.6), 0 0 16px ${color}, 0 0 6px ${color}`; });
    diamond.addEventListener('mouseleave', () => { hideLabel(); diamond.style.boxShadow = `0 0 8px ${color}, 0 2px 6px rgba(0,0,0,0.5)`; });

    const popup = new mapboxgl.Popup({ offset: 14, closeButton: true, maxWidth: '280px' }).setHTML(createGHLPopup(opp));
    const ghlMarker = new mapboxgl.Marker(diamond, { anchor: 'center' }).setLngLat([opp.lon, opp.lat]).setPopup(popup).addTo(map);
    allMarkers.push({ marker: ghlMarker, el: diamond, category: ghlCat, source: 'ghl', zone: oppZone });
  });

  initSupplierLayers();
  initWeatherRisk();
  applyWeatherZoneFlash();
  buildDashboard();
  document.getElementById('loading').style.display = 'none';
});'''

NEW_LOAD_BLOCK = '''  initHoverLabel();
  _mapLoaded = true;

  // If live data already arrived, render pins now; otherwise fetchLiveData callback handles it
  if (_dataLoaded) {
    addJTMarkers();
    addGHLMarkers();
    initWeatherRisk();
    applyWeatherZoneFlash();
    buildDashboard();
    searchIndex = buildSearchIndex();
  }

  initSupplierLayers();
  document.getElementById('loading').style.display = 'none';
});

// ─── JT MARKER RENDERER ──────────────────────────────────────────────────────

function addJTMarkers() {
  JT_JOBS.forEach(job => {
    if (!job.lat || !job.lon) return;
    const color = getJTColor(job.status);
    const category = getJTCategory(job.status);
    const jobZone = getZoneForCoords(job.lon, job.lat);
    const isActive = category === 'jt-active';

    const el = document.createElement('div');
    el.dataset.category = category;
    el.dataset.zone = jobZone;

    if (isActive && weatherRiskActive) {
      el.style.cssText = `
        width:20px;height:20px;border-radius:50%;
        background:${color};border:2.5px solid rgba(255,255,255,0.9);
        box-shadow:0 0 8px ${color},0 2px 6px rgba(0,0,0,0.5),0 0 0 4px rgba(231,76,60,0.4);
        cursor:pointer;transition:box-shadow 0.15s;
        animation:weatherPulse 1.5s ease-in-out infinite;
      `;
    } else {
      el.style.cssText = `
        width:16px;height:16px;border-radius:50%;
        background:${color};border:2.5px solid rgba(255,255,255,0.9);
        box-shadow:0 0 8px ${color},0 2px 6px rgba(0,0,0,0.5);
        cursor:pointer;transition:box-shadow 0.15s;
      `;
    }

    if (isActive && weatherRiskActive) {
      const badge = document.createElement('div');
      badge.style.cssText = `position:absolute;top:-8px;right:-8px;width:14px;height:14px;background:#e74c3c;border-radius:50%;border:2px solid #fff;font-size:8px;display:flex;align-items:center;justify-content:center;pointer-events:none;`;
      badge.textContent = '!';
      el.style.position = 'relative';
      el.appendChild(badge);
    }

    const displayName = (job.name || 'Job').split(' ').slice(0,2).join(' ');
    el.addEventListener('mouseenter', () => { showLabel(displayName, el); el.style.boxShadow = `0 0 0 3px rgba(255,255,255,0.6), 0 0 16px ${color}, 0 0 6px ${color}`; });
    el.addEventListener('mouseleave', () => { hideLabel(); el.style.boxShadow = `0 0 8px ${color}, 0 2px 6px rgba(0,0,0,0.5)`; });

    const popup = new mapboxgl.Popup({ offset: 14, closeButton: true, maxWidth: '280px' }).setHTML(createJTPopup(job));
    const jtMarker = new mapboxgl.Marker(el).setLngLat([job.lon, job.lat]).setPopup(popup).addTo(map);
    allMarkers.push({ marker: jtMarker, el, category, source: 'jt', zone: jobZone });
  });
}

// ─── GHL MARKER RENDERER ─────────────────────────────────────────────────────

function addGHLMarkers() {
  const jtGhlIds = new Set(JT_JOBS.map(j => j.ghlId).filter(Boolean));
  GHL_OPPS.forEach(opp => {
    if (!opp.lat || !opp.lon) return;
    const ghlCat = getGHLCategory(opp.stage_name);
    if (!ghlCat) return;
    const color = getGHLColor(opp.stage_name);
    const oppZone = getZoneForCoords(opp.lon, opp.lat);
    const isAppt = ghlCat === 'ghl-appt';

    const diamond = document.createElement('div');
    diamond.dataset.category = ghlCat;
    diamond.dataset.zone = oppZone;
    diamond.style.cssText = `
      width:14px;height:14px;
      background:${color};border:2px solid rgba(255,255,255,0.85);
      box-shadow:0 0 8px ${color},0 2px 6px rgba(0,0,0,0.5);
      transform:rotate(45deg);border-radius:1px;
      cursor:pointer;transition:box-shadow 0.15s;
    `;

    // For Appt Booked: show name + date on hover
    const displayName = (opp.name || 'Lead').split(' ').slice(0,2).join(' ');
    const apptLabel = isAppt && opp.appt_start
      ? `${displayName} · ${formatApptDate(opp.appt_start)}`
      : displayName;

    diamond.addEventListener('mouseenter', () => { showLabel(apptLabel, diamond); diamond.style.boxShadow = `0 0 0 3px rgba(255,255,255,0.6), 0 0 16px ${color}, 0 0 6px ${color}`; });
    diamond.addEventListener('mouseleave', () => { hideLabel(); diamond.style.boxShadow = `0 0 8px ${color}, 0 2px 6px rgba(0,0,0,0.5)`; });

    const popup = new mapboxgl.Popup({ offset: 14, closeButton: true, maxWidth: '280px' }).setHTML(createGHLPopup(opp));
    const ghlMarker = new mapboxgl.Marker(diamond, { anchor: 'center' }).setLngLat([opp.lon, opp.lat]).setPopup(popup).addTo(map);
    allMarkers.push({ marker: ghlMarker, el: diamond, category: ghlCat, source: 'ghl', zone: oppZone });
  });
}'''

if OLD_LOAD_BLOCK in html:
    html = html.replace(OLD_LOAD_BLOCK, NEW_LOAD_BLOCK)
    print('SUCCESS: map.on(load) block refactored')
else:
    print('ERROR: Could not find the target block to replace')
    # Show a snippet to debug
    idx = html.find('initHoverLabel();')
    print(f'initHoverLabel found at index: {idx}')
    idx2 = html.find('initSupplierLayers();')
    print(f'initSupplierLayers found at index: {idx2}')

with open('/home/ubuntu/rtlo-map/index_new.html', 'w') as f:
    f.write(html)

print('File written.')
