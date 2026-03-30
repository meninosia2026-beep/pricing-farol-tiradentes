"""
Dashboard de Acompanhamento de Feriados — Streamlit
Conecta na tabela sandbox gerada pelo notebook Databricks.

Instalar:
    pip install streamlit pandas plotly databricks-sql-connector python-dotenv

Rodar:
    streamlit run dashboard_feriado.py

Variáveis de ambiente (crie um .env ou defina no shell):
    DATABRICKS_HOST      = adb-xxxx.azuredatabricks.net
    DATABRICKS_TOKEN     = dapi...
    DATABRICKS_HTTP_PATH = /sql/1.0/warehouses/xxxx
    SANDBOX_TABLE        = proj_pricing_sandbox.base_consulta_feriado
"""

import os
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Configuração da página
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Curva Feriado",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
    background-color: #0d0f14;
    color: #e2e8f0;
}
.dash-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 18px 0 12px 0;
    border-bottom: 1px solid #1e2530;
    margin-bottom: 18px;
}
.dash-header h1 {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.15rem;
    font-weight: 600;
    color: #f0f4ff;
    margin: 0;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.dash-header .badge {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    padding: 3px 8px;
    background: #1a2236;
    border: 1px solid #2d3a52;
    border-radius: 3px;
    color: #7b9ed9;
    letter-spacing: 0.08em;
}
.metric-row { display: flex; gap: 12px; margin-bottom: 16px; }
.metric-card {
    flex: 1;
    background: #111622;
    border: 1px solid #1e2733;
    border-radius: 6px;
    padding: 14px 18px;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.metric-card.blue::before  { background: #3b82f6; }
.metric-card.green::before { background: #10b981; }
.metric-card.amber::before { background: #f59e0b; }
.metric-card.red::before   { background: #ef4444; }
.metric-card .label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #64748b;
    margin-bottom: 6px;
}
.metric-card .value {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.5rem;
    font-weight: 600;
    color: #f1f5f9;
    line-height: 1;
}
.metric-card .sub { font-size: 0.72rem; color: #475569; margin-top: 4px; }
.metric-card .delta-pos { color: #10b981; font-size: 0.78rem; }
.metric-card .delta-neg { color: #ef4444; font-size: 0.78rem; }
div[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 2px; background: #111622; border-radius: 6px;
    padding: 3px; border: 1px solid #1e2733; width: fit-content;
}
div[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent; border-radius: 4px; color: #64748b;
    font-size: 0.78rem; font-weight: 500; padding: 6px 16px;
    border: none; letter-spacing: 0.02em;
}
div[data-testid="stTabs"] [aria-selected="true"] {
    background: #1e2d4a !important; color: #93c5fd !important;
}
div[data-testid="stSelectbox"] > div > div {
    background: #111622 !important; border-color: #1e2733 !important;
    border-radius: 4px !important; color: #e2e8f0 !important; font-size: 0.8rem !important;
}
div[data-testid="stDataFrame"] {
    border: 1px solid #1e2733; border-radius: 6px; overflow: hidden;
}
.section-label {
    font-size: 0.65rem; text-transform: uppercase;
    letter-spacing: 0.12em; color: #475569; margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Conexão Databricks (cacheada)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_connection():
    try:
        from databricks import sql as dbsql
        conn = dbsql.connect(
            server_hostname=os.getenv("DATABRICKS_HOST", ""),
            http_path=os.getenv("DATABRICKS_HTTP_PATH", ""),
            access_token=os.getenv("DATABRICKS_TOKEN", ""),
        )
        return conn
    except Exception:
        return None


@st.cache_data(ttl=300, show_spinner="Carregando dados...")
def load_data(table: str) -> pd.DataFrame:
    conn = get_connection()
    if conn is None:
        return _mock_data()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {table}")
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            return pd.DataFrame(rows, columns=cols)
    except Exception:
        return _mock_data()


def _mock_data() -> pd.DataFrame:
    """Dados mock para dev sem Databricks."""
    import numpy as np
    rng = np.random.default_rng(42)
    rotas = ["SAO-RIO", "SAO-CWB", "RIO-BHZ", "SAO-GYN", "BHZ-RIO", "RIO-SAO"]
    turnos = ["MANHA", "TARDE", "NOITE"]
    datas = pd.date_range("2026-04-17", "2026-04-21")
    records = []
    for dt in datas:
        for rota in rotas:
            for turno in turnos:
                for ant in range(0, 30, 2):
                    lf_proj = rng.uniform(0.55, 0.85)
                    lf_atual = lf_proj * rng.uniform(0.7, 1.3)
                    records.append({
                        "data": dt.date(),
                        "rota_principal": rota,
                        "sentido": rota,
                        "turno": turno,
                        "antecedencia": ant,
                        "dia_da_semana": dt.dayofweek + 1,
                        "pax": int(rng.integers(10, 45)),
                        "capacidade_atual": 46,
                        "occ_atual": round(rng.uniform(0.2, 0.95), 2),
                        "vagas_restantes": int(rng.integers(0, 20)),
                        "lf_proj_2026": round(lf_proj, 4),
                        "lf_atual": round(lf_atual, 4),
                        "ratio_vs_proj": round(lf_atual / lf_proj, 4),
                        "tkm_atual": round(rng.uniform(80, 180), 2),
                        "tkm_comp": round(rng.uniform(75, 170), 2),
                        "preco_base": round(rng.uniform(60, 130), 2),
                        "preco_est_draft": round(rng.uniform(70, 160), 2),
                        "preco_est_novo": round(rng.uniform(70, 160), 2),
                        "preco_praticado": round(rng.uniform(70, 160), 2),
                        "mult_final": round(rng.uniform(1.0, 1.8), 3),
                        "mult_flutuacao": round(rng.uniform(-0.1, 0.2), 3) if rng.random() > 0.4 else None,
                        "price_cc": round(rng.uniform(65, 150), 2),
                    })
    return pd.DataFrame(records)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def fmt_pct(v, digits=1):
    if v is None or (isinstance(v, float) and pd.isna(v)): return "—"
    return f"{v*100:.{digits}f}%"

def fmt_num(v, digits=2):
    if v is None or (isinstance(v, float) and pd.isna(v)): return "—"
    return f"{v:.{digits}f}"

def status_icon(ratio):
    if pd.isna(ratio): return "⬜"
    if ratio >= 1.10: return "🟢"
    if ratio >= 0.90: return "🟡"
    return "🔴"

def color_ratio(val):
    try:
        v = float(val)
        if v >= 1.10: return "color: #10b981"
        if v >= 0.90: return "color: #f59e0b"
        return "color: #ef4444"
    except Exception:
        return ""

def plotly_theme():
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0d1117",
        font=dict(family="IBM Plex Mono, monospace", color="#94a3b8", size=11),
        xaxis=dict(gridcolor="#1e2733", zerolinecolor="#1e2733", linecolor="#1e2733"),
        yaxis=dict(gridcolor="#1e2733", zerolinecolor="#1e2733", linecolor="#1e2733"),
        margin=dict(l=10, r=10, t=36, b=10),
    )

# ─────────────────────────────────────────────────────────────────────────────
# Load
# ─────────────────────────────────────────────────────────────────────────────
SANDBOX_TABLE = os.getenv("SANDBOX_TABLE", "proj_pricing_sandbox.base_consulta_feriado")
df_raw = load_data(SANDBOX_TABLE)
df_raw["data"] = pd.to_datetime(df_raw["data"]).dt.date

# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="dash-header">
  <h1>📈 Curva Feriado</h1>
  <span class="badge">ACOMPANHAMENTO</span>
  <span class="badge" style="margin-left:auto; color:#475569">{len(df_raw):,} linhas carregadas</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Filters
# ─────────────────────────────────────────────────────────────────────────────
datas_disp  = sorted(df_raw["data"].unique())
rotas_disp  = sorted(df_raw["rota_principal"].dropna().unique())
turnos_disp = sorted(df_raw["turno"].dropna().unique())

c1, c2, c3, c4, c5 = st.columns([1.2, 1.6, 1.2, 1.2, 1.2])
with c1:
    sel_data = st.selectbox("Data", ["Todas"] + [str(d) for d in datas_disp])
with c2:
    sel_rota = st.selectbox("Rota", ["Todas"] + rotas_disp)
with c3:
    sel_turno = st.selectbox("Turno", ["Todos"] + turnos_disp)

sentidos_pool = (
    df_raw.loc[df_raw["rota_principal"] == sel_rota, "sentido"].dropna().unique()
    if sel_rota != "Todas" else df_raw["sentido"].dropna().unique()
)
with c4:
    sel_sentido = st.selectbox("Sentido", ["Todos"] + sorted(sentidos_pool))
with c5:
    ant_max = int(df_raw["antecedencia"].max()) if "antecedencia" in df_raw.columns else 79
    sel_ant = st.selectbox("Antecedência ≤", ["Todas"] + list(range(0, ant_max + 1, 5)))

# Apply filters
df = df_raw.copy()
if sel_data    != "Todas": df = df[df["data"].astype(str) == sel_data]
if sel_rota    != "Todas": df = df[df["rota_principal"] == sel_rota]
if sel_turno   != "Todos": df = df[df["turno"] == sel_turno]
if sel_sentido != "Todos": df = df[df["sentido"] == sel_sentido]
if sel_ant     != "Todas": df = df[df["antecedencia"] <= int(sel_ant)]

# ─────────────────────────────────────────────────────────────────────────────
# KPI cards
# ─────────────────────────────────────────────────────────────────────────────
def smean(col):
    return df[col].mean() if col in df.columns and len(df) else None

ratio_med = smean("ratio_vs_proj")
occ_med   = smean("occ_atual")
lf_med    = smean("lf_atual")
lf_proj   = smean("lf_proj_2026")
tkm_med   = smean("tkm_atual")
tkm_comp  = smean("tkm_comp")

ratio_delta = (ratio_med - 1) if ratio_med is not None else None
preco_gap   = ((tkm_med / tkm_comp) - 1) if (tkm_med and tkm_comp and tkm_comp > 0) else None

def delta_html(v, suffix=""):
    if v is None: return ""
    icon = "▲" if v > 0 else "▼"
    cls  = "delta-pos" if v > 0 else "delta-neg"
    return f'<span class="{cls}">{icon} {abs(v)*100:.1f}%{suffix}</span>'

def kpi(label, value, sub, color_cls, extra=""):
    return f"""
    <div class="metric-card {color_cls}">
      <div class="label">{label}</div>
      <div class="value">{value}</div>
      <div class="sub">{sub} {extra}</div>
    </div>"""

st.markdown(f"""
<div class="metric-row">
  {kpi("LF Atual / Projetado", fmt_num(ratio_med, 3), f"Projetado médio: {fmt_pct(lf_proj)}", "blue", delta_html(ratio_delta))}
  {kpi("LF Atual", fmt_pct(lf_med), f"vs proj. {fmt_pct(lf_proj)}", "green")}
  {kpi("Ocupação Média", fmt_pct(occ_med), f"{len(df):,} obs filtradas", "amber")}
  {kpi("TKM Atual", f"R$ {fmt_num(tkm_med)}", f"Concorrência: R$ {fmt_num(tkm_comp)}", "red", delta_html(preco_gap, " vs comp."))}
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "LF Atual vs Projetado",
    "Diferença %",
    "Preços & Mult.",
    "Ocupação",
    "Tabela completa",
])

# ── TAB 1 ────────────────────────────────────────────────────────────────────
with tab1:
    if df.empty:
        st.info("Sem dados para os filtros selecionados.")
    else:
        grp = (
            df.groupby("antecedencia", as_index=False)
            .agg(lf_atual=("lf_atual","mean"), lf_proj=("lf_proj_2026","mean"))
            .sort_values("antecedencia", ascending=False)
        )
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=grp["antecedencia"], y=grp["lf_proj"],
            name="LF Projetado 2026",
            line=dict(color="#3b82f6", width=2, dash="dot"),
        ))
        fig.add_trace(go.Scatter(
            x=grp["antecedencia"], y=grp["lf_atual"],
            name="LF Atual",
            line=dict(color="#10b981", width=2.5),
            mode="lines+markers", marker=dict(size=4),
        ))
        fig.update_layout(
            **plotly_theme(), height=340,
            title=dict(text="Curva de Antecedência — LF médio", font=dict(size=12)),
            xaxis_title="Antecedência (dias)", yaxis_title="Load Factor",
            yaxis_tickformat=".0%",
            legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=1.1),
            xaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig, use_container_width=True)

        grp_rota = (
            df.groupby("rota_principal", as_index=False)
            .agg(ratio=("ratio_vs_proj","mean"))
            .sort_values("ratio", ascending=True)
        )
        colors = ["#10b981" if r >= 1 else "#ef4444" for r in grp_rota["ratio"]]
        fig2 = go.Figure(go.Bar(
            x=grp_rota["ratio"] - 1,
            y=grp_rota["rota_principal"],
            orientation="h",
            marker_color=colors,
            text=[f"{(v-1)*100:+.1f}%" for v in grp_rota["ratio"]],
            textposition="outside",
        ))
        fig2.update_layout(
            **plotly_theme(), height=max(200, len(grp_rota) * 32 + 60),
            title=dict(text="Ratio LF atual/projetado por rota", font=dict(size=12)),
            xaxis_title="Δ vs projetado", xaxis_tickformat="+.0%",
            xaxis=dict(zeroline=True, zerolinecolor="#374151", zerolinewidth=1.5),
        )
        st.plotly_chart(fig2, use_container_width=True)

# ── TAB 2 ────────────────────────────────────────────────────────────────────
with tab2:
    if df.empty:
        st.info("Sem dados para os filtros selecionados.")
    else:
        if "data" in df.columns and "rota_principal" in df.columns:
            piv = (
                df.groupby(["rota_principal","data"], as_index=False)
                .agg(ratio=("ratio_vs_proj","mean"))
                .pivot(index="rota_principal", columns="data", values="ratio")
            )
            piv.columns = [str(c) for c in piv.columns]
            fig = go.Figure(go.Heatmap(
                z=piv.values,
                x=piv.columns.tolist(),
                y=piv.index.tolist(),
                colorscale=[[0.0,"#7f1d1d"],[0.45,"#1f2937"],[0.55,"#1f2937"],[1.0,"#064e3b"]],
                zmid=1.0,
                text=[[f"{v:.2f}" if not pd.isna(v) else "" for v in row] for row in piv.values],
                texttemplate="%{text}",
                textfont=dict(size=10),
                colorbar=dict(title="Ratio", tickformat=".2f"),
            ))
            fig.update_layout(
                **plotly_theme(), height=max(260, len(piv) * 36 + 80),
                title=dict(text="Ratio LF atual/proj — Rota × Data", font=dict(size=12)),
                xaxis=dict(side="top"),
            )
            st.plotly_chart(fig, use_container_width=True)

        grp_t = df.groupby("turno", as_index=False).agg(
            ratio=("ratio_vs_proj","mean"), lf=("lf_atual","mean"), proj=("lf_proj_2026","mean")
        )
        cols_t = st.columns(len(grp_t))
        for i, row in grp_t.iterrows():
            delta = (row["ratio"] - 1) * 100
            icon  = "▲" if delta >= 0 else "▼"
            color = "#10b981" if delta >= 0 else "#ef4444"
            cols_t[i % len(cols_t)].markdown(f"""
            <div class="metric-card {'green' if delta>=0 else 'red'}">
              <div class="label">{row['turno']}</div>
              <div class="value" style="font-size:1.1rem">{row['ratio']:.3f}</div>
              <div class="sub"><span style="color:{color}">{icon} {abs(delta):.1f}%</span> vs proj.</div>
            </div>""", unsafe_allow_html=True)

# ── TAB 3 ────────────────────────────────────────────────────────────────────
with tab3:
    if df.empty:
        st.info("Sem dados para os filtros selecionados.")
    else:
        c_l, c_r = st.columns(2)
        with c_l:
            st.markdown('<div class="section-label">Preço praticado vs Concorrência</div>', unsafe_allow_html=True)
            grp_p = df.groupby("rota_principal", as_index=False).agg(
                buser=("tkm_atual","mean"), comp=("tkm_comp","mean")
            ).dropna(subset=["buser","comp"]).sort_values("buser")
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Buser (TKM)", x=grp_p["rota_principal"], y=grp_p["buser"], marker_color="#3b82f6"))
            fig.add_trace(go.Bar(name="Concorrência", x=grp_p["rota_principal"], y=grp_p["comp"], marker_color="#475569"))
            fig.update_layout(**plotly_theme(), height=300, barmode="group",
                              legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=1.1),
                              yaxis_title="R$")
            st.plotly_chart(fig, use_container_width=True)

        with c_r:
            st.markdown('<div class="section-label">Distribuição de Multiplicadores</div>', unsafe_allow_html=True)
            if "mult_final" in df.columns:
                fig = go.Figure()
                fig.add_trace(go.Histogram(x=df["mult_final"].dropna(), nbinsx=25,
                                           name="mult_final", marker_color="#6366f1", opacity=0.8))
                if "mult_flutuacao" in df.columns and df["mult_flutuacao"].notna().any():
                    fig.add_trace(go.Histogram(x=df["mult_flutuacao"].dropna(), nbinsx=20,
                                               name="mult_flutuacao", marker_color="#f59e0b", opacity=0.7))
                fig.update_layout(**plotly_theme(), height=300, barmode="overlay",
                                  legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", y=1.1))
                st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="section-label">Mult. Final × Ratio LF</div>', unsafe_allow_html=True)
        sc = df[["rota_principal","turno","mult_final","ratio_vs_proj","antecedencia"]].dropna()
        if not sc.empty:
            fig = px.scatter(
                sc, x="mult_final", y="ratio_vs_proj",
                color="turno", size="antecedencia",
                hover_data=["rota_principal"],
                color_discrete_sequence=["#3b82f6","#10b981","#f59e0b","#a855f7"],
                opacity=0.7,
            )
            fig.update_layout(**plotly_theme(), height=300,
                              xaxis_title="Multiplicador Final", yaxis_title="Ratio LF atual/proj",
                              legend=dict(bgcolor="rgba(0,0,0,0)"))
            fig.add_hline(y=1.0, line_dash="dot", line_color="#374151")
            st.plotly_chart(fig, use_container_width=True)

# ── TAB 4 ────────────────────────────────────────────────────────────────────
with tab4:
    if df.empty:
        st.info("Sem dados para os filtros selecionados.")
    else:
        c_l, c_r = st.columns(2)
        with c_l:
            st.markdown('<div class="section-label">Ocupação por Data</div>', unsafe_allow_html=True)
            grp_d = df.groupby("data", as_index=False).agg(occ=("occ_atual","mean")).sort_values("data")
            fig = go.Figure(go.Bar(x=[str(d) for d in grp_d["data"]], y=grp_d["occ"], marker_color="#3b82f6"))
            fig.add_hline(y=0.80, line_dash="dot", line_color="#10b981",
                          annotation_text="Meta 80%", annotation_position="right")
            fig.update_layout(**plotly_theme(), height=280, yaxis_tickformat=".0%", yaxis_range=[0, 1.05])
            st.plotly_chart(fig, use_container_width=True)

        with c_r:
            st.markdown('<div class="section-label">Vagas Restantes por Rota</div>', unsafe_allow_html=True)
            grp_v = df.groupby("rota_principal", as_index=False).agg(vagas=("vagas_restantes","mean")).sort_values("vagas")
            fig = go.Figure(go.Bar(
                x=grp_v["vagas"], y=grp_v["rota_principal"], orientation="h",
                marker_color=["#10b981" if v < 5 else "#f59e0b" if v < 15 else "#ef4444" for v in grp_v["vagas"]],
                text=[f"{v:.0f}" for v in grp_v["vagas"]], textposition="outside",
            ))
            fig.update_layout(**plotly_theme(), height=280, xaxis_title="Vagas restantes (média)")
            st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="section-label">Curva de Ocupação × Antecedência</div>', unsafe_allow_html=True)
        grp_a = df.groupby("antecedencia", as_index=False).agg(occ=("occ_atual","mean")).sort_values("antecedencia", ascending=False)
        fig = go.Figure(go.Scatter(
            x=grp_a["antecedencia"], y=grp_a["occ"],
            fill="tozeroy", fillcolor="rgba(59,130,246,0.12)",
            line=dict(color="#3b82f6", width=2),
        ))
        fig.update_layout(**plotly_theme(), height=220, xaxis=dict(autorange="reversed"),
                          yaxis_tickformat=".0%", xaxis_title="Antecedência (dias)", yaxis_title="Ocupação")
        st.plotly_chart(fig, use_container_width=True)

# ── TAB 5 ────────────────────────────────────────────────────────────────────
with tab5:
    if df.empty:
        st.info("Sem dados.")
    else:
        COLS = [
            "data","rota_principal","sentido","turno","antecedencia","dia_da_semana",
            "pax","capacidade_atual","occ_atual","vagas_restantes",
            "lf_proj_2026","lf_atual","ratio_vs_proj",
            "tkm_atual","tkm_comp","preco_praticado","mult_final","mult_flutuacao","price_cc",
        ]
        cols_exib = [c for c in COLS if c in df.columns]
        df_show = df[cols_exib].copy()
        if "ratio_vs_proj" in df_show.columns:
            df_show.insert(0, "⬤", df_show["ratio_vs_proj"].apply(status_icon))

        fmt_cols = {
            "occ_atual":"{:.1%}","lf_proj_2026":"{:.1%}","lf_atual":"{:.1%}",
            "ratio_vs_proj":"{:.3f}","mult_final":"{:.3f}","mult_flutuacao":"{:.3f}",
            "tkm_atual":"R$ {:.2f}","tkm_comp":"R$ {:.2f}",
            "preco_praticado":"R$ {:.2f}","price_cc":"R$ {:.2f}",
        }

        st.markdown(f'<div class="section-label">{len(df_show):,} linhas · {len(cols_exib)} colunas</div>',
                    unsafe_allow_html=True)

        styled = (
            df_show.style
            .format(fmt_cols, na_rep="—")
            .applymap(color_ratio, subset=["ratio_vs_proj"] if "ratio_vs_proj" in df_show.columns else [])
            .set_properties(**{"font-size":"11px","font-family":"IBM Plex Mono, monospace"})
        )
        st.dataframe(styled, use_container_width=True, height=520)

        csv = df_show.to_csv(index=False).encode("utf-8")
        st.download_button("⬇  Baixar CSV", data=csv,
                           file_name="base_consulta_feriado.csv", mime="text/csv")

# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:40px;padding-top:12px;border-top:1px solid #1e2733;
            font-size:0.65rem;color:#334155;text-align:center;font-family:'IBM Plex Mono',monospace;">
  CURVA FERIADO · PRICING · dados atualizados via sandbox Databricks
</div>
""", unsafe_allow_html=True)
