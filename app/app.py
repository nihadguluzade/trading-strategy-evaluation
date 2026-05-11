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
  color-scheme:dark;
"""
LIGHT_VARS = """
  --bg:#f4f6fa;--surface:#ffffff;--surface2:#eef0f5;
  --border:rgba(0,0,0,0.09);
  --accent:#00b87a;--accent2:#2563eb;--accent3:#d4a017;
  --text:#0f1117;--muted:#6b7280;--danger:#dc2626;
  --card-shadow:0 1px 4px rgba(0,0,0,0.07);
  --grid-color:rgba(0,0,0,0.05);
  --input-text:#0f1117;
  color-scheme:light;
"""

CSS_VARS = DARK_VARS if dark else LIGHT_VARS

st.markdown(
    f"""<style>
:root{{{CSS_VARS}--font-ui:'Geist','Segoe UI',system-ui,sans-serif;--font-mono:'Geist','Segoe UI',system-ui,sans-serif;--font-display:'Geist','Segoe UI',system-ui,sans-serif;}}
*{{font-family:var(--font-ui)!important}}
html,body,[data-testid="stAppViewContainer"]{{background-color:var(--bg)!important;color:var(--text)!important}}
[data-testid="stAppViewContainer"]>.main,[data-testid="stHeader"]{{background-color:var(--bg)!important}}
section[data-testid="stSidebar"]{{display:none!important}}
[data-testid="collapsedControl"]{{display:none!important}}
/* Hide the Streamlit deploy toolbar — it disappears in production automatically */
[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"]{{display:none!important}}
header[data-testid="stHeader"]{{display:none!important}}

/* ── TOPBAR */
.topbar{{display:flex;align-items:center;justify-content:space-between;padding:12px 0 20px;border-bottom:1px solid var(--border);margin-bottom:24px;gap:12px}}
.topbar-left{{display:flex;align-items:center;gap:16px;flex:1;min-width:0}}
.logo-badge{{background:var(--accent);color:#000;font-family:var(--font-ui)!important;font-size:9px;padding:2px 7px;border-radius:3px;text-transform:uppercase;font-weight:700;letter-spacing:.08em;flex-shrink:0}}
.run-status{{display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-size:11px;color:var(--muted)}}
.pulse{{width:7px;height:7px;border-radius:50%;background:var(--accent);display:inline-block;flex-shrink:0;animation:pulse 2s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.4;transform:scale(.8)}}}}
.topbar-right{{display:flex;align-items:center;gap:8px;flex-shrink:0}}

/* ── TOP ACTION BUTTONS (Export + Theme) */
.top-btn{{
  display:inline-flex;align-items:center;gap:6px;
  font-size:11px;font-weight:500;
  padding:6px 14px;border-radius:6px;cursor:pointer;
  border:1px solid var(--border);
  background:var(--surface);color:var(--muted);
  transition:background .15s,color .15s,border-color .15s;
  white-space:nowrap;text-decoration:none;
}}
.top-btn:hover{{background:var(--surface2);color:var(--text);border-color:var(--muted)}}
.top-btn.export{{border-color:var(--border);color:var(--muted)}}

/* ── PAGE TITLE */
.page-title{{font-family:var(--font-display)!important;font-size:30px;letter-spacing:-.5px;line-height:1.1}}
.page-title em{{color:var(--accent);font-style:italic}}
.page-subtitle{{font-size:11px;color:var(--muted);margin-top:6px}}

/* ── STAT CARDS */
.stat-card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:18px 20px;position:relative;overflow:hidden;box-shadow:var(--card-shadow)}}
.stat-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px}}
.stat-card.green::before{{background:var(--accent)}}.stat-card.blue::before{{background:var(--accent2)}}
.stat-card.yellow::before{{background:var(--accent3)}}.stat-card.red::before{{background:var(--danger)}}.stat-card.grey::before{{background:var(--muted)}}
.stat-label{{font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}}
.stat-value{{font-family:var(--font-display)!important;font-size:28px;letter-spacing:-1px;line-height:1}}
.stat-value.pos{{color:var(--accent)}}.stat-value.neg{{color:var(--danger)}}.stat-value.blue{{color:var(--accent2)}}
.stat-delta{{font-size:10px;color:var(--muted);margin-top:6px}}.stat-delta span{{color:var(--accent)}}

/* ── DASH CARDS */
.dash-card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden;box-shadow:var(--card-shadow)}}
.card-header{{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;border-bottom:1px solid var(--border)}}
.card-title{{font-size:13px;font-weight:700;letter-spacing:.02em;display:flex;align-items:center;gap:8px}}
.dot{{width:6px;height:6px;border-radius:50%;display:inline-block}}.card-body{{padding:18px 20px}}

/* ── TRADE TABLE */
.trade-table{{width:100%;border-collapse:collapse}}
.trade-table thead th{{font-size:9px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);text-align:left;padding:0 12px 10px;border-bottom:1px solid var(--border)}}
.trade-table thead th:first-child{{padding-left:4px}}
.trade-table thead th.num{{text-align:right}}
.trade-table tbody tr{{border-bottom:1px solid var(--border)}}.trade-table tbody tr:last-child{{border-bottom:none}}
.trade-table tbody td{{padding:10px 12px;font-size:11px;color:var(--text)}}
.trade-table tbody td:first-child{{padding-left:4px}}
.trade-table tbody td.num{{text-align:right}}
.tag{{display:inline-block;font-size:9px;font-weight:700;padding:2px 7px;border-radius:3px;text-transform:uppercase;letter-spacing:.05em}}
.tag-long{{background:rgba(0,229,160,.15);color:var(--accent)}}.tag-short{{background:rgba(255,79,106,.15);color:var(--danger)}}
.pos-val{{color:var(--accent)}}.neg-val{{color:var(--danger)}}
.error-box{{background:rgba(220,38,38,.1);border:1px solid rgba(220,38,38,.3);border-radius:8px;padding:16px;color:var(--danger);font-size:12px;white-space:pre-wrap}}

/* ── STREAMLIT INPUT OVERRIDES */
[data-testid="stSlider"]>div>div>div{{background:var(--accent)!important}}[data-testid="stSlider"]>div>div{{background:var(--surface2)!important}}
.stSelectbox>div>div,.stTextInput>div>div>input,.stNumberInput>div>div>input{{background:var(--surface2)!important;border:1px solid var(--border)!important;color:var(--input-text)!important}}
[data-testid="stDateInput"] input,[data-testid="stDateInput"]>div,[data-testid="stDateInput"]>div>div,.stDateInput>div,.stDateInput>div>div,.stDateInput>div>div>div,[data-baseweb="input"],[data-baseweb="base-input"]{{background:var(--surface2)!important;color:var(--input-text)!important;border-color:var(--border)!important}}
[data-testid="stNumberInputContainer"],[data-testid="stNumberInputContainer"]>div,[data-testid="stNumberInputContainer"] input{{background:var(--surface2)!important;color:var(--input-text)!important;border-color:var(--border)!important}}
[data-testid="stNumberInputContainer"] button{{background:var(--surface2)!important;color:var(--muted)!important;border-color:var(--border)!important}}
[data-testid="stSelectbox"]>div>div,[data-testid="stSelectbox"] [data-baseweb="select"]>div{{background:var(--surface2)!important;color:var(--input-text)!important;border-color:var(--border)!important}}
[data-baseweb="popover"] ul,[data-baseweb="menu"]{{background:var(--surface)!important;border:1px solid var(--border)!important}}
[data-baseweb="popover"] li,[data-baseweb="menu"] li{{background:var(--surface)!important;color:var(--text)!important}}
[data-baseweb="popover"] li:hover,[data-baseweb="menu"] li:hover{{background:var(--surface2)!important}}
[data-baseweb="calendar"]{{background:var(--surface)!important;color:var(--text)!important}}
[data-baseweb="calendar"] button{{background:transparent!important;color:var(--text)!important}}
[data-baseweb="calendar"] button:hover{{background:var(--surface2)!important}}
label[data-testid="stWidgetLabel"] p{{font-size:9px!important;text-transform:uppercase!important;color:var(--muted)!important;letter-spacing:.08em!important}}

/* ── RUN BUTTON */
.stButton>button{{
  width:100%!important;
  background:var(--accent)!important;
  border:none!important;
  border-radius:7px!important;
  font-size:12px!important;
  font-weight:700!important;
  color:#000!important;
  text-transform:uppercase!important;
  letter-spacing:.08em!important;
  padding:10px 20px!important;
  transition:opacity .12s,transform .1s,box-shadow .12s!important;
  box-shadow:0 2px 8px rgba(0,0,0,0.10)!important;
}}
.stButton>button:hover{{opacity:.88!important;box-shadow:0 4px 16px rgba(0,0,0,0.15)!important}}
.stButton>button:active{{opacity:1!important;transform:scale(0.97) translateY(1px)!important;box-shadow:0 1px 3px rgba(0,0,0,0.10)!important}}

/* ── LAYOUT */
.block-container{{padding:1.5rem 2rem 2rem!important;max-width:100%!important}}.stMarkdown p{{margin:0}}
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
_last_result = st.session_state.get("last_result")
if _last_result is not None:
    def _pill(label, value):
        s = f"<span style='display:inline-flex;align-items:center;gap:4px;background:var(--surface2);border:1px solid var(--border);border-radius:4px;padding:1px 7px;white-space:nowrap'>"
        s += f"<span style='color:var(--muted);font-size:9px;text-transform:uppercase;letter-spacing:.07em'>{label}</span>"
        s += f"&thinsp;<span style='color:var(--text);font-size:11px;font-weight:600'>{value}</span></span>"
        return s
    _p = meta.get("params", {})
    _pills = [
        _pill("Strategy", meta.get("strategy", "—")),
        _pill("Asset", meta.get("asset", "—")),
        _pill("Period", str(meta.get("start_date",""))[:10] + " → " + str(meta.get("end_date",""))[:10]),
        _pill("Capital", "${:,.0f}".format(meta.get("capital", 0))),
    ]
    for k, v in _p.items():
        _label = k.replace("_", " ").title()
        _pills.append(_pill(_label, ("{:g}".format(v)) if isinstance(v, float) else str(v)))
    status_text = " ".join(_pills)
else:
    status_text = "No backtest run yet — configure below and click Run"
theme_label = "☀ Light" if dark else "🌙 Dark"

# Topbar: status on the left, Export + theme toggle on the right
top_left, top_right = st.columns([7, 3])

with top_left:
    st.markdown(
        f"""<div class="topbar">
          <div class="topbar-left">
            <span class="logo-badge">ALPHA</span>
            <div class="run-status"><span class="pulse"></span>{status_text}</div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

with top_right:
    btn_col1, btn_col2 = st.columns([1, 1])
    with btn_col1:
        # Dummy Export button — functionality to be wired up when backend is ready
        st.markdown(
            """<div style="display:flex;justify-content:flex-end;padding-top:12px">
              <button class="top-btn export" disabled title="Export (coming soon)">
                ↓ Export
              </button>
            </div>""",
            unsafe_allow_html=True,
        )
    with btn_col2:
        st.markdown("<div style='padding-top:6px'>", unsafe_allow_html=True)
        if st.button(theme_label, key="theme_toggle"):
            st.session_state["dark_mode"] = not dark
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

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
if st.button("▶  RUN BACKTEST"):
    with st.spinner("Running backtest on backend…"):
        result, err = call_backend(
            strategy, asset, sd, ed, capital, tuple(sorted(params.items()))
        )
    if err:
        st.markdown(f'<div class="error-box">{err}</div>', unsafe_allow_html=True)
    elif result:
        st.session_state["last_result"] = result
        backend_meta = result.get("meta", {})
        st.session_state["last_meta"] = {
            "strategy": backend_meta.get("strategy", strategy),
            "asset": backend_meta.get("asset", asset),
            "start_date": backend_meta.get("start_date", str(sd)),
            "end_date": backend_meta.get("end_date", str(ed)),
            "capital": capital,
            "params": dict(params),
        }
        st.rerun()

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
        font=dict(family="Geist, Segoe UI, sans-serif", color=tick_color, size=9),
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
        "<div style='height:240px;display:flex;align-items:center;justify-content:center;color:var(--muted);font-family:'Geist','Segoe UI',sans-serif;font-size:12px'>Run a backtest to see the equity curve</div>",
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
            rows += f"<tr><td>{t['entryDate']}</td><td>{tag}</td><td class='num'>${t['entryPrice']:,.2f}</td><td class='num'>${t['exitPrice']:,.2f}</td><td class='num {pc}'>{rs}</td><td class='num'>{t.get('days','—')}d</td></tr>"
        st.markdown(
            f"""<div class="card-body"><table class="trade-table"><thead><tr><th>Entry</th><th>Side</th><th class="num">Entry $</th><th class="num">Exit $</th><th class="num">Return</th><th class="num">Hold</th></tr></thead><tbody>{rows}</tbody></table></div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='card-body' style='color:var(--muted);font-family:'Geist','Segoe UI',sans-serif;font-size:12px'>No trade data yet</div>",
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
                f"<td style='padding:9px 12px 9px 4px;font-family:'Geist','Segoe UI',sans-serif;font-size:10px;color:var(--muted)'>{label}</td>"
                f"<td style='padding:9px 4px 9px 12px;font-family:'Geist','Segoe UI',sans-serif;font-size:11px;text-align:right;{color}'>{formatted}</td>"
                f"</tr>"
            )
        st.markdown(
            f"""<div class="card-body"><table style="width:100%;border-collapse:collapse"><tbody>{trows}</tbody></table></div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='card-body' style='color:var(--muted);font-family:'Geist','Segoe UI',sans-serif;font-size:12px'>Run a backtest to see metrics</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)