"""
Dashboard de Acompanhamento de Feriados — Streamlit
Lê CSVs do GitHub (gerados pelo Databricks) e exibe curvas de demanda.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import requests
import json
from datetime import datetime

# ── CONFIGURAÇÃO ──────────────────────────────────────────────────────────────
GITHUB_RAW  = "https://raw.githubusercontent.com/seu-org/seu-repo/main"
CONFIG_URL  = f"{GITHUB_RAW}/data/config.json"

st.set_page_config(
    page_title="Curva de Feriados",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── ESTILO ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

.stApp { background: #0d0f14; color: #e8eaf0; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #13161e;
    border-right: 1px solid #1e2230;
}

/* Cards de métrica */
.metric-card {
    background: #13161e;
    border: 1px solid #1e2230;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.metric-label {
    font-size: 11px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #6b7280;
    font-family: 'IBM Plex Mono', monospace;
    margin-bottom: 4px;
}
.metric-value {
    font-size: 28px;
    font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;
    color: #e8eaf0;
}
.metric-value.green  { color: #34d399; }
.metric-value.red    { color: #f87171; }
.metric-value.yellow { color: #fbbf24; }

/* Badges */
.badge {
    display: inline-block;
    font-size: 10px;
    font-family: 'IBM Plex Mono', monospace;
    letter-spacing: 0.08em;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 600;
}
.badge-green  { background: #064e3b; color: #34d399; }
.badge-red    { background: #450a0a; color: #f87171; }
.badge-yellow { background: #451a03; color: #fbbf24; }
.badge-gray   { background: #1e2230; color: #9ca3af; }

/* Títulos */
h1, h2, h3 { font-family: 'IBM Plex Mono', monospace; }
h1 { font-size: 20px; font-weight: 600; color: #e8eaf0; letter-spacing: -0.02em; }
h2 { font-size: 13px; font-weight: 600; color: #6b7280; letter-spacing: 0.1em; text-transform: uppercase; }

/* Tabela */
.stDataFrame { border: 1px solid #1e2230; border-radius: 8px; }

/* Divider */
hr { border-color: #1e2230; }

/* Atualizado em */
.updated-tag {
    font-size: 11px;
    font-family: 'IBM Plex Mono', monospace;
    color: #4b5563;
}
</style>
""", unsafe_allow_html=True)


# ── FUNÇÕES DE DADOS ──────────────────────────────────────────────────────────
@st.cache_data(ttl=120)   # recarrega a cada 2 min
def load_config():
    try:
        r = requests.get(CONFIG_URL, timeout=10)
        return r.json()
    except Exception as e:
        st.error(f"Erro ao carregar config: {e}")
        return {"feriados": []}

@st.cache_data(ttl=120)
def load_csv(url: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(url)
        # Normaliza tipos
        for col in ["antecedencia", "dia_da_semana"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        for col in ["occ_atual", "lf_atual", "lf_proj_2026", "ratio_vs_proj",
                    "rpk_proj_2026", "ask_proj_2026", "rpk", "ask",
                    "price_cc", "preco_praticado", "mult_final", "mult_flutuacao"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        if "data" in df.columns:
            df["data"] = pd.to_datetime(df["data"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar CSV: {e}")
        return pd.DataFrame()

def color_ratio(val):
    if pd.isna(val): return "badge-gray", "–"
    label = f"{val:.2f}x"
    if val >= 1.1:   return "badge-green",  label
    if val >= 0.9:   return "badge-yellow", label
    return "badge-red", label

def fmt_pct(val):
    if pd.isna(val): return "–"
    return f"{val:.1%}"

def fmt_brl(val):
    if pd.isna(val): return "–"
    return f"R$ {val:,.2f}"


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
config = load_config()
feriados = config.get("feriados", [])

if not feriados:
    st.warning("Nenhum feriado publicado ainda. Rode o notebook no Databricks.")
    st.stop()

with st.sidebar:
    st.markdown("### 📅 Feriado")
    feriado_options = {f["nome"]: f for f in feriados}
    feriado_nome    = st.selectbox("Selecione", list(feriado_options.keys()), label_visibility="collapsed")
    feriado_cfg     = feriado_options[feriado_nome]

    if "atualizado" in feriado_cfg:
        st.markdown(f'<div class="updated-tag">atualizado {feriado_cfg["atualizado"]}</div>', unsafe_allow_html=True)

    st.divider()

    # Carrega dados do feriado selecionado
    csv_url = f"{GITHUB_RAW}/{feriado_cfg['arquivo']}"
    df_raw  = load_csv(csv_url)

    if df_raw.empty:
        st.error("Sem dados para este feriado.")
        st.stop()

    st.markdown("### 🔍 Filtros")

    # Datas
    datas_disp = sorted(df_raw["data"].dt.date.unique()) if "data" in df_raw.columns else []
    datas_sel  = st.multiselect("Data", datas_disp, default=datas_disp, format_func=lambda d: d.strftime("%d/%m"))

    # Turnos
    turnos_disp = sorted(df_raw["turno"].dropna().unique()) if "turno" in df_raw.columns else []
    turnos_sel  = st.multiselect("Turno", turnos_disp, default=turnos_disp)

    # Rotas
    rotas_disp = sorted(df_raw["rota_principal"].dropna().unique()) if "rota_principal" in df_raw.columns else []
    rotas_sel  = st.multiselect("Rota", rotas_disp, default=rotas_disp[:10] if len(rotas_disp) > 10 else rotas_disp)

    # Antecedência
    ant_min = int(df_raw["antecedencia"].min()) if "antecedencia" in df_raw.columns else 0
    ant_max = int(df_raw["antecedencia"].max()) if "antecedencia" in df_raw.columns else 80
    ant_sel = st.slider("Antecedência (dias)", ant_min, ant_max, (ant_min, ant_max))

    st.divider()
    if st.button("🔄 Recarregar dados"):
        st.cache_data.clear()
        st.rerun()


# ── FILTRA ────────────────────────────────────────────────────────────────────
df = df_raw.copy()
if datas_sel and "data" in df.columns:
    df = df[df["data"].dt.date.isin(datas_sel)]
if turnos_sel and "turno" in df.columns:
    df = df[df["turno"].isin(turnos_sel)]
if rotas_sel and "rota_principal" in df.columns:
    df = df[df["rota_principal"].isin(rotas_sel)]
if "antecedencia" in df.columns:
    df = df[df["antecedencia"].between(ant_sel[0], ant_sel[1])]


# ── HEADER ────────────────────────────────────────────────────────────────────
col_title, col_period = st.columns([3, 1])
with col_title:
    st.markdown(f"<h1>📈 {feriado_nome}</h1>", unsafe_allow_html=True)
with col_period:
    st.markdown(
        f'<div class="updated-tag" style="text-align:right;margin-top:8px">'
        f'{feriado_cfg.get("dt_ini","")} → {feriado_cfg.get("dt_fim","")}'
        f'</div>',
        unsafe_allow_html=True,
    )

st.divider()


# ── KPIs ──────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)

with k1:
    ratio_med = df["ratio_vs_proj"].mean() if "ratio_vs_proj" in df.columns else None
    css_cls, label = color_ratio(ratio_med)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">LF atual / Projetado</div>
        <div class="metric-value {'green' if ratio_med and ratio_med>=1.1 else 'red' if ratio_med and ratio_med<0.9 else 'yellow'}">{label}</div>
    </div>""", unsafe_allow_html=True)

with k2:
    occ_med = df["occ_atual"].mean() if "occ_atual" in df.columns else None
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Ocupação média</div>
        <div class="metric-value {'green' if occ_med and occ_med>=0.7 else 'yellow' if occ_med and occ_med>=0.5 else 'red'}">{fmt_pct(occ_med)}</div>
    </div>""", unsafe_allow_html=True)

with k3:
    preco_med = df["preco_praticado"].mean() if "preco_praticado" in df.columns else None
    cc_med    = df["price_cc"].mean() if "price_cc" in df.columns else None
    delta_pct = (preco_med / cc_med - 1) if preco_med and cc_med else None
    delta_str = f" ({delta_pct:+.1%} vs CC)" if delta_pct is not None else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Preço médio praticado</div>
        <div class="metric-value">{fmt_brl(preco_med)}</div>
        <div class="updated-tag">{f"CC: {fmt_brl(cc_med)}{delta_str}" if cc_med else "–"}</div>
    </div>""", unsafe_allow_html=True)

with k4:
    n_rotas = df["rota_principal"].nunique() if "rota_principal" in df.columns else 0
    n_rows  = len(df)
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Rotas | Linhas</div>
        <div class="metric-value">{n_rotas}</div>
        <div class="updated-tag">{n_rows:,} registros filtrados</div>
    </div>""", unsafe_allow_html=True)

st.divider()


# ── GRÁFICOS ──────────────────────────────────────────────────────────────────
PLOT_BG   = "#0d0f14"
GRID_CLR  = "#1e2230"
FONT_CLR  = "#9ca3af"
PLOT_FONT = dict(family="IBM Plex Mono", color=FONT_CLR, size=11)

def base_layout(title=""):
    return dict(
        title=dict(text=title, font=dict(family="IBM Plex Mono", size=13, color="#e8eaf0"), x=0),
        paper_bgcolor=PLOT_BG, plot_bgcolor=PLOT_BG,
        font=PLOT_FONT,
        xaxis=dict(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR, tickfont=PLOT_FONT),
        yaxis=dict(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR, tickfont=PLOT_FONT),
        margin=dict(l=48, r=16, t=40, b=40),
        legend=dict(bgcolor="#13161e", bordercolor=GRID_CLR, borderwidth=1),
        hovermode="x unified",
    )

tab_curva, tab_rota, tab_preco, tab_tabela = st.tabs([
    "📉 Curva de Antecedência",
    "🗺️ Ranking de Rotas",
    "💰 Preço vs Concorrência",
    "📋 Tabela Detalhada",
])

# ── Tab 1: Curva de Antecedência ──────────────────────────────
with tab_curva:
    if "antecedencia" not in df.columns:
        st.info("Coluna antecedencia não encontrada.")
    else:
        grp = (
            df.groupby("antecedencia", as_index=False)
            .agg(
                lf_atual      = ("lf_atual",     "mean"),
                lf_proj_2026  = ("lf_proj_2026", "mean"),
                ratio_vs_proj = ("ratio_vs_proj","mean"),
                occ_atual     = ("occ_atual",     "mean"),
            )
            .sort_values("antecedencia", ascending=False)
        )

        fig = go.Figure()
        if "lf_proj_2026" in grp.columns:
            fig.add_trace(go.Scatter(
                x=grp["antecedencia"], y=grp["lf_proj_2026"],
                name="LF Projetado", mode="lines",
                line=dict(color="#4b5563", width=2, dash="dot"),
            ))
        if "lf_atual" in grp.columns:
            fig.add_trace(go.Scatter(
                x=grp["antecedencia"], y=grp["lf_atual"],
                name="LF Atual", mode="lines+markers",
                line=dict(color="#60a5fa", width=2.5),
                marker=dict(size=5),
            ))

        # Zona de over/under
        if "lf_proj_2026" in grp.columns and "lf_atual" in grp.columns:
            fig.add_trace(go.Scatter(
                x=pd.concat([grp["antecedencia"], grp["antecedencia"][::-1]]),
                y=pd.concat([grp["lf_proj_2026"], grp["lf_atual"][::-1]]),
                fill="toself", fillcolor="rgba(96,165,250,0.08)",
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False, hoverinfo="skip",
            ))

        layout = base_layout("LF Atual vs Projetado por Antecedência")
        layout["xaxis"].update(title="Dias de antecedência", autorange="reversed")
        layout["yaxis"].update(title="Load Factor", tickformat=".0%")
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)

        # Ratio bar
        if "ratio_vs_proj" in grp.columns:
            colors = ["#34d399" if v >= 1.05 else "#f87171" if v < 0.95 else "#fbbf24"
                      for v in grp["ratio_vs_proj"]]
            fig2 = go.Figure(go.Bar(
                x=grp["antecedencia"], y=grp["ratio_vs_proj"] - 1,
                marker_color=colors, name="Delta vs Proj",
            ))
            fig2.add_hline(y=0, line_color="#4b5563", line_width=1)
            layout2 = base_layout("Desvio vs Projetado (ratio − 1)")
            layout2["xaxis"].update(title="Dias de antecedência", autorange="reversed")
            layout2["yaxis"].update(title="Desvio", tickformat="+.1%")
            fig2.update_layout(**layout2)
            st.plotly_chart(fig2, use_container_width=True)


# ── Tab 2: Ranking de Rotas ───────────────────────────────────
with tab_rota:
    if "rota_principal" not in df.columns:
        st.info("Coluna rota_principal não encontrada.")
    else:
        col_ant = st.slider("Antecedência de referência", ant_min, ant_max, ant_min, key="rota_ant")
        df_ant  = df[df["antecedencia"] == col_ant] if col_ant in df["antecedencia"].values else df

        grp_rota = (
            df_ant.groupby(["rota_principal", "sentido"], as_index=False)
            .agg(
                ratio_vs_proj = ("ratio_vs_proj","mean"),
                occ_atual     = ("occ_atual",     "mean"),
                lf_atual      = ("lf_atual",      "mean"),
                lf_proj_2026  = ("lf_proj_2026",  "mean"),
            )
            .sort_values("ratio_vs_proj", ascending=True)
        )

        colors_rota = ["#34d399" if v >= 1.05 else "#f87171" if v < 0.95 else "#fbbf24"
                       for v in grp_rota["ratio_vs_proj"]]

        fig3 = go.Figure(go.Bar(
            x=grp_rota["ratio_vs_proj"],
            y=grp_rota["sentido"].fillna(grp_rota["rota_principal"]),
            orientation="h",
            marker_color=colors_rota,
            text=[f"{v:.2f}x" for v in grp_rota["ratio_vs_proj"]],
            textposition="outside",
        ))
        fig3.add_vline(x=1, line_color="#4b5563", line_width=1.5, line_dash="dot")
        layout3 = base_layout(f"Ratio LF Atual/Proj por Sentido — d={col_ant}")
        layout3["xaxis"].update(title="ratio_vs_proj", tickformat=".2f")
        layout3["yaxis"].update(title="")
        layout3["height"] = max(400, len(grp_rota) * 24)
        fig3.update_layout(**layout3)
        st.plotly_chart(fig3, use_container_width=True)


# ── Tab 3: Preço vs Concorrência ─────────────────────────────
with tab_preco:
    if "price_cc" not in df.columns or "preco_praticado" not in df.columns:
        st.info("Colunas de preço não encontradas.")
    else:
        grp_preco = (
            df.groupby("antecedencia", as_index=False)
            .agg(
                preco_praticado = ("preco_praticado","mean"),
                price_cc        = ("price_cc",       "mean"),
            )
            .sort_values("antecedencia", ascending=False)
        )

        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=grp_preco["antecedencia"], y=grp_preco["price_cc"],
            name="Concorrência", mode="lines",
            line=dict(color="#f87171", width=2, dash="dot"),
        ))
        fig4.add_trace(go.Scatter(
            x=grp_preco["antecedencia"], y=grp_preco["preco_praticado"],
            name="Buser praticado", mode="lines+markers",
            line=dict(color="#34d399", width=2.5),
            marker=dict(size=5),
        ))
        layout4 = base_layout("Preço Praticado vs Concorrência por Antecedência")
        layout4["xaxis"].update(title="Dias de antecedência", autorange="reversed")
        layout4["yaxis"].update(title="R$", tickprefix="R$ ")
        fig4.update_layout(**layout4)
        st.plotly_chart(fig4, use_container_width=True)

        # Scatter rota: preco vs ratio
        st.markdown("<h2>Preço vs Demanda por Rota</h2>", unsafe_allow_html=True)
        df_scatter = (
            df.groupby(["rota_principal"], as_index=False)
            .agg(
                preco_praticado = ("preco_praticado","mean"),
                price_cc        = ("price_cc",       "mean"),
                ratio_vs_proj   = ("ratio_vs_proj",  "mean"),
                occ_atual       = ("occ_atual",       "mean"),
            )
        )
        df_scatter["gap_preco_pct"] = (df_scatter["preco_praticado"] / df_scatter["price_cc"] - 1) * 100

        fig5 = px.scatter(
            df_scatter.dropna(subset=["gap_preco_pct","ratio_vs_proj"]),
            x="gap_preco_pct", y="ratio_vs_proj",
            size="occ_atual", color="ratio_vs_proj",
            color_continuous_scale=["#f87171","#fbbf24","#34d399"],
            hover_name="rota_principal",
            labels={"gap_preco_pct": "Preço vs CC (%)", "ratio_vs_proj": "LF Atual/Proj"},
        )
        fig5.add_hline(y=1,  line_color="#4b5563", line_dash="dot")
        fig5.add_vline(x=0,  line_color="#4b5563", line_dash="dot")
        fig5.update_layout(**base_layout("Posicionamento de Preço vs Demanda"))
        fig5.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig5, use_container_width=True)


# ── Tab 4: Tabela ─────────────────────────────────────────────
with tab_tabela:
    COLS_SHOW = [c for c in [
        "data","rota_principal","sentido","turno","antecedencia",
        "occ_atual","lf_atual","lf_proj_2026","ratio_vs_proj",
        "preco_praticado","price_cc","mult_final","mult_flutuacao",
        "pax","vagas_restantes",
    ] if c in df.columns]

    df_show = df[COLS_SHOW].copy()

    # Formata para exibição
    for col in ["occ_atual","lf_atual","lf_proj_2026","ratio_vs_proj"]:
        if col in df_show.columns:
            df_show[col] = df_show[col].map(lambda v: f"{v:.3f}" if pd.notna(v) else "–")
    for col in ["preco_praticado","price_cc"]:
        if col in df_show.columns:
            df_show[col] = df_show[col].map(lambda v: f"R$ {v:.2f}" if pd.notna(v) else "–")
    if "data" in df_show.columns:
        df_show["data"] = df_show["data"].dt.strftime("%d/%m")

    busca = st.text_input("🔎 Filtrar rota / sentido", "")
    if busca:
        mask = df_show.apply(lambda r: r.astype(str).str.contains(busca, case=False).any(), axis=1)
        df_show = df_show[mask]

    st.dataframe(df_show, use_container_width=True, height=500)
    st.download_button(
        "⬇️ Baixar CSV filtrado",
        df[COLS_SHOW].to_csv(index=False).encode("utf-8"),
        file_name=f"feriado_{feriado_cfg['key']}_filtrado.csv",
        mime="text/csv",
    )
