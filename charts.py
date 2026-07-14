import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Any, Optional


TEMPLATE = {
    "plot_bgcolor": "#ffffff",
    "paper_bgcolor": "#ffffff",
    "font_color": "#1e293b",
    "grid_color": "#e9eef3",
}

DARK_TEMPLATE = {
    "plot_bgcolor": "#dbeafe",
    "paper_bgcolor": "#dbeafe",
    "font_color": "#1e293b",
    "grid_color": "#bfdbfe",
}

_IS_DARK = False


def set_dark(is_dark: bool):
    global _IS_DARK
    _IS_DARK = is_dark


def _get_template():
    return DARK_TEMPLATE if _IS_DARK else TEMPLATE


def create_gex_histogram(
    strikes: list[dict[str, Any]],
    spot: float,
    call_wall: Optional[float] = None,
    put_wall: Optional[float] = None,
    gamma_flip: Optional[float] = None,
) -> go.Figure:
    tmpl = _get_template()
    fig = go.Figure()

    strikes_sorted = sorted(strikes, key=lambda s: s["strike"])

    strikes_x = [s["strike"] for s in strikes_sorted]
    net_gex = [s["net_gex"] for s in strikes_sorted]

    net_colors = ["#00cc96" if v >= 0 else "#ef553b" for v in net_gex]

    hover_template = (
        "<b>Strike: %{x}</b><br>"
        "Call GEX: %{customdata[0]:$,.0f}<br>"
        "Put GEX: %{customdata[1]:$,.0f}<br>"
        "Net GEX: %{customdata[2]:$,.0f}<br>"
        "<extra></extra>"
    )

    customdata = [[s["call_gex"], s["put_gex"], s["net_gex"]] for s in strikes_sorted]
    customdata_arr = np.array(customdata)

    fig.add_trace(go.Bar(
        x=strikes_x,
        y=net_gex,
        name="Net GEX",
        marker_color=net_colors,
        hovertemplate=hover_template,
        customdata=customdata_arr,
        showlegend=True,
    ))

    fig.add_vline(
        x=spot,
        line_dash="dash",
        line_color="#ffa15a",
        annotation_text=f"Spot: ${spot:.2f}",
        annotation_position="top",
        annotation_font_color="#ffa15a",
    )

    if call_wall:
        fig.add_vline(
            x=call_wall,
            line_dash="dot",
            line_color="#ef553b",
            annotation_text=f"Call Wall: ${call_wall:.2f}",
            annotation_position="top",
            annotation_font_color="#ef553b",
        )

    if put_wall:
        fig.add_vline(
            x=put_wall,
            line_dash="dot",
            line_color="#00cc96",
            annotation_text=f"Put Wall: ${put_wall:.2f}",
            annotation_position="bottom",
            annotation_font_color="#00cc96",
        )

    if gamma_flip:
        fig.add_vline(
            x=gamma_flip,
            line_dash="longdash",
            line_color="#ab63fa",
            annotation_text=f"Gamma Flip: ${gamma_flip:.2f}",
            annotation_position="bottom",
            annotation_font_color="#ab63fa",
        )

    fig.update_layout(
        title="Gamma Exposure by Strike",
        xaxis_title="Strike",
        yaxis_title="Net Gamma Exposure ($)",
        barmode="relative",
        hovermode="x unified",
        plot_bgcolor=tmpl["plot_bgcolor"],
        paper_bgcolor=tmpl["paper_bgcolor"],
        font_color=tmpl["font_color"],
        xaxis=dict(
            gridcolor=tmpl["grid_color"],
            showgrid=True,
            zeroline=False,
            tickmode="array",
            tickvals=strikes_x,
            ticktext=[f"{s:g}" for s in strikes_x],
        ),
        yaxis=dict(
            gridcolor=tmpl["grid_color"],
            showgrid=True,
            zeroline=True,
            zerolinecolor=tmpl["grid_color"],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=40, r=40, t=60, b=40),
    )

    return fig


def create_gex_by_expiration(
    by_exp: list[dict[str, Any]],
    max_exps: Optional[int] = None,
) -> go.Figure:
    from datetime import datetime

    tmpl = _get_template()
    fig = go.Figure()

    weekdays = [e for e in by_exp if datetime.strptime(e["expiration"], "%Y-%m-%d").weekday() < 5]
    if max_exps is not None:
        weekdays = weekdays[:max_exps]

    exps = [datetime.strptime(e["expiration"], "%Y-%m-%d").strftime("%m/%d") for e in weekdays]
    call_gex = [e["call_gex"] for e in weekdays]
    put_gex = [-e["put_gex"] for e in weekdays]
    net_gex = [e["net_gex"] for e in weekdays]

    fig.add_trace(go.Bar(
        x=exps,
        y=call_gex,
        name="Call GEX",
        marker_color="#00cc96",
    ))

    fig.add_trace(go.Bar(
        x=exps,
        y=put_gex,
        name="Put GEX",
        marker_color="#ef553b",
    ))

    fig.add_trace(go.Scatter(
        x=exps,
        y=net_gex,
        name="Net GEX",
        mode="lines+markers",
        line=dict(color="#ffa15a", width=2),
        marker=dict(size=6),
    ))

    fig.update_layout(
        title="Gamma Exposure by Expiration",
        xaxis_title="Expiration",
        yaxis_title="Gamma Exposure ($)",
        barmode="relative",
        hovermode="x unified",
        plot_bgcolor=tmpl["plot_bgcolor"],
        paper_bgcolor=tmpl["paper_bgcolor"],
        font_color=tmpl["font_color"],
        xaxis=dict(gridcolor=tmpl["grid_color"], type="category"),
        yaxis=dict(gridcolor=tmpl["grid_color"], zeroline=True, zerolinecolor=tmpl["grid_color"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        clickmode="event+select",
    )

    return fig


def create_oi_by_strike(
    strikes: list[dict[str, Any]],
    spot: float,
    mode: str = "oi",
) -> go.Figure:
    tmpl = _get_template()
    fig = go.Figure()

    strikes_sorted = sorted(strikes, key=lambda s: s["strike"])
    x = [s["strike"] for s in strikes_sorted]

    if mode == "oi_vol":
        oi_vals = [s["call_oi"] + s["put_oi"] for s in strikes_sorted]
        vol_vals = [s["call_volume"] + s["put_volume"] for s in strikes_sorted]
        
        fig.add_trace(go.Bar(
            x=x, y=oi_vals, name="OI", marker_color="#00cc96",
            hovertemplate="Strike: %{x}<br>OI: %{y:,.0f}<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            x=x, y=vol_vals, name="Volume", marker_color="#ab63fa",
            hovertemplate="Strike: %{x}<br>Volume: %{y:,.0f}<extra></extra>",
        ))
        title = "Total OI and Volume by Strike"
        ytitle = "Count"
    
    elif mode == "oi":
        call_vals = [s["call_oi"] for s in strikes_sorted]
        put_vals = [s["put_oi"] for s in strikes_sorted]
        
        fig.add_trace(go.Bar(
            x=x, y=call_vals, name="Call OI", marker_color="#00cc96",
            hovertemplate="Strike: %{x}<br>Call OI: %{y:,.0f}<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            x=x, y=put_vals, name="Put OI", marker_color="#ef553b",
            hovertemplate="Strike: %{x}<br>Put OI: %{y:,.0f}<extra></extra>",
        ))
        title = "Call vs Put Open Interest by Strike"
        ytitle = "Open Interest"
    
    elif mode == "volume":
        call_vals = [s["call_volume"] for s in strikes_sorted]
        put_vals = [s["put_volume"] for s in strikes_sorted]
        
        fig.add_trace(go.Bar(
            x=x, y=call_vals, name="Call Vol", marker_color="#00cc96",
            hovertemplate="Strike: %{x}<br>Call Vol: %{y:,.0f}<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            x=x, y=put_vals, name="Put Vol", marker_color="#ef553b",
            hovertemplate="Strike: %{x}<br>Put Vol: %{y:,.0f}<extra></extra>",
        ))
        title = "Call vs Put Volume by Strike"
        ytitle = "Volume"

    fig.add_vline(
        x=spot,
        line_dash="dash",
        line_color="#ffa15a",
        annotation_text=f"Spot: ${spot:.2f}",
        annotation_position="top",
        annotation_font_color="#ffa15a",
    )

    fig.update_layout(
        title=title,
        xaxis_title="Strike",
        yaxis_title=ytitle,
        barmode="group",
        hovermode="x unified",
        plot_bgcolor=tmpl["plot_bgcolor"],
        paper_bgcolor=tmpl["paper_bgcolor"],
        font_color=tmpl["font_color"],
        xaxis=dict(gridcolor=tmpl["grid_color"],
            tickmode="array",
            tickvals=x,
            ticktext=[f"{s:g}" for s in x],
        ),
        yaxis=dict(gridcolor=tmpl["grid_color"]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
    )

    return fig


def create_vrp_by_strike(
    strikes: list[dict[str, Any]],
    spot: float,
    rv: float = 0.0,
    mode: str = "vrp",
    iv_rank: float | None = None,
) -> go.Figure:
    tmpl = _get_template()
    fig = go.Figure()

    strikes_sorted = sorted(strikes, key=lambda s: s["strike"])
    labels = [f"{s['strike']:g}" for s in strikes_sorted]
    ivs = [
        s.get("call_iv", 0) if s["strike"] >= spot else s.get("put_iv", 0)
        for s in strikes_sorted
    ]
    if mode == "vrp":
        values = [iv - rv for iv in ivs]
        title = "VRP by Strike"
        yaxis_title = "VRP (IV - RV)"
        hovertemplate = "Strike: %{x}<br>VRP: %{y:.2%}<extra></extra>"
        tickformat = ".0%"
        ref_line = 0
    else:
        values = [iv / rv if rv > 0 else 0 for iv in ivs]
        title = "VRP Ratio by Strike"
        yaxis_title = "VRP Ratio (IV / RV)"
        hovertemplate = "Strike: %{x}<br>VRP Ratio: %{y:.2f}<extra></extra>"
        tickformat = ".2f"
        ref_line = 1

    min_v = min(values) if values else 0
    max_v = max(values) if values else 1
    v_range = max_v - min_v if max_v > min_v else 1
    norm_vs = [(v - min_v) / v_range for v in values]
    colors = []
    for n in norm_vs:
        if n < 0.33:
            t = n / 0.33
            r = int(0 + t * 50)
            g = int(200 - t * 30)
            b = int(100 + t * 50)
        elif n < 0.66:
            t = (n - 0.33) / 0.33
            r = int(50 + t * 205)
            g = int(170 - t * 70)
            b = int(150 - t * 100)
        else:
            t = (n - 0.66) / 0.34
            r = int(255)
            g = int(100 - t * 70)
            b = int(50 - t * 30)
        colors.append(f"rgb({max(0, min(255, r))},{max(0, min(255, g))},{max(0, min(255, b))})")

    fig.add_trace(go.Bar(
        x=labels,
        y=values,
        marker_color=colors,
        hovertemplate=hovertemplate,
    ))

    fig.add_hline(y=ref_line, line_dash="dash", line_color="#ab63fa")

    spot_f = float(spot)
    nearest_label = min(labels, key=lambda x: abs(float(x) - spot_f))
    nearest_idx = labels.index(nearest_label)
    fig.add_vline(
        x=nearest_idx,
        line_dash="dash",
        line_color="#ffa15a",
        annotation_text=f"Spot: ${spot_f:.2f}",
        annotation_position="top",
        annotation_font_color="#ffa15a",
    )

    fig.update_layout(
        title=title,
        xaxis_title="Strike",
        yaxis_title=yaxis_title,
        hovermode="x unified",
        plot_bgcolor=tmpl["plot_bgcolor"],
        paper_bgcolor=tmpl["paper_bgcolor"],
        font_color=tmpl["font_color"],
        xaxis=dict(gridcolor=tmpl["grid_color"], type="category"),
        yaxis=dict(gridcolor=tmpl["grid_color"], tickformat=tickformat),
        margin=dict(l=40, r=40, t=60, b=40),
    )

    return fig


def create_heatmap(
    data: list[dict[str, Any]],
    value_field: str,
    title: str,
    spot: float | None = None,
    call_wall: float | None = None,
    put_wall: float | None = None,
) -> go.Figure:
    tmpl = _get_template()

    from datetime import datetime
    active_exps = set(e["expiration"] for e in data if e.get("open_interest", 0) > 0)
    data = [e for e in data if e["expiration"] in active_exps]

    expirations = sorted(set(e["expiration"] for e in data))
    exp_labels = [datetime.strptime(e, "%Y-%m-%d").strftime("%m/%d") for e in expirations]
    strikes = sorted(set(e["strike"] for e in data))
    strike_labels = [f"{s:g}" for s in strikes]

    strike_to_idx = {s: i for i, s in enumerate(strikes)}
    exp_to_idx = {e: i for i, e in enumerate(expirations)}

    z = np.full((len(strikes), len(expirations)), np.nan)

    for entry in data:
        s_idx = strike_to_idx.get(entry["strike"])
        e_idx = exp_to_idx.get(entry["expiration"])
        if s_idx is not None and e_idx is not None:
            val = entry.get(value_field, 0) or 0
            if np.isfinite(val):
                z[s_idx, e_idx] = val

    z_int = np.where(np.isnan(z), 0, z).astype(int)
    text = np.where(np.isnan(z), "", z_int.astype(str))

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=exp_labels,
        y=strikes,
        text=text,
        texttemplate="%{text}",
        colorscale="RdYlGn" if value_field in ("gex", "net_gex") else "Viridis",
        colorbar=dict(title=value_field.replace("_", " ").title()),
        hovertemplate=(
            f"Expiration: %{{x}}<br>"
            f"Strike: %{{y}}<br>"
            f"{value_field.replace('_', ' ').title()}: %{{z:,.0f}}<br>"
            "<extra></extra>"
        ),
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Expiration",
        yaxis_title="Strike",
        plot_bgcolor=tmpl["plot_bgcolor"],
        paper_bgcolor=tmpl["paper_bgcolor"],
        font_color=tmpl["font_color"],
        xaxis=dict(gridcolor=tmpl["grid_color"], tickangle=45, type="category", fixedrange=True),
        yaxis=dict(gridcolor=tmpl["grid_color"], tickmode="array", tickvals=strikes, ticktext=strike_labels),
        margin=dict(l=40, r=40, t=60, b=80),
    )

    if spot is not None:
        fig.add_hline(
            y=spot,
            line_dash="dash",
            line_color="#ffa15a",
        )
        fig.add_annotation(
            x=1, y=spot, xref="paper", yref="y",
            text=f"Spot<br>${spot:.2f}",
            showarrow=False,
            xanchor="left",
            font_size=11,
            font_color="#ffa15a",
        )

    if call_wall is not None:
        fig.add_hline(
            y=call_wall,
            line_dash="dot",
            line_color="#ef553b",
        )
        fig.add_annotation(
            x=1, y=call_wall, xref="paper", yref="y",
            text=f"Call Wall<br>${call_wall:.2f}",
            showarrow=False,
            xanchor="left",
            font_size=11,
            font_color="#ef553b",
        )

    if put_wall is not None:
        fig.add_hline(
            y=put_wall,
            line_dash="dot",
            line_color="#00cc96",
        )
        fig.add_annotation(
            x=1, y=put_wall, xref="paper", yref="y",
            text=f"Put Wall<br>${put_wall:.2f}",
            showarrow=False,
            xanchor="left",
            font_size=11,
            font_color="#00cc96",
        )

    return fig


def create_gamma_surface(
    data: list[dict[str, Any]],
) -> go.Figure:
    tmpl = _get_template()

    from datetime import datetime
    expirations = sorted(set(e["expiration"] for e in data))
    exp_labels = [datetime.strptime(e, "%Y-%m-%d").strftime("%m/%d") for e in expirations]
    strikes = sorted(set(e["strike"] for e in data))

    strike_to_idx = {s: i for i, s in enumerate(strikes)}
    exp_to_idx = {e: i for i, e in enumerate(expirations)}

    z = np.full((len(strikes), len(expirations)), np.nan)
    for entry in data:
        s_idx = strike_to_idx.get(entry["strike"])
        e_idx = exp_to_idx.get(entry["expiration"])
        if s_idx is not None and e_idx is not None:
            val = entry.get("gex", 0) or 0
            if not np.isnan(z[s_idx, e_idx]):
                z[s_idx, e_idx] += val
            else:
                z[s_idx, e_idx] = val

    X, Y = np.meshgrid(range(len(expirations)), range(len(strikes)))

    fig = go.Figure(data=[go.Surface(
        x=exp_labels,
        y=strikes,
        z=z,
        colorscale="RdYlGn",
        colorbar=dict(title="GEX ($)"),
        hovertemplate=(
            "Expiration: %{x}<br>"
            "Strike: %{y}<br>"
            "GEX: %{z:$,.0f}<br>"
            "<extra></extra>"
        ),
    )])

    fig.update_layout(
        title="Gamma Exposure Surface",
        scene=dict(
            xaxis_title="Expiration",
            yaxis_title="Strike",
            zaxis_title="GEX ($)",
        xaxis=dict(gridcolor=tmpl["grid_color"], tickangle=45, type="category"),
            yaxis=dict(gridcolor=tmpl["grid_color"]),
            zaxis=dict(gridcolor=tmpl["grid_color"]),
        ),
        plot_bgcolor=tmpl["plot_bgcolor"],
        paper_bgcolor=tmpl["paper_bgcolor"],
        font_color=tmpl["font_color"],
        margin=dict(l=40, r=40, t=60, b=40),
    )

    return fig


def create_vol_surface(
    data: list[dict[str, Any]],
) -> go.Figure:
    tmpl = _get_template()

    from datetime import datetime
    expirations = sorted(set(e["expiration"] for e in data))
    exp_labels = [datetime.strptime(e, "%Y-%m-%d").strftime("%m/%d") for e in expirations]
    strikes = sorted(set(e["strike"] for e in data))

    strike_to_idx = {s: i for i, s in enumerate(strikes)}
    exp_to_idx = {e: i for i, e in enumerate(expirations)}

    z = np.full((len(strikes), len(expirations)), np.nan)
    for entry in data:
        s_idx = strike_to_idx.get(entry["strike"])
        e_idx = exp_to_idx.get(entry["expiration"])
        if s_idx is not None and e_idx is not None:
            iv = entry.get("iv", 0) or 0
            if iv > 3:
                iv = iv / 100
            z[s_idx, e_idx] = iv

    X, Y = np.meshgrid(range(len(expirations)), range(len(strikes)))

    fig = go.Figure(data=[go.Surface(
        x=exp_labels,
        y=strikes,
        z=z,
        colorscale="Viridis",
        colorbar=dict(title="IV", tickformat=".0%"),
        hovertemplate=(
            "Expiration: %{x}<br>"
            "Strike: %{y}<br>"
            "IV: %{z:.2%}<br>"
            "<extra></extra>"
        ),
    )])

    fig.update_layout(
        title="Volatility Surface",
        scene=dict(
            xaxis_title="Expiration",
            yaxis_title="Strike",
            zaxis_title="IV",
            xaxis=dict(gridcolor=tmpl["grid_color"], tickangle=45, type="category"),
            yaxis=dict(gridcolor=tmpl["grid_color"]),
            zaxis=dict(gridcolor=tmpl["grid_color"], tickformat=".0%"),
        ),
        plot_bgcolor=tmpl["plot_bgcolor"],
        paper_bgcolor=tmpl["paper_bgcolor"],
        font_color=tmpl["font_color"],
        margin=dict(l=40, r=40, t=60, b=40),
    )

    return fig


def create_vol_surface_2d(
    data: list[dict[str, Any]],
    rv: float,
    strike_min: float,
    strike_max: float,
    spot: float,
    mode: str = "vrp",
) -> go.Figure:
    tmpl = _get_template()

    from datetime import datetime
    filtered = [e for e in data if strike_min <= e["strike"] <= strike_max]
    if not filtered:
        fig = go.Figure()
        fig.update_layout(title="No data in strike range")
        return fig

    active_exps = set(e["expiration"] for e in filtered if e.get("open_interest", 0) > 0)
    filtered = [e for e in filtered if e["expiration"] in active_exps]
    if not filtered:
        fig = go.Figure()
        fig.update_layout(title="No data in strike range")
        return fig

    expirations = sorted(set(e["expiration"] for e in filtered))
    exp_labels = [datetime.strptime(e, "%Y-%m-%d").strftime("%m/%d") for e in expirations]
    strikes = sorted(set(e["strike"] for e in filtered))
    strike_labels = [f"{s:g}" for s in strikes]

    strike_to_idx = {s: i for i, s in enumerate(strikes)}
    exp_to_idx = {e: i for i, e in enumerate(expirations)}

    z = np.full((len(strikes), len(expirations)), np.nan)
    for entry in filtered:
        s_idx = strike_to_idx.get(entry["strike"])
        e_idx = exp_to_idx.get(entry["expiration"])
        if s_idx is not None and e_idx is not None:
            iv = entry.get("iv", 0) or 0
            if iv > 3:
                iv = iv / 100
            if mode == "vrp":
                z[s_idx, e_idx] = iv - rv
            else:
                z[s_idx, e_idx] = iv / rv if rv > 0 else 0

    if mode == "vrp":
        title = "Volatility Surface (VRP)"
        colorbar_title = "VRP"
        text = np.where(np.isnan(z), "", np.round(z * 100, 1).astype(str))
        texttemplate = "%{text}%"
        tickformat = ".0%"
        hovertemplate = (
            "Expiration: %{x}<br>"
            "Strike: %{y}<br>"
            "VRP: %{z:.2%}<br>"
            "<extra></extra>"
        )
    else:
        title = "Volatility Surface (VRP Ratio)"
        colorbar_title = "VRP Ratio"
        text = np.where(np.isnan(z), "", np.round(z, 2).astype(str))
        texttemplate = "%{text}"
        tickformat = ".2f"
        hovertemplate = (
            "Expiration: %{x}<br>"
            "Strike: %{y}<br>"
            "VRP Ratio: %{z:.2f}<br>"
            "<extra></extra>"
        )

    fig = go.Figure(data=go.Heatmap(
        x=exp_labels,
        y=strikes,
        z=z,
        text=text,
        texttemplate=texttemplate,
        colorscale="RdYlGn",
        colorbar=dict(title=colorbar_title, tickformat=tickformat, x=1.02),
        hovertemplate=hovertemplate,
    ))

    fig.update_layout(
        title=title,
        xaxis=dict(title="Expiration", gridcolor=tmpl["grid_color"], tickangle=45, type="category", fixedrange=True),
        yaxis=dict(title="Strike", gridcolor=tmpl["grid_color"], tickmode="array", tickvals=strikes, ticktext=strike_labels),
        plot_bgcolor=tmpl["plot_bgcolor"],
        paper_bgcolor=tmpl["paper_bgcolor"],
        font_color=tmpl["font_color"],
        margin=dict(l=40, r=80, t=60, b=40),
    )

    fig.add_hline(
        y=spot,
        line_dash="dash",
        line_color="#ffa15a",
    )
    fig.add_annotation(
        x=1, y=spot, xref="paper", yref="y",
        text=f"Spot<br>${spot:.2f}",
        showarrow=False,
        xanchor="left",
        font_size=11,
        font_color="#ffa15a",
    )

    return fig


def create_dealer_gamma_curve(
    strikes: list[dict[str, Any]],
    spot: float,
    mode: str = "gex",
    gamma_flip: Optional[float] = None,
    call_wall: Optional[float] = None,
    put_wall: Optional[float] = None,
    vex_magnet: Optional[float] = None,
    vex_repellent: Optional[float] = None,
) -> go.Figure:
    tmpl = _get_template()
    fig = go.Figure()

    strikes_sorted = sorted(strikes, key=lambda s: s["strike"])

    spot_prices = np.linspace(
        min(s["strike"] for s in strikes_sorted) * 0.95,
        max(s["strike"] for s in strikes_sorted) * 1.05,
        200,
    )

    cumulative_gex = []
    cumulative_vex = []
    cumulative_cex = []
    for sp in spot_prices:
        cum_g = sum(
            s["net_gex"] for s in strikes_sorted if s["strike"] >= sp
        )
        cumulative_gex.append(cum_g)
        cum_v = sum(
            s["net_vex"] for s in strikes_sorted if s["strike"] >= sp
        )
        cumulative_vex.append(cum_v)
        cum_c = sum(
            s["net_cex"] for s in strikes_sorted if s["strike"] >= sp
        )
        cumulative_cex.append(cum_c)

    if mode == "gex":
        y_vals = cumulative_gex
        line_color = "#636efa"
        trace_name = "Gamma Exposure"
        yaxis_title = "Net GEX ($)"
        zero_label = "Zero<br>Gamma"
    elif mode == "vex":
        y_vals = cumulative_vex
        line_color = "#00cc96"
        trace_name = "Vanna Exposure"
        yaxis_title = "Net VEX ($)"
        zero_label = "Zero<br>Vanna"
    else:
        y_vals = cumulative_cex
        line_color = "#ff7f0e"
        trace_name = "Charm Exposure"
        yaxis_title = "Net CEX ($)"
        zero_label = "Zero<br>Charm"

    fill_colors = {"gex": "rgba(99, 110, 250, 0.1)", "vex": "rgba(0, 204, 150, 0.1)", "cex": "rgba(255, 127, 14, 0.1)"}
    fill_rgba = fill_colors[mode]

    fig.add_trace(go.Scatter(
        x=spot_prices,
        y=y_vals,
        mode="lines",
        name=trace_name,
        line=dict(color=line_color, width=2),
        fill="tozeroy",
        fillcolor=fill_rgba,
    ))

    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="#ab63fa",
    )
    fig.add_annotation(
        x=1, y=0, xref="paper", yref="y",
        text=zero_label,
        showarrow=False,
        font_color="#ab63fa",
        xanchor="left",
    )

    fig.add_vline(
        x=spot,
        line_dash="dash",
        line_color="#ffa15a",
        annotation_text=f"Spot: ${spot:.2f}",
        annotation_position="top",
        annotation_font_color="#ffa15a",
    )

    if mode == "gex" and gamma_flip:
        fig.add_vline(
            x=gamma_flip,
            line_dash="longdash",
            line_color="#ab63fa",
        )
        fig.add_annotation(
            x=gamma_flip, yref="paper", y=0.08,
            text=f"Gamma Flip: ${gamma_flip:.2f}",
            showarrow=False,
            font_color="#ab63fa",
            font_size=11,
        )

    if mode == "gex":
        if call_wall:
            fig.add_vline(
                x=call_wall,
                line_dash="dot",
                line_color="#ef553b",
                annotation_text=f"Call Wall: ${call_wall:.2f}",
                annotation_position="top",
                annotation_font_color="#ef553b",
            )
        if put_wall:
            fig.add_vline(
                x=put_wall,
                line_dash="dot",
                line_color="#00cc96",
            )
            fig.add_annotation(
                x=put_wall, yref="paper", y=0.08,
                text=f"Put Wall: ${put_wall:.2f}",
                showarrow=False,
                font_color="#00cc96",
                font_size=11,
            )

    if mode == "vex":
        if vex_magnet:
            fig.add_vline(
                x=vex_magnet,
                line_dash="dot",
                line_color="#ffa15a",
            )
            fig.add_annotation(
                x=vex_magnet, yref="paper", y=0.12,
                text=f"Magnet: ${vex_magnet:.2f}",
                showarrow=False,
                font_color="#ffa15a",
                font_size=11,
            )
        if vex_repellent:
            fig.add_vline(
                x=vex_repellent,
                line_dash="dot",
                line_color="#ef553b",
            )
            fig.add_annotation(
                x=vex_repellent, yref="paper", y=0.12,
                text=f"Repellent: ${vex_repellent:.2f}",
                showarrow=False,
                font_color="#ef553b",
                font_size=11,
            )

    fig.update_layout(
        title=f"Dealer Curve ({trace_name})",
        xaxis_title="Strike",
        yaxis_title=yaxis_title,
        hovermode="x unified",
        plot_bgcolor=tmpl["plot_bgcolor"],
        paper_bgcolor=tmpl["paper_bgcolor"],
        font_color=tmpl["font_color"],
        xaxis=dict(
            gridcolor=tmpl["grid_color"],
            tickmode="auto",
            nticks=20,
            automargin=True,
        ),
        yaxis=dict(gridcolor=tmpl["grid_color"], zeroline=True, zerolinecolor=tmpl["grid_color"]),
        margin=dict(l=40, r=60, t=60, b=80),
    )

    return fig



def create_atm_iv_histogram(
    by_exp: list[dict[str, Any]],
    rv: float = 0.0,
) -> go.Figure:
    """Create a bar chart of ATM IV by expiration date.

    Bars are colored by IV magnitude using a color scale.
    A horizontal line at RV is included.
    """
    from datetime import datetime

    tmpl = _get_template()
    fig = go.Figure()

    # Filter to entries that have expiration dates (weekdays)
    weekdays = []
    for e in by_exp:
        try:
            dt = datetime.strptime(e["expiration"], "%Y-%m-%d")
            if dt.weekday() < 5:
                weekdays.append(e)
        except (ValueError, TypeError):
            weekdays.append(e)

    if not weekdays:
        fig.add_annotation(
            text="No expiration data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
        )
        fig.update_layout(
            title="IV by Expiration",
            plot_bgcolor=tmpl["plot_bgcolor"],
            paper_bgcolor=tmpl["paper_bgcolor"],
            font_color=tmpl["font_color"],
        )
        return fig

    # Sort by expiration date
    weekdays.sort(key=lambda e: e["expiration"])

    # Format expiration labels as short date strings
    labels = []
    for e in weekdays:
        try:
            dt = datetime.strptime(e["expiration"], "%Y-%m-%d")
            labels.append(dt.strftime("%m/%d"))
        except (ValueError, TypeError):
            labels.append(e["expiration"])

    atm_ivs = [e.get("atm_iv", 0.0) or 0.0 for e in weekdays]
    dtes = [e.get("dte", 0) or 0 for e in weekdays]

    # Build a color scale based on IV magnitude
    min_iv = min(atm_ivs) if atm_ivs else 0
    max_iv = max(atm_ivs) if atm_ivs else 1
    iv_range = max_iv - min_iv if max_iv > min_iv else 1

    # Normalize IVs to [0, 1] for color mapping
    norm_ivs = [(v - min_iv) / iv_range for v in atm_ivs]

    # Create colors using a Viridis-like scale (greens for low, yellows for mid, reds for high)
    colors = []
    for n in norm_ivs:
        if n < 0.33:
            # Green range
            t = n / 0.33
            r = int(0 + t * 50)
            g = int(200 - t * 30)
            b = int(100 + t * 50)
        elif n < 0.66:
            # Yellow-orange range
            t = (n - 0.33) / 0.33
            r = int(50 + t * 205)
            g = int(170 - t * 70)
            b = int(150 - t * 100)
        else:
            # Red range
            t = (n - 0.66) / 0.34
            r = int(255)
            g = int(100 - t * 70)
            b = int(50 - t * 30)
        colors.append(f"rgb({max(0, min(255, r))},{max(0, min(255, g))},{max(0, min(255, b))})")

    hover_template = (
        "<b>Expiration: %{x}</b><br>"
        "ATM IV: %{y:.2%}<br>"
        "DTE: %{customdata[0]}<br>"
        "<extra></extra>"
    )
    customdata_arr = [[d] for d in dtes]

    fig.add_trace(go.Bar(
        x=labels,
        y=atm_ivs,
        name="ATM IV",
        marker_color=colors,
        hovertemplate=hover_template,
        customdata=customdata_arr,
        showlegend=False,
    ))

    # Add horizontal line at RV
    if rv > 0:
        fig.add_hline(
            y=rv,
            line_dash="dash",
            line_color="#636efa",
            annotation_text=f"RV: {rv*100:.2f}%",
            annotation_position="bottom right",
            annotation_font_color="#636efa",
        )

    fig.update_layout(
        title="IV by Expiration",
        xaxis_title="Expiration",
        yaxis_title="ATM Implied Volatility",
        barmode="group",
        hovermode="x unified",
        plot_bgcolor=tmpl["plot_bgcolor"],
        paper_bgcolor=tmpl["paper_bgcolor"],
        font_color=tmpl["font_color"],
        xaxis=dict(
            gridcolor=tmpl["grid_color"],
            type="category",
        ),
        yaxis=dict(
            gridcolor=tmpl["grid_color"],
            zeroline=True,
            zerolinecolor=tmpl["grid_color"],
            tickformat=".0%",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=40, r=40, t=60, b=40),
    )

    return fig


def create_vrp_chart(
    by_exp: list[dict[str, Any]],
    rv: float,
    mode: str = "vrp",
) -> go.Figure:
    from datetime import datetime

    tmpl = _get_template()
    fig = go.Figure()

    weekdays = []
    for e in by_exp:
        try:
            dt = datetime.strptime(e["expiration"], "%Y-%m-%d")
            if dt.weekday() < 5:
                weekdays.append(e)
        except (ValueError, TypeError):
            weekdays.append(e)

    if not weekdays or rv <= 0:
        fig.add_annotation(
            text="No VRP data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
        )
        fig.update_layout(
            title="VRP by Expiration",
            plot_bgcolor=tmpl["plot_bgcolor"],
            paper_bgcolor=tmpl["paper_bgcolor"],
            font_color=tmpl["font_color"],
        )
        return fig

    weekdays.sort(key=lambda e: e["expiration"])
    labels = []
    for e in weekdays:
        try:
            dt = datetime.strptime(e["expiration"], "%Y-%m-%d")
            labels.append(dt.strftime("%m/%d"))
        except (ValueError, TypeError):
            labels.append(e["expiration"])

    atm_ivs = [e.get("atm_iv", 0.0) or 0.0 for e in weekdays]
    if mode == "vrp_ratio":
        vals = [iv / rv if rv > 0 else 0 for iv in atm_ivs]
        title = "VRP Ratio by Expiration"
        yaxis_title = "VRP Ratio (ATM IV / RV)"
        hover_label = "VRP Ratio"
        hover_fmt = "%{y:.2f}"
        tick_fmt = ".2f"
        ref_val = 1
    else:
        vals = [iv - rv for iv in atm_ivs]
        title = "VRP by Expiration"
        yaxis_title = "VRP (ATM IV - RV)"
        hover_label = "VRP"
        hover_fmt = "%{y:.2%}"
        tick_fmt = ".0%"
        ref_val = 0

    min_v = min(vals) if vals else 0
    max_v = max(vals) if vals else 1
    v_range = max_v - min_v if max_v > min_v else 1
    norm_vs = [(v - min_v) / v_range for v in vals]
    colors = []
    for n in norm_vs:
        if n < 0.33:
            t = n / 0.33
            r = int(0 + t * 50)
            g = int(200 - t * 30)
            b = int(100 + t * 50)
        elif n < 0.66:
            t = (n - 0.33) / 0.33
            r = int(50 + t * 205)
            g = int(170 - t * 70)
            b = int(150 - t * 100)
        else:
            t = (n - 0.66) / 0.34
            r = int(255)
            g = int(100 - t * 70)
            b = int(50 - t * 30)
        colors.append(f"rgb({max(0, min(255, r))},{max(0, min(255, g))},{max(0, min(255, b))})")

    fig.add_trace(go.Bar(
        x=labels,
        y=vals,
        name=hover_label,
        marker_color=colors,
        hovertemplate=f"<b>Expiration: %{{x}}</b><br>{hover_label}: {hover_fmt}<br><extra></extra>",
        showlegend=False,
    ))

    fig.add_hline(y=ref_val, line_dash="dash", line_color="#ab63fa")

    fig.update_layout(
        title=title,
        xaxis_title="Expiration",
        yaxis_title=yaxis_title,
        hovermode="x unified",
        plot_bgcolor=tmpl["plot_bgcolor"],
        paper_bgcolor=tmpl["paper_bgcolor"],
        font_color=tmpl["font_color"],
        xaxis=dict(gridcolor=tmpl["grid_color"], type="category"),
        yaxis=dict(gridcolor=tmpl["grid_color"], zeroline=True, zerolinecolor=tmpl["grid_color"], tickformat=tick_fmt),
        margin=dict(l=40, r=40, t=60, b=40),
    )

    return fig


def create_iv_by_strike(
    strikes: list[dict[str, Any]],
    spot: float,
    rv: float = 0.0,
    iv_rank: float | None = None,
    ssvi_surface: Any = None,
    ssvi_tte: float | None = None,
) -> go.Figure:
    tmpl = _get_template()
    fig = go.Figure()

    strikes_sorted = sorted(strikes, key=lambda s: s["strike"])
    x = [s["strike"] for s in strikes_sorted]
    call_iv = [s.get("call_iv", 0) for s in strikes_sorted]
    put_iv = [s.get("put_iv", 0) for s in strikes_sorted]

    # ATM strike = strike closest to spot; OTM calls = strikes > spot, OTM puts = strikes < spot.
    # Per README: use put IV for strikes below spot (OTM puts) and call IV for strikes >= spot
    # (OTM calls + ATM), matching the convention used in create_vrp_by_strike.
    spot_f = float(spot)
    atm_strike = min(x, key=lambda k: abs(k - spot_f)) if x else None
    iv = [
        put_iv[i] if (atm_strike is not None and s["strike"] < spot_f) else call_iv[i]
        for i, s in enumerate(strikes_sorted)
    ]

    min_iv = min(iv) if iv else 0
    max_iv = max(iv) if iv else 1
    iv_range = max_iv - min_iv if max_iv > min_iv else 1
    norm_ivs = [(v - min_iv) / iv_range for v in iv]
    colors = []
    for n in norm_ivs:
        if n < 0.33:
            t = n / 0.33
            r = int(0 + t * 50)
            g = int(200 - t * 30)
            b = int(100 + t * 50)
        elif n < 0.66:
            t = (n - 0.33) / 0.33
            r = int(50 + t * 205)
            g = int(170 - t * 70)
            b = int(150 - t * 100)
        else:
            t = (n - 0.66) / 0.34
            r = int(255)
            g = int(100 - t * 70)
            b = int(50 - t * 30)
        colors.append(f"rgb({max(0, min(255, r))},{max(0, min(255, g))},{max(0, min(255, b))})")

    # Moneyness tags for hover ("ATM", "OTM Call", "OTM Put") and bar edge styling
    otm_call_edge = "#1f77b4"   # blue edge for OTM calls (strikes above spot)
    otm_put_edge  = "#ff7f0e"   # orange edge for OTM puts (strikes below spot)
    atm_edge      = "#ffffff"   # white edge highlights the ATM bar
    edge_colors = []
    moneyness = []
    for s in strikes_sorted:
        sk = s["strike"]
        if atm_strike is not None and sk == atm_strike:
            moneyness.append("ATM")
            edge_colors.append(atm_edge)
        elif sk > spot_f:
            moneyness.append("OTM Call")
            edge_colors.append(otm_call_edge)
        else:
            moneyness.append("OTM Put")
            edge_colors.append(otm_put_edge)

    hovertext = [
        f"Strike: {sk:g}<br>IV: {_iv:.2%}<br>{mn}"
        for sk, _iv, mn in zip(x, iv, moneyness)
    ]

    fig.add_trace(go.Bar(
        x=x, y=iv, name="IV",
        marker_color=colors,
        marker_line_color=edge_colors,
        marker_line_width=[2.5 if m == "ATM" else 1 for m in moneyness],
        hovertext=hovertext,
        hoverinfo="text",
    ))

    # SSVI fitted smile overlay — arbitrage-free parametric IV surface
    # evaluated at the visible strikes and the tenor's TTE (in years).
    # Drawn across the visible strike range only (matches the bar x-axis),
    # per README: "SSVI model overlay on IV-by-Strike chart".
    if ssvi_surface is not None and ssvi_tte is not None and ssvi_tte > 0 and x:
        ssvi_curve = [ssvi_surface.iv(float(k), float(ssvi_tte)) for k in x]
        if any(v and v > 0 for v in ssvi_curve):
            fig.add_trace(go.Scatter(
                x=x,
                y=ssvi_curve,
                name="SSVI fit",
                mode="lines+markers",
                line=dict(color="#FFD700", width=2.5, dash="solid"),
                marker=dict(size=5, color="#FFD700",
                            line=dict(color="#fff", width=1)),
                hovertemplate="<b>Strike: %{x:g}</b><br>SSVI IV: %{y:.2%}<extra></extra>",
            ))

    # Spot / ATM vertical reference line
    if atm_strike is not None:
        fig.add_vline(
            x=atm_strike,
            line_dash="dash",
            line_color="#ffa15a",
            annotation_text=f"Spot/ATM: ${spot_f:.2f} ({atm_strike:g})",
            annotation_position="top",
            annotation_font_color="#ffa15a",
        )

    if rv > 0:
        fig.add_hline(y=rv, line_dash="dash", line_color="#ab63fa",
                      annotation_text=f"RV: {rv*100:.2f}%",
                      annotation_font_color="#ab63fa")

    if iv_rank is not None:
        rank_val = iv_rank / 100.0
        fig.add_hline(y=rank_val, line_dash="dot", line_color="#00cc96",
                      annotation_text=f"IV Rank: {iv_rank:.2f}%",
                      annotation_font_color="#00cc96")

    fig.update_layout(
        title="Implied Volatility by Strike",
        xaxis_title="Strike",
        yaxis_title="Implied Volatility",
        hovermode="x unified",
        plot_bgcolor=tmpl["plot_bgcolor"],
        paper_bgcolor=tmpl["paper_bgcolor"],
        font_color=tmpl["font_color"],
        xaxis=dict(gridcolor=tmpl["grid_color"]),
        yaxis=dict(gridcolor=tmpl["grid_color"], tickformat=".2%"),
        showlegend=False,
        margin=dict(l=40, r=40, t=60, b=40),
    )
    return fig

def _get_est_offset() -> int:
    from zoneinfo import ZoneInfo
    from datetime import datetime
    offset = ZoneInfo("America/New_York").utcoffset(datetime.now()).total_seconds()
    return int(offset)


INDICATORS = {
    "SMA 20": {"period": 20, "color": "#ffa15a", "lineWidth": 2},
    "SMA 50": {"period": 50, "color": "#ab63fa", "lineWidth": 2},
    "EMA 20": {"period": 20, "color": "#ef553b", "lineWidth": 2},
    "EMA 200": {"period": 200, "color": "#2196f3", "lineWidth": 2},
    "Trend": {"alphaLength": 50},
    "Volume": {},
    "ATM_Option_Flow": {},
    "Andean Osc": {"length": 50, "sigLength": 9},
    "EMA 50 Squeeze": {},
    "Volume Profile": {},
    "Anchored VWAP": {"color": "#8b5cf6", "lineWidth": 2},
}


def _sma(values: list[float], period: int) -> list[float]:
    return [sum(values[i-period+1:i+1]) / period for i in range(period-1, len(values))]


def _ema(values: list[float], period: int) -> list[float]:
    k = 2 / (period + 1)
    ema = [values[period-1]]
    for v in values[period:]:
        ema.append(v * k + ema[-1] * (1 - k))
    return ema


def _trend(opens: list[float], closes: list[float], alpha_length: int) -> list[float]:
    alpha = 2.0 / (alpha_length + 1)
    up = [max(opens[0], closes[0])]
    dn = [min(opens[0], closes[0])]
    for i in range(1, len(closes)):
        u = max(max(closes[i], opens[i]), up[-1] - alpha * (up[-1] - closes[i]))
        d = min(min(closes[i], opens[i]), dn[-1] + alpha * (closes[i] - dn[-1]))
        up.append(u)
        dn.append(d)
    return [(up[i] + dn[i]) / 2 for i in range(len(up))]


# RTH session open in seconds-of-day (ET wall-clock), 9:30 ET = 34200s.
_RTH_OPEN_SOD = 9 * 3600 + 30 * 60


def _anchored_vwap(
    times: list[int],
    highs: list[float],
    lows: list[float],
    closes: list[float],
    volumes: list[float],
) -> list[float | None]:
    """Anchored VWAP (session / RTH-open anchor).

    Each new RTH session — the first bar whose ET wall-clock seconds-of-day
    is >= 9:30 ET (i.e. >= 34200s) on a new ET date — starts a fresh
    cumulative sum:  vwap[i] = sum(typical * vol) / sum(vol) within the
    current session. Bars before the first 9:30 ET in the loaded history
    (e.g. overnight data with no RTH open yet) accumulate into the
    "pending first session" so the VWAP line is continuous and useful.

    `times` MUST be the same ET-adjusted unix seconds produced by
    `_convert_time(t, et_offset)` (negative `et_offset`), so that
    `T % 86400` reads out as ET seconds-of-day and `T // 86400` is the
    ET date index.

    Returns a list the same length as the inputs; entries where
    cumulative volume is 0 (no volume and no prior anchor) are returned
    as None so the caller can filter them out for chart plotting.
    """
    n = len(times)
    if n == 0:
        return []
    out: list[float | None] = [None] * n
    cum_pv = 0.0
    cum_v = 0.0
    cur_day = None
    have_session = False
    for i in range(n):
        t = int(times[i])
        et_day = t // 86400
        et_sod = t % 86400
        # Start a fresh session on the first bar at/after 9:30 ET of a new
        # ET date. The very first bar always seeds the initial session so
        # the VWAP isn't blank when history begins pre-9:30 ET.
        new_session = False
        if not have_session:
            new_session = True
        elif et_sod >= _RTH_OPEN_SOD and et_day != cur_day:
            new_session = True
        if new_session:
            cur_day = et_day
            have_session = True
            cum_pv = 0.0
            cum_v = 0.0
        v = float(volumes[i]) if volumes and volumes[i] else 0.0
        h = float(highs[i]); l = float(lows[i]); c = float(closes[i])
        if v > 0:
            typical = (h + l + c) / 3.0
            cum_pv += typical * v
            cum_v += v
        if cum_v > 0:
            out[i] = cum_pv / cum_v
    return out


def _andean_oscillator(
    opens: list[float],
    closes: list[float],
    length: int = 50,
    sigLength: int = 9,
) -> tuple[list[float], list[float], list[float]]:
    alpha = 2.0 / (length + 1)
    up1 = [closes[0]]
    up2 = [closes[0] * closes[0]]
    dn1 = [closes[0]]
    dn2 = [closes[0] * closes[0]]
    for i in range(1, len(closes)):
        c = closes[i]
        o = opens[i]
        c2 = c * c
        o2 = o * o
        up1.append(max(max(c, o), up1[-1] - (up1[-1] - c) * alpha))
        up2.append(max(max(c2, o2), up2[-1] - (up2[-1] - c2) * alpha))
        dn1.append(min(min(c, o), dn1[-1] + (c - dn1[-1]) * alpha))
        dn2.append(min(min(c2, o2), dn2[-1] + (c2 - dn2[-1]) * alpha))
    bull = []
    bear = []
    signal = []
    for i in range(len(closes)):
        br = dn2[i] - dn1[i] * dn1[i]
        ber = up2[i] - up1[i] * up1[i]
        b = br ** 0.5 if br > 0 else 0.0
        be = ber ** 0.5 if ber > 0 else 0.0
        bull.append(b)
        bear.append(be)
        dom = max(b, be)
        if i == 0:
            sig = dom
        else:
            sig = signal[-1] + (1.0 / sigLength) * (dom - signal[-1])
        signal.append(sig)
    return bull, bear, signal


def _add_sqz_series(series: list, cd: list, sqz_data: list, color: str):
    pts = [(i, v) for i, v in enumerate(sqz_data) if v is not None]
    if not pts:
        return
    segments = []
    seg = [pts[0]]
    for j in range(1, len(pts)):
        if pts[j][0] == pts[j-1][0] + 1:
            seg.append(pts[j])
        else:
            segments.append(seg)
            seg = [pts[j]]
    segments.append(seg)
    for seg in segments:
        series.append({
            "type": "Line",
            "data": [{"time": cd[i]["time"], "value": v} for i, v in seg],
            "options": {"color": color, "lineWidth": 3, "title": color, "priceLineVisible": False},
        })


def _ema50_squeeze(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    length: int = 20,
    lowDev: float = 1.0,
    midDev: float = 1.5,
    highDev: float = 2.0,
) -> tuple[list[float], list[float | None], list[float | None], list[float | None]]:
    ema50 = _ema(closes, 50)
    ema50 = [None] * 49 + ema50  # pad to align with input length
    sma20 = [None] * 19 + _sma(closes, 20)
    bb_dev = [None] * 19
    for i in range(19, len(closes)):
        chunk = closes[i-19:i+1]
        mean = sum(chunk) / len(chunk)
        variance = sum((x - mean) ** 2 for x in chunk) / len(chunk)
        bb_dev.append(variance ** 0.5)

    tr = [highs[i] - lows[i] for i in range(len(closes))]
    for i in range(1, len(closes)):
        tr[i] = max(tr[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1]))
    atr = [None] * 19 + _sma(tr, 20)

    sqz_red = [None] * len(closes)
    sqz_black = [None] * len(closes)
    sqz_orange = [None] * len(closes)

    for i in range(19, len(closes)):
        if ema50[i] is None or sma20[i] is None or bb_dev[i] is None or atr[i] is None:
            continue
        ml = sma20[i]
        ub = ml + highDev * bb_dev[i]
        hc = ml + highDev * atr[i]
        mc = ml + midDev * atr[i]
        lc = ml + lowDev * atr[i]

        if ub < lc:
            sqz_orange[i] = ema50[i]
        elif ub < mc:
            sqz_red[i] = ema50[i]
        elif ub < hc:
            sqz_black[i] = ema50[i]

    return ema50, sqz_red, sqz_black, sqz_orange


def create_candlestick_chart(
    candles: list[dict],
    title: str = "Price History",
    indicators: list[str] | None = None,
    call_wall: float | None = None,
    put_wall: float | None = None,
    max_candles: int = 0,
) -> list[dict]:
    """Build a lightweight-charts chart dict for 1-min OHLCV."""
    if max_candles > 0 and len(candles) > max_candles:
        candles = candles[-max_candles:]
    tmpl = _get_template()
    bg = tmpl["plot_bgcolor"]
    tc = tmpl["font_color"]
    grid_col = tmpl["grid_color"]
    et_offset = _get_est_offset()

    if not candles:
        return [{
            "chart": {
                "height": 500,
                "layout": {"background": {"type": "solid", "color": bg}, "textColor": tc},
            },
            "series": [
                {"type": "Candlestick", "data": [],
                 "options": {"title": "No data — waiting for streaming..."}},
            ],
        }]



    # convert datetime ms → seconds for LWC time, offset to Eastern Time, sort ascending
    cd = []
    for c in candles:
        t = c["datetime"]
        if isinstance(t, (int, float)) and t > 1e11:
            t = int(t / 1000)
        cd.append({
            "time": int(t) + et_offset,
            "open": float(c["open"]),
            "high": float(c["high"]),
            "low": float(c["low"]),
            "close": float(c["close"]),
        })
    cd.sort(key=lambda x: x["time"])

    # deduplicate: keep last entry per unique time
    seen: set[int] = set()
    deduped: list[dict] = []
    for c in cd:
        if c["time"] not in seen:
            seen.add(c["time"])
            deduped.append(c)
        else:
            # Replace existing entry with the new one (keep last)
            for i, d in enumerate(deduped):
                if d["time"] == c["time"]:
                    deduped[i] = c
                    break
    cd = deduped

    closes = [c["close"] for c in cd]
    opens = [c["open"] for c in cd]
    highs = [c["high"] for c in cd]
    lows = [c["low"] for c in cd]

    vol_map = {}
    for c in candles:
        t = c["datetime"]
        if isinstance(t, (int, float)) and t > 1e11:
            t = int(t / 1000)
        t = int(t) + et_offset
        vol_map[t] = float(c.get("volume", 0))

    buy_vol = []
    sell_vol = []
    for c in cd:
        vol = vol_map.get(c["time"], 0)
        if "buy_vol" in c and "sell_vol" in c:
            bv = int(c["buy_vol"])
            sv = int(c["sell_vol"])
        else:
            hl = c["high"] - c["low"]
            if hl > 0:
                bv = round(vol * (c["close"] - c["low"]) / hl)
                sv = round(vol * (c["high"] - c["close"]) / hl)
            else:
                bv = round(vol * 0.5)
                sv = round(vol * 0.5)
        buy_vol.append({"time": c["time"], "value": bv, "color": "#26a69a"})
        sell_vol.append({"time": c["time"], "value": sv, "color": "#ef5350"})

    has_sub_charts = bool(indicators and (("Volume" in indicators) or ("Andean Osc" in indicators)))

    time_scale: dict = {
        "borderColor": grid_col,
        "visible": not has_sub_charts,
    }
    if not has_sub_charts:
        time_scale["timeVisible"] = True
        time_scale["secondsVisible"] = False
    n_cd = len(cd)
    if n_cd > 100:
        time_scale["barSpacing"] = 4 if n_cd > 500 else 6
        visible_from = cd[-100]["time"] if n_cd >= 100 else cd[0]["time"]
        time_scale["visibleRange"] = {"from": visible_from, "to": cd[-1]["time"]}
    elif n_cd > 0:
        time_scale["visibleRange"] = {"from": cd[0]["time"], "to": cd[-1]["time"]}

    # Sub-chart time scales mirror the main candlestick time scale so the
    # Volume / Andean Osc subplots stay x-axis-aligned with the price chart.
    sub_time_scale: dict = {
        "borderColor": grid_col,
        "timeVisible": True,
        "secondsVisible": False,
    }
    if "visibleRange" in time_scale:
        sub_time_scale["visibleRange"] = dict(time_scale["visibleRange"])
    if "barSpacing" in time_scale:
        sub_time_scale["barSpacing"] = time_scale["barSpacing"]
    volume_time_scale = dict(sub_time_scale)
    andean_time_scale = dict(sub_time_scale)

    layout = {
        "height": 500,
        "layout": {"background": {"type": "solid", "color": bg}, "textColor": tc},
        "handleScroll": True,
        "handleScale": True,
        "grid": {
            "vertLines": {"color": grid_col},
            "horzLines": {"color": grid_col},
        },
        "rightPriceScale": {
            "scaleMargins": {"top": 0.0, "bottom": 0.25},
            "borderVisible": True,
        },
        
        "timeScale": time_scale,
        "crosshair": {"mode": 0},
    }

    series: list[dict] = [
        {"type": "Candlestick", "data": cd,
         "options": {
             "upColor": "#00cc96", "downColor": "#ef553b",
             "borderUpColor": "#00cc96", "borderDownColor": "#ef553b",
             "wickUpColor": "#00cc96", "wickDownColor": "#ef553b",
          }},
    ]

    if call_wall is not None:
        series.append({
            "type": "Line",
            "data": [{"time": cd[i]["time"], "value": call_wall} for i in range(len(cd))],
            "options": {"color": "#ef553b", "lineWidth": 1, "lineStyle": 2, "title": "Call Wall"},
        })
    if put_wall is not None:
        series.append({
            "type": "Line",
            "data": [{"time": cd[i]["time"], "value": put_wall} for i in range(len(cd))],
            "options": {"color": "#00cc96", "lineWidth": 1, "lineStyle": 2, "title": "Put Wall"},
        })

    volume_added = False
    
    if indicators:
        for name in indicators:
            cfg = INDICATORS.get(name)
            if not cfg:
                continue
            if name == "Volume":
                volume_added = True
                continue
            if name in ("Andean Osc", "EMA 50 Squeeze", "Trend"):
                continue
            period = cfg["period"]
            if len(closes) < period:
                continue
            if name.startswith("EMA"):
                vals = _ema(closes, period)
            else:
                vals = _sma(closes, period)
            offset = period - 1
            if name in ("EMA 200", "EMA 20"):
                opts = {"color": cfg["color"], "lineWidth": cfg["lineWidth"], "lastValueVisible": False}
            else:
                opts = {"color": cfg["color"], "lineWidth": cfg["lineWidth"], "title": name}
            series.append({
                "type": "Line",
                "data": [{"time": cd[i]["time"], "value": vals[i-offset]} for i in range(offset, len(cd))],
                "options": opts,
            })

    if "EMA 50 Squeeze" in (indicators or []):
        ema50, sqz_red, sqz_black, sqz_orange = _ema50_squeeze(highs, lows, closes)
        series.append({"type": "Line", "data": [{"time": cd[i]["time"], "value": ema50[i]} for i in range(len(cd)) if ema50[i] is not None], "options": {"color": "#00cc96", "lineWidth": 2, "title": "EMA 50"}})
        _add_sqz_series(series, cd, sqz_red, "#ef553b")
        _add_sqz_series(series, cd, sqz_black, "#000000")
        _add_sqz_series(series, cd, sqz_orange, "#ffa500")

    if "Trend" in (indicators or []):
        alpha_length = 50
        mid_vals = _trend(opens, closes, alpha_length)
        series.append({
            "type": "Line",
            "data": [{"time": cd[i]["time"], "value": mid_vals[i]} for i in range(len(cd))],
            "options": {"color": "#ffa15a", "lineWidth": 2, "title": "Trend", "lastValueVisible": False},
        })

    charts = []
    
    main_chart = {
        "height": 500,
        "layout": {"background": {"type": "solid", "color": bg}, "textColor": tc},
        "handleScroll": True,
        "handleScale": True,
        "grid": {
            "vertLines": {"color": grid_col},
            "horzLines": {"color": grid_col},
        },
        "rightPriceScale": {
            "scaleMargins": {"top": 0.0, "bottom": 0.25},
            "borderVisible": False,
        },
        "timeScale": time_scale,
        "crosshair": {"mode": 0},
    }
    charts.append({"chart": main_chart, "series": series})
    
    if "Volume" in (indicators or []):
        volume_chart = {
            "height": 150,
            "layout": {"background": {"type": "solid", "color": bg}, "textColor": tc},
            "handleScroll": True,
            "handleScale": True,
            "grid": {
                "vertLines": {"color": grid_col},
                "horzLines": {"color": grid_col},
            },
            "rightPriceScale": {
                "scaleMargins": {"top": 0.15, "bottom": 0.15},
                "borderVisible": False,
            },
            "timeScale": volume_time_scale,
            "crosshair": {"mode": 0},
        }
        volume_series = [{
            "type": "Histogram",
            "data": buy_vol,
            "options": {
                "color": "#26a69a",
                "priceFormat": {"type": "volume"},
                "lastValueVisible": False,
            },
        }, {
            "type": "Histogram",
            "data": sell_vol,
            "options": {
                "color": "#ef5350",
                "priceFormat": {"type": "volume"},
                "lastValueVisible": False,
            },
        }]
        charts.append({"chart": volume_chart, "series": volume_series})
    
    if "Andean Osc" in (indicators or []):
        bull, bear, signal = _andean_oscillator(opens, closes,
                                                INDICATORS["Andean Osc"]["length"],
                                                INDICATORS["Andean Osc"]["sigLength"])
        andean_chart = {
            "height": 150,
            "layout": {"background": {"type": "solid", "color": bg}, "textColor": tc},
            "handleScroll": True,
            "handleScale": True,
            "grid": {
                "vertLines": {"color": grid_col},
                "horzLines": {"color": grid_col},
            },
            "rightPriceScale": {
                "scaleMargins": {"top": 0.15, "bottom": 0.15},
                "borderVisible": False,
            },
            "timeScale": andean_time_scale,
            "crosshair": {"mode": 0},
        }
        andean_series = [
            {"type": "Line", "data": [{"time": cd[i]["time"], "value": bull[i]} for i in range(len(cd))],
             "options": {"color": "#00cc96", "lineWidth": 2, "priceLineVisible": False}},
            {"type": "Line", "data": [{"time": cd[i]["time"], "value": bear[i]} for i in range(len(cd))],
             "options": {"color": "#ef553b", "lineWidth": 2, "priceLineVisible": False}},
            {"type": "Line", "data": [{"time": cd[i]["time"], "value": signal[i]} for i in range(len(cd))],
             "options": {"color": "#ffa15a", "lineWidth": 1, "priceLineVisible": False}},
            {"type": "Line", "data": [{"time": cd[i]["time"], "value": 0} for i in range(len(cd))],
             "options": {"color": "#ffffff", "lineWidth": 1, "lineStyle": 2, "priceLineVisible": False, "lastValueVisible": False, "crosshairMarkerVisible": False}},
        ]
        charts.append({"chart": andean_chart, "series": andean_series})
    
    return charts


STYLE = """
<style>
    .stApp > header { display: none; }
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }
    .stSelectbox label, .stMultiSelect label {
        font-size: 0.85rem !important;
    }
    .stAlert, .stSuccess, .stWarning, .stInfo {
        background: none !important;
        background-color: transparent !important;
    }
</style>
"""

CSS = """
<style>
    .gex-metric {
        background: #f8fafc;
        border-radius: 8px;
        padding: 12px 16px;
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    .gex-metric .label {
        font-size: 0.75rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .gex-metric .value {
        font-size: 1.25rem;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
    }
    .gex-metric .value.positive { color: #00cc96; }
    .gex-metric .value.negative { color: #ef553b; }
    .gex-metric .value.neutral { color: #1e293b; }
</style>
"""


def _get_style(is_dark: bool) -> str:
    return DARK_STYLE if is_dark else STYLE


def _get_css(is_dark: bool) -> str:
    return DARK_CSS if is_dark else CSS


DARK_STYLE = """
<style>
    .stApp > header { display: none; }
    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }
    .stSelectbox label, .stMultiSelect label {
        font-size: 0.85rem !important;
    }
    .stAlert, .stSuccess, .stWarning, .stInfo {
        background: none !important;
        background-color: transparent !important;
    }
    .stApp { background-color: #0f172a; }
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div {
        background-color: #0b1120 !important;
    }
    .stSidebar p, .stSidebar label, .stSidebar span,
    .stSidebar .stMarkdown { color: #e2e8f0 !important; }
    .main > div { color: #e2e8f0; }
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        border-color: #334155 !important;
    }
    section[data-testid="stSidebar"] .stMultiSelect div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border-color: #d1d5db !important;
    }
    section[data-testid="stSidebar"] .stMultiSelect div[data-baseweb="tag"] {
        background-color: #e2e8f0 !important;
        color: #1e293b !important;
    }
    section[data-testid="stSidebar"] .stMultiSelect div[data-baseweb="tag"] * { color: #1e293b !important; }

    .main .stMultiSelect div[data-baseweb="select"] > div {
        background-color: #1a365d !important;
        color: #e2e8f0 !important;
        border-color: #2b6cb0 !important;
    }
    .main .stMultiSelect div[data-baseweb="tag"] {
        background-color: #2b6cb0 !important;
        color: #ffffff !important;
    }
    .main .stMultiSelect div[data-baseweb="tag"] * { color: #ffffff !important; }
    .main .stMultiSelect div[data-baseweb="input"] { color: #e2e8f0 !important; }
    .main .stMultiSelect div[data-baseweb="input"] input { color: #e2e8f0 !important; }
    div[role="listbox"] ul { background-color: #1e293b !important; }
    div[role="listbox"] li { color: #e2e8f0 !important; }
    div[role="listbox"] li:hover { background-color: #334155 !important; }
    .stRadio div[role="radiogroup"] label { color: #ffffff !important; }
    .stRadio div[role="radiogroup"] label * { color: #ffffff !important; }
    .stRadio div[role="radiogroup"] p { color: #ffffff !important; }
    .stRadio div[role="radiogroup"] span { color: #ffffff !important; }
    .stRadio div[role="radiogroup"] div { color: #ffffff !important; }
    .stToggle label { color: #ffffff !important; }
    .stToggle label * { color: #ffffff !important; }
    .stToggle p { color: #ffffff !important; }
    .stToggle span { color: #ffffff !important; }
    .stCheckbox label { color: #e2e8f0 !important; }
    .stNumberInput input {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        border-color: #334155 !important;
    }
    .stTextInput input {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        border-color: #334155 !important;
    }
    div[data-testid="stTabs"] [data-baseweb="tab-list"] { background-color: transparent !important; border-bottom-color: #334155 !important; }
    div[data-testid="stTabs"] [data-baseweb="tab"],
    div[data-testid="stTabs"] [data-baseweb="tab"] *,
    div[data-testid="stTabs"] [data-baseweb="tab"] span,
    div[data-testid="stTabs"] [data-baseweb="tab"] div,
    div[data-testid="stTabs"] [data-baseweb="tab"] p { color: #ffffff !important; fill: #ffffff !important; }
    div[data-testid="stTabs"] [data-baseweb="tab"] svg { fill: #ffffff !important; }
    div[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"],
    div[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] * { color: #ffffff !important; fill: #ffffff !important; border-bottom-color: #60a5fa !important; }
    div[data-testid="stTabs"] [data-baseweb="tab"]:hover,
    div[data-testid="stTabs"] [data-baseweb="tab"]:hover * { color: #ffffff !important; fill: #ffffff !important; }
    div[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background-color: #60a5fa !important; }
    div[data-testid="stTabs"] [data-baseweb="tab-border"] { border-bottom-color: #334155 !important; }
    [data-baseweb="tab-panel"] { color: #e2e8f0 !important; }
    div[data-testid="stExpander"] { background-color: #ffffff !important; border-color: #e2e8f0 !important; }
    div[data-testid="stExpander"] summary { color: #1e293b !important; }
    div[data-testid="stExpander"] > div { background-color: #ffffff !important; }
    div[data-testid="stExpander"] p,
    div[data-testid="stExpander"] li,
    div[data-testid="stExpander"] span,
    div[data-testid="stExpander"] h1,
    div[data-testid="stExpander"] h2,
    div[data-testid="stExpander"] h3,
    div[data-testid="stExpander"] h4,
    div[data-testid="stExpander"] h5,
    div[data-testid="stExpander"] h6,
    div[data-testid="stExpander"] strong,
    div[data-testid="stExpander"] label { color: #1e293b !important; }
    div[data-testid="stExpander"] strong { color: #0f172a !important; }
    .stButton button {
        color: #e2e8f0 !important;
        background-color: #1e293b !important;
        border-color: #334155 !important;
    }
    .stButton button:hover {
        background-color: #334155 !important;
        border-color: #60a5fa !important;
    }
    h1, h2, h3, h4, h5, h6 { color: #e2e8f0 !important; }
    .stSubheader { color: #e2e8f0 !important; }
    .stCaption { color: #94a3b8 !important; }
</style>
"""

DARK_CSS = """
<style>
    .gex-metric { background: #1e293b; border-radius: 8px; padding: 12px 16px; border: 1px solid #334155; text-align: center; }
    .gex-metric .label { font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
    .gex-metric .value { font-size: 1.25rem; font-weight: 700; font-variant-numeric: tabular-nums; }
    .gex-metric .value.positive { color: #34d399; }
    .gex-metric .value.negative { color: #f87171; }
    .gex-metric .value.neutral { color: #e2e8f0; }
</style>
"""
