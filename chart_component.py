"""Lightweight-charts component rendered via st.html with unique root IDs.

Each call generates a unique DOM element ID so that Streamlit re-renders
(fragment re-execution, tab switches) always target the correct container.
"""

import json
import streamlit as st

_JS_LIB = '<script src="https://unpkg.com/lightweight-charts@4.2.1/dist/lightweight-charts.standalone.production.js"></script>'

_HTML_TEMPLATE = """
<div id="%(root_id)s" style="position:relative;width:100%%;"></div>
%(lib)s
<script>
(function() {
    const ROOT_ID = '%(root_id)s';
    const DATA = %(json_data)s;
    const container = document.getElementById(ROOT_ID);

    // ---- Cancel stale callbacks from previous renders ----------------- //
    const RENDER_KEY = '__lwc_render_' + ROOT_ID;
    const RENDER_VERSION = (window[RENDER_KEY] || 0) + 1;
    window[RENDER_KEY] = RENDER_VERSION;

    // ---- Preserve visible range across Streamlit re-renders ---------- //
    const SAVED_KEY = '__lwc_saved_' + ROOT_ID;
    const prevSaved = window[SAVED_KEY];
    window[SAVED_KEY] = null;

    const d = DATA.init;
    const bg = '%(bg)s';
    const tc = '%(tc)s';
    const gc = '%(gc)s';

    // -------- Single chart with multiple price scales (shared x-axis) ----- //
    // All series (candlesticks, volume, ATM, oscillator) live in one chart
    // instance so they natively share the same time scale.  Each group gets
    // its own price scale (a vertical pane) via priceScaleId on the series.
    const MAIN_H = %(main_height)d;
    const VOL_H = %(vol_height)d;
    const OSC_H = %(osc_height)d;
    const IV_SKEW_H = %(iv_skew_height)d;
    const IV_SKEW_HIST_H = %(iv_skew_hist_height)d;

    // Build visible pane list so chart height adjusts to whichever
    // indicators are active — the main pane gets the full window when
    // no indicators are shown.
    const panes = [{id: 'right', h: MAIN_H}];
    if (d.volume_series) panes.push({id: 'volume', h: VOL_H});
    if (d.andean_series) panes.push({id: 'osc', h: OSC_H});
    if (d.iv_skew_series) panes.push({id: 'iv_skew', h: IV_SKEW_H});
    if (d.iv_skew_hist) panes.push({id: 'iv_skew_hist', h: IV_SKEW_HIST_H});

    // Defensive: collect EVERY priceScaleId referenced by any series so
    // we can guarantee a dedicated pane exists for each indicator scale.
    // An indicator series must NEVER fall back to the candlestick 'right'
    // price scale — that would mix oscillator/volume values with price and
    // corrupt the visible range of the main pane.
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

    const GAP = 4; // px margin on each side of every price scale

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
        },
    });

    let candleSeries = null;
    // Per-priceScale list of series handles so we can read/write each pane's
    // visible price range via coordinateToPrice/priceToCoordinate AND pin the
    // range across EVERY series on the pane (LWC v4 unions the
    // autoscaleInfoProvider outputs of all attached series, so installing
    // the provider on only one series is insufficient — other series would
    // push the price scale back to their own data's fit range).
    const paneSeries = {};          // {paneId: firstSeries} — used by read watchers
    const paneSeriesAll = {};       // {paneId: [series, ...]}
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
        }
        if (series && s.key) {
            _allSeriesByKey[s.key] = series;
        }
        // Track every series attached to each sub-pane price scale and on the
        // main 'right' pane (Line overlays like SMA/EMA/Trend/Anchored VWAP/
        // Call Wall/Put Wall live on the right pane too — they must all be
        // pinned when we restore a manual y-zoom, otherwise LWC unions their
        // default auto-fit range with our pinned range and the pin loses).
        if (series) {
            // An indicator series MUST keep its dedicated priceScaleId and
            // never fall back to the candlestick 'right' scale. If the series
            // declared a non-right priceScaleId but that pane was somehow not
            // created, we drop the series entirely rather than contaminate the
            // main price scale with oscillator/volume values.
            const declaredPid = (s.options || {}).priceScaleId;
            if (declaredPid && declaredPid !== 'right') {
                if (!paneIds.has(declaredPid)) {
                    // Pane missing — refuse to add to 'right'. Discard series.
                    try { chart.removeSeries(series); } catch (_) {}
                    return;
                }
            }
            const pid = declaredPid || 'right';
            _registerSeries(pid, series);
        }
    }

    // Add all series to the single chart. Sub-pane series have a priceScaleId
    // in their options so they render on their own price scale.
    for (const s of d.series || []) { addSeries(s); }
    for (const s of d.volume_series || []) { addSeries(s); }
    for (const s of d.andean_series || []) { addSeries(s); }
    for (const s of d.iv_skew_series || []) { addSeries(s); }
    for (const s of d.iv_skew_hist || []) { addSeries(s); }

    // ---- Configure ALL price scale margins + Y-axis visibility ---------- //
    // scaleMargins.top  = distance from chart TOP    to price scale TOP    (fraction)
    // scaleMargins.bottom = distance from chart BOTTOM to price scale BOTTOM (fraction)
    // Also build paneEdges[] mapping pane.id -> {top, bottom} in canvas pixels
    // so the save/restore Y-zoom code can sample coordinateToPrice() at the
    // correct pane bounds (the chart canvas spans TOTAL_H, but each pane
    // occupies only its own [top, bottom] slice of that single canvas).
    //
    // Each indicator pane gets its OWN visible y-axis (price scale) so the
    // oscillator / volume values render their own tick labels instead of
    // being absorbed into the candlestick 'right' scale. LWC v4 overlays
    // every price scale on the same right edge by default; to give each pane
    // a distinct, readable axis we (a) set `visible: true` and
    // `borderVisible: true` so the axis line + ticks draw, and (b) install a
    // per-series `priceFormat` so the tick labels format in the pane's own
    // units (volume vs. raw oscillator value) rather than inheriting the
    // candlesticks' price format. The scaleMargins slice each pane to its own
    // vertical band so the y-axes never overlap.
    const paneEdges = {};
    let y = 0;
    for (const p of panes) {
        const topPx = y + GAP;
        const bottomPx = y + p.h - GAP;
        paneEdges[p.id] = {top: topPx, bottom: bottomPx};
        // autoScale defaults to true so brand-new panes fit their data;
        // restoreRange() (below) turns it OFF for any pane that has a saved
        // manual y-zoom, otherwise LWC immediately overwrites the user's
        // zoom with a fit-to-bars range on the next animation frame.
        const isMain = (p.id === 'right');
        chart.priceScale(p.id).applyOptions({
            scaleMargins: {top: topPx / TOTAL_H, bottom: (TOTAL_H - bottomPx) / TOTAL_H},
            visible: true,
            autoScale: true,
            borderVisible: true,
            // The main 'right' scale inherits the candlestick priceFormat.
            // Indicator scales get a plain numeric formatter so their own
            // y-axis tick labels show the pane's values (volume / oscillator)
            // instead of mirroring the candlestick's $price formatting.
            // We hide LWC's built-in axis labels for indicator panes and
            // draw our own via the custom canvas overlay below — this avoids
            // two overlapping sets of labels that appear misaligned.
            ...(isMain ? {} : {
                visible: false,
                borderVisible: false,
                mode: 0,
            }),
        });
        y += p.h;
    }

    // Tag every indicator-pane series with a numeric priceFormat so the
    // pane's own y-axis renders tick labels in the indicator's units rather
    // than the candlestick's currency format. Volume/ATM histograms already
    // carry a volume priceFormat; Andean Osc lines get a price-style format.
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

    // ---- Custom y-axis overlay for each indicator pane ------------------- //
    // LWC v4 overlays every price scale on the same right edge, so indicator
    // panes don't get their own visible, independent y-axis tick labels by
    // default — their values mirror the candlestick 'right' scale. To give
    // each pane its own axis with its OWN values, we draw a canvas overlay on
    // the right edge of each indicator pane and render tick labels computed
    // from that pane's series priceToCoordinate() mapping. The overlay also
    // paints a background strip that covers LWC's overlaid axis labels so the
    // candlestick's $price ticks don't bleed into the indicator panes.
    const AXIS_W = 60;  // px width reserved on the right for label strips
    const indicatorPanes = panes.filter(function(p) { return p.id !== 'right'; });
    const axisOverlays = [];  // {paneId, canvas, ctx, lastSig}
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
        // Derive the pane's visible price range from the series mapping at
        // the pane's top/bottom canvas edges.
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
        // Choose ~5 "nice" tick values across the pane's value range.
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
        // Background strip covers LWC's overlaid candlestick axis labels so
        // the indicator pane only shows its own values.
        ctx.fillStyle = bg;
        ctx.fillRect(0, 0, stripW, stripH);
        // Border line on the left edge of the strip.
        ctx.strokeStyle = gc;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(0.5, 0);
        ctx.lineTo(0.5, stripH);
        ctx.stroke();
        // Tick labels.
        ctx.fillStyle = tc;
        ctx.font = '11px system-ui, -apple-system, sans-serif';
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        for (let i = 0; i < NUM_TICKS; i++) {
            const frac = (NUM_TICKS === 1) ? 0.5 : i / (NUM_TICKS - 1);
            const val = lo + frac * span;
            // Map this value back to a canvas y within the pane.
            let cy;
            try { cy = series.priceToCoordinate(val); } catch (_) { continue; }
            if (cy == null) continue;
            // Translate to strip-local coords (strip starts at edges.top).
            const localY = cy - edges.top;
            if (localY < 0 || localY > stripH) continue;
            // Faint tick mark.
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

    // Redraw axis overlays whenever the time/x range or any pane y-range moves.
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
        // Detect pane y-range movement by sampling each indicator pane's
        // top/bottom mapped price; redraw only when it changes.
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



    // Streaming status overlay — drawn on top of the candlestick pane.
    // Replaces the old separate st.info / st.warning widget above the chart.
    if (d.status && d.status.text) {
        const lvl = d.status.level || 'info';
        const colors = {
            'info':    {bg: 'rgba(33,150,243,0.92)', fg: '#ffffff'},
            'success': {bg: 'rgba(0,204,150,0.92)', fg: '#0e1117'},
            'warning': {bg: 'rgba(255,193,7,0.95)',  fg: '#31333f'},
        };
        const c = colors[lvl] || colors['info'];
        const badge = document.createElement('div');
        badge.textContent = d.status.text;
        badge.style.cssText = 'position:absolute;top:4px;left:4px;padding:4px 10px;border-radius:6px;background:' + c.bg + ';color:' + c.fg + ';font-size:12px;font-weight:600;pointer-events:none;z-index:10;box-shadow:0 1px 3px rgba(0,0,0,0.35);white-space:nowrap;';
        container.appendChild(badge);
    }

    // ---- Save/restore visible range across fragment re-renders --------- //
    const ts = chart.timeScale();

    // readVisibleRange(id) returns the live visible price range of a pane
    // by sampling the series attached to it at the pane's top/bottom
    // canvas pixel edges (LWC v4 IPriceScaleApi has no range getter/setter,
    // but ISeriesApi exposes coordinateToPrice / priceToCoordinate).
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

    // applyVisibleRange(id, from, to) restores a saved manual y-zoom by
    // installing an `autoscaleInfoProvider` on EVERY series attached to the
    // pane (LWC v4 unions each series's autoscaleInfoProvider output to
    // compute the price scale's range — installing it on only one series
    // would let the OTHER series' default auto-fit override the pin).
    // It also forces the price scale's autoScale true so the providers
    // are consulted. Once the user drags Y, LWC flips autoScale off for
    // that pane itself; pointers/wheel then update the saved range and
    // the next 1s render re-pins all series to the new range. Sticking
    // to autoScale=true (no rAF-flip-to-false) avoids a race between
    // restore and the user's own first drag gesture.
    //
    // pinnedPanes tracks every pane that has a provider-pin currently
    // installed. Because we keep autoScale=true on pinned panes (so the
    // provider is consulted), ps.options().autoScale reads true EVEN
    // after a Y drag has ended; without this set savePosition(false)
    // could not distinguish a pinned pane from an untouched auto-fit pane
    // and would null-out the saved Y range on every x-gesture callback
    // (e.g. the async subscribeVisibleTimeRangeChange fired by the X
    // restore itself), causing the Y zoom to silently snap back.
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
        // Read each pane's visible y-range. Persistence rules:
        //   - forcePrice=true (a user Y gesture just ended — y body-drag
        //     OR native axis-label drag): sample the painted range via
        //     readVisibleRange so the captured value reflects EXACTLY what
        //     the user dragged to, even when LWC entered manual mode
        //     (autoScale=false) outside our provider pin (native axis-label
        //     drag doesn't install a pin of ours). Using the pin's stored
        //     value here would silently ignore native axis-label drags and
        //     snap back to whatever we last pinned.
        //   - forcePrice=false (per-frame re-save, async x-range callback
        //     during re-render): if our provider pin is installed, return
        //     the pin's exact from/to WITHOUT re-sampling the canvas. LWC's
        //     internal price→coordinate rounding accumulates epsilon every
        //     tick, so re-sampling caused the saved range to drift slowly
        //     upward as new bars streamed in. Returning the pin value
        //     losslessly freezes the user's Y-zoom across re-renders.
        //   - Untouched pane (auto-fit, no pin, forcePrice=false) → null
        //     so autoscale-to-data behaviour stays intact.
        function snapPrice(id) {
            const ps = chart.priceScale(id);
            let auto = true;
            try { auto = !!ps.options().autoScale; } catch (_) {}
            const pin = pinnedPanes[id];
            if (forcePrice) {
                // Genuine user gesture just ended — capture reality.
                return readVisibleRange(id);
            }
            if (pin) {
                // Re-save path (per-frame / async) — use the lossless pin.
                return { from: pin.from, to: pin.to };
            }
            // Manual pane (LWC native axis-label drag) — we have no pin but
            // LWC marks autoScale=false; preserve its live range.
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

    // Restore range SYNCHRONOUSLY right after chart creation + data set,
    // before yielding to the browser paint cycle — eliminates the flicker
    // caused by the old requestAnimationFrame-based deferred restore.
    let restoredPanes = null;  // {pid: {from,to}} that we just restored
    if (prevSaved && (prevSaved.logicalRange || prevSaved.mainRange)) {
        restoreRange(ts, prevSaved);
        // Restore each pane's manual y-zoom via its attached series'
        // autoscaleInfoProvider + autoScale:true (LWC v4 IPriceScaleApi has
        // no price-range setter; the series-level provider is the supported
        // mechanism for fixing a price scale's range at init time).
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

    // Re-establish the saved state on window so it survives the next 1s
    // fragment re-render, and pre-populate X-range too (mirrors prevSaved).
    // This call will NOT clobber restoredPanes because applyVisibleRange
    // left autoScale=true on those panes → snapPrice(forcePrice=false)
    // returns null for them. So we explicitly re-seed window[SAVED_KEY]
    // with the restored Y-ranges right after, on the first animation frame
    // once LWC has painted and coordinateToPrice becomes readable.
    savePosition();
    if (restoredPanes && Object.keys(restoredPanes).length) {
        // Immediately re-seed with the restored Y-ranges so the next
        // fragment render restores from them even before any user gesture
        // (savePosition() above doesn't capture auto=true panes).
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

    // Save at the end of every drag/zoom gesture on the TIME (x) axis.
    // Don't forcePrice here — x-gestures cause autoScale to refit y,
    // and we must NOT pin that refit range on a pane the user never
    // manually y-zoomed (otherwise the auto-fit-to-data behaviour is
    // lost once they touch the x-axis). savePosition() will still save
    // the current y range of panes already in manual mode (autoScale off).
    ts.subscribeVisibleTimeRangeChange(function(timeRange) {
        if (!timeRange) return;
        if (window[RENDER_KEY] !== RENDER_VERSION) return;
        savePosition(false);
    });

    // Catch y-axis-only pan/zoom gestures, which do NOT fire
    // subscribeVisibleTimeRangeChange. forcePrice=true ENABLES save for
    // the pane(s) the user just touched even if autoScale is still
    // returning true at this exact moment (LWC flips autoScale off
    // slightly asynchronously). This is the path that actually persists
    // a drag/zoom on the Y axis end-of-gesture — see the pointerup and
    // wheel handlers below.
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

    // ---- TradingView-style body drag pans Y (and the section above) -------- //
    // LWC v4's `pressedMouseMove` only pans the TIME (X) scale when you drag
    // in the chart body. To match TradingView (drag in body pans BOTH axes),
    // we add a parallel pointer gesture that pans the visible PRICE range of
    // whichever pane the user pressed in. The horizontal motion keeps being
    // handled by LWC natively (so X+Y pan together); we only handle the
    // vertical component here. Dragging directly on a price-AXIS label is
    // left to LWC's built-in `axisPressedMouseMove.price` handler; we only
    // engage when the gesture starts in a pane's chart body (not over an
    // axis label area, time scale (bottom) or the volume-profile overlay).
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
        // Time scale sits at the very bottom; if y is in that strip we let
        // LWC handle it (horizontal-only pan) — there's no Y to pan there.
        return px >= chartW - axisW;
    }
    container.addEventListener('pointerdown', function(ev) {
        // Only respond to the primary (left) button — right-click / middle
        // are reserved.
        if (ev.button !== 0) return;
        if (window[RENDER_KEY] !== RENDER_VERSION) return;
        const r = container.getBoundingClientRect();
        const px = ev.clientX - r.left;
        const py = ev.clientY - r.top;
        // Don't engage if the press is over a price-axis label (LWC's
        // axisPressedMouseMove.price handles it natively) or on the time
        // scale at the bottom of the chart.
        if (overPriceAxisLabel(px, py)) return;
        const tScaleH = 28; // approximate height of LWC's bottom time scale
        if (py > TOTAL_H - tScaleH) return;
        const p = paneAt(py);
        if (!p) return;
        // Snapshot the LIVE visible price range to pan from. If a provider
        // pin is currently installed (manual mode from a prior Y gesture),
        // readVisibleRange reads that pinned range. Otherwise we read the
        // auto-fit range — first pan from there is fine.
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
        if (!(ev.buttons & 1)) { yDrag = null; return; } // button released
        const r = container.getBoundingClientRect();
        const py = ev.clientY - r.top;
        const dy = py - yDrag.startY;
        if (!yDrag.moving && Math.abs(dy) < 3) return; // dead-zone for clicks
        yDrag.moving = true;
        const span = yDrag.startTo - yDrag.startFrom;
        if (!(span > 0)) return;
        const paneH = yDrag.botPx - yDrag.topPx;
        if (paneH <= 0) return;
        // The content under the cursor should follow the cursor (TradingView
        // "grab the chart and drag it" feel): drag DOWN → prices move DOWN
        // on screen → visible range shifts UP in price. So shift is +dy-based
        // and the range goes UP (newFrom/newTo increase) as the user drags
        // down. Drag UP → content follows up → visible range shifts DOWN.
        const shift = (dy / paneH) * span;
        const newFrom = yDrag.startFrom + shift;
        const newTo = yDrag.startTo + shift;
        applyVisibleRange(yDrag.paneId, newFrom, newTo);
    }, {passive: true});
    const endYDrag = function() { yDrag = null; };
    container.addEventListener('pointerup', endYDrag);
    container.addEventListener('pointerleave', endYDrag);
    container.addEventListener('pointercancel', endYDrag);

    // Per-frame fallback so mid-gesture fragment re-renders (which can
    // fire at any second boundary) pick up the very latest x + y range
    // even between user pointer events. savePosition() skips panes that
    // are still in autoScale, so this never corrupts a not-yet-touched
    // pane — it only persists the manual mode the user has engaged.
    function saveLoop() {
        try {
            if (window[RENDER_KEY] !== RENDER_VERSION) return;
            savePosition(false);
        } catch (_) {}
        requestAnimationFrame(saveLoop);
    }
    requestAnimationFrame(saveLoop);
    // ---- Volume Profile Visible Range (VPVR) right-edge overlay --------- //
    // Bins bar volume by price across the bars currently visible on the
    // main pane's x-axis and draws horizontal bars on a transparent canvas
    // layered above LWC's price scale (right edge). POC (max-volume bin) is
    // rendered brighter; the rest are translucent. Recomputes whenever the
    // visible time range or the main pane's visible price range changes.
    const vpBars = d.vp_vols ? d.vp_vols.slice() : null;
    if (vpBars && candleSeries) {
        // Overlay canvas — sized/clipped to the main (top) pane only.
        const overlay = document.createElement('canvas');
        overlay.style.cssText = 'position:absolute;left:0;top:0;pointer-events:none;z-index:5;';
        container.appendChild(overlay);
        const ctx = overlay.getContext('2d');

        const MAX_W_FRAC = 0.18;   // widest VPVR bar = 18%% of chart width
        const NUM_BINS = 60;       // price-level resolution
        let vpDirty = true;

        function drawVPVR() {
            const w = container.clientWidth;
            const mainBottom = MAIN_H; // main pane occupies [0, MAIN_H)
            const logical = chart.timeScale().getVisibleLogicalRange();
            if (!logical) return;
            // The candlestick series was built from the same array as `vpBars`,
            // so vpBars[i] corresponds to logical index i (same order, no gaps).
            // LWC v4's series API exposes no .data() getter, so we index
            // vpBars directly by logical index in the visible window.
            const fromLog = Math.max(0, Math.floor(logical.from));
            const toLog = Math.min(vpBars.length - 1, Math.ceil(logical.to));
            if (toLog < fromLog) return;

            // Visible price range — derive from the chart's coordinate→price
            // mapping at the main pane's top/bottom edges. This works for
            // both autoScale (fits bars) AND manual y-zoom, and avoids
            // IPriceScaleApi which has no range getter in LWC v4.
            const hiPrice = candleSeries.coordinateToPrice(0);
            const loPrice = candleSeries.coordinateToPrice(mainBottom - 1);
            if (hiPrice === null || loPrice === null) return;
            const lo = Math.min(hiPrice, loPrice);
            const hi = Math.max(hiPrice, loPrice);
            if (!(lo < hi)) return;
            const binSize = (hi - lo) / NUM_BINS;
            if (binSize <= 0) return;

            // Hi-DPI sizing.
            const dpw = typeof window.devicePixelRatio === 'number' ? window.devicePixelRatio : 1;
            if (overlay.width !== Math.floor(w * dpw) || overlay.height !== Math.floor(mainBottom * dpw)) {
                overlay.width = Math.floor(w * dpw);
                overlay.height = Math.floor(mainBottom * dpw);
                overlay.style.width = w + 'px';
                overlay.style.height = mainBottom + 'px';
            }
            ctx.setTransform(dpw, 0, 0, dpw, 0, 0);
            ctx.clearRect(0, 0, w, mainBottom);

            // Bin buy- and sell-volume separately across [bar.low, bar.high]
            // for each visible bar. Buy/sell split comes from the websocket
            // streaming buy_vol/sell_vol; bars without it fall back to a
            // price-proxy split computed in build_init_data (see Python).
            // maxVol is the largest BUY-or-SELL bin so each side is drawn
            // against a common scale (POC = the bin with the max combined
            // volume — buy+sell — so the price level with the most traded
            // volume is highlighted regardless of direction).
            const buyBins = new Array(NUM_BINS).fill(0);
            const sellBins = new Array(NUM_BINS).fill(0);
            let maxSide = 0;  // max single side (for scaling bar widths)
            let maxTotal = 0; // max buy+sell (for POC)
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

            // Draw horizontal bars from the right edge. Sell (red) attaches
            // to the right edge; Buy (green) extends to its left, so both
            // sides of the buy/sell split are visible without occlusion.
            // POC (max total volume bin) is drawn with brighter fills.
            const halfW = Math.floor(w * MAX_W_FRAC); // max width per side (buy | sell)
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
                // Sell (red) attaches to the right edge; buy (green) extends
                // to its left so both halves of the split are visible.
                if (sellLen > 0) {
                    ctx.fillStyle = isPoc ? 'rgba(239,85,92,0.95)' : 'rgba(239,85,92,0.55)';
                    ctx.fillRect(w - sellLen - 2, y0, sellLen, barH);
                }
                if (buyLen > 0) {
                    ctx.fillStyle = isPoc ? 'rgba(38,166,154,0.95)' : 'rgba(38,166,154,0.55)';
                    ctx.fillRect(w - sellLen - buyLen - 2, y0, buyLen, barH);
                }
            }
            // POC price label on the right edge.
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

        // Recompute on visible-range change and on resize.
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
        // Also redraw whenever the main price scale's visible range shifts
        // (autoScale refits, manual y-zoom, etc.) by polling the saved
        // range each frame; if it moved, flip vpDirty. LWC v4's price-scale
        // API exposes no range getter, so we sample coordinateToPrice at
        // the main pane's top/bottom edges to detect y-range movement.
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
        requestAnimationFrame(vpLoop);
    }

    // ---- Store chart references for streaming updates (avoid full redraw) --- //
    const CHART_KEY = '__lwc_chart_' + ROOT_ID;
    window[CHART_KEY] = {
        chart: chart,
        candleSeries: candleSeries,
        paneSeries: paneSeries,
        paneEdges: paneEdges,
    };
    // Store each indicator series by key so update script can find+update it
    for (const sk of Object.keys(_allSeriesByKey)) {
        window[CHART_KEY + '_' + sk] = _allSeriesByKey[sk];
    }
})();
"""

_UPDATE_TEMPLATE = """
<script>
(function() {
    const ROOT_ID = '%(root_id)s';
    const DATA = %(json_data)s;
    const RENDER_KEY = '__lwc_render_' + ROOT_ID;
    const curVer = (window[RENDER_KEY] || 0) + 1;
    window[RENDER_KEY] = curVer;

    // Check if chart exists from initial render
    const CHART_KEY = '__lwc_chart_' + ROOT_ID;
    const chartRef = window[CHART_KEY];
    if (!chartRef) return;

    // Update candlestick if new bar provided
    if (DATA.update && DATA.update.bar) {
        try { chartRef.candleSeries.update(DATA.update.bar); } catch (_) {}
    }

    // Update indicators
    if (DATA.update && DATA.update.indicators) {
        const ind = DATA.update.indicators;
        for (const key of Object.keys(ind)) {
            const sKey = CHART_KEY + '_' + key;
            const series = window[sKey];
            if (series) {
                try { series.update(ind[key]); } catch (_) {}
            }
        }
    }

    // Update IV skew
    if (DATA.update && DATA.update.iv_skew) {
        const ivData = DATA.update.iv_skew;
        if (ivData.iv_skew != null) {
            const mainKey = CHART_KEY + '_iv_skew_main';
            const sMain = window[mainKey];
            if (sMain) {
                try { sMain.update({time: ivData.time, value: ivData.iv_skew}); } catch (_) {}
            }
            const histKey = CHART_KEY + '_iv_skew_hist_series';
            const sHist = window[histKey];
            if (sHist) {
                try { sHist.update({time: ivData.time, value: ivData.iv_skew}); } catch (_) {}
            }
            if (ivData.put_iv_25d != null) {
                const s = window[CHART_KEY + '_iv_skew_put'];
                if (s) try { s.update({time: ivData.time, value: ivData.put_iv_25d}); } catch (_) {}
            }
            if (ivData.call_iv_25d != null) {
                const s = window[CHART_KEY + '_iv_skew_call'];
                if (s) try { s.update({time: ivData.time, value: ivData.call_iv_25d}); } catch (_) {}
            }
            if (ivData.atm_iv != null) {
                const s = window[CHART_KEY + '_iv_skew_atm'];
                if (s) try { s.update({time: ivData.time, value: ivData.atm_iv}); } catch (_) {}
            }
        }
    }

    // Save visible range after update
    try {
        const SAVED_KEY = '__lwc_saved_' + ROOT_ID;
        const ts = chartRef.chart.timeScale();
        const tr = ts.getVisibleRange();
        if (tr) {
            const subPriceRanges = {};
            // Sample each indicator pane's Y range losslessly
            for (const pid of Object.keys(chartRef.paneSeries)) {
                if (pid === 'right') continue;
                const series = chartRef.paneSeries[pid];
                if (!series) continue;
                try {
                    const topP = series.coordinateToPrice(chartRef.paneEdges[pid].top);
                    const botP = series.coordinateToPrice(chartRef.paneEdges[pid].bottom);
                    if (topP != null && botP != null) {
                        subPriceRanges[pid] = {from: Math.min(topP, botP), to: Math.max(topP, botP)};
                    }
                } catch (_) {}
            }
            window[SAVED_KEY] = {
                mainRange: { from: tr.from, to: tr.to },
                subPriceRanges: subPriceRanges,
                hasManual: true,
            };
        }
    } catch (_) {}
})();
</script>
"""


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
    from charts import _get_est_offset, _sma, _ema, _trend, _andean_oscillator, _ema50_squeeze, _anchored_vwap, INDICATORS

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
    atm_series = None
    iv_skew_series = None
    iv_skew_hist = None
    vp_vols = None

    candlestick_options = {
        "upColor": "#00cc96", "downColor": "#ef553b",
        "borderUpColor": "#00cc96", "borderDownColor": "#ef553b",
        "wickUpColor": "#00cc96", "wickDownColor": "#ef553b",
    }
    # Last-close yellow dashed price line (matches the original Plotly "Close: $X.XX" line)
    if last_close is not None:
        candlestick_options.update({
            "priceLineVisible": True,
            "priceLineColor": "#ffeb3b",
            "priceLineStyle": 2,  # dashed
            "priceLineWidth": 1,
            "priceLineSource": 1,  # last bar
        })

    series_list.append({
        "type": "Candlestick", "key": build_series_key("candlestick"), "data": cd,
        "options": candlestick_options,
    })

    if call_wall is not None:
        series_list.append({
            "type": "Line", "key": build_series_key("call_wall"),
            "data": [{"time": cd[i]["time"], "value": call_wall} for i in range(len(cd))],
            "options": {"color": "#ef553b", "lineWidth": 1, "lineStyle": 2, "title": "Call Wall"},
        })
    if put_wall is not None:
        series_list.append({
            "type": "Line", "key": build_series_key("put_wall"),
            "data": [{"time": cd[i]["time"], "value": put_wall} for i in range(len(cd))],
            "options": {"color": "#00cc96", "lineWidth": 1, "lineStyle": 2, "title": "Put Wall"},
        })

    if indicators:
        for name in indicators:
            cfg = INDICATORS.get(name)
            # NB: some indicators (Volume, EMA 50 Squeeze) use an
            # empty cfg dict on purpose — only skip if the name is unknown entirely.
            if cfg is None:
                continue
            if name == "Volume":
                vol_map = {}
                buy_map = {}
                sell_map = {}
                for c in candles:
                    t = _convert_time(c["datetime"], et_offset)
                    raw_vol = c.get("volume", 0)
                    if raw_vol is None or raw_vol != raw_vol:  # NaN check
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
                # Volume series use a separate price scale ('volume') on the
                # single shared chart, surfaced via result["volume_series"].
                volume_series = [
                    {"type": "Histogram", "key": "buy_vol", "data": buy_vol, "options": {"color": "#26a69a", "priceFormat": {"type": "volume"}, "priceScaleId": "volume", "lastValueVisible": False}},
                    {"type": "Histogram", "key": "sell_vol", "data": sell_vol, "options": {"color": "#ef5350", "priceFormat": {"type": "volume"}, "priceScaleId": "volume", "lastValueVisible": False}},
                ]
                continue
            if name == "Andean Osc":
                bull, bear, signal = _andean_oscillator(opens, closes, cfg["length"], cfg["sigLength"])
                andean_series = [
                    {"type": "Line", "key": "andean_bull", "data": [{"time": cd[i]["time"], "value": bull[i]} for i in range(len(cd))], "options": {"color": "#00cc96", "lineWidth": 2, "priceScaleId": "osc", "priceLineVisible": False}},
                    {"type": "Line", "key": "andean_bear", "data": [{"time": cd[i]["time"], "value": bear[i]} for i in range(len(cd))], "options": {"color": "#ef553b", "lineWidth": 2, "priceScaleId": "osc", "priceLineVisible": False}},
                    {"type": "Line", "key": "andean_signal", "data": [{"time": cd[i]["time"], "value": signal[i]} for i in range(len(cd))], "options": {"color": "#ffa15a", "lineWidth": 1, "priceScaleId": "osc", "priceLineVisible": False}},
                    {"type": "Line", "key": "andean_zero", "data": [{"time": cd[i]["time"], "value": 0} for i in range(len(cd))], "options": {"color": "#ffffff", "lineWidth": 1, "lineStyle": 2, "priceScaleId": "osc", "priceLineVisible": False, "lastValueVisible": False, "crosshairMarkerVisible": False, "priceLineVisible": False}},
                ]
                continue
            if name == "EMA 50 Squeeze":
                ema50, sqz_red, sqz_black, sqz_orange = _ema50_squeeze(highs, lows, closes)
                ema50_data = [{"time": cd[i]["time"], "value": ema50[i]} for i in range(len(cd)) if ema50[i] is not None]
                if ema50_data:
                    series_list.append({"type": "Line", "key": "ema50", "data": ema50_data,                 "options": {"color": cfg.get("color", "#00cc96"), "lineWidth": 2, "lastValueVisible": False, "priceLineVisible": False}})
                def _emit_sqz(sqz_list, color):
                    pts = [(i, v) for i, v in enumerate(sqz_list) if v is not None]
                    if not pts: return
                    for i, v in pts:
                        series_list.append({"type": "Line", "data": [{"time": cd[i]["time"], "value": v}], "options": {"color": color, "lineWidth": 4, "priceLineVisible": False, "lastValueVisible": False}})
                _emit_sqz(sqz_red, "#ef553b")
                _emit_sqz(sqz_black, "#000000")
                _emit_sqz(sqz_orange, "#ffa500")
                continue
            if name == "Volume Profile":
                # VPVR (Volume Profile Visible Range) — bins bar volume at
                # each price level over the *visible* bars on the main pane.
                # Buy/sell split is sourced from the websocket streaming
                # `buy_vol` / `sell_vol`; bars without those (historical
                # fetch only) fall back to a price-proxy split identical
                # to the Volume indicator's. The price-level binning runs
                # client-side so VPVR recomputes on every pan/zoom without
                # round-tripping to Python.
                vol_map = {}
                buy_map = {}
                sell_map = {}
                for c in candles:
                    t = _convert_time(c["datetime"], et_offset)
                    raw_vol = c.get("volume", 0)
                    if raw_vol is None or raw_vol != raw_vol:  # NaN check
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
                    # Prefer the websocket buy/sell split; fall back to a
                    # price-based proxy split when only historical volume
                    # is available (mirrors the Volume indicator's logic).
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
                # Session-anchored VWAP: cumulative ∑(typical * vol) / ∑(vol)
                # within the current RTH session, reset at the first bar
                # whose ET wall-clock seconds-of-day >= 9:30 ET each new day.
                # Computed entirely in Python from the (already ET-adjusted)
                # cd times so the JS chart renders it as a static main-pane
                # line series — no per-frame recompute needed.
                vol_map = {}
                for c in candles:
                    t = _convert_time(c["datetime"], et_offset)
                    raw_vol = c.get("volume", 0)
                    if raw_vol is None or raw_vol != raw_vol:  # NaN check
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
                            "lineStyle": 0,  # solid
                            "priceLineVisible": False,
                            "lastValueVisible": False,
                        },
                    })
                continue
            if name == "Trend":
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
    if atm_series is not None:
        result["atm_series"] = atm_series
    if andean_series is not None:
        result["andean_series"] = andean_series
    if vp_vols is not None:
        result["vp_vols"] = vp_vols
    return result


def build_update_data(
    latest_candle: dict,
    indicator_values: dict | None = None,
) -> dict:
    from charts import _get_est_offset
    try:
        et = _get_est_offset()
    except Exception:
        et = 0
    t = _convert_time(latest_candle["datetime"], et)
    bar = {"time": t, "open": float(latest_candle["open"]), "high": float(latest_candle["high"]), "low": float(latest_candle["low"]), "close": float(latest_candle["close"])}
    r = {"bar": bar}
    if indicator_values:
        r["indicators"] = indicator_values
    return r


def compute_latest_indicators(
    candle: dict,
    history: list[dict],
    indicators: list[str] | None,
) -> dict:
    from charts import _get_est_offset, _sma, _ema, _trend, _andean_oscillator, _ema50_squeeze, INDICATORS

    if not indicators:
        return {}

    et = _get_est_offset()

    all_candles = list(history)
    if all_candles and all_candles[-1].get("datetime") != candle.get("datetime"):
        all_candles.append(candle)
    elif not all_candles:
        all_candles = [candle]
    else:
        all_candles[-1] = candle

    cd = []
    for c in all_candles:
        t = _convert_time(c["datetime"], 0)
        cd.append({"time": t, "open": float(c["open"]), "high": float(c["high"]), "low": float(c["low"]), "close": float(c["close"])})
    cd.sort(key=lambda x: x["time"])

    closes = [c["close"] for c in cd]
    opens = [c["open"] for c in cd]
    highs = [c["high"] for c in cd]
    lows = [c["low"] for c in cd]
    times = [c["time"] for c in cd]
    last_t = times[-1]

    result = {}
    for name in indicators or []:
        cfg = INDICATORS.get(name)
        if not cfg: continue
        if name == "Volume": continue
        if name == "Volume Profile": continue
        if name == "Anchored VWAP": continue
        if name == "Andean Osc":
            bull, bear, signal = _andean_oscillator(opens, closes, cfg["length"], cfg["sigLength"])
            result["andean"] = {"time": last_t, "bull": round(bull[-1], 2), "bear": round(bear[-1], 2), "signal": round(signal[-1], 2)}
            continue
        if name == "EMA 50 Squeeze": continue
        if name == "Trend":
            mv = _trend(opens, closes, cfg["alphaLength"])
            result["trend"] = {"time": last_t, "value": round(mv[-1], 2)}
            continue
        period = cfg["period"]
        if len(closes) < period: continue
        vals = _ema(closes, period) if name.startswith("EMA") else _sma(closes, period)
        result[f"ma_{name}"] = {"time": times[period - 1 + len(vals) - period], "value": round(vals[-1], 2)}

    return result


def render_chart(candles, indicators=None, call_wall=None, put_wall=None, force_reinit=False, last_close=None, status=None, symbol="SPY", iv_skew_history=None):
    import time
    main_height = 420
    vol_height = 100 if (indicators and "Volume" in indicators) else 0
    osc_height = 100 if (indicators and "Andean Osc" in indicators) else 0
    iv_skew_height = 100 if (indicators and "IV Skew (25Δ)" in indicators) and iv_skew_history and len(iv_skew_history) > 0 else 0
    iv_skew_hist_height = 50 if (indicators and "IV Skew (25Δ)" in indicators) and iv_skew_history and len(iv_skew_history) > 0 else 0
    init_data = build_init_data(candles, indicators, call_wall, put_wall, last_close=last_close)
    if status:
        init_data["status"] = status
    payload = {"init": init_data}
    root_id = f"lwc_candlestick_{symbol}"
    json_str = json.dumps(payload)
    total_height = main_height + vol_height + osc_height + iv_skew_height + iv_skew_hist_height
    from charts import _IS_DARK
    if _IS_DARK:
        _bg, _tc, _gc = "#dbeafe", "#1e293b", "#bfdbfe"
    else:
        _bg, _tc, _gc = "#ffffff", "#1e293b", "#e9eef3"
    html = _HTML_TEMPLATE % {"root_id": root_id, "main_height": main_height, "vol_height": vol_height, "osc_height": osc_height, "iv_skew_height": iv_skew_height, "iv_skew_hist_height": iv_skew_hist_height, "total_height": total_height, "lib": _JS_LIB, "json_data": json_str, "bg": _bg, "tc": _tc, "gc": _gc}
    st.html(html, unsafe_allow_javascript=True)
