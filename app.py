"""
app.py — Pricing Dashboard | Feriado Tiradentes 2026
Farol de rotas + Alertas de oportunidade de pricing

Run:
  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import date, timedelta

from db import load_base, load_alertas
from logic import enrich_farol, resumo_por_rota, fmt_pct, fmt_brl, fmt_x

# ──────────────────────────────────────────────────────────────
# Configuração da página
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Pricing · Farol Tiradentes",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# CSS customizado — dark, industrial, denso
# ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

  html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0d0f14;
    color: #e0e4ef;
  }

  /* Sidebar */
  section[data-testid="stSidebar"] {
    background: #13161f;
    border-right: 1px solid #1e2130;
  }

  /* Métricas */
  [data-testid="metric-container"] {
    background: #13161f;
    border: 1px solid #1e2130;
    border-radius: 8px;
    padding: 12px 16px;
  }
  [data-testid="metric-container"] label {
    color: #7b82a0 !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-family: 'IBM Plex Mono', monospace !important;
  }
  [data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 22px !important;
    color: #e0e4ef !important;
  }

  /* Dataframe */
  [data-testid="stDataFrame"] {
    border: 1px solid #1e2130;
    border-radius: 8px;
  }

  /* Tabs */
  [data-testid="stTabs"] button {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #7b82a0;
  }
  [data-testid="stTabs"] button[aria-selected="true"] {
    color: #e0e4ef;
    border-bottom: 2px solid #4f7ef8;
  }

  /* Header customizado */
  .dash-header {
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 4px;
  }
  .dash-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 22px;
    font-weight: 600;
    color: #e0e4ef;
    letter-spacing: -0.02em;
  }
  .dash-subtitle {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 13px;
    color: #7b82a0;
  }

  /* Card farol */
  .farol-card {
    background: #13161f;
    border: 1px solid #1e2130;
    border-left: 4px solid;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
  }
  .farol-rota {
    font-size: 15px;
    font-weight: 600;
    color: #e0e4ef;
    margin-bottom: 4px;
  }
  .farol-meta {
    color: #7b82a0;
    font-size: 11px;
  }

  /* Badge status */
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 600;
    letter-spacing: 0.04em;
  }
  .badge-critico  { background: rgba(255,65,54,0.15);  color: #ff4136; border: 1px solid rgba(255,65,54,0.3); }
  .badge-atencao  { background: rgba(255,220,0,0.12);  color: #ffd000; border: 1px solid rgba(255,220,0,0.3); }
  .badge-ok       { background: rgba(46,204,64,0.12);  color: #2ecc40; border: 1px solid rgba(46,204,64,0.3); }

  /* Alerta row */
  .alerta-row {
    background: #13161f;
    border: 1px solid #1e2130;
    border-left: 3px solid #ff4136;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 6px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
  }
  .alerta-rota { font-weight: 600; color: #e0e4ef; font-size: 13px; }
  .alerta-meta { color: #7b82a0; margin-top: 3px; }
  .alerta-nums { color: #ff4136; font-weight: 600; }

  /* Divider */
  hr { border-color: #1e2130; margin: 16px 0; }

  /* Plotly bg fix */
  .js-plotly-plot .plotly .bg { fill: #13161f !important; }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: #0d0f14; }
  ::-webkit-scrollbar-thumb { background: #2a2e3d; border-radius: 3px; }

  /* Input / select */
  [data-testid="stSelectbox"] select,
  [data-testid="stMultiSelect"] > div,
  [data-baseweb="select"] {
    background: #13161f !important;
    border-color: #1e2130 !important;
    color: #e0e4ef !important;
  }

  /* Stale cache warning */
  .stAlert { border-radius: 6px; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# Sidebar — Filtros
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🚌 Pricing Farol")
    st.markdown('<div class="dash-subtitle">Tiradentes 2026</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("**📅 Período**")
    data_ini = st.date_input("De", value=date(2026, 4, 17), key="data_ini")
    data_fim = st.date_input("Até", value=date(2026, 4, 21), key="data_fim")

    st.markdown("---")
    st.markdown("**🔔 Parâmetros de Alerta**")
    ratio_min = st.slider("Ratio mínimo (demanda/proj)", 1.0, 2.0, 1.30, 0.05,
                          help="ratio_vs_proj > X dispara alerta")
    mult_max  = st.slider("Mult máximo (subprecificado)", 1.0, 2.5, 1.50, 0.05,
                          help="mult_final < X indica mult ainda baixo")
    occ_min   = st.slider("Occ mínima", 0.0, 1.0, 0.33, 0.05,
                          help="occ_atual > X para filtrar ruído")

    st.markdown("---")
    st.markdown("**🔍 Filtros de Rota**")
    turno_sel = st.multiselect("Turno", ["MANHA", "TARDE", "NOITE", "MADRUGADA"], default=[])

    st.markdown("---")
    atualizar = st.button("⟳  Atualizar dados", use_container_width=True, type="primary")
    st.caption("Cache: 5 min | Databricks SQL")


# ──────────────────────────────────────────────────────────────
# Carregamento de dados
# ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def get_data(data_ini_str, data_fim_str, ratio_min, mult_max, occ_min):
    df_base    = load_base(data_ini_str, data_fim_str)
    df_alertas = load_alertas(data_ini_str, data_fim_str, ratio_min, mult_max, occ_min)
    return df_base, df_alertas

if atualizar:
    st.cache_data.clear()

with st.spinner("Buscando dados no Databricks..."):
    try:
        df_base, df_alertas = get_data(
            str(data_ini), str(data_fim), ratio_min, mult_max, occ_min
        )
        data_ok = True
    except Exception as e:
        st.error(f"❌ Erro ao conectar ao Databricks: {e}")
        st.info("💡 Verifique as variáveis no `.env` (DATABRICKS_HOST, HTTP_PATH, TOKEN)")
        data_ok = False
        df_base = pd.DataFrame()
        df_alertas = pd.DataFrame()

# Aplicar filtro de turno
if turno_sel and not df_base.empty:
    df_base    = df_base[df_base["turno"].isin(turno_sel)]
    df_alertas = df_alertas[df_alertas["turno"].isin(turno_sel)]


# ──────────────────────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <div class="dash-header">
      <span class="dash-title">PRICING · FAROL</span>
      <span class="dash-subtitle">Tiradentes 2026 · {data_ini.strftime("%d/%m")} → {data_fim.strftime("%d/%m")}</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if not data_ok:
    st.stop()


# ──────────────────────────────────────────────────────────────
# KPIs topo
# ──────────────────────────────────────────────────────────────
df_enriched = enrich_farol(df_base) if not df_base.empty else pd.DataFrame()

n_critico = int((df_enriched["nivel"] == 2).sum()) if not df_enriched.empty else 0
n_atencao = int((df_enriched["nivel"] == 1).sum()) if not df_enriched.empty else 0
n_ok      = int((df_enriched["nivel"] == 0).sum()) if not df_enriched.empty else 0
n_alertas = len(df_alertas)

ratio_medio = df_base["ratio_vs_proj"].mean() if not df_base.empty else 0
lf_atual    = df_base["lf_atual"].mean()      if not df_base.empty else 0
lf_proj     = df_base["lf_proj_2026"].mean()  if not df_base.empty else 0
mult_med    = df_base["mult_final"].mean()     if not df_base.empty else 0

col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
col1.metric("🔴 Críticos",  n_critico)
col2.metric("🟡 Atenção",   n_atencao)
col3.metric("🟢 OK",        n_ok)
col4.metric("🔔 Alertas",   n_alertas)
col5.metric("Ratio médio",  f"{ratio_medio:.2f}×")
col6.metric("LF atual",     fmt_pct(lf_atual))
col7.metric("Mult médio",   f"{mult_med:.2f}×")

st.markdown("---")


# ──────────────────────────────────────────────────────────────
# Abas principais
# ──────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🚨  Alertas",
    "🗺️  Farol por Rota",
    "📈  Curvas & Demanda",
    "💰  Preço vs Concorrência",
])


# ════════════════════════════════════════════════════════════════
# TAB 1 — ALERTAS
# ════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("#### Rotas com demanda acima do projetado e mult abaixo do ideal")

    if df_alertas.empty:
        st.success("✅ Nenhum alerta nos parâmetros atuais.")
    else:
        # Ordenar
        df_al = df_alertas.copy()
        df_al = df_al.sort_values("ratio_vs_proj", ascending=False)

        # Cards de alerta
        for _, row in df_al.iterrows():
            gap_demanda = (row.get("ratio_vs_proj", 1) - 1) * 100
            vagas       = row.get("vagas_restantes", None)
            cap         = row.get("capacidade_atual", None)
            occ_str     = fmt_pct(row.get("occ_atual"))
            pcc         = row.get("price_cc")
            preco       = row.get("preco_praticado")
            gap_preco   = f"−{round((1-pcc/preco)*100)}% vs CC" if pcc and preco and pcc < preco else ""

            vagas_str = f"{int(vagas)}/{int(cap)} vagas" if vagas is not None and cap is not None else ""

            st.markdown(f"""
            <div class="alerta-row">
              <div class="alerta-rota">
                {row['rota_principal']} · <span style="color:#7b82a0">{row['sentido']}</span>
                &nbsp;|&nbsp; {row['data']} &nbsp;·&nbsp; {row['turno']}
              </div>
              <div class="alerta-meta">
                <span class="alerta-nums">Ratio {row['ratio_vs_proj']:.2f}×</span>
                &nbsp;(demanda +{gap_demanda:.0f}% acima do proj.)
                &nbsp;·&nbsp; Mult atual: <b>{row['mult_final']:.2f}×</b>
                &nbsp;·&nbsp; Occ: <b>{occ_str}</b>
                &nbsp;·&nbsp; {vagas_str}
                &nbsp;·&nbsp; LF atual: <b>{fmt_pct(row.get('lf_atual'))}</b> / proj: <b>{fmt_pct(row.get('lf_proj_2026'))}</b>
                {f'&nbsp;·&nbsp; <span style="color:#ff4136">{gap_preco}</span>' if gap_preco else ''}
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        # Tabela exportável
        with st.expander("📋 Ver tabela completa de alertas"):
            cols_show = [
                "data","turno","rota_principal","sentido","antecedencia",
                "ratio_vs_proj","mult_final","occ_atual","lf_atual","lf_proj_2026",
                "vagas_restantes","preco_praticado","price_cc"
            ]
            cols_show = [c for c in cols_show if c in df_al.columns]
            st.dataframe(df_al[cols_show], use_container_width=True, hide_index=True)
            st.download_button(
                "⬇ Exportar CSV",
                df_al[cols_show].to_csv(index=False).encode(),
                "alertas_pricing.csv",
                "text/csv",
            )

        # Scatter: Ratio vs Mult (bubble = occ)
        st.markdown("#### Ratio vs Multiplicador — posicionamento das rotas")
        fig_scatter = go.Figure()

        fig_scatter.add_shape(
            type="rect", x0=ratio_min, x1=df_al["ratio_vs_proj"].max()*1.05,
            y0=0, y1=mult_max,
            fillcolor="rgba(255,65,54,0.07)", line=dict(width=0),
        )
        fig_scatter.add_annotation(
            x=ratio_min + 0.01, y=mult_max - 0.02,
            text="ZONA CRÍTICA", showarrow=False,
            font=dict(color="#ff4136", size=10, family="IBM Plex Mono"),
            xanchor="left", yanchor="top",
        )

        for turno_g, grp in df_al.groupby("turno"):
            fig_scatter.add_trace(go.Scatter(
                x=grp["ratio_vs_proj"],
                y=grp["mult_final"],
                mode="markers+text",
                name=turno_g,
                text=grp["rota_principal"],
                textposition="top center",
                textfont=dict(size=9, family="IBM Plex Mono"),
                marker=dict(
                    size=grp["occ_atual"].fillna(0.3) * 40 + 8,
                    opacity=0.85,
                    line=dict(width=1, color="#0d0f14"),
                ),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Ratio: %{x:.2f}×<br>"
                    "Mult: %{y:.2f}×<br>"
                    "<extra></extra>"
                ),
            ))

        fig_scatter.add_hline(y=mult_max, line_dash="dot", line_color="#ff4136", line_width=1,
                              annotation_text=f"mult máx {mult_max}×", annotation_font_color="#ff4136")
        fig_scatter.add_vline(x=ratio_min, line_dash="dot", line_color="#ff4136", line_width=1,
                              annotation_text=f"ratio mín {ratio_min}×", annotation_font_color="#ff4136")

        fig_scatter.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0d0f14",
            plot_bgcolor="#13161f",
            font=dict(family="IBM Plex Mono", color="#e0e4ef"),
            height=420,
            margin=dict(l=40, r=20, t=20, b=40),
            xaxis=dict(title="Ratio demanda/proj", gridcolor="#1e2130", zeroline=False),
            yaxis=dict(title="Mult final", gridcolor="#1e2130", zeroline=False),
            legend=dict(bgcolor="#13161f", bordercolor="#1e2130", borderwidth=1),
        )
        st.plotly_chart(fig_scatter, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# TAB 2 — FAROL POR ROTA
# ════════════════════════════════════════════════════════════════
with tab2:
    if df_base.empty:
        st.warning("Sem dados para o período selecionado.")
    else:
        resumo = resumo_por_rota(df_base)

        # Filtros rápidos
        fc1, fc2 = st.columns([2, 1])
        with fc1:
            filtro_status = fc1.multiselect(
                "Filtrar por status",
                ["🔴 CRÍTICO", "🟡 ATENÇÃO", "🟢 OK"],
                default=["🔴 CRÍTICO", "🟡 ATENÇÃO"],
            )
        with fc2:
            busca_rota = fc2.text_input("Buscar rota", placeholder="ex: RIO-SAO")

        df_resumo = resumo.copy()
        if filtro_status:
            df_resumo = df_resumo[df_resumo["status"].isin(filtro_status)]
        if busca_rota:
            df_resumo = df_resumo[df_resumo["rota_principal"].str.contains(busca_rota.upper())]

        # Heatmap rota × turno
        st.markdown("#### Heatmap — Ratio por Rota e Turno")
        if not df_enriched.empty:
            pivot = (
                df_enriched.groupby(["rota_principal", "turno"])["ratio_vs_proj"]
                .mean()
                .reset_index()
                .pivot(index="rota_principal", columns="turno", values="ratio_vs_proj")
            )
            top_rotas = (
                df_enriched.groupby("rota_principal")["ratio_vs_proj"]
                .mean()
                .nlargest(25)
                .index
            )
            pivot = pivot.loc[pivot.index.isin(top_rotas)]

            fig_heat = go.Figure(go.Heatmap(
                z=pivot.values,
                x=pivot.columns.tolist(),
                y=pivot.index.tolist(),
                colorscale=[
                    [0.0,  "#1a2e1a"],
                    [0.5,  "#2d3d00"],
                    [0.75, "#7a5c00"],
                    [0.9,  "#cc2200"],
                    [1.0,  "#ff4136"],
                ],
                zmid=1.0,
                text=pivot.values.round(2),
                texttemplate="%{text}×",
                textfont=dict(size=10, family="IBM Plex Mono"),
                hovertemplate="<b>%{y}</b> · %{x}<br>Ratio: %{z:.2f}×<extra></extra>",
                colorbar=dict(
                    title="Ratio",
                    tickfont=dict(family="IBM Plex Mono", size=10),
                    bgcolor="#13161f",
                    bordercolor="#1e2130",
                ),
            ))
            fig_heat.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0d0f14",
                plot_bgcolor="#13161f",
                font=dict(family="IBM Plex Mono", color="#e0e4ef"),
                height=max(300, len(pivot) * 28 + 80),
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(side="top"),
            )
            st.plotly_chart(fig_heat, use_container_width=True)

        st.markdown("---")
        st.markdown("#### Status por Rota")

        # Cards de farol
        cols = st.columns(3)
        for i, (_, row) in enumerate(df_resumo.iterrows()):
            cor   = row["cor"]
            badge_cls = {
                "🔴 CRÍTICO": "badge-critico",
                "🟡 ATENÇÃO": "badge-atencao",
                "🟢 OK":      "badge-ok",
            }.get(row["status"], "badge-ok")

            with cols[i % 3]:
                st.markdown(f"""
                <div class="farol-card" style="border-left-color:{cor}">
                  <div class="farol-rota">{row['rota_principal']}</div>
                  <span class="badge {badge_cls}">{row['status']}</span>
                  <div class="farol-meta" style="margin-top:8px">
                    Ratio médio: <b style="color:#e0e4ef">{row['ratio_medio']:.2f}×</b>
                    &nbsp;·&nbsp; Mult: <b style="color:#e0e4ef">{row['mult_medio']:.2f}×</b><br>
                    LF: <b style="color:#e0e4ef">{fmt_pct(row['lf_atual_medio'])}</b>
                    / proj <b style="color:#e0e4ef">{fmt_pct(row['lf_proj_medio'])}</b>
                    &nbsp;·&nbsp; Occ: <b style="color:#e0e4ef">{fmt_pct(row['occ_medio'])}</b>
                  </div>
                </div>
                """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# TAB 3 — CURVAS & DEMANDA
# ════════════════════════════════════════════════════════════════
with tab3:
    if df_base.empty:
        st.warning("Sem dados.")
    else:
        st.markdown("#### Curva de Booking — LF Atual vs Projetado por Antecedência")

        rotas_disp = sorted(df_base["rota_principal"].dropna().unique())
        c1, c2, c3 = st.columns(3)
        rota_sel  = c1.selectbox("Rota", rotas_disp)
        sentidos  = sorted(df_base[df_base["rota_principal"] == rota_sel]["sentido"].dropna().unique())
        sent_sel  = c2.selectbox("Sentido", sentidos)
        turnos_d  = sorted(df_base["turno"].dropna().unique())
        turno_d   = c3.selectbox("Turno", turnos_d)

        df_curva = (
            df_base[
                (df_base["rota_principal"] == rota_sel) &
                (df_base["sentido"]        == sent_sel) &
                (df_base["turno"]          == turno_d)
            ]
            .groupby("antecedencia")[["lf_atual", "lf_proj_2026", "ratio_vs_proj"]]
            .mean()
            .reset_index()
            .sort_values("antecedencia", ascending=False)
        )

        if df_curva.empty:
            st.info("Sem dados para essa combinação.")
        else:
            fig_curva = go.Figure()

            fig_curva.add_trace(go.Scatter(
                x=df_curva["antecedencia"],
                y=df_curva["lf_proj_2026"],
                name="LF Projetado 2026",
                mode="lines",
                line=dict(color="#4f7ef8", width=2, dash="dot"),
                fill=None,
            ))
            fig_curva.add_trace(go.Scatter(
                x=df_curva["antecedencia"],
                y=df_curva["lf_atual"],
                name="LF Atual",
                mode="lines+markers",
                line=dict(color="#2ecc40", width=2.5),
                marker=dict(size=5),
                fill="tonexty",
                fillcolor="rgba(46,204,64,0.06)",
            ))

            # Área crítica (ratio > 1.3)
            df_crit = df_curva[df_curva["ratio_vs_proj"] > 1.3]
            if not df_crit.empty:
                fig_curva.add_trace(go.Scatter(
                    x=df_crit["antecedencia"],
                    y=df_crit["lf_atual"],
                    name="⚠ Demanda >130%",
                    mode="markers",
                    marker=dict(size=10, color="#ff4136", symbol="diamond"),
                ))

            fig_curva.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0d0f14",
                plot_bgcolor="#13161f",
                font=dict(family="IBM Plex Mono", color="#e0e4ef"),
                height=380,
                margin=dict(l=40, r=20, t=20, b=40),
                xaxis=dict(
                    title="Antecedência (dias)",
                    autorange="reversed",
                    gridcolor="#1e2130",
                    zeroline=False,
                ),
                yaxis=dict(title="Load Factor", gridcolor="#1e2130", tickformat=".0%"),
                legend=dict(bgcolor="#13161f", bordercolor="#1e2130"),
            )
            st.plotly_chart(fig_curva, use_container_width=True)

            # Ratio por antecedência
            st.markdown("#### Ratio (demanda/projetado) por Antecedência")
            fig_ratio = go.Figure()
            colors = [
                "#ff4136" if r > 1.3 else "#ffd000" if r > 1.15 else "#2ecc40"
                for r in df_curva["ratio_vs_proj"]
            ]
            fig_ratio.add_trace(go.Bar(
                x=df_curva["antecedencia"],
                y=df_curva["ratio_vs_proj"],
                marker_color=colors,
                name="Ratio",
                hovertemplate="Antec: %{x}d<br>Ratio: %{y:.2f}×<extra></extra>",
            ))
            fig_ratio.add_hline(y=1.0, line_color="#7b82a0", line_width=1, line_dash="dot")
            fig_ratio.add_hline(y=1.3, line_color="#ff4136", line_width=1, line_dash="dot",
                                annotation_text="1.30×", annotation_font_color="#ff4136")
            fig_ratio.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0d0f14",
                plot_bgcolor="#13161f",
                font=dict(family="IBM Plex Mono", color="#e0e4ef"),
                height=260,
                margin=dict(l=40, r=20, t=10, b=40),
                xaxis=dict(title="Antecedência (dias)", autorange="reversed", gridcolor="#1e2130"),
                yaxis=dict(title="Ratio", gridcolor="#1e2130"),
                showlegend=False,
            )
            st.plotly_chart(fig_ratio, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# TAB 4 — PREÇO vs CONCORRÊNCIA
# ════════════════════════════════════════════════════════════════
with tab4:
    if df_base.empty:
        st.warning("Sem dados.")
    else:
        st.markdown("#### Posicionamento de Preço vs Concorrência por Rota")

        df_preco = df_base.dropna(subset=["preco_praticado", "price_cc"]).copy()
        df_preco["gap_pct"] = (df_preco["preco_praticado"] / df_preco["price_cc"] - 1) * 100
        df_preco["gap_abs"] = df_preco["preco_praticado"] - df_preco["price_cc"]

        if df_preco.empty:
            st.info("Sem dados de concorrência disponíveis.")
        else:
            # Resumo por rota
            resumo_preco = (
                df_preco.groupby(["rota_principal", "sentido"])
                .agg(
                    preco_med   = ("preco_praticado", "mean"),
                    cc_med      = ("price_cc", "mean"),
                    gap_pct_med = ("gap_pct", "mean"),
                )
                .reset_index()
                .sort_values("gap_pct_med")
            )

            fig_preco = go.Figure()
            cores_gap = [
                "#ff4136" if g < -10 else "#ffd000" if g < 0 else "#2ecc40"
                for g in resumo_preco["gap_pct_med"]
            ]
            fig_preco.add_trace(go.Bar(
                x=resumo_preco["sentido"],
                y=resumo_preco["gap_pct_med"],
                marker_color=cores_gap,
                text=[f"{v:+.1f}%" for v in resumo_preco["gap_pct_med"]],
                textposition="outside",
                textfont=dict(size=10, family="IBM Plex Mono"),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Gap médio: %{y:+.1f}%<br>"
                    "<extra></extra>"
                ),
            ))
            fig_preco.add_hline(y=0, line_color="#7b82a0", line_width=1)
            fig_preco.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0d0f14",
                plot_bgcolor="#13161f",
                font=dict(family="IBM Plex Mono", color="#e0e4ef"),
                height=380,
                margin=dict(l=20, r=20, t=10, b=80),
                xaxis=dict(
                    title="",
                    tickangle=-35,
                    gridcolor="#1e2130",
                ),
                yaxis=dict(
                    title="Gap Preço vs CC (%)",
                    gridcolor="#1e2130",
                    ticksuffix="%",
                ),
                showlegend=False,
            )
            st.plotly_chart(fig_preco, use_container_width=True)

            # Detalhe por sentido selecionado
            c1, c2 = st.columns(2)
            sentido_preco = c1.selectbox(
                "Detalhar sentido",
                sorted(df_preco["sentido"].unique()),
                key="sent_preco"
            )
            df_det = df_preco[df_preco["sentido"] == sentido_preco].copy()

            fig_comp = go.Figure()
            fig_comp.add_trace(go.Scatter(
                x=df_det["data"].astype(str),
                y=df_det["preco_praticado"],
                name="Nosso preço",
                mode="lines+markers",
                line=dict(color="#4f7ef8", width=2.5),
                marker=dict(size=6),
            ))
            fig_comp.add_trace(go.Scatter(
                x=df_det["data"].astype(str),
                y=df_det["price_cc"],
                name="Concorrência (CC)",
                mode="lines+markers",
                line=dict(color="#ff4136", width=2, dash="dash"),
                marker=dict(size=6, symbol="x"),
            ))
            fig_comp.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0d0f14",
                plot_bgcolor="#13161f",
                font=dict(family="IBM Plex Mono", color="#e0e4ef"),
                height=300,
                margin=dict(l=40, r=20, t=10, b=40),
                xaxis=dict(title="Data", gridcolor="#1e2130"),
                yaxis=dict(title="Preço (R$)", gridcolor="#1e2130", tickprefix="R$ "),
                legend=dict(bgcolor="#13161f", bordercolor="#1e2130"),
            )
            st.plotly_chart(fig_comp, use_container_width=True)

            # Tabela resumo
            with st.expander("📋 Tabela preço vs CC por sentido"):
                cols_p = ["data","turno","rota_principal","sentido","preco_praticado","price_cc","gap_pct","gap_abs","mult_final"]
                cols_p = [c for c in cols_p if c in df_preco.columns]
                st.dataframe(df_preco[cols_p].sort_values("gap_pct"), use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="font-family:IBM Plex Mono;font-size:11px;color:#3a3e52;text-align:center">'
    'Pricing Farol · Tiradentes 2026 · Cache 5min · Databricks SQL'
    '</div>',
    unsafe_allow_html=True,
)
