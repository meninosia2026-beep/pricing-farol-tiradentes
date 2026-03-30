"""
Farol de Feriados — Dashboard de acompanhamento de demanda e preço
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests, json
from datetime import datetime

# ── CONFIG ─────────────────────────────────────────────────────────────────────
GITHUB_RAW = "https://raw.githubusercontent.com/meninosia2026-beep/pricing-farol-tiradentes/main"
CONFIG_URL = f"{GITHUB_RAW}/data/config.json"

st.set_page_config(
    page_title="Farol · Feriados",
    page_icon="🔦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── DESIGN ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;700&display=swap');

*, html, body { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: #080b12;
    color: #cdd5e0;
}

section[data-testid="stSidebar"] {
    background: #0c1018 !important;
    border-right: 1px solid #151c28;
    padding-top: 8px;
}
section[data-testid="stSidebar"] * { font-size: 13px; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stMultiSelect label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stTextInput label {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #3d4f6b !important;
}

.page-header {
    display: flex;
    align-items: baseline;
    gap: 14px;
    padding: 4px 0 20px 0;
    border-bottom: 1px solid #151c28;
    margin-bottom: 24px;
}
.page-title {
    font-family: 'DM Mono', monospace;
    font-size: 22px;
    font-weight: 500;
    color: #e8eef6;
    letter-spacing: -0.03em;
    margin: 0;
}
.page-subtitle {
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    color: #2e4060;
    letter-spacing: 0.04em;
}

.kpi-row { display: flex; gap: 12px; margin-bottom: 28px; }
.kpi {
    flex: 1;
    background: #0c1018;
    border: 1px solid #151c28;
    border-radius: 10px;
    padding: 18px 20px 14px;
    position: relative;
    overflow: hidden;
}
.kpi::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: #1e3a5f;
}
.kpi.up::before   { background: linear-gradient(90deg,#00d9a3,#0066ff); }
.kpi.down::before { background: linear-gradient(90deg,#ff4560,#ff8c42); }
.kpi.warn::before { background: linear-gradient(90deg,#f5a623,#ffd700); }
.kpi.neu::before  { background: linear-gradient(90deg,#2e4060,#3d5a80); }
.kpi-label {
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #2e4060;
    margin-bottom: 8px;
}
.kpi-value {
    font-family: 'DM Mono', monospace;
    font-size: 30px;
    font-weight: 500;
    line-height: 1;
    color: #e8eef6;
    margin-bottom: 4px;
}
.kpi.up   .kpi-value { color: #00d9a3; }
.kpi.down .kpi-value { color: #ff4560; }
.kpi.warn .kpi-value { color: #f5a623; }
.kpi-sub { font-size: 11px; color: #2e4060; }

.section-label {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #2e4060;
    margin-bottom: 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid #151c28;
}

.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    gap: 4px;
    border-bottom: 1px solid #151c28;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.06em;
    color: #2e4060;
    background: transparent;
    border-radius: 6px 6px 0 0;
    padding: 8px 16px;
    border: none;
}
.stTabs [aria-selected="true"] {
    color: #e8eef6 !important;
    background: #0c1018 !important;
    border-bottom: 2px solid #0066ff !important;
}

.chart-wrap {
    background: #0c1018;
    border: 1px solid #151c28;
    border-radius: 10px;
    padding: 8px;
    margin-bottom: 16px;
}

hr { border-color: #151c28 !important; }

.stDownloadButton button {
    background: #0c1018;
    border: 1px solid #1e3a5f;
    color: #4a90d9;
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    border-radius: 6px;
}
</style>
""", unsafe_allow_html=True)


# ── FUNÇÕES ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_config():
    try:
        r = requests.get(CONFIG_URL, timeout=10)
        if r.status_code != 200:
            return {"feriados": [], "_erro": f"HTTP {r.status_code}"}
        text = r.text.strip()
        if not text:
            return {"feriados": [], "_erro": "config.json vazio"}
        return json.loads(text)
    except json.JSONDecodeError as e:
        return {"feriados": [], "_erro": f"JSON inválido: {e}"}
    except Exception as e:
        return {"feriados": [], "_erro": str(e)}

@st.cache_data(ttl=120)
def load_csv(url: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(url)
        num_cols = [
            "antecedencia","dia_da_semana","occ_atual","lf_atual","lf_proj_2026",
            "ratio_vs_proj","rpk_proj_2026","ask_proj_2026","rpk","ask",
            "price_cc","preco_praticado","preco_base","mult_final","mult_flutuacao",
            "pax","vagas_restantes","capacidade_atual",
        ]
        for c in num_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        if "data" in df.columns:
            df["data"] = pd.to_datetime(df["data"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar CSV: {e}")
        return pd.DataFrame()

def fmt_pct(v):  return f"{v:.1%}"       if pd.notna(v) else "–"
def fmt_brl(v):  return f"R$ {v:,.0f}"   if pd.notna(v) else "–"
def fmt_x(v):    return f"{v:.2f}×"      if pd.notna(v) else "–"
def kpi_cls(v, hi=1.05, lo=0.95):
    if pd.isna(v): return "neu"
    return "up" if v >= hi else ("down" if v < lo else "warn")

# ── PALETA / PLOT ────────────────────────────────────────────────────────────────
CARD_BG = "#0c1018"
GRID    = "#151c28"
BLUE    = "#0066ff"
TEAL    = "#00d9a3"
RED     = "#ff4560"
AMBER   = "#f5a623"
GRAY    = "#2e4060"
MONO    = "DM Mono"
PFONT   = dict(family=MONO, color="#4a6080", size=11)

def base_fig(h=380):
    return dict(
        paper_bgcolor=CARD_BG, plot_bgcolor=CARD_BG,
        font=PFONT, height=h,
        margin=dict(l=52, r=24, t=36, b=44),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, tickfont=PFONT, linecolor=GRID),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, tickfont=PFONT, linecolor=GRID),
        legend=dict(
            bgcolor=CARD_BG, bordercolor=GRID, borderwidth=1,
            font=dict(family=MONO, size=11, color="#6b8cae"),
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
        ),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#0c1828", font=dict(family=MONO, size=12)),
    )


# ── SIDEBAR ─────────────────────────────────────────────────────────────────────
config   = load_config()
feriados = config.get("feriados", [])
_err     = config.get("_erro")

with st.sidebar:
    st.markdown("**FAROL · FERIADOS**")
    st.divider()

    if _err:
        st.caption(f"⚠ {_err}")

    usar_manual = st.toggle("URL manual", value=(not feriados))

    if usar_manual or not feriados:
        csv_url = st.text_input(
            "URL raw do CSV",
            placeholder=f"{GITHUB_RAW}/data/feriado_tiradentes_2026.csv",
        ).strip()
        feriado_cfg  = {
            "nome":  st.text_input("Nome", "Feriado"),
            "key":   "manual",
            "dt_ini": "",
            "dt_fim": "",
        }
        feriado_nome = feriado_cfg["nome"]
        if not csv_url:
            st.info("Cole a URL do CSV para carregar.")
            st.stop()
    else:
        opts         = {f["nome"]: f for f in feriados}
        feriado_nome = st.selectbox("Feriado", list(opts.keys()))
        feriado_cfg  = opts[feriado_nome]
        if "atualizado" in feriado_cfg:
            st.caption(f"atualizado {feriado_cfg['atualizado']}")
        csv_url = f"{GITHUB_RAW}/{feriado_cfg['arquivo']}"

    st.divider()
    df_raw = load_csv(csv_url)
    if df_raw.empty:
        st.error("Sem dados.")
        st.stop()

    st.markdown("**FILTROS**")

    datas_disp  = sorted(df_raw["data"].dt.date.unique())       if "data"           in df_raw.columns else []
    datas_sel   = st.multiselect("Data",  datas_disp,  default=datas_disp,  format_func=lambda d: d.strftime("%d/%m"))
    turnos_disp = sorted(df_raw["turno"].dropna().unique())     if "turno"          in df_raw.columns else []
    turnos_sel  = st.multiselect("Turno", turnos_disp, default=turnos_disp)
    rotas_disp  = sorted(df_raw["rota_principal"].dropna().unique()) if "rota_principal" in df_raw.columns else []
    rotas_sel   = st.multiselect("Rota",  rotas_disp,  default=rotas_disp[:12] if len(rotas_disp) > 12 else rotas_disp)
    ant_min = int(df_raw["antecedencia"].min()) if "antecedencia" in df_raw.columns else 0
    ant_max = int(df_raw["antecedencia"].max()) if "antecedencia" in df_raw.columns else 80
    ant_sel = st.slider("Antecedência (dias)", ant_min, ant_max, (ant_min, ant_max))

    st.divider()
    if st.button("↺  Recarregar"):
        st.cache_data.clear()
        st.rerun()


# ── FILTROS ──────────────────────────────────────────────────────────────────────
df = df_raw.copy()
if datas_sel  and "data"           in df.columns: df = df[df["data"].dt.date.isin(datas_sel)]
if turnos_sel and "turno"          in df.columns: df = df[df["turno"].isin(turnos_sel)]
if rotas_sel  and "rota_principal" in df.columns: df = df[df["rota_principal"].isin(rotas_sel)]
if "antecedencia" in df.columns:                  df = df[df["antecedencia"].between(*ant_sel)]


# ── HEADER ────────────────────────────────────────────────────────────────────────
periodo_str = f"{feriado_cfg.get('dt_ini','')}  →  {feriado_cfg.get('dt_fim','')}"
st.markdown(f"""
<div class="page-header">
  <span class="page-title">🔦 {feriado_nome}</span>
  <span class="page-subtitle">{periodo_str}</span>
</div>
""", unsafe_allow_html=True)


# ── KPIs ─────────────────────────────────────────────────────────────────────────
ratio_med = df["ratio_vs_proj"].mean()    if "ratio_vs_proj"   in df.columns else None
occ_med   = df["occ_atual"].mean()        if "occ_atual"        in df.columns else None
preco_med = df["preco_praticado"].mean()  if "preco_praticado"  in df.columns else None
cc_med    = df["price_cc"].mean()         if "price_cc"         in df.columns else None
n_rotas   = df["rota_principal"].nunique() if "rota_principal"  in df.columns else 0
delta_p   = ((preco_med / cc_med) - 1)   if preco_med and cc_med else None

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="kpi {kpi_cls(ratio_med)}">
      <div class="kpi-label">LF atual / projetado</div>
      <div class="kpi-value">{fmt_x(ratio_med)}</div>
      <div class="kpi-sub">ratio médio filtrado</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="kpi {kpi_cls(occ_med, hi=0.70, lo=0.50)}">
      <div class="kpi-label">Ocupação média</div>
      <div class="kpi-value">{fmt_pct(occ_med)}</div>
      <div class="kpi-sub">pax / capacidade</div>
    </div>""", unsafe_allow_html=True)
with c3:
    sub_p = f"{delta_p:+.1%} vs CC" if delta_p is not None else "sem dados CC"
    cls_p = "up" if delta_p and delta_p > 0 else ("down" if delta_p and delta_p < -0.05 else "warn")
    st.markdown(f"""<div class="kpi {cls_p}">
      <div class="kpi-label">Preço praticado</div>
      <div class="kpi-value">{fmt_brl(preco_med)}</div>
      <div class="kpi-sub">{sub_p}</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="kpi neu">
      <div class="kpi-label">Rotas ativas</div>
      <div class="kpi-value">{n_rotas}</div>
      <div class="kpi-sub">{len(df):,} registros</div>
    </div>""", unsafe_allow_html=True)


# ── TABS ──────────────────────────────────────────────────────────────────────────
tab_lf, tab_preco, tab_rotas, tab_tabela = st.tabs([
    "  Load Factor  ",
    "  Preço  ",
    "  Rotas  ",
    "  Tabela  ",
])


# ══ TAB 1 · LOAD FACTOR ══════════════════════════════════════════════════════════
with tab_lf:
    if "antecedencia" not in df.columns:
        st.info("Coluna antecedencia não encontrada.")
    else:
        grp = (
            df.groupby("antecedencia", as_index=False)
            .agg(
                lf_atual      = ("lf_atual",      "mean"),
                lf_proj_2026  = ("lf_proj_2026",  "mean"),
                ratio_vs_proj = ("ratio_vs_proj", "mean"),
            )
            .sort_values("antecedencia", ascending=False)
        )

        st.markdown('<div class="section-label">LF Atual × Projetado por antecedência</div>', unsafe_allow_html=True)

        fig = go.Figure()

        # Área de gap
        if {"lf_proj_2026","lf_atual"}.issubset(grp.columns):
            fig.add_trace(go.Scatter(
                x=pd.concat([grp["antecedencia"], grp["antecedencia"][::-1]]),
                y=pd.concat([
                    grp[["lf_atual","lf_proj_2026"]].max(axis=1),
                    grp[["lf_atual","lf_proj_2026"]].min(axis=1)[::-1],
                ]),
                fill="toself", fillcolor="rgba(0,217,163,0.06)",
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False, hoverinfo="skip",
            ))

        # LF projetado
        if "lf_proj_2026" in grp.columns:
            fig.add_trace(go.Scatter(
                x=grp["antecedencia"], y=grp["lf_proj_2026"],
                name="LF Projetado",
                mode="lines",
                line=dict(color=GRAY, width=1.5, dash="dash"),
                hovertemplate="Proj: %{y:.1%}<extra></extra>",
            ))

        # LF atual — pontos coloridos por status
        if "lf_atual" in grp.columns:
            ref = grp["lf_proj_2026"] if "lf_proj_2026" in grp.columns else grp["lf_atual"]
            pt_colors = [TEAL if (pd.notna(a) and pd.notna(p) and a >= p) else RED
                         for a, p in zip(grp["lf_atual"], ref)]
            fig.add_trace(go.Scatter(
                x=grp["antecedencia"], y=grp["lf_atual"],
                name="LF Atual",
                mode="lines+markers",
                line=dict(color=TEAL, width=2.5),
                marker=dict(size=7, color=pt_colors, line=dict(width=0)),
                hovertemplate="Atual: %{y:.1%}<extra></extra>",
            ))

        l = base_fig(420)
        l["xaxis"].update(title="dias de antecedência", autorange="reversed")
        l["yaxis"].update(title="Load Factor", tickformat=".0%")
        l["title"] = dict(text="LF Atual  ×  Projetado", font=dict(family=MONO, size=13, color="#6b8cae"), x=0)
        fig.update_layout(**l)
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Barras de desvio
        if "ratio_vs_proj" in grp.columns:
            st.markdown('<div class="section-label">Desvio ratio (atual ÷ projetado − 1)</div>', unsafe_allow_html=True)
            delta_vals = grp["ratio_vs_proj"] - 1
            bar_colors = [TEAL if v >= 0.05 else RED if v < -0.05 else AMBER for v in delta_vals]

            fig2 = go.Figure(go.Bar(
                x=grp["antecedencia"], y=delta_vals,
                marker=dict(color=bar_colors, opacity=0.85),
                hovertemplate="d=%{x}  Δ=%{y:+.1%}<extra></extra>",
            ))
            fig2.add_hline(y=0, line_color=GRAY, line_width=1)
            fig2.add_hrect(y0=-0.05, y1=0.05, fillcolor="rgba(255,255,255,0.015)", line_width=0)
            l2 = base_fig(230)
            l2["xaxis"].update(autorange="reversed")
            l2["yaxis"].update(tickformat="+.0%", title="")
            l2["showlegend"] = False
            l2["bargap"] = 0.25
            fig2.update_layout(**l2)
            st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
            st.plotly_chart(fig2, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)


# ══ TAB 2 · PREÇO ════════════════════════════════════════════════════════════════
with tab_preco:
    has_prat = "preco_praticado" in df.columns
    has_base = "preco_base"      in df.columns
    has_cc   = "price_cc"        in df.columns

    if not has_prat:
        st.info("Coluna preco_praticado não encontrada.")
    else:
        agg_dict = {k: (k, "mean") for k in ["preco_praticado","preco_base","price_cc"] if k in df.columns}
        grp_p = (
            df.groupby("antecedencia", as_index=False)
            .agg(**agg_dict)
            .sort_values("antecedencia", ascending=False)
        )

        st.markdown('<div class="section-label">Preço Praticado × Base × Concorrência</div>', unsafe_allow_html=True)

        fig3 = go.Figure()

        # Área gap praticado vs CC
        if has_cc:
            fig3.add_trace(go.Scatter(
                x=pd.concat([grp_p["antecedencia"], grp_p["antecedencia"][::-1]]),
                y=pd.concat([grp_p["preco_praticado"], grp_p["price_cc"][::-1]]),
                fill="toself", fillcolor="rgba(0,102,255,0.06)",
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False, hoverinfo="skip",
            ))
            fig3.add_trace(go.Scatter(
                x=grp_p["antecedencia"], y=grp_p["price_cc"],
                name="Concorrência",
                mode="lines",
                line=dict(color=RED, width=1.5, dash="dot"),
                hovertemplate="CC: R$%{y:,.0f}<extra></extra>",
            ))

        # Preço base
        if has_base:
            fig3.add_trace(go.Scatter(
                x=grp_p["antecedencia"], y=grp_p["preco_base"],
                name="Preço Base",
                mode="lines",
                line=dict(color=GRAY, width=1.5, dash="dash"),
                hovertemplate="Base: R$%{y:,.0f}<extra></extra>",
            ))

        # Preço praticado
        fig3.add_trace(go.Scatter(
            x=grp_p["antecedencia"], y=grp_p["preco_praticado"],
            name="Praticado",
            mode="lines+markers",
            line=dict(color=BLUE, width=2.5),
            marker=dict(size=7, color=BLUE, line=dict(width=0)),
            hovertemplate="Praticado: R$%{y:,.0f}<extra></extra>",
        ))

        l3 = base_fig(420)
        l3["xaxis"].update(title="dias de antecedência", autorange="reversed")
        l3["yaxis"].update(title="R$", tickprefix="R$ ", tickformat=",.0f")
        l3["title"] = dict(text="Preço Praticado  ×  Base  ×  Concorrência", font=dict(family=MONO, size=13, color="#6b8cae"), x=0)
        fig3.update_layout(**l3)
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Gap % praticado vs CC
        if has_cc:
            st.markdown('<div class="section-label">Gap praticado vs concorrência (%)</div>', unsafe_allow_html=True)
            grp_p["gap_cc"] = grp_p["preco_praticado"] / grp_p["price_cc"] - 1
            gap_colors = [BLUE if v >= 0 else AMBER for v in grp_p["gap_cc"].fillna(0)]

            fig4 = go.Figure(go.Bar(
                x=grp_p["antecedencia"], y=grp_p["gap_cc"],
                marker=dict(color=gap_colors, opacity=0.80),
                hovertemplate="d=%{x}  gap=%{y:+.1%}<extra></extra>",
            ))
            fig4.add_hline(y=0, line_color=GRAY, line_width=1)
            l4 = base_fig(230)
            l4["xaxis"].update(autorange="reversed")
            l4["yaxis"].update(tickformat="+.0%", title="")
            l4["showlegend"] = False
            l4["bargap"] = 0.25
            fig4.update_layout(**l4)
            st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
            st.plotly_chart(fig4, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)


# ══ TAB 3 · ROTAS ════════════════════════════════════════════════════════════════
with tab_rotas:
    if "rota_principal" not in df.columns:
        st.info("Coluna rota_principal não encontrada.")
    else:
        ants_disp = sorted(df["antecedencia"].dropna().unique().astype(int))
        col_ref   = st.select_slider("Antecedência de referência", options=ants_disp, value=ants_disp[0])
        df_ref    = df[df["antecedencia"] == col_ref]
        nome_col  = "sentido" if "sentido" in df_ref.columns else "rota_principal"

        grp_r = (
            df_ref.groupby(nome_col, as_index=False)
            .agg(
                ratio_vs_proj   = ("ratio_vs_proj",   "mean"),
                lf_atual        = ("lf_atual",         "mean"),
                lf_proj_2026    = ("lf_proj_2026",     "mean"),
                occ_atual       = ("occ_atual",         "mean"),
                preco_praticado = ("preco_praticado",  "mean"),
            )
            .sort_values("ratio_vs_proj", ascending=True)
        )

        r_colors = [TEAL if v >= 1.05 else RED if v < 0.95 else AMBER for v in grp_r["ratio_vs_proj"]]

        st.markdown(f'<div class="section-label">Ratio LF por sentido — d = {col_ref}</div>', unsafe_allow_html=True)

        fig5 = go.Figure(go.Bar(
            x=grp_r["ratio_vs_proj"],
            y=grp_r[nome_col],
            orientation="h",
            marker=dict(color=r_colors, opacity=0.85),
            text=[f"{v:.2f}×" for v in grp_r["ratio_vs_proj"]],
            textfont=dict(family=MONO, size=11),
            textposition="outside",
            hovertemplate="%{y}  %{x:.3f}×<extra></extra>",
        ))
        fig5.add_vline(x=1, line_color=GRAY, line_width=1.5, line_dash="dot")
        l5 = base_fig(max(420, len(grp_r) * 22))
        l5["xaxis"].update(title="ratio (1.0 = no target)", tickformat=".2f")
        l5["yaxis"].update(title="", tickfont=dict(family=MONO, size=11))
        l5["showlegend"] = False
        l5["bargap"] = 0.30
        fig5.update_layout(**l5)
        st.markdown('<div class="chart-wrap">', unsafe_allow_html=True)
        st.plotly_chart(fig5, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-label">Detalhe por sentido</div>', unsafe_allow_html=True)
        tbl = grp_r.copy()
        for c, fn in [("ratio_vs_proj",fmt_x),("lf_atual",fmt_pct),("lf_proj_2026",fmt_pct),
                      ("occ_atual",fmt_pct),("preco_praticado",fmt_brl)]:
            if c in tbl.columns: tbl[c] = tbl[c].map(fn)
        st.dataframe(tbl.sort_values(nome_col), use_container_width=True, hide_index=True)


# ══ TAB 4 · TABELA ═══════════════════════════════════════════════════════════════
with tab_tabela:
    COLS = [c for c in [
        "data","rota_principal","sentido","turno","antecedencia","dia_da_semana",
        "occ_atual","lf_atual","lf_proj_2026","ratio_vs_proj",
        "preco_base","preco_praticado","price_cc",
        "mult_final","mult_flutuacao",
        "pax","vagas_restantes","capacidade_atual",
    ] if c in df.columns]

    df_show = df[COLS].copy()
    if "data" in df_show.columns:
        df_show["data"] = df_show["data"].dt.strftime("%d/%m")
    for c in ["occ_atual","lf_atual","lf_proj_2026","ratio_vs_proj"]:
        if c in df_show.columns:
            df_show[c] = df_show[c].map(lambda v: f"{v:.3f}" if pd.notna(v) else "–")
    for c in ["preco_base","preco_praticado","price_cc"]:
        if c in df_show.columns:
            df_show[c] = df_show[c].map(lambda v: f"R${v:,.0f}" if pd.notna(v) else "–")

    busca = st.text_input("🔎 Buscar rota / sentido", "")
    if busca:
        mask = df_show.astype(str).apply(lambda r: r.str.contains(busca, case=False)).any(axis=1)
        df_show = df_show[mask]

    st.dataframe(df_show, use_container_width=True, height=520, hide_index=True)
    st.download_button(
        "⬇  Exportar CSV filtrado",
        df[COLS].to_csv(index=False).encode("utf-8"),
        file_name=f"farol_{feriado_cfg.get('key','feriado')}.csv",
        mime="text/csv",
    )
