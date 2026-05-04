import os, streamlit as st, plotly.graph_objects as go, pandas as pd, requests

API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(
    page_title="VectorBT",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── THEME STATE (light default)
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False

dark = st.session_state["dark_mode"]

DARK_VARS = """
  --bg:#0a0c10;--surface:#10141c;--surface2:#161b26;
  --border:rgba(255,255,255,0.07);
  --accent:#00e5a0;--accent2:#3b7dff;--accent3:#f7c948;
  --text:#e8eaf0;--muted:#5a6175;--danger:#ff4f6a;
  --card-shadow:none;
  --grid-color:rgba(255,255,255,0.04);
  --input-text:#e8eaf0;
"""
LIGHT_VARS = """
  --bg:#f4f6fa;--surface:#ffffff;--surface2:#eef0f5;
  --border:rgba(0,0,0,0.09);
  --accent:#00b87a;--accent2:#2563eb;--accent3:#d4a017;
  --text:#0f1117;--muted:#6b7280;--danger:#dc2626;
  --card-shadow:0 1px 4px rgba(0,0,0,0.07);
  --grid-color:rgba(0,0,0,0.05);
  --input-text:#0f1117;
"""

CSS_VARS = DARK_VARS if dark else LIGHT_VARS

st.markdown(
    f"""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,400&family=Instrument+Serif:ital@0;1&family=Syne:wght@400;600;700;800&display=swap');
:root{{{CSS_VARS}}}
html,body,[data-testid="stAppViewContainer"]{{background-color:var(--bg)!important;color:var(--text)!important;font-family:'Syne',sans-serif!important}}
[data-testid="stAppViewContainer"]>.main,[data-testid="stHeader"]{{background-color:var(--bg)!important}}
section[data-testid="stSidebar"]{{display:none!important}}
[data-testid="collapsedControl"]{{display:none!important}}
.logo{{font-family:'Instrument Serif',serif;font-size:22px;color:var(--text);display:flex;align-items:center;gap:8px}}
.logo-badge{{background:var(--accent);color:#000;font-family:'DM Mono',monospace;font-size:9px;padding:2px 6px;border-radius:3px;text-transform:uppercase}}
.topbar{{display:flex;align-items:center;justify-content:space-between;padding:10px 0 18px;border-bottom:1px solid var(--border);margin-bottom:24px}}
.run-status{{display:flex;align-items:center;gap:8px;font-family:'DM Mono',monospace;font-size:11px;color:var(--muted)}}
.pulse{{width:8px;height:8px;border-radius:50%;background:var(--accent);display:inline-block;animation:pulse 2s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.4;transform:scale(.8)}}}}
.page-title{{font-family:'Instrument Serif',serif;font-size:30px;letter-spacing:-.5px;line-height:1.1}}
.page-title em{{color:var(--accent);font-style:italic}}
.page-subtitle{{font-family:'DM Mono',monospace;font-size:11px;color:var(--muted);margin-top:6px}}
.stat-card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:18px 20px;position:relative;overflow:hidden;box-shadow:var(--card-shadow)}}
.stat-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px}}
.stat-card.green::before{{background:var(--accent)}}.stat-card.blue::before{{background:var(--accent2)}}
.stat-card.yellow::before{{background:var(--accent3)}}.stat-card.red::before{{background:var(--danger)}}.stat-card.grey::before{{background:var(--muted)}}
.stat-label{{font-family:'DM Mono',monospace;font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}}
.stat-value{{font-family:'Instrument Serif',serif;font-size:28px;letter-spacing:-1px;line-height:1}}
.stat-value.pos{{color:var(--accent)}}.stat-value.neg{{color:var(--danger)}}.stat-value.blue{{color:var(--accent2)}}
.stat-delta{{font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);margin-top:6px}}.stat-delta span{{color:var(--accent)}}
.dash-card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden;box-shadow:var(--card-shadow)}}
.card-header{{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;border-bottom:1px solid var(--border)}}
.card-title{{font-size:13px;font-weight:700;letter-spacing:.02em;display:flex;align-items:center;gap:8px}}
.dot{{width:6px;height:6px;border-radius:50%;display:inline-block}}.card-body{{padding:18px 20px}}
.trade-table{{width:100%;border-collapse:collapse}}
.trade-table thead th{{font-family:'DM Mono',monospace;font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);text-align:left;padding:0 0 10px;border-bottom:1px solid var(--border)}}
.trade-table tbody tr{{border-bottom:1px solid var(--border)}}.trade-table tbody tr:last-child{{border-bottom:none}}
.trade-table tbody td{{padding:10px 0;font-family:'DM Mono',monospace;font-size:11px;color:var(--text)}}
.tag{{display:inline-block;font-size:9px;font-weight:700;padding:2px 7px;border-radius:3px;text-transform:uppercase;letter-spacing:.05em}}
.tag-long{{background:rgba(0,229,160,.15);color:var(--accent)}}.tag-short{{background:rgba(255,79,106,.15);color:var(--danger)}}
.pos-val{{color:var(--accent)}}.neg-val{{color:var(--danger)}}
.error-box{{background:rgba(220,38,38,.1);border:1px solid rgba(220,38,38,.3);border-radius:8px;padding:16px;color:var(--danger);font-family:'DM Mono',monospace;font-size:12px;white-space:pre-wrap}}
[data-testid="stSlider"]>div>div>div{{background:var(--accent)!important}}[data-testid="stSlider"]>div>div{{background:var(--surface2)!important}}
.stSelectbox>div>div,.stTextInput>div>div>input,.stNumberInput>div>div>input{{background:var(--surface2)!important;border:1px solid var(--border)!important;color:var(--input-text)!important;font-family:'DM Mono',monospace!important}}
label[data-testid="stWidgetLabel"] p{{font-family:'DM Mono',monospace!important;font-size:9px!important;text-transform:uppercase!important;color:var(--muted)!important}}
.stButton>button{{width:100%;background:var(--accent)!important;border:none!important;border-radius:8px!important;font-family:'Syne',sans-serif!important;font-size:13px!important;font-weight:800!important;color:#000!important;text-transform:uppercase!important;padding:12px 0!important}}
.block-container{{padding:1.5rem 2rem 2rem!important;max-width:100%!important}}.stMarkdown p{{margin:0}}
.theme-btn{{cursor:pointer;background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:5px 12px;font-family:'DM Mono',monospace;font-size:11px;color:var(--muted);display:inline-flex;align-items:center;gap:6px}}
</style>""",
    unsafe_allow_html=True,
)


# ── HELPERS
def fmt_pct(v):
    return f"+{v*100:.1f}%" if v >= 0 else f"{v*100:.1f}%"


def fmt_val(v):
    return f"${v:,.0f}"


def pct_cls(v):
    return "pos" if v >= 0 else "neg"


def fmt_metric_label(key):
    """Convert camelCase key to readable label."""
    import re

    s = re.sub(r"([A-Z])", r" \1", key).strip()
    return s.title()


def fmt_metric_value(key, val):
    """Format a metric value based on its key name."""
    key_lower = key.lower()
    if val is None:
        return "—"
    if (
        "return" in key_lower
        or "drawdown" in key_lower
        or "volatility" in key_lower
        or "rate" in key_lower
        or "alpha" in key_lower
    ):
        if isinstance(val, (int, float)):
            return fmt_pct(val)
    if "value" in key_lower or "capital" in key_lower or "portfolio" in key_lower:
        if isinstance(val, (int, float)):
            return fmt_val(val)
    if isinstance(val, float):
        return f"{val:.2f}"
    return str(val)


def metric_raw_for_color(key, val):
    """Return raw numeric val if it makes sense to color it."""
    key_lower = key.lower()
    if "return" in key_lower or "drawdown" in key_lower or "alpha" in key_lower:
        return val
    return None


# ── API CALLS
@st.cache_data(ttl=300, show_spinner=False)
def fetch_strategies():
    try:
        r = requests.get(f"{API_BASE}/api/strategies", timeout=10)
        r.raise_for_status()
        data = r.json()
        # Accept list or {"strategies": [...]}
        if isinstance(data, list):
            return data, None
        if isinstance(data, dict):
            return data.get("strategies", list(data.keys())), None
        return [], "Unexpected response format"
    except requests.exceptions.ConnectionError:
        return [], "Cannot reach backend"
    except Exception as e:
        return [], str(e)


@st.cache_data(ttl=300, show_spinner=False)
def fetch_strategy_params(strategy_name):
    try:
        r = requests.get(
            f"{API_BASE}/api/strategies/{strategy_name}/parameters", timeout=10
        )
        r.raise_for_status()
        data = r.json()
        return data.get("parameters", {}), None
    except requests.exceptions.ConnectionError:
        return {}, "Cannot reach backend"
    except Exception as e:
        return {}, str(e)


@st.cache_data(ttl=120, show_spinner=False)
def call_backend(strategy, asset, start_date, end_date, capital, params_tuple):
    params = dict(params_tuple)
    try:
        r = requests.post(
            f"{API_BASE}/api/run",
            json={
                "strategy": strategy,
                "asset": asset,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "initial_capital": float(capital),
                "parameters": params,
            },
            timeout=90,
        )
        r.raise_for_status()
        return r.json(), None
    except requests.exceptions.ConnectionError:
        return (
            None,
            "Cannot reach the backend. Is it running?\n\nStart it with:\n  uvicorn src.engine.main:app --reload --port 8000",
        )
    except requests.exceptions.HTTPError as e:
        try:
            detail = e.response.json().get("detail", str(e))
        except:
            detail = str(e)
        return None, f"Backend error: {detail}"
    except Exception as e:
        return None, str(e)


# ── TOPBAR
meta = st.session_state.get("last_meta", {})
if meta:
    status = (
        f"Last backtest: <strong style='color:var(--text)'>"
        f"{meta.get('strategy','—')} — {meta.get('asset','—')} "
        f"{str(meta.get('start_date',''))[:4]}–{str(meta.get('end_date',''))[:4]}"
        f"</strong> &nbsp;·&nbsp; source: {meta.get('data_source','—')}"
    )
else:
    status = "No backtest run yet — configure below and click Run"

top_left, top_right = st.columns([8, 1])
with top_left:
    st.markdown(
        f"""<div class="topbar"><div class="logo">VectorBT <span class="logo-badge">ALPHA</span></div>
        <div class="run-status"><span class="pulse"></span> {status}</div></div>""",
        unsafe_allow_html=True,
    )
with top_right:
    theme_label = "☀ Light" if dark else "🌙 Dark"
    if st.button(theme_label, key="theme_toggle"):
        st.session_state["dark_mode"] = not dark
        st.rerun()

# ── FETCH STRATEGIES
strategies_list, strat_err = fetch_strategies()
if strat_err and not strategies_list:
    st.markdown(
        f'<div class="error-box">Could not load strategies: {strat_err}</div>',
        unsafe_allow_html=True,
    )
    strategies_list = []

# ── CONFIG CARD HEADER
st.markdown(
    """<div class="dash-card" style="margin-bottom:16px"><div class="card-header"><div class="card-title"><span class="dot" style="background:#f7c948"></span> Strategy Configuration</div></div></div>""",
    unsafe_allow_html=True,
)

c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
strategy = c1.selectbox("STRATEGY", strategies_list if strategies_list else ["—"])
asset = c2.text_input("ASSET", value="AAPL")
sd = c3.date_input("START DATE", value=pd.Timestamp("2018-01-01"))
ed = c4.date_input("END DATE", value=pd.Timestamp("2024-06-30"))
capital = c5.number_input("CAPITAL ($)", value=100000, step=10000)

# ── DYNAMIC STRATEGY PARAMETERS
params = {}
if strategy and strategy != "—":
    param_defs, param_err = fetch_strategy_params(strategy)
    if param_err:
        st.markdown(
            f'<div class="error-box" style="margin-bottom:8px">Could not load parameters: {param_err}</div>',
            unsafe_allow_html=True,
        )
    elif param_defs:
        param_keys = list(param_defs.keys())
        param_cols = st.columns(max(len(param_keys), 1))
        for col, pkey in zip(param_cols, param_keys):
            pdef = param_defs[pkey]
            ptype = pdef.get("type", "float")
            pdefault = pdef.get("default", 0)
            label = pkey.replace("_", " ").upper()
            if ptype == "int":
                params[pkey] = col.number_input(label, value=int(pdefault), step=1)
            else:
                params[pkey] = col.number_input(
                    label, value=float(pdefault), step=0.1, format="%.2f"
                )

# ── RUN BUTTON
if st.button(" ▶   RUN BACKTEST "):
    with st.spinner("Running backtest on backend…"):
        result, err = call_backend(
            strategy, asset, sd, ed, capital, tuple(sorted(params.items()))
        )
    if err:
        st.markdown(f'<div class="error-box">{err}</div>', unsafe_allow_html=True)
    elif result:
        st.session_state["last_result"] = result
        st.session_state["last_meta"] = result.get("meta", {})

st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── DATA
data = st.session_state.get("last_result")
has_data = data is not None
metrics = data["metrics"] if has_data else {}
charts = data["charts"] if has_data else {}
trades = data["trades"] if has_data else []
meta = st.session_state.get("last_meta", {})
ts = meta.get("strategy", strategy)
ta = meta.get("asset", asset)
ss = str(meta.get("start_date", sd))[:10]
es = str(meta.get("end_date", ed))[:10]

st.markdown(
    f"""<div style="margin-bottom:22px"><div class="page-title">{ts} &nbsp;<em>vs</em>&nbsp; Benchmark</div>
<div class="page-subtitle">{ta} · {ss} → {es} · Initial capital: {fmt_val(capital)}</div></div>""",
    unsafe_allow_html=True,
)

# ── STAT CARDS — show only metrics present in response
CARD_TEMPLATES = [
    (
        "green",
        "cumulativeReturn",
        lambda m: fmt_pct(m["cumulativeReturn"]),
        lambda m: f"Alpha: <span>{fmt_pct(m['alpha'])}</span>" if "alpha" in m else "",
    ),
    (
        "blue",
        "sharpeRatio",
        lambda m: f"{m['sharpeRatio']:.2f}",
        lambda m: "Annualised risk-adj.",
    ),
    (
        "yellow",
        "maxDrawdown",
        lambda m: fmt_pct(m["maxDrawdown"]),
        lambda m: "Peak → Trough",
    ),
    (
        "red",
        "winRate",
        lambda m: f"{m['winRate']*100:.1f}%",
        lambda m: "Daily positive sessions",
    ),
    (
        "grey",
        "finalPortfolioValue",
        lambda m: fmt_val(m["finalPortfolioValue"]),
        lambda m: "Final value",
    ),
]

# Build only the cards whose metric key exists in the response
active_cards = [t for t in CARD_TEMPLATES if not has_data or t[1] in metrics]
if not active_cards:
    active_cards = CARD_TEMPLATES  # fallback to show placeholders

cols5 = st.columns(len(active_cards))
if has_data:
    for col, (cls, key, val_fn, delta_fn) in zip(cols5, active_cards):
        if key not in metrics:
            continue
        raw = metrics[key]
        val = val_fn(metrics)
        delta = delta_fn(metrics)
        vc = (
            pct_cls(raw)
            if isinstance(raw, (int, float))
            and ("Return" in key or "Drawdown" in key or "winRate" in key)
            else ""
        )
        col.markdown(
            f"""<div class="stat-card {cls}"><div class="stat-label">{fmt_metric_label(key)}</div><div class="stat-value {vc}">{val}</div><div class="stat-delta">{delta}</div></div>""",
            unsafe_allow_html=True,
        )
else:
    for col, (cls, key, _, __) in zip(cols5, active_cards):
        col.markdown(
            f"""<div class="stat-card grey"><div class="stat-label">{fmt_metric_label(key)}</div><div class="stat-value" style="color:var(--muted)">—</div><div class="stat-delta">Run a backtest</div></div>""",
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── EQUITY CURVE
st.markdown(
    """<div class="dash-card"><div class="card-header"><div class="card-title"><span class="dot" style="background:#00e5a0"></span> Equity Curve</div></div></div>""",
    unsafe_allow_html=True,
)

grid_color = "rgba(255,255,255,0.04)" if dark else "rgba(0,0,0,0.06)"
tick_color = "#5a6175" if dark else "#9ca3af"
legend_color = "#e8eaf0" if dark else "#0f1117"

if has_data and charts.get("strategy"):
    sdf = pd.DataFrame(charts["strategy"])
    bdf = pd.DataFrame(charts["benchmark"])
    sdf["time"] = pd.to_datetime(sdf["time"])
    bdf["time"] = pd.to_datetime(bdf["time"])
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=bdf["time"],
            y=bdf["value"],
            name="Benchmark",
            line=dict(color="#3b7dff", width=1.5, dash="dot"),
            fill="tozeroy",
            fillcolor="rgba(59,125,255,0.05)",
        )
    )
    accent_hex = "#00e5a0" if dark else "#00b87a"
    fig.add_trace(
        go.Scatter(
            x=sdf["time"],
            y=sdf["value"],
            name=ts,
            line=dict(color=accent_hex, width=2.5),
            fill="tozeroy",
            fillcolor="rgba(0,229,160,0.08)",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Mono", color=tick_color, size=9),
        margin=dict(l=10, r=10, t=10, b=10),
        height=240,
        legend=dict(
            orientation="h",
            x=1,
            xanchor="right",
            y=1.05,
            font=dict(color=legend_color, size=10),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            tickfont=dict(color=tick_color, size=9),
            tickformat="%Y",
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=grid_color,
            zeroline=False,
            tickformat="$,.0f",
            tickfont=dict(color=tick_color, size=9),
        ),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
else:
    st.markdown(
        "<div style='height:240px;display:flex;align-items:center;justify-content:center;color:var(--muted);font-family:DM Mono;font-size:12px'>Run a backtest to see the equity curve</div>",
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── TRADES + RISK METRICS
ct, cr = st.columns(2, gap="medium")
with ct:
    st.markdown(
        """<div class="dash-card"><div class="card-header"><div class="card-title"><span class="dot" style="background:#3b7dff"></span> Recent Trades</div></div>""",
        unsafe_allow_html=True,
    )
    if has_data and trades:
        rows = ""
        for t in trades[:8]:
            pc = "pos-val" if t["return"] >= 0 else "neg-val"
            rs = (
                f"+{t['return']*100:.2f}%"
                if t["return"] >= 0
                else f"{t['return']*100:.2f}%"
            )
            tag = f"<span class='tag tag-{t['action']}'>{t['action'].upper()}</span>"
            rows += f"<tr><td>{t['entryDate']}</td><td>{tag}</td><td>${t['entryPrice']:,.2f}</td><td>${t['exitPrice']:,.2f}</td><td class='{pc}'>{rs}</td><td>{t.get('days','—')}d</td></tr>"
        st.markdown(
            f"""<div class="card-body"><table class="trade-table"><thead><tr><th>Entry</th><th>Side</th><th>Entry $</th><th>Exit $</th><th>Return</th><th>Hold</th></tr></thead><tbody>{rows}</tbody></table></div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='card-body' style='color:var(--muted);font-family:DM Mono;font-size:12px'>No trade data yet</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

with cr:
    st.markdown(
        """<div class="dash-card"><div class="card-header"><div class="card-title"><span class="dot" style="background:#f7c948"></span> Risk Metrics</div></div>""",
        unsafe_allow_html=True,
    )
    if has_data and metrics:
        trows = ""
        for key, val in metrics.items():
            label = fmt_metric_label(key)
            formatted = fmt_metric_value(key, val)
            raw = metric_raw_for_color(key, val)
            color = (
                "color:var(--accent)"
                if (raw is not None and isinstance(raw, (int, float)) and raw >= 0)
                else ("color:var(--danger)" if raw is not None else "color:var(--text)")
            )
            trows += (
                f"<tr style='border-bottom:1px solid var(--border)'>"
                f"<td style='padding:8px 0;font-family:DM Mono;font-size:10px;color:var(--muted)'>{label}</td>"
                f"<td style='padding:8px 0;font-family:DM Mono;font-size:11px;text-align:right;{color}'>{formatted}</td>"
                f"</tr>"
            )
        st.markdown(
            f"""<div class="card-body"><table style="width:100%;border-collapse:collapse"><tbody>{trows}</tbody></table></div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='card-body' style='color:var(--muted);font-family:DM Mono;font-size:12px'>Run a backtest to see metrics</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
