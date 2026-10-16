"""Lightweight-charts rendered directly in the main Streamlit document.

The chart lives in a *constant* ``st.html`` host element (with
``unsafe_allow_javascript=True``): Streamlit's frontend only re-runs the
embedded scripts when the sanitized body changes, so a constant host body
means the chart DOM (and any pan/zoom state) survives every fragment tick.

Each tick also renders a tiny *payload* element whose body changes (it holds
the current chart data).  Its script re-executes every tick and calls the
host-registered dispatcher ``window.__cw_tick_<root_id>(init)``, which either
rebuilds the chart (structure changed) or incrementally updates only the last
bar of each series (structure unchanged) via ``series.update()``.
"""

import json
import os
import shutil

import streamlit as st

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_ID = "lwc_candlestick"
_STATIC_LIB_DIR = os.path.join(_BASE_DIR, "static")
_STATIC_LIB_PATH = os.path.join(_STATIC_LIB_DIR, "_lwc_lib.js")
_STATIC_LIB_URL = "/app/static/_lwc_lib.js"
_STATIC_LIB_CHECKED = False


def _load_vendored_lwc() -> str:
    """Read the vendored lightweight-charts bundle (v4.2.1) if present."""
    try:
        with open(os.path.join(_BASE_DIR, "_lwc_lib.js"), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def _ensure_static_lib() -> bool:
    """Copy the vendored LWC bundle into static/ so Streamlit serves it over HTTP.

    Requires ``server.enableStaticServing = true`` in .streamlit/config.toml
    (see the config file shipped with the app).
    """
    global _STATIC_LIB_CHECKED
    if _STATIC_LIB_CHECKED:
        return True
    try:
        src = os.path.join(_BASE_DIR, "_lwc_lib.js")
        if not os.path.exists(src):
            return False
        os.makedirs(_STATIC_LIB_DIR, exist_ok=True)
        need_copy = True
        if os.path.exists(_STATIC_LIB_PATH):
            try:
                if (os.path.getmtime(src) == os.path.getmtime(_STATIC_LIB_PATH)
                        and os.path.getsize(src) == os.path.getsize(_STATIC_LIB_PATH)):
                    need_copy = False
            except OSError:
                need_copy = True
        if need_copy:
            shutil.copy2(src, _STATIC_LIB_PATH)
        _STATIC_LIB_CHECKED = True
        return True
    except Exception:
        return False


# ------------------------------------------------------------------
# Chart init logic (kept free of < at top-level of the HTML source --
# scripts are injected via st.html(unsafe_allow_javascript=True)).

def build_host_js(root_id: str = _ROOT_ID) -> str:
    """Build the chart host JavaScript as a single self-contained JS snippet.

    All per-render values (data, colors, pane heights) arrive at runtime via
    ``window.__cw_tick_<root_id>(init)`` dispatch calls, so the host script is
    a constant string: its st.html element never re-runs its innerHTML/scripts,
    keeping the chart DOM (and any pan/zoom state) alive across ticks.
    """
    return """
(function() {
    const ROOT_ID = '%(root_id)s';
    var DATA = null;
    let container = document.getElementById(ROOT_ID);
    if (!container) {
        container = document.createElement('div');
        container.id = ROOT_ID;
        container.style.cssText = 'width:100%%;position:relative;';
        document.body.appendChild(container);
    }

    const RENDER_KEY = '__lwc_render_' + ROOT_ID;
    let RENDER_VERSION = (window[RENDER_KEY] || 0) + 1;
    window[RENDER_KEY] = RENDER_VERSION;
    const CHART_KEY = '__lwc_chart_' + ROOT_ID;
    // Invalidate any stale chart state from a previous host-script instance so
    // the next dispatch rebuilds fresh chart DOM (e.g. after an element remount).
    window[CHART_KEY + '__state'] = null;

    function __cwSetStatus(stObj) {
        const colors = {
            info:    {bg: 'rgba(33,150,243,0.92)', fg: '#ffffff'},
            success: {bg: 'rgba(0,204,150,0.92)', fg: '#0e1117'},
            warning: {bg: 'rgba(255,193,7,0.95)',  fg: '#31333f'},
        };
        let badge = document.getElementById('cw_status_badge');
        if (stObj && stObj.text) {
            const c = colors[stObj.level || 'info'] || colors.info;
            if (!badge) {
                badge = document.createElement('div');
                badge.id = 'cw_status_badge';
                badge.style.cssText = 'position:absolute;top:4px;left:4px;padding:4px 10px;border-radius:6px;background:' + c.bg + ';color:' + c.fg + ';font-size:12px;font-weight:600;pointer-events:none;z-index:10;box-shadow:0 1px 3px rgba(0,0,0,0.35);white-space:nowrap;';
                if (container) container.appendChild(badge);
            }
            badge.textContent = stObj.text;
            badge.style.background = c.bg;
            badge.style.color = c.fg;
            badge.style.display = '';
        } else if (badge) {
            badge.style.display = 'none';
        }
    }

    function initChart() {
        if (typeof LightweightCharts === 'undefined') {
            requestAnimationFrame(initChart);
            return;
        }
        doInit();
    }
    function doInit() {
        if (window[RENDER_KEY] !== RENDER_VERSION) return;
        if (!DATA || !DATA.init) return;
        // Refresh the container reference: React may have recreated the div
        // (innerHTML reset) since the host script ran; never build into a
        // detached node.
        container = document.getElementById(ROOT_ID) || container;

        const PAYLOAD_HASH_KEY = '__lwc_payload_hash_' + ROOT_ID;
        const PAYLOAD_VERSION_KEY = '__lwc_payload_version_' + ROOT_ID;
        let _payloadHash = '';
        try { _payloadHash = JSON.stringify(DATA.init); } catch (e) { _payloadHash = ''; }
        if (window[PAYLOAD_HASH_KEY] === _payloadHash && container && container.firstChild && (window[PAYLOAD_VERSION_KEY] || 0) > 0) {
            window[RENDER_KEY] = window[PAYLOAD_VERSION_KEY];
            return;
        }
        window[PAYLOAD_HASH_KEY] = _payloadHash;
        window[PAYLOAD_VERSION_KEY] = RENDER_VERSION;

        const SAVED_KEY = '__lwc_saved_' + ROOT_ID;
        const prevSaved = window[SAVED_KEY];
        window[SAVED_KEY] = null;

        const d = DATA.init;
        const bg = (d.theme && d.theme.bg) || '#ffffff';
        const tc = (d.theme && d.theme.text) || '#1e293b';
        const gc = (d.theme && d.theme.grid) || '#e9eef3';

        const MAIN_H = (d.heights && d.heights.main) || 420;
        const VOL_H = (d.heights && d.heights.vol) || 0;
        const OSC_H = (d.heights && d.heights.osc) || 0;
        const IV_SKEW_H = (d.heights && d.heights.iv_skew) || 0;
        const IV_SKEW_HIST_H = (d.heights && d.heights.iv_skew_hist) || 0;

        const panes = [{id: 'right', h: MAIN_H}];
        if (d.volume_series) panes.push({id: 'volume', h: VOL_H});
        if (d.andean_series) panes.push({id: 'osc', h: OSC_H});
        if (d.iv_skew_series) panes.push({id: 'iv_skew', h: IV_SKEW_H});
        if (d.iv_skew_hist) panes.push({id: 'iv_skew_hist', h: IV_SKEW_HIST_H});

        const paneIds = new Set(panes.map(function(p) { return p.id; }));
        const PANE_H_DEFAULT = 100;
        function ensurePane(pid) {
            if (pid === 'right' || pid === '' || pid == null) return;
            if (paneIds.has(pid)) return;
            paneIds.add(pid);
            panes.push({id: pid, h: PANE_H_DEFAULT});
        }
        function collectPaneIds(seriesArr) {
            if (!seriesArr) return;
            for (const s of seriesArr) {
                const pid = (s.options || {}).priceScaleId;
                if (pid && pid !== 'right') ensurePane(pid);
            }
        }
        collectPaneIds(d.series);
        collectPaneIds(d.volume_series);
        collectPaneIds(d.andean_series);
        collectPaneIds(d.iv_skew_series);
        collectPaneIds(d.iv_skew_hist);

        const TOTAL_H = panes.reduce(function(s, p) { return s + p.h; }, 0);
        const GAP = 4;

        container.style.height = TOTAL_H + 'px';

        while (container.firstChild) container.removeChild(container.firstChild);

        const chart = LightweightCharts.createChart(container, {
            height: TOTAL_H,
            layout: {background:{type:'solid',color:bg}, textColor:tc},
            grid: {vertLines:{color:gc}, horzLines:{color:gc}},
            crosshair: {mode:0},
            handleScroll: true,
            handleScale: {
                mouseWheel: true,
                pressedMouseMove: true,
                axisPressedMouseMove: true,
                axisTouch: true,
            },
            timeScale: {
                borderColor: gc,
                timeVisible: true,
                secondsVisible: false,
                fixLeftEdge: false,
                fixRightEdge: false,
                lockFirstTime: false,
                allowScroll: true,
                allowZoom: true,
                rightOffset: 5,
            },
        });

        let candleSeries = null;
        const paneSeries = {};
        const paneSeriesAll = {};
        function _registerSeries(paneId, series) {
            if (!paneId || !series) return;
            if (!paneSeriesAll[paneId]) paneSeriesAll[paneId] = [];
            paneSeriesAll[paneId].push(series);
            if (!paneSeries[paneId]) paneSeries[paneId] = series;
        }
        const _allSeriesByKey = {};
        function addSeries(s) {
            let series = null;
            if (s.type === 'Candlestick') {
                series = chart.addCandlestickSeries(s.options || {});
                candleSeries = series;
                _registerSeries('right', series);
            } else if (s.type === 'Line') {
                series = chart.addLineSeries(s.options || {});
            } else if (s.type === 'Histogram') {
                series = chart.addHistogramSeries(s.options || {});
            }
            if (series && s.data) {
                series.setData(s.data);
                series.__cwN = s.data.length;
            }
            if (series && s.key) {
                _allSeriesByKey[s.key] = series;
            }
            if (series) {
                const declaredPid = (s.options || {}).priceScaleId;
                if (declaredPid && declaredPid !== 'right') {
                    if (!paneIds.has(declaredPid)) {
                        try { chart.removeSeries(series); } catch (_) {}
                        return;
                    }
                }
                const pid = declaredPid || 'right';
                _registerSeries(pid, series);
            }
        }

        for (const s of d.series || []) { addSeries(s); }
        for (const s of d.volume_series || []) { addSeries(s); }
        for (const s of d.andean_series || []) { addSeries(s); }
        for (const s of d.iv_skew_series || []) { addSeries(s); }
        for (const s of d.iv_skew_hist || []) { addSeries(s); }

        const paneEdges = {};
        let y = 0;
        for (const p of panes) {
            const topPx = y + GAP;
            const bottomPx = y + p.h - GAP;
            paneEdges[p.id] = {top: topPx, bottom: bottomPx};
            const isMain = (p.id === 'right');
            chart.priceScale(p.id).applyOptions({
                scaleMargins: {top: topPx / TOTAL_H, bottom: (TOTAL_H - bottomPx) / TOTAL_H},
                visible: true,
                autoScale: true,
                borderVisible: true,
                ...(isMain ? {} : {
                    visible: false,
                    borderVisible: false,
                    mode: 0,
                }),
            });
            y += p.h;
        }

        function applyPanePriceFormat(seriesArr) {
            if (!seriesArr) return;
            for (const s of seriesArr) {
                const pid = (s.options || {}).priceScaleId;
                if (!pid || pid === 'right') continue;
                const opts = s.options || (s.options = {});
                if (!opts.priceFormat) {
                    opts.priceFormat = {type: 'price', precision: 2, minMove: 0.01};
                }
            }
        }
        applyPanePriceFormat(d.andean_series);
        applyPanePriceFormat(d.iv_skew_series);
        applyPanePriceFormat(d.iv_skew_hist);

        const AXIS_W = 60;
        const indicatorPanes = panes.filter(function(p) { return p.id !== 'right'; });
        const axisOverlays = [];
        for (const p of indicatorPanes) {
            const ov = document.createElement('canvas');
            ov.style.cssText = 'position:absolute;right:0;pointer-events:none;z-index:6;';
            container.appendChild(ov);
            axisOverlays.push({paneId: p.id, canvas: ov, ctx: ov.getContext('2d'), lastSig: null});
        }

        function formatTick(v, isVolume, isPct) {
            if (v == null || isNaN(v)) return '';
            if (isVolume) {
                const a = Math.abs(v);
                if (a >= 1e9) return (v / 1e9).toFixed(1) + 'B';
                if (a >= 1e6) return (v / 1e6).toFixed(1) + 'M';
                if (a >= 1e3) return (v / 1e3).toFixed(1) + 'K';
                return String(Math.round(v));
            }
            if (isPct) return (v * 100).toFixed(2) + '%%';
            return v.toFixed(2);
        }

        function drawPaneAxis(ov) {
            const series = paneSeries[ov.paneId];
            const edges = paneEdges[ov.paneId];
            if (!series || !edges) return;
            const isVolume = (ov.paneId === 'volume');
            const isIVSkew = (ov.paneId === 'iv_skew' || ov.paneId === 'iv_skew_hist');
            let topP, botP;
            try {
                topP = series.coordinateToPrice(edges.top);
                botP = series.coordinateToPrice(edges.bottom);
            } catch (_) { return; }
            if (topP == null || botP == null) return;
            const lo = Math.min(topP, botP);
            const hi = Math.max(topP, botP);
            if (!(lo < hi)) return;
            const span = hi - lo;
            const NUM_TICKS = 5;
            const w = container.clientWidth;
            const dpw = typeof window.devicePixelRatio === 'number' ? window.devicePixelRatio : 1;
            const stripW = AXIS_W;
            const stripH = edges.bottom - edges.top;
            if (stripH <= 0) return;
            if (ov.canvas.width !== Math.floor(stripW * dpw) || ov.canvas.height !== Math.floor(stripH * dpw)) {
                ov.canvas.width = Math.floor(stripW * dpw);
                ov.canvas.height = Math.floor(stripH * dpw);
                ov.canvas.style.width = stripW + 'px';
                ov.canvas.style.height = stripH + 'px';
                ov.canvas.style.top = edges.top + 'px';
            }
            const ctx = ov.ctx;
            ctx.setTransform(dpw, 0, 0, dpw, 0, 0);
            ctx.clearRect(0, 0, stripW, stripH);
            ctx.fillStyle = bg;
            ctx.fillRect(0, 0, stripW, stripH);
            ctx.strokeStyle = gc;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(0.5, 0);
            ctx.lineTo(0.5, stripH);
            ctx.stroke();
            ctx.fillStyle = tc;
            ctx.font = '11px system-ui, -apple-system, sans-serif';
            ctx.textAlign = 'right';
            ctx.textBaseline = 'middle';
            for (let i = 0; i < NUM_TICKS; i++) {
                const frac = (NUM_TICKS === 1) ? 0.5 : i / (NUM_TICKS - 1);
                const val = lo + frac * span;
                let cy;
                try { cy = series.priceToCoordinate(val); } catch (_) { continue; }
                if (cy == null) continue;
                const localY = cy - edges.top;
                if (localY < 0 || localY > stripH) continue;
                ctx.strokeStyle = gc;
                ctx.beginPath();
                ctx.moveTo(0, localY);
                ctx.lineTo(4, localY);
                ctx.stroke();
                ctx.fillStyle = tc;
                ctx.fillText(formatTick(val, isVolume, isIVSkew), stripW - 4, localY);
            }
        }

        function redrawIndicatorAxes() {
            for (const ov of axisOverlays) {
                try { drawPaneAxis(ov); } catch (_) {}
            }
        }

        let axesDirty = true;
        function markAxesDirty() { axesDirty = true; }
        try {
            chart.timeScale().subscribeVisibleTimeRangeChange(markAxesDirty);
            chart.timeScale().subscribeVisibleLogicalRangeChange(markAxesDirty);
        } catch (_) {}
        const axisRO = new ResizeObserver(markAxesDirty);
        axisRO.observe(container);
        let lastAxisSigs = {};
        function axisLoop() {
            if (window[RENDER_KEY] !== RENDER_VERSION) { axisRO.disconnect(); return; }
            let moved = axesDirty;
            for (const p of indicatorPanes) {
                const s = paneSeries[p.id];
                const e = paneEdges[p.id];
                if (!s || !e) continue;
                let sig = '';
                try {
                    const a = s.coordinateToPrice(e.top);
                    const b = s.coordinateToPrice(e.bottom);
                    if (a != null && b != null) sig = a + ':' + b;
                } catch (_) {}
                if (sig !== lastAxisSigs[p.id]) { lastAxisSigs[p.id] = sig; moved = true; }
            }
            if (moved) {
                axesDirty = false;
                redrawIndicatorAxes();
            }
            requestAnimationFrame(axisLoop);
        }
        requestAnimationFrame(axisLoop);

        __cwSetStatus(d.status);

        const ts = chart.timeScale();

        function readVisibleRange(id) {
            const series = paneSeries[id];
            const edges = paneEdges[id];
            if (!series || !edges) return null;
            try {
                const topP = series.coordinateToPrice(edges.top);
                const botP = series.coordinateToPrice(edges.bottom);
                if (topP === null || botP === null) return null;
                const lo = Math.min(topP, botP);
                const hi = Math.max(topP, botP);
                if (!(lo < hi)) return null;
                return { from: lo, to: hi };
            } catch (_) { return null; }
        }

        const pinnedPanes = {};
        function applyVisibleRange(id, from, to) {
            const all = paneSeriesAll[id];
            if (!all || !all.length) return false;
            try {
                const lo = Math.min(from, to);
                const hi = Math.max(from, to);
                const ps = chart.priceScale(id);
                ps.applyOptions({ autoScale: true });
                for (let k = 0; k < all.length; k++) {
                    all[k].applyOptions({
                        autoscaleInfoProvider: function() {
                            return { priceRange: { minValue: lo, maxValue: hi }, margins: { above: 0, below: 0 } };
                        },
                    });
                }
                pinnedPanes[id] = {from: lo, to: hi};
                return true;
            } catch (_) { return false; }
        }

        function savePosition(forcePrice) {
            const tr = ts.getVisibleRange();
            if (!tr) return;
            const logicalRange = ts.getVisibleLogicalRange();
            function snapPrice(id) {
                const ps = chart.priceScale(id);
                let auto = true;
                try { auto = !!ps.options().autoScale; } catch (_) {}
                const pin = pinnedPanes[id];
                if (forcePrice) {
                    return readVisibleRange(id);
                }
                if (pin) {
                    return { from: pin.from, to: pin.to };
                }
                if (!auto) return readVisibleRange(id);
                return null;
            }
            const priceRange = snapPrice('right');
            const subPriceRanges = {};
            for (const pid of Object.keys(paneSeries)) {
                if (pid === 'right') continue;
                const pr = snapPrice(pid);
                if (pr) subPriceRanges[pid] = pr;
            }
            const hadAny = priceRange || Object.keys(subPriceRanges).length;
            window[SAVED_KEY] = {
                mainRange: { from: tr.from, to: tr.to },
                barSpacing: ts.options().barSpacing,
                logicalRange: logicalRange ? { from: logicalRange.from, to: logicalRange.to } : null,
                priceRange: priceRange,
                subPriceRanges: subPriceRanges,
                hasManual: !!hadAny,
            };
        }

        function restoreRange(tsApi, saved) {
            if (!saved) return;
            if (saved.logicalRange) {
                try {
                    tsApi.setVisibleLogicalRange({
                        from: saved.logicalRange.from,
                        to: saved.logicalRange.to,
                    });
                    return true;
                } catch (_) {}
            }
            if (saved.mainRange) {
                try {
                    tsApi.applyOptions({ barSpacing: saved.barSpacing });
                    tsApi.setVisibleRange({ from: saved.mainRange.from, to: saved.mainRange.to });
                    return true;
                } catch (_) {}
            }
            return false;
        }

        let restoredPanes = null;
        if (prevSaved && (prevSaved.logicalRange || prevSaved.mainRange)) {
            restoreRange(ts, prevSaved);
            restoredPanes = {};
            if (prevSaved.priceRange) {
                applyVisibleRange('right', prevSaved.priceRange.from, prevSaved.priceRange.to);
                restoredPanes['right'] = {from: prevSaved.priceRange.from, to: prevSaved.priceRange.to};
            }
            if (prevSaved.subPriceRanges) {
                for (const pid of Object.keys(prevSaved.subPriceRanges)) {
                    const pr = prevSaved.subPriceRanges[pid];
                    if (!pr) continue;
                    applyVisibleRange(pid, pr.from, pr.to);
                    restoredPanes[pid] = {from: pr.from, to: pr.to};
                }
            }
        }

        savePosition();
        if (restoredPanes && Object.keys(restoredPanes).length) {
            const cur = window[SAVED_KEY] || {};
            for (const pid of Object.keys(restoredPanes)) {
                if (pid === 'right') {
                    cur.priceRange = restoredPanes[pid];
                } else {
                    cur.subPriceRanges = cur.subPriceRanges || {};
                    cur.subPriceRanges[pid] = restoredPanes[pid];
                }
            }
            window[SAVED_KEY] = cur;
        }

        ts.subscribeVisibleTimeRangeChange(function(timeRange) {
            if (window[RENDER_KEY] !== RENDER_VERSION) return;
            savePosition(false);
        });

        let ySavePending = false;
        function scheduleYSave() {
            if (ySavePending) return;
            ySavePending = true;
            requestAnimationFrame(function() {
                ySavePending = false;
                if (window[RENDER_KEY] !== RENDER_VERSION) return;
                savePosition(true);
            });
        }
        container.addEventListener('pointerup', scheduleYSave);
        container.addEventListener('wheel', scheduleYSave, {passive: true});

        let yDrag = null;
        function paneAt(cy) {
            let acc = 0;
            for (const p of panes) {
                if (cy >= acc && cy < acc + p.h) return p;
                acc += p.h;
            }
            return null;
        }
        function overPriceAxisLabel(px, py) {
            const p = paneAt(py);
            if (!p) return false;
            let axisW = 0;
            try { axisW = chart.priceScale(p.id).width(); } catch (_) { axisW = 0; }
            if (axisW <= 0) return false;
            const chartW = container.clientWidth;
            return px >= chartW - axisW;
        }
        container.addEventListener('pointerdown', function(ev) {
            if (ev.button !== 0) return;
            if (window[RENDER_KEY] !== RENDER_VERSION) return;
            const r = container.getBoundingClientRect();
            const px = ev.clientX - r.left;
            const py = ev.clientY - r.top;
            if (overPriceAxisLabel(px, py)) return;
            const tScaleH = 28;
            if (py > TOTAL_H - tScaleH) return;
            const p = paneAt(py);
            if (!p) return;
            const vr = readVisibleRange(p.id);
            if (!vr) return;
            const edges = paneEdges[p.id];
            yDrag = {
                paneId: p.id,
                startY: py,
                startFrom: Math.min(vr.from, vr.to),
                startTo: Math.max(vr.from, vr.to),
                topPx: edges.top,
                botPx: edges.bottom,
                moving: false,
            };
        }, {passive: true});
        container.addEventListener('pointermove', function(ev) {
            if (!yDrag || window[RENDER_KEY] !== RENDER_VERSION) return;
            if (!(ev.buttons & 1)) { yDrag = null; return; }
            const r = container.getBoundingClientRect();
            const py = ev.clientY - r.top;
            const dy = py - yDrag.startY;
            if (!yDrag.moving && Math.abs(dy) < 3) return;
            yDrag.moving = true;
            const span = yDrag.startTo - yDrag.startFrom;
            if (!(span > 0)) return;
            const paneH = yDrag.botPx - yDrag.topPx;
            if (paneH <= 0) return;
            const shift = (dy / paneH) * span;
            const newFrom = yDrag.startFrom + shift;
            const newTo = yDrag.startTo + shift;
            applyVisibleRange(yDrag.paneId, newFrom, newTo);
        }, {passive: true});
        const endYDrag = function() { yDrag = null; };
        container.addEventListener('pointerup', endYDrag);
        container.addEventListener('pointerleave', endYDrag);
        container.addEventListener('pointercancel', endYDrag);

        function saveLoop() {
            try {
                if (window[RENDER_KEY] !== RENDER_VERSION) return;
                savePosition(false);
            } catch (_) {}
            requestAnimationFrame(saveLoop);
        }
        requestAnimationFrame(saveLoop);

        let vpBars = d.vp_vols ? d.vp_vols.slice() : null;
        let vpDirty = true;
        if (vpBars && candleSeries) {
            const overlay = document.createElement('canvas');
            overlay.style.cssText = 'position:absolute;left:0;top:0;pointer-events:none;z-index:5;';
            container.appendChild(overlay);
            const ctx = overlay.getContext('2d');

            const MAX_W_FRAC = 0.18;
            const NUM_BINS = 60;

            function drawVPVR() {
                const w = container.clientWidth;
                const mainBottom = MAIN_H;
                const logical = chart.timeScale().getVisibleLogicalRange();
                if (!logical) return;
                const fromLog = Math.max(0, Math.floor(logical.from));
                const toLog = Math.min(vpBars.length - 1, Math.ceil(logical.to));
                if (toLog < fromLog) return;

                const hiPrice = candleSeries.coordinateToPrice(0);
                const loPrice = candleSeries.coordinateToPrice(mainBottom - 1);
                if (hiPrice === null || loPrice === null) return;
                const lo = Math.min(hiPrice, loPrice);
                const hi = Math.max(hiPrice, loPrice);
                if (!(lo < hi)) return;
                const binSize = (hi - lo) / NUM_BINS;
                if (binSize <= 0) return;

                const dpw = typeof window.devicePixelRatio === 'number' ? window.devicePixelRatio : 1;
                if (overlay.width !== Math.floor(w * dpw) || overlay.height !== Math.floor(mainBottom * dpw)) {
                    overlay.width = Math.floor(w * dpw);
                    overlay.height = Math.floor(mainBottom * dpw);
                    overlay.style.width = w + 'px';
                    overlay.style.height = mainBottom + 'px';
                }
                ctx.setTransform(dpw, 0, 0, dpw, 0, 0);
                ctx.clearRect(0, 0, w, mainBottom);

                const buyBins = new Array(NUM_BINS).fill(0);
                const sellBins = new Array(NUM_BINS).fill(0);
                let maxSide = 0;
                let maxTotal = 0;
                for (let i = fromLog; i <= toLog; i++) {
                    const v = vpBars[i];
                    if (!v) continue;
                    const bv = v.buy || 0;
                    const sv = v.sell || 0;
                    if (bv <= 0 && sv <= 0) continue;
                    let bLo = v.low, bHi = v.high;
                    if (bHi < lo || bLo > hi) continue;
                    if (bLo < lo) bLo = lo;
                    if (bHi > hi) bHi = hi;
                    const spanLoIdx = Math.floor((bLo - lo) / binSize);
                    const spanHiIdx = Math.min(NUM_BINS - 1, Math.floor((bHi - lo) / binSize));
                    if (spanHiIdx < spanLoIdx) {
                        const idx = Math.max(0, Math.min(NUM_BINS - 1, Math.floor(((bLo + bHi) / 2 - lo) / binSize)));
                        buyBins[idx] += bv; sellBins[idx] += sv;
                        const tot = buyBins[idx] + sellBins[idx];
                        if (buyBins[idx] > maxSide) maxSide = buyBins[idx];
                        if (sellBins[idx] > maxSide) maxSide = sellBins[idx];
                        if (tot > maxTotal) maxTotal = tot;
                        continue;
                    }
                    const span = bHi - bLo;
                    const buyPerUnit = bv / span;
                    const sellPerUnit = sv / span;
                    for (let b = spanLoIdx; b <= spanHiIdx; b++) {
                        const cLo = Math.max(lo + b * binSize, bLo);
                        const cHi = Math.min(lo + (b + 1) * binSize, bHi);
                        const seg = cHi - cLo;
                        if (seg <= 0) continue;
                        const ba = buyPerUnit * seg;
                        const sa = sellPerUnit * seg;
                        buyBins[b] += ba; sellBins[b] += sa;
                        if (buyBins[b] > maxSide) maxSide = buyBins[b];
                        if (sellBins[b] > maxSide) maxSide = sellBins[b];
                        const tot = buyBins[b] + sellBins[b];
                        if (tot > maxTotal) maxTotal = tot;
                    }
                }
                if (maxTotal <= 0) return;

                const halfW = Math.floor(w * MAX_W_FRAC);
                let pocIdx = 0;
                for (let b = 0; b < NUM_BINS; b++) {
                    if ((buyBins[b] + sellBins[b]) > (buyBins[pocIdx] + sellBins[pocIdx])) pocIdx = b;
                }
                for (let b = 0; b < NUM_BINS; b++) {
                    const bv = buyBins[b];
                    const sv = sellBins[b];
                    if (bv <= 0 && sv <= 0) continue;
                    const priceLo = lo + b * binSize;
                    const priceHi = priceLo + binSize;
                    const yHi = candleSeries.priceToCoordinate(priceHi);
                    const yLo = candleSeries.priceToCoordinate(priceLo);
                    if (yHi === null || yLo === null) continue;
                    let y0 = yHi, y1 = yLo;
                    if (y1 < y0) { const t = y0; y0 = y1; y1 = t; }
                    if (y0 > mainBottom || y1 < 0) continue;
                    const isPoc = (b === pocIdx);
                    const barH = Math.max(1, y1 - y0);
                    const buyLen = Math.floor((bv / maxSide) * halfW);
                    const sellLen = Math.floor((sv / maxSide) * halfW);
                    if (sellLen > 0) {
                        ctx.fillStyle = isPoc ? 'rgba(239,85,92,0.95)' : 'rgba(239,85,92,0.55)';
                        ctx.fillRect(w - sellLen - 2, y0, sellLen, barH);
                    }
                    if (buyLen > 0) {
                        ctx.fillStyle = isPoc ? 'rgba(38,166,154,0.95)' : 'rgba(38,166,154,0.55)';
                        ctx.fillRect(w - sellLen - buyLen - 2, y0, buyLen, barH);
                    }
                }
                const pocPrice = lo + (pocIdx + 0.5) * binSize;
                const pocY = candleSeries.priceToCoordinate(pocPrice);
                if (pocY !== null) {
                    ctx.fillStyle = '#ffeb3b';
                    ctx.font = '10px system-ui, -apple-system, sans-serif';
                    ctx.textAlign = 'right';
                    ctx.fillText('POC ' + pocPrice.toFixed(2), w - 4, pocY + 3 || 0);
                    ctx.textAlign = 'left';
                }
            }

            const ro = new ResizeObserver(function() { vpDirty = true; });
            ro.observe(container);
            chart.timeScale().subscribeVisibleTimeRangeChange(function() {
                if (window[RENDER_KEY] !== RENDER_VERSION) return;
                vpDirty = true;
            });
            chart.timeScale().subscribeVisibleLogicalRangeChange(function() {
                if (window[RENDER_KEY] !== RENDER_VERSION) return;
                vpDirty = true;
            });
            let lastPriceSig = null;
            function vpLoop() {
                if (window[RENDER_KEY] !== RENDER_VERSION) { ro.disconnect(); return; }
                let sig = '';
                try {
                    const topP = candleSeries.coordinateToPrice(0);
                    const botP = candleSeries.coordinateToPrice(MAIN_H - 1);
                    if (topP !== null && botP !== null) sig = topP + ':' + botP;
                } catch (_) {}
                if (sig !== lastPriceSig) {
                    lastPriceSig = sig;
                    vpDirty = true;
                }
                if (vpDirty) {
                    vpDirty = false;
                    try { drawVPVR(); } catch (_) {}
                }
                requestAnimationFrame(vpLoop);
            }
            window[CHART_KEY + '__setVp'] = function(v) {
                vpBars = v ? v.slice() : null;
                vpDirty = true;
            };
            requestAnimationFrame(vpLoop);
        }

        window[CHART_KEY] = {
            chart: chart,
            candleSeries: candleSeries,
            paneSeries: paneSeries,
            paneEdges: paneEdges,
        };
        for (const sk of Object.keys(_allSeriesByKey)) {
            window[CHART_KEY + '_' + sk] = _allSeriesByKey[sk];
        }
        window[CHART_KEY + '__state'] = {
            sig: __cwSigOf(d),
            symbol: d.symbol || '',
            chart: chart,
            candleSeries: candleSeries,
            byKey: _allSeriesByKey,
            container: container,
            setStatusFn: __cwSetStatus,
        };
    }

    // ---------------- Per-tick dispatcher (defined once, in-page) ----------------
    function __cwSigOf(d) {
        const keys = [];
        function collect(list) {
            if (!list) return;
            for (let i = 0; i < list.length; i++) keys.push(list[i].type + '|' + (list[i].key || ''));
        }
        collect(d.series); collect(d.volume_series); collect(d.andean_series); collect(d.iv_skew_series);
        if (d.vp_vols && d.vp_vols.length) keys.push('vp|1');
        keys.sort();
        // Wall level changes (call/put wall values) alter the flat series values:
        // include the current levels so a wall move triggers a full rebuild.
        const ser = d.series || [];
        const walls = [];
        for (let i = 0; i < ser.length; i++) {
            const s = ser[i];
            if (s.key === 'call_wall' || s.key === 'put_wall') {
                const arr = s.data || [];
                walls.push(arr.length ? arr[arr.length - 1].value : null);
            }
        }
        return JSON.stringify([d.symbol || '', keys, d.heights || null, walls]);
    }

    function tryUpdate(ser, row) {
        if (!row) return true;
        try {
            ser.update(row.value === null ? {time: row.time} : row);
            return true;
        } catch (err) {
            return false;
        }
    }

    function __applyRows(ser, rows) {
        if (!ser || !rows || !rows.length) return;
        const prev = ser.__cwN || 0;
        const n = rows.length;
        if (prev === 0 || n < prev) {
            try { ser.setData(rows); } catch (_) {}
            ser.__cwN = n;
            return;
        }
        // n === prev: refresh the last point (live tick). n > prev: append new bars.
        let ok = true;
        const start = (n === prev) ? n - 1 : prev;
        for (let i = start; i < n && ok; i++) {
            ok = tryUpdate(ser, rows[i]);
        }
        if (!ok) {
            // Out-of-order or stale tail: full (visual) replace for this series only.
            try { ser.setData(rows); } catch (_) {}
        }
        ser.__cwN = n;
    }

    function __applyList(byKey, list) {
        if (!list || !byKey) return;
        for (let i = 0; i < list.length; i++) {
            const s = list[i];
            if (s.type === 'Candlestick') continue;
            const series = byKey[s.key];
            if (series) __applyRows(series, s.data);
        }
    }

    window['__cw_tick_' + ROOT_ID] = function(init) {
        try {
            const cur = window[CHART_KEY + '__state'];
            const sig = __cwSigOf(init);
            // If the container vanished or was recreated empty (innerHTML reset,
            // fragment reconciliation), force a rebuild so the chart repaints.
            const containerNow = document.getElementById(ROOT_ID);
            const domOk = !!(containerNow && containerNow.childElementCount > 0);
            if (!cur || cur.sig !== sig || !domOk) {
                // On a symbol switch the saved pan/zoom (incl. PINNED price ranges)
                // belongs to the old ticker's price levels; restoring it would pin
                // the new ticker's price axis to wrong values. Clear it.
                try {
                    if (cur && cur.symbol && init.symbol && cur.symbol !== init.symbol) {
                        window['__lwc_saved_' + ROOT_ID] = null;
                    }
                } catch (_) {}
                try { if (cur && cur.chart && cur.chart.remove) cur.chart.remove(); } catch (_) {}
                window[CHART_KEY + '__state'] = null;
                DATA = {init: init};
                initChart();
                return;
            }
            let cs = null;
            const serList = init.series || [];
            for (let i = 0; i < serList.length; i++) {
                if (serList[i].type === 'Candlestick') { cs = serList[i].data; break; }
            }
            if (cs) __applyRows(cur.candleSeries, cs);
            __applyList(cur.byKey, serList);
            __applyList(cur.byKey, init.volume_series);
            __applyList(cur.byKey, init.andean_series);
            __applyList(cur.byKey, init.iv_skew_series);
            try {
                if (window[CHART_KEY + '__setVp'] && init.vp_vols) window[CHART_KEY + '__setVp'](init.vp_vols);
            } catch (_) {}
            if (cur.setStatusFn) try { cur.setStatusFn(init.status); } catch (_) {}
        } catch (err) {
            if (window.console && console.error) console.error('cw tick error', err);
        }
    };
})();
""" % {'root_id': root_id}


def build_series_key(name: str) -> str:
    return name


def _convert_time(t, et_offset):
    if isinstance(t, (int, float)) and t > 1e11:
        t = int(t / 1000)
    return int(t) + et_offset


def build_init_data(
    candles: list[dict],
    indicators: list[str] | None = None,
    call_wall: float | None = None,
    put_wall: float | None = None,
    last_close: float | None = None,
) -> dict:
    from charts import _get_est_offset, _sma, _ema, _trend, _andean_oscillator, _anchored_vwap, _squeeze_detector, INDICATORS

    try:
        et_offset = _get_est_offset()
    except Exception:
        et_offset = 0

    cd = []
    for c in candles:
        t = _convert_time(c["datetime"], et_offset)
        cd.append({
            "time": t, "open": float(c["open"]),
            "high": float(c["high"]), "low": float(c["low"]),
            "close": float(c["close"]),
        })
    cd.sort(key=lambda x: x["time"])
    seen = set()
    deduped = []
    for c in cd:
        if c["time"] not in seen:
            seen.add(c["time"])
            deduped.append(c)
    cd = deduped

    closes = [c["close"] for c in cd]
    opens = [c["open"] for c in cd]
    highs = [c["high"] for c in cd]
    lows = [c["low"] for c in cd]

    series_list = []
    andean_series = None
    volume_series = None
    vp_vols = None

    candlestick_options = {
        "upColor": "#00cc96", "downColor": "#ef553b",
        "borderUpColor": "#00cc96", "borderDownColor": "#ef553b",
        "wickUpColor": "#00cc96", "wickDownColor": "#ef553b",
    }
    if last_close is not None:
        candlestick_options.update({
            "priceLineVisible": True,
            "priceLineColor": "#ffeb3b",
            "priceLineStyle": 2,
            "priceLineWidth": 1,
            "priceLineSource": 1,
        })

    series_list.append({
        "type": "Candlestick", "key": build_series_key("candlestick"), "data": cd,
        "options": candlestick_options,
    })

    if call_wall is not None:
        series_list.append({
            "type": "Line", "key": build_series_key("call_wall"),
            "data": [{"time": cd[i]["time"], "value": call_wall} for i in range(len(cd))],
            "options": {"color": "#ef553b", "lineWidth": 1, "lineStyle": 2, "title": "Resistance"},
        })
    if put_wall is not None:
        series_list.append({
            "type": "Line", "key": build_series_key("put_wall"),
            "data": [{"time": cd[i]["time"], "value": put_wall} for i in range(len(cd))],
            "options": {"color": "#00cc96", "lineWidth": 1, "lineStyle": 2, "title": "Support"},
        })

    if indicators:
        for name in indicators:
            cfg = INDICATORS.get(name)
            if cfg is None:
                continue
            if name == "Volume":
                vol_map = {}
                buy_map = {}
                sell_map = {}
                for c in candles:
                    t = _convert_time(c["datetime"], et_offset)
                    raw_vol = c.get("volume", 0)
                    if raw_vol is None or raw_vol != raw_vol:
                        raw_vol = 0
                    vol_map[t] = float(raw_vol)
                    if "buy_vol" in c and c.get("buy_vol") is not None:
                        buy_map[t] = int(c.get("buy_vol", 0) or 0)
                    if "sell_vol" in c and c.get("sell_vol") is not None:
                        sell_map[t] = int(c.get("sell_vol", 0) or 0)
                buy_vol = []
                sell_vol = []
                for c in cd:
                    vol = vol_map.get(c["time"], 0)
                    if c["time"] in buy_map and c["time"] in sell_map:
                        bv = buy_map[c["time"]]
                        sv = sell_map[c["time"]]
                    else:
                        hl = c["high"] - c["low"]
                        if hl > 0:
                            bv = round(vol * (c["close"] - c["low"]) / hl)
                            sv = round(vol * (c["high"] - c["close"]) / hl)
                        else:
                            bv = sv = round(vol * 0.5)
                    bv = 0 if (bv is None or bv != bv) else bv
                    sv = 0 if (sv is None or sv != sv) else sv
                    buy_vol.append({"time": c["time"], "value": bv, "color": "#26a69a"})
                    sell_vol.append({"time": c["time"], "value": sv, "color": "#ef5350"})
                volume_series = [
                    {"type": "Histogram", "key": "buy_vol", "data": buy_vol, "options": {"color": "#26a69a", "priceFormat": {"type": "volume"}, "priceScaleId": "volume", "lastValueVisible": False}},
                    {"type": "Histogram", "key": "sell_vol", "data": sell_vol, "options": {"color": "#ef5350", "priceFormat": {"type": "volume"}, "priceScaleId": "volume", "lastValueVisible": False}},
                ]
                continue
            if name == "Andean Squeeze":
                bull, bear, osc, signal = _andean_oscillator(opens, closes, cfg["length"], cfg["sigLength"])
                _oscd = []
                for i in range(len(cd)):
                    o = osc[i]
                    s = signal[i]
                    if o > 0 and o > s:
                        clr = "#00bcd4"
                    elif o > 0 and o < s:
                        clr = "#0d47a1"
                    elif o < 0 and o < s:
                        clr = "#ef5350"
                    else:
                        clr = "#ffa726"
                    _oscd.append({"time": cd[i]["time"], "value": o, "color": clr})
                sqzRed, sqzBlack, sqzOrange = _squeeze_detector(closes, highs, lows)
                sqzRed_data = [{"time": cd[i]["time"], "value": 0.1, "color": "#ef5350"} for i in range(len(cd)) if sqzRed[i] and sqzRed[i].get("state") == "red"]
                sqzBlack_data = [{"time": cd[i]["time"], "value": 0.1, "color": "#000000"} for i in range(len(cd)) if sqzBlack[i] and sqzBlack[i].get("state") == "black"]
                sqzOrange_data = [{"time": cd[i]["time"], "value": 0.1, "color": "#ff9800"} for i in range(len(cd)) if sqzOrange[i] and sqzOrange[i].get("state") == "orange"]
                andean_series = [
                    {"type": "Histogram", "key": "andean_osc", "data": _oscd, "options": {"priceScaleId": "osc", "priceLineVisible": False, "lastValueVisible": False}},
                    {"type": "Line", "key": "andean_signal", "data": [{"time": cd[i]["time"], "value": signal[i]} for i in range(len(cd))], "options": {"color": "#ffa15a", "lineWidth": 2, "priceScaleId": "osc", "priceLineVisible": False, "lastValueVisible": False}},
                    {"type": "Line", "key": "andean_zero", "data": [{"time": cd[i]["time"], "value": 0} for i in range(len(cd))], "options": {"color": "#808080", "lineWidth": 1, "lineStyle": 2, "priceScaleId": "osc", "priceLineVisible": False, "lastValueVisible": False, "crosshairMarkerVisible": False}},
                    {"type": "Histogram", "key": "sqz_red", "data": sqzRed_data, "options": {"priceScaleId": "osc", "priceLineVisible": False, "lastValueVisible": False, "base": 0}},
                    {"type": "Histogram", "key": "sqz_black", "data": sqzBlack_data, "options": {"priceScaleId": "osc", "priceLineVisible": False, "lastValueVisible": False, "base": 0}},
                    {"type": "Histogram", "key": "sqz_orange", "data": sqzOrange_data, "options": {"priceScaleId": "osc", "priceLineVisible": False, "lastValueVisible": False, "base": 0}},
                ]
                continue
            if name == "EMA 50":
                period = cfg.get("period", 50)
                if len(closes) < period:
                    continue
                ema50_vals = _ema(closes, period)
                offset = period - 1
                ema50_data = [{"time": cd[i]["time"], "value": ema50_vals[i - offset]} for i in range(offset, len(cd))]
                if ema50_data:
                    series_list.append({"type": "Line", "key": "ema50", "data": ema50_data, "options": {"color": cfg.get("color", "#ab63fa"), "lineWidth": cfg.get("lineWidth", 2), "lastValueVisible": False, "priceLineVisible": False}})
                continue
            if name == "Volume Profile":
                vol_map = {}
                buy_map = {}
                sell_map = {}
                for c in candles:
                    t = _convert_time(c["datetime"], et_offset)
                    raw_vol = c.get("volume", 0)
                    if raw_vol is None or raw_vol != raw_vol:
                        raw_vol = 0
                    vol_map[t] = float(raw_vol)
                    if "buy_vol" in c and c.get("buy_vol") is not None:
                        buy_map[t] = int(c.get("buy_vol", 0) or 0)
                    if "sell_vol" in c and c.get("sell_vol") is not None:
                        sell_map[t] = int(c.get("sell_vol", 0) or 0)
                vp_vols = []
                for c in cd:
                    vol = vol_map.get(c["time"], 0)
                    if vol is None or vol != vol:
                        vol = 0
                    if c["time"] in buy_map and c["time"] in sell_map:
                        bv = buy_map[c["time"]]
                        sv = sell_map[c["time"]]
                    else:
                        hl = c["high"] - c["low"]
                        if hl > 0:
                            bv = round(vol * (c["close"] - c["low"]) / hl)
                            sv = round(vol * (c["high"] - c["close"]) / hl)
                        else:
                            bv = sv = round(vol * 0.5)
                    bv = 0 if (bv is None or bv != bv) else bv
                    sv = 0 if (sv is None or sv != sv) else sv
                    vp_vols.append({"time": c["time"], "high": c["high"], "low": c["low"], "buy": float(bv), "sell": float(sv)})
                continue
            if name == "Anchored VWAP":
                vol_map = {}
                for c in candles:
                    t = _convert_time(c["datetime"], et_offset)
                    raw_vol = c.get("volume", 0)
                    if raw_vol is None or raw_vol != raw_vol:
                        raw_vol = 0
                    vol_map[t] = float(raw_vol)
                vw_times = [c["time"] for c in cd]
                vw_highs = [c["high"] for c in cd]
                vw_lows = [c["low"] for c in cd]
                vw_closes = [c["close"] for c in cd]
                vw_vols = [vol_map.get(c["time"], 0) or 0 for c in cd]
                vw_vals = _anchored_vwap(vw_times, vw_highs, vw_lows, vw_closes, vw_vols)
                vw_data = [{"time": vw_times[i], "value": vw_vals[i]} for i in range(len(cd)) if vw_vals[i] is not None]
                if vw_data:
                    series_list.append({
                        "type": "Line", "key": "anchored_vwap",
                        "data": vw_data,
                        "options": {
                            "color": cfg.get("color", "#ff9800"),
                            "lineWidth": cfg.get("lineWidth", 2),
                            "lineStyle": 0,
                            "priceLineVisible": False,
                            "lastValueVisible": False,
                        },
                    })
                continue
            if name == "Half Trend":
                mv = _trend(opens, closes, cfg["alphaLength"])
                series_list.append({
                    "type": "Line", "key": "trend",
                    "data": [{"time": cd[i]["time"], "value": mv[i]} for i in range(len(cd))],
                    "options": {"color": cfg.get("color", "#ffa15a"), "lineWidth": cfg.get("lineWidth", 2), "priceLineVisible": False, "lastValueVisible": False},
                })
                continue
            period = cfg.get("period")
            if period is None: continue
            if len(closes) < period: continue
            vals = _ema(closes, period) if name.startswith("EMA") else _sma(closes, period)
            offset = period - 1
            if name in ("EMA 200", "EMA 20", "SMA 50", "SMA 20"):
                opts = {"color": cfg["color"], "lineWidth": cfg["lineWidth"], "lastValueVisible": False}
            else:
                opts = {"color": cfg["color"], "lineWidth": cfg["lineWidth"], "title": name}
            series_list.append({"type": "Line", "key": f"ma_{name}", "data": [{"time": cd[i]["time"], "value": vals[i - offset]} for i in range(offset, len(cd))], "options": opts})

    result = {"isDark": False, "series": series_list}
    if volume_series is not None:
        result["volume_series"] = volume_series
    if andean_series is not None:
        result["andean_series"] = andean_series
    if vp_vols is not None:
        result["vp_vols"] = vp_vols
    return result


def _build_iv_skew_data(iv_skew_history: list, et_offset: int) -> dict | None:
    """Build IV Skew series data for the chart."""
    if not iv_skew_history:
        return None
    try:
        from charts import _get_est_offset
        try:
            et_offset = _get_est_offset()
        except Exception:
            et_offset = 0
    except Exception:
        pass

    series = []
    hist_data = []
    for row in iv_skew_history:
        t = _convert_time(row.get("datetime", 0), et_offset)
        val = row.get("value", 0)
        hist_data.append({"time": t, "value": float(val) if val is not None else 0})

    if hist_data:
        series.append({
            "type": "Line",
            "key": "iv_skew",
            "data": hist_data,
            "options": {"color": "#9c27b0", "lineWidth": 2, "priceScaleId": "iv_skew", "priceLineVisible": False, "lastValueVisible": False},
        })

    # IV Skew Histogram (positive = premium, negative = discount)
    hist_bar_data = []
    for row in iv_skew_history:
        t = _convert_time(row.get("datetime", 0), et_offset)
        val = row.get("histogram", 0)
        if val is not None:
            color = "#26a69a" if val >= 0 else "#ef5350"
            hist_bar_data.append({"time": t, "value": float(val), "color": color})

    if hist_bar_data:
        series.append({
            "type": "Histogram",
            "key": "iv_skew_hist",
            "data": hist_bar_data,
            "options": {"priceScaleId": "iv_skew_hist", "priceLineVisible": False, "lastValueVisible": False},
        })

    return {"series": series} if series else None


def render_chart_host():
    """Render the persistent chart host element (constant body).

    Must be called every fragment tick (including when there is no candle
    payload) so the host div always exists and the chart DOM survives.
    """
    st.html(get_host_html(), unsafe_allow_javascript=True, width="stretch")


def render_chart(candles, indicators=None, call_wall=None, put_wall=None, last_close=None, status=None, symbol="SPY", iv_skew_history=None):
    main_height = 420
    vol_height = 100 if (indicators and "Volume" in indicators) else 0
    osc_height = 100 if (indicators and "Andean Squeeze" in indicators) else 0
    iv_skew_height = 100 if (indicators and "IV Skew (25Δ)" in indicators) and iv_skew_history and len(iv_skew_history) > 0 else 0
    iv_skew_hist_height = 50 if (indicators and "IV Skew (25Δ)" in indicators) and iv_skew_history and len(iv_skew_history) > 0 else 0

    # Try to get ET offset for consistent time conversion
    try:
        from charts import _get_est_offset
        et_offset = _get_est_offset()
    except Exception:
        et_offset = 0

    init_data = build_init_data(candles, indicators, call_wall, put_wall, last_close=last_close)
    if status:
        init_data["status"] = status

    # Build IV skew data if available
    if iv_skew_history and len(iv_skew_history) > 0:
        iv_skew_result = _build_iv_skew_data(iv_skew_history, et_offset)
        if iv_skew_result:
            init_data["iv_skew_series"] = iv_skew_result.get("series", [])

    init_data["symbol"] = symbol
    init_data["heights"] = {
        "main": main_height, "vol": vol_height, "osc": osc_height,
        "iv_skew": iv_skew_height, "iv_skew_hist": iv_skew_hist_height,
    }
    init_data["theme"] = {"bg": "#ffffff", "text": "#1e293b", "grid": "#e9eef3"}

    # Dispatch the current data. The host element is rendered by
    # render_chart_host() (called every tick, unconditional). This element's
    # body changes every tick, so its script re-executes and the host
    # dispatcher either rebuilds (structure changed) or updates just the last
    # bar of each series.
    payload_js = json.dumps(init_data).replace("<", "\\u003c")
    payload_html = (
        '<script>window.__cw_tick_' + _ROOT_ID
        + ' && window.__cw_tick_' + _ROOT_ID + '(' + payload_js + ');</script>'
    )
    st.html(payload_html, unsafe_allow_javascript=True, width="stretch")


_HOST_JS_CACHE: str | None = None


def get_host_html() -> str:
    """Constant host HTML: vendored LWC script tag + container div + chart code."""
    global _HOST_JS_CACHE
    if _HOST_JS_CACHE is None:
        _ensure_static_lib()
        _HOST_JS_CACHE = (
            '<script src="' + _STATIC_LIB_URL + '"></script>'
            '<div id="' + _ROOT_ID + '" style="width:100%;position:relative;"></div>'
            '<script>' + build_host_js(_ROOT_ID) + '</script>'
        )
    return _HOST_JS_CACHE
