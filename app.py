"""
Farol de Feriados — app.py
Puxa CSV do GitHub (gerado pelo Databricks) e renderiza um dashboard HTML inline.
"""

import streamlit as st
import pandas as pd
import requests
import json

# ── CONFIG ─────────────────────────────────────────────────────────────────────
GITHUB_RAW = "https://raw.githubusercontent.com/meninosia2026-beep/pricing-farol-tiradentes/main"
CONFIG_URL = f"{GITHUB_RAW}/data/config.json"

st.set_page_config(
    page_title="Farol · Feriados",
    page_icon="🔦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
section[data-testid="stSidebar"] { background:#0c1018; border-right:1px solid #1a2236; }
section[data-testid="stSidebar"] * { color:#8a9bb5 !important; font-size:13px; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] strong { color:#c8d4e6 !important; font-size:14px; }
.stApp { background:#080c14; }
.block-container { padding-top:1rem !important; }
hr { border-color:#1a2236 !important; }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_config():
    try:
        r = requests.get(CONFIG_URL, timeout=10)
        if r.status_code != 200:
            return {"feriados": [], "_erro": f"HTTP {r.status_code}"}
        t = r.text.strip()
        return json.loads(t) if t else {"feriados": [], "_erro": "config.json vazio"}
    except json.JSONDecodeError as e:
        return {"feriados": [], "_erro": f"JSON inválido: {e}"}
    except Exception as e:
        return {"feriados": [], "_erro": str(e)}

@st.cache_data(ttl=120)
def load_csv(url: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(url)
        num = ["antecedencia","dia_da_semana","occ_atual","lf_atual","lf_proj_2026",
               "ratio_vs_proj","price_cc","preco_praticado","preco_base",
               "preco_est_draft","preco_est_novo","mult_final","mult_flutuacao",
               "pax","vagas_restantes","capacidade_atual","tkm_atual","tkm_comp"]
        for c in num:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        if "data" in df.columns:
            df["data"] = pd.to_datetime(df["data"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"Erro: {e}")
        return pd.DataFrame()


# ── SIDEBAR ────────────────────────────────────────────────────────────────────
config   = load_config()
feriados = config.get("feriados", [])
_err     = config.get("_erro")

with st.sidebar:
    st.markdown("**🔦 FAROL · FERIADOS**")
    st.divider()
    if _err:
        st.caption(f"⚠ config.json: {_err}")

    usar_manual = st.toggle("URL manual", value=(not feriados))

    if usar_manual or not feriados:
        csv_url = st.text_input(
            "URL raw do CSV",
            placeholder=f"{GITHUB_RAW}/data/feriado_tiradentes_2026.csv",
        ).strip()
        feriado_cfg  = {"nome": st.text_input("Nome", "Feriado"), "key": "manual", "dt_ini": "", "dt_fim": ""}
        feriado_nome = feriado_cfg["nome"]
        if not csv_url:
            st.info("Cole a URL do CSV para carregar.")
            st.stop()
    else:
        opts         = {f["nome"]: f for f in feriados}
        feriado_nome = st.selectbox("Feriado", list(opts.keys()))
        feriado_cfg  = opts[feriado_nome]
        if "atualizado" in feriado_cfg:
            st.caption(f"↺ atualizado {feriado_cfg['atualizado']}")
        csv_url = f"{GITHUB_RAW}/{feriado_cfg['arquivo']}"

    st.divider()
    df_raw = load_csv(csv_url)
    if df_raw.empty:
        st.error("Sem dados.")
        st.stop()

    if st.button("↺  Recarregar dados"):
        st.cache_data.clear()
        st.rerun()


# ── PREPARA JSON PARA O HTML ───────────────────────────────────────────────────
df = df_raw.copy()
if "data" in df.columns:
    df["data"] = df["data"].dt.strftime("%Y-%m-%d")

rows = df.to_dict(orient="records")
# garante que NaN vira null no JSON
data_json = json.dumps(rows, default=lambda v: None if (isinstance(v, float) and v != v) else v)

periodo_str = f"{feriado_cfg.get('dt_ini', '')} → {feriado_cfg.get('dt_fim', '')}"


# ── HTML DASHBOARD ─────────────────────────────────────────────────────────────
html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

*{{box-sizing:border-box;margin:0;padding:0}}
body{{
  background:#080c14;
  color:#8a9bb5;
  font-family:'DM Sans',sans-serif;
  padding:20px 24px;
  min-height:100vh;
}}

/* ── Header ── */
.header{{
  display:flex;
  align-items:baseline;
  gap:12px;
  padding-bottom:18px;
  border-bottom:1px solid #131d2e;
  margin-bottom:22px;
}}
.header-title{{
  font-family:'DM Mono',monospace;
  font-size:20px;
  font-weight:500;
  color:#dce6f5;
  letter-spacing:-0.02em;
}}
.header-period{{
  font-family:'DM Mono',monospace;
  font-size:11px;
  color:#2a3d5c;
  letter-spacing:0.05em;
}}

/* ── KPI row ── */
.kpi-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:22px}}
.kpi{{
  background:#0c1220;
  border:1px solid #131d2e;
  border-radius:10px;
  padding:16px 18px 13px;
  position:relative;
  overflow:hidden;
}}
.kpi::after{{
  content:'';
  position:absolute;
  top:0;left:0;right:0;
  height:2px;
  background:var(--ac,#1e3a5f);
}}
.kpi.up::after   {{background:linear-gradient(90deg,#00c896,#0055e0)}}
.kpi.down::after {{background:linear-gradient(90deg,#e03030,#f07030)}}
.kpi.warn::after {{background:linear-gradient(90deg,#d4860a,#e8c030)}}
.kpi.neu::after  {{background:linear-gradient(90deg,#1e3a5f,#2a4f7a)}}
.kpi-label{{
  font-family:'DM Mono',monospace;
  font-size:9px;
  letter-spacing:0.14em;
  text-transform:uppercase;
  color:#1e3a5f;
  margin-bottom:7px;
}}
.kpi-value{{
  font-family:'DM Mono',monospace;
  font-size:28px;
  font-weight:500;
  line-height:1;
  color:#c8d8f0;
  margin-bottom:3px;
}}
.kpi.up   .kpi-value{{color:#00c896}}
.kpi.down .kpi-value{{color:#e05050}}
.kpi.warn .kpi-value{{color:#d4860a}}
.kpi-sub{{font-size:11px;color:#1e3a5f}}

/* ── Filters ── */
.filter-row{{
  display:flex;
  gap:10px;
  flex-wrap:wrap;
  align-items:center;
  margin-bottom:18px;
  padding:12px 14px;
  background:#0c1220;
  border:1px solid #131d2e;
  border-radius:10px;
}}
.filter-group{{display:flex;flex-direction:column;gap:3px}}
.filter-label{{
  font-family:'DM Mono',monospace;
  font-size:9px;
  letter-spacing:0.12em;
  text-transform:uppercase;
  color:#1e3a5f;
}}
.filter-row select{{
  background:#080c14;
  border:1px solid #1a2a44;
  color:#8a9bb5;
  border-radius:6px;
  padding:5px 10px;
  font-size:12px;
  font-family:'DM Sans',sans-serif;
  outline:none;
  cursor:pointer;
  min-width:130px;
}}
.filter-row select:focus{{border-color:#0055e0}}

/* ── Tabs ── */
.tabs{{display:flex;gap:4px;margin-bottom:14px;border-bottom:1px solid #131d2e;padding-bottom:0}}
.tab{{
  font-family:'DM Mono',monospace;
  font-size:11px;
  letter-spacing:0.04em;
  color:#2a3d5c;
  background:transparent;
  border:none;
  border-bottom:2px solid transparent;
  padding:8px 16px 10px;
  cursor:pointer;
  transition:color .15s,border-color .15s;
}}
.tab:hover{{color:#7a9abf}}
.tab.active{{color:#dce6f5;border-bottom-color:#0055e0}}

/* ── Panel / Card ── */
.panel{{display:none}}
.panel.active{{display:block}}
.card{{
  background:#0c1220;
  border:1px solid #131d2e;
  border-radius:10px;
  padding:16px 18px;
  margin-bottom:14px;
}}
.card-title{{
  font-family:'DM Mono',monospace;
  font-size:10px;
  letter-spacing:0.12em;
  text-transform:uppercase;
  color:#2a3d5c;
  margin-bottom:12px;
  padding-bottom:8px;
  border-bottom:1px solid #131d2e;
}}
.legend{{
  display:flex;gap:16px;flex-wrap:wrap;
  font-size:11px;color:#3a5070;
  margin-bottom:10px;
  font-family:'DM Mono',monospace;
}}
.leg{{display:flex;align-items:center;gap:5px}}
.leg-sq{{width:9px;height:9px;border-radius:2px;flex-shrink:0}}

/* ── Canvas wrapper ── */
.chart-box{{position:relative;width:100%}}

/* ── Table ── */
.tbl-wrap{{overflow-x:auto}}
table{{
  width:100%;
  border-collapse:collapse;
  font-size:12px;
  font-family:'DM Sans',sans-serif;
}}
thead th{{
  background:#080c14;
  color:#2a3d5c;
  font-family:'DM Mono',monospace;
  font-size:9px;
  letter-spacing:0.1em;
  text-transform:uppercase;
  padding:9px 11px;
  text-align:left;
  border-bottom:1px solid #131d2e;
  white-space:nowrap;
  position:sticky;top:0;
}}
tbody td{{
  padding:8px 11px;
  border-bottom:1px solid #0e1624;
  color:#7a8faa;
  white-space:nowrap;
}}
tbody tr:hover td{{background:#0e1828}}

/* ── Badges ── */
.badge{{
  display:inline-block;
  font-family:'DM Mono',monospace;
  font-size:10px;
  font-weight:500;
  padding:2px 8px;
  border-radius:4px;
}}
.badge.crit {{background:#2a0a0a;color:#e05050;border:1px solid #3d1010}}
.badge.warn {{background:#231500;color:#d4860a;border:1px solid #3d2500}}
.badge.ok   {{background:#0a1f12;color:#00c896;border:1px solid #0d3020}}
.badge.gray {{background:#111822;color:#3a5070;border:1px solid #1a2a44}}

/* ── Scrollbar ── */
::-webkit-scrollbar{{width:5px;height:5px}}
::-webkit-scrollbar-track{{background:#080c14}}
::-webkit-scrollbar-thumb{{background:#1a2a44;border-radius:3px}}
</style>
</head>
<body>

<div class="header">
  <span class="header-title">🔦 {feriado_nome}</span>
  <span class="header-period">{periodo_str}</span>
</div>

<div class="kpi-row" id="kpi-row"></div>

<div class="filter-row">
  <div class="filter-group">
    <span class="filter-label">Data</span>
    <select id="f-data"   onchange="render()"><option value="">Todas</option></select>
  </div>
  <div class="filter-group">
    <span class="filter-label">Rota</span>
    <select id="f-rota"   onchange="render()"><option value="">Todas</option></select>
  </div>
  <div class="filter-group">
    <span class="filter-label">Turno</span>
    <select id="f-turno"  onchange="render()">
      <option value="">Todos</option>
      <option>MANHA</option><option>TARDE</option><option>NOITE</option><option>MADRUGADA</option>
    </select>
  </div>
  <div class="filter-group">
    <span class="filter-label">Status</span>
    <select id="f-status" onchange="render()">
      <option value="">Todos</option>
      <option value="crit">Crítico</option>
      <option value="warn">Atenção</option>
      <option value="ok">Saudável</option>
    </select>
  </div>
  <div class="filter-group">
    <span class="filter-label">Antecedência</span>
    <select id="f-ant" onchange="render()"><option value="">Todas</option></select>
  </div>
</div>

<div class="tabs">
  <button class="tab active" onclick="showTab('lf',this)">LF Atual vs Projetado</button>
  <button class="tab" onclick="showTab('curva',this)">Curva por Antecedência</button>
  <button class="tab" onclick="showTab('preco',this)">Preço vs Base</button>
  <button class="tab" onclick="showTab('occ',this)">Ocupação</button>
  <button class="tab" onclick="showTab('tabela',this)">Tabela completa</button>
</div>

<!-- LF por eixo -->
<div id="panel-lf" class="panel active">
  <div class="card">
    <div class="card-title">lf atual vs lf projetado — por eixo</div>
    <div class="legend">
      <span class="leg"><span class="leg-sq" style="background:#0055e0"></span>LF Projetado 2026</span>
      <span class="leg"><span class="leg-sq" style="background:#00c896"></span>LF Atual</span>
    </div>
    <div class="chart-box" id="box-lf"><canvas id="chart-lf"></canvas></div>
  </div>
</div>

<!-- Curva por antecedência -->
<div id="panel-curva" class="panel">
  <div class="card">
    <div class="card-title">curva de antecedência — lf atual vs projetado (média dos eixos filtrados)</div>
    <div class="legend">
      <span class="leg"><span class="leg-sq" style="background:#0055e0;opacity:.6"></span>LF Projetado</span>
      <span class="leg"><span class="leg-sq" style="background:#00c896"></span>LF Atual</span>
    </div>
    <div class="chart-box" style="height:340px"><canvas id="chart-curva"></canvas></div>
  </div>
  <div class="card">
    <div class="card-title">curva de antecedência — preço praticado vs base (média dos eixos filtrados)</div>
    <div class="legend">
      <span class="leg"><span class="leg-sq" style="background:#3a5070;border:1px dashed #3a5070"></span>Preço Base</span>
      <span class="leg"><span class="leg-sq" style="background:#0055e0"></span>Preço Praticado</span>
    </div>
    <div class="chart-box" style="height:340px"><canvas id="chart-curva-preco"></canvas></div>
  </div>
</div>

<!-- Preço -->
<div id="panel-preco" class="panel">
  <div class="card">
    <div class="card-title">preço praticado vs preço base — por eixo</div>
    <div class="legend">
      <span class="leg"><span class="leg-sq" style="background:#1e3a5f"></span>Preço Base</span>
      <span class="leg"><span class="leg-sq" style="background:#0055e0"></span>Praticado</span>
      <span class="leg"><span class="leg-sq" style="background:#e05050;border:1px dashed #e05050"></span>Concorrência</span>
    </div>
    <div class="chart-box" id="box-preco"><canvas id="chart-preco"></canvas></div>
  </div>
</div>

<!-- Ocupação -->
<div id="panel-occ" class="panel">
  <div class="card">
    <div class="card-title">ocupação atual % — por eixo</div>
    <div class="legend">
      <span class="leg"><span class="leg-sq" style="background:#e05050"></span>&lt; 12%</span>
      <span class="leg"><span class="leg-sq" style="background:#d4860a"></span>12 – 20%</span>
      <span class="leg"><span class="leg-sq" style="background:#00c896"></span>&gt; 20%</span>
    </div>
    <div class="chart-box" id="box-occ"><canvas id="chart-occ"></canvas></div>
  </div>
</div>

<!-- Tabela -->
<div id="panel-tabela" class="panel">
  <div class="card">
    <div class="card-title">tabela completa</div>
    <div class="tbl-wrap">
      <table>
        <thead><tr>
          <th>Status</th><th>Rota</th><th>Sentido</th><th>Turno</th><th>Data</th><th>Ant.</th>
          <th>LF Proj</th><th>LF Atual</th><th>Ratio</th>
          <th>PAX</th><th>Cap.</th><th>Occ%</th>
          <th>Preço Base</th><th>Praticado</th><th>Mult.</th><th>CC</th>
        </tr></thead>
        <tbody id="tbody"></tbody>
      </table>
    </div>
  </div>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script>
const ALL = {data_json};

// ── Defaults globais do Chart.js ─────────────────────────────
Chart.defaults.color          = '#2a3d5c';
Chart.defaults.borderColor    = '#131d2e';
Chart.defaults.font.family    = 'DM Mono, monospace';
Chart.defaults.font.size      = 11;

// ── Helpers ──────────────────────────────────────────────────
const avg  = arr => arr.filter(v=>v!=null&&!isNaN(v)).length
                    ? arr.filter(v=>v!=null&&!isNaN(v)).reduce((a,b)=>a+b,0) / arr.filter(v=>v!=null&&!isNaN(v)).length
                    : null;

function classifica(ratio) {{
  if (ratio == null) return 'gray';
  if (ratio < 0.30)  return 'crit';
  if (ratio < 0.60)  return 'warn';
  return 'ok';
}}

function ratioColor(r) {{
  if (r == null) return '#1e3a5f';
  if (r < 0.30)  return '#e05050';
  if (r < 0.60)  return '#d4860a';
  return '#00c896';
}}

function badge(cls) {{
  const lbl = {{crit:'Crítico',warn:'Atenção',ok:'Saudável',gray:'Sem proj.'}};
  return `<span class="badge ${{cls}}">${{lbl[cls]||''}}</span>`;
}}

// ── Popula selects ───────────────────────────────────────────
const sel = id => document.getElementById(id);

[...new Set(ALL.map(d=>d.data))].sort().forEach(v=>{{
  const o=document.createElement('option'); o.value=v; o.textContent=v.slice(5); sel('f-data').appendChild(o);
}});
[...new Set(ALL.map(d=>d.rota_principal))].sort().forEach(v=>{{
  const o=document.createElement('option'); o.value=v; o.textContent=v; sel('f-rota').appendChild(o);
}});
[...new Set(ALL.map(d=>d.antecedencia).filter(v=>v!=null))].sort((a,b)=>a-b).forEach(v=>{{
  const o=document.createElement('option'); o.value=v; o.textContent='d='+v; sel('f-ant').appendChild(o);
}});

// ── Filtro ───────────────────────────────────────────────────
function filtered() {{
  const fD=sel('f-data').value, fR=sel('f-rota').value,
        fT=sel('f-turno').value, fS=sel('f-status').value,
        fA=sel('f-ant').value;
  return ALL.filter(d=>{{
    if(fD && d.data!==fD) return false;
    if(fR && d.rota_principal!==fR) return false;
    if(fT && d.turno!==fT) return false;
    if(fA && String(d.antecedencia)!==fA) return false;
    if(fS){{
      const r = d.lf_proj_2026>0 ? d.lf_atual/d.lf_proj_2026 : null;
      if(classifica(r)!==fS) return false;
    }}
    return true;
  }});
}}

// ── Agrupa por eixo ──────────────────────────────────────────
function byEixo(data) {{
  const m={{}};
  data.forEach(d=>{{
    const k=d.sentido||d.rota_principal;
    if(!m[k]) m[k]={{lp:[],la:[],pax:0,cap:0,base:[],prat:[],cc:[],mult:[]}};
    m[k].lp.push(d.lf_proj_2026); m[k].la.push(d.lf_atual);
    m[k].pax+=(d.pax||0); m[k].cap+=(d.capacidade_atual||0);
    if(d.preco_base!=null)      m[k].base.push(+d.preco_base);
    if(d.preco_praticado!=null) m[k].prat.push(+d.preco_praticado);
    if(d.price_cc!=null)        m[k].cc.push(+d.price_cc);
    if(d.mult_final!=null)      m[k].mult.push(d.mult_final);
  }});
  return Object.entries(m).map(([eixo,v])=>{{
    const lp=avg(v.lp), la=avg(v.la);
    const ratio=lp&&lp>0 ? la/lp : null;
    return {{
      eixo, lp, la, ratio,
      pax:v.pax, cap:v.cap,
      occ:v.cap?v.pax/v.cap:0,
      base:avg(v.base), prat:avg(v.prat), cc:avg(v.cc), mult:avg(v.mult),
    }};
  }}).sort((a,b)=>(a.ratio??0)-(b.ratio??0));
}}

// ── Agrupa por antecedência ──────────────────────────────────
function byAnt(data) {{
  const m={{}};
  data.forEach(d=>{{
    const k=d.antecedencia;
    if(k==null) return;
    if(!m[k]) m[k]={{lp:[],la:[],base:[],prat:[]}};
    m[k].lp.push(d.lf_proj_2026); m[k].la.push(d.lf_atual);
    if(d.preco_base!=null)      m[k].base.push(+d.preco_base);
    if(d.preco_praticado!=null) m[k].prat.push(+d.preco_praticado);
  }});
  return Object.entries(m)
    .map(([ant,v])=>({{'ant':+ant, lp:avg(v.lp), la:avg(v.la), base:avg(v.base), prat:avg(v.prat)}}))
    .sort((a,b)=>b.ant-a.ant);   // maior antecedência → esquerda
}}

// ── Chart registry ───────────────────────────────────────────
const CH={{}};
function mkChart(id, cfg){{
  if(CH[id]) CH[id].destroy();
  const el=document.getElementById(id);
  if(el) CH[id]=new Chart(el, cfg);
}}

// ── Render ───────────────────────────────────────────────────
function render() {{
  const data=filtered();
  const grp =byEixo(data);
  const ants=byAnt(data);

  // KPIs
  const criticos = grp.filter(r=>r.ratio!=null&&r.ratio<0.30).length;
  const atencao  = grp.filter(r=>r.ratio!=null&&r.ratio>=0.30&&r.ratio<0.60).length;
  const saudavel = grp.filter(r=>r.ratio!=null&&r.ratio>=0.60).length;
  const ratioMed = avg(grp.map(r=>r.ratio).filter(v=>v!=null));
  const kpiCls   = ratioMed==null?'neu':ratioMed>=0.60?'up':ratioMed>=0.30?'warn':'down';

  sel('kpi-row').innerHTML=`
    <div class="kpi ${{kpiCls}}">
      <div class="kpi-label">Ratio médio (lf_atual/proj)</div>
      <div class="kpi-value">${{ratioMed!=null?(ratioMed*100).toFixed(0)+'%':'–'}}</div>
      <div class="kpi-sub">${{grp.length}} eixos filtrados</div>
    </div>
    <div class="kpi ${{criticos>0?'down':'neu'}}">
      <div class="kpi-label">Críticos (&lt; 30% do proj)</div>
      <div class="kpi-value">${{criticos}}</div>
      <div class="kpi-sub">eixos abaixo do threshold</div>
    </div>
    <div class="kpi ${{atencao>0?'warn':'neu'}}">
      <div class="kpi-label">Atenção (30 – 60%)</div>
      <div class="kpi-value">${{atencao}}</div>
      <div class="kpi-sub">eixos em zona amarela</div>
    </div>
    <div class="kpi up">
      <div class="kpi-label">Saudáveis (≥ 60%)</div>
      <div class="kpi-value">${{saudavel}}</div>
      <div class="kpi-sub">eixos no target</div>
    </div>
  `;

  // ── Tab LF por eixo ──
  const h = Math.max(320, grp.length*32+80);
  sel('box-lf').style.height = h+'px';
  mkChart('chart-lf',{{
    type:'bar',
    data:{{
      labels: grp.map(r=>r.eixo),
      datasets:[
        {{
          label:'LF Projetado',
          data: grp.map(r=>r.lp!=null?+(r.lp*100).toFixed(1):0),
          backgroundColor:'rgba(0,85,224,0.55)',
          borderRadius:3,
        }},
        {{
          label:'LF Atual',
          data: grp.map(r=>r.la!=null?+(r.la*100).toFixed(1):0),
          backgroundColor: grp.map(r=>ratioColor(r.ratio)),
          borderRadius:3,
        }},
      ]
    }},
    options:{{
      indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{{
        legend:{{display:false}},
        tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+c.parsed.x.toFixed(1)+'%'}}}}
      }},
      scales:{{
        x:{{ticks:{{callback:v=>v+'%'}}, grid:{{color:'#131d2e'}}}},
        y:{{ticks:{{font:{{size:11}}}}, grid:{{display:false}}}}
      }}
    }}
  }});

  // ── Tab Curva LF por antecedência ──
  mkChart('chart-curva',{{
    type:'line',
    data:{{
      labels: ants.map(a=>a.ant),
      datasets:[
        {{
          label:'LF Projetado',
          data: ants.map(a=>a.lp!=null?+(a.lp*100).toFixed(2):null),
          borderColor:'rgba(0,85,224,0.5)',
          backgroundColor:'rgba(0,85,224,0.06)',
          borderWidth:1.5,
          borderDash:[5,4],
          pointRadius:0,
          fill:false,
          tension:0.3,
        }},
        {{
          label:'LF Atual',
          data: ants.map(a=>a.la!=null?+(a.la*100).toFixed(2):null),
          borderColor:'#00c896',
          backgroundColor:'rgba(0,200,150,0.07)',
          borderWidth:2.5,
          pointRadius:4,
          pointBackgroundColor: ants.map(a=>{{
            if(a.la==null||a.lp==null) return '#1e3a5f';
            return a.la>=a.lp ? '#00c896' : '#e05050';
          }}),
          pointBorderWidth:0,
          fill:false,
          tension:0.3,
        }},
      ]
    }},
    options:{{
      responsive:true, maintainAspectRatio:false,
      spanGaps:true,
      plugins:{{
        legend:{{display:false}},
        tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+c.parsed.y?.toFixed(1)+'%'}}}}
      }},
      scales:{{
        x:{{
          reverse:false,
          title:{{display:true,text:'dias de antecedência (maior → menor)',color:'#1e3a5f',font:{{size:10}}}},
          ticks:{{maxTicksLimit:20}},
          grid:{{color:'#131d2e'}}
        }},
        y:{{
          title:{{display:true,text:'Load Factor',color:'#1e3a5f',font:{{size:10}}}},
          ticks:{{callback:v=>v+'%'}},
          grid:{{color:'#131d2e'}}
        }}
      }}
    }}
  }});

  // ── Tab Curva Preço por antecedência ──
  mkChart('chart-curva-preco',{{
    type:'line',
    data:{{
      labels: ants.map(a=>a.ant),
      datasets:[
        {{
          label:'Preço Base',
          data: ants.map(a=>a.base!=null?+a.base.toFixed(0):null),
          borderColor:'rgba(58,80,112,0.8)',
          borderWidth:1.5,
          borderDash:[5,4],
          pointRadius:0,
          fill:false,
          tension:0.3,
        }},
        {{
          label:'Preço Praticado',
          data: ants.map(a=>a.prat!=null?+a.prat.toFixed(0):null),
          borderColor:'#0055e0',
          backgroundColor:'rgba(0,85,224,0.05)',
          borderWidth:2.5,
          pointRadius:4,
          pointBackgroundColor:'#0055e0',
          pointBorderWidth:0,
          fill:false,
          tension:0.3,
        }},
      ]
    }},
    options:{{
      responsive:true, maintainAspectRatio:false,
      spanGaps:true,
      plugins:{{
        legend:{{display:false}},
        tooltip:{{callbacks:{{label:c=>c.dataset.label+': R$ '+c.parsed.y?.toFixed(0)}}}}
      }},
      scales:{{
        x:{{
          title:{{display:true,text:'dias de antecedência',color:'#1e3a5f',font:{{size:10}}}},
          ticks:{{maxTicksLimit:20}},
          grid:{{color:'#131d2e'}}
        }},
        y:{{
          title:{{display:true,text:'R$',color:'#1e3a5f',font:{{size:10}}}},
          ticks:{{callback:v=>'R$'+v}},
          grid:{{color:'#131d2e'}}
        }}
      }}
    }}
  }});

  // ── Tab Preço por eixo ──
  const grpP=[...grp].sort((a,b)=>(b.prat||0)-(a.prat||0));
  const hp=Math.max(320,grpP.length*32+80);
  sel('box-preco').style.height=hp+'px';
  mkChart('chart-preco',{{
    type:'bar',
    data:{{
      labels:grpP.map(r=>r.eixo),
      datasets:[
        {{
          label:'Preço Base',
          data:grpP.map(r=>r.base!=null?+r.base.toFixed(0):0),
          backgroundColor:'rgba(30,58,95,0.7)',
          borderRadius:3,
        }},
        {{
          label:'Praticado',
          data:grpP.map(r=>r.prat!=null?+r.prat.toFixed(0):0),
          backgroundColor:'rgba(0,85,224,0.75)',
          borderRadius:3,
        }},
        {{
          label:'CC',
          data:grpP.map(r=>r.cc!=null?+r.cc.toFixed(0):0),
          backgroundColor:'rgba(224,80,80,0.55)',
          borderRadius:3,
        }},
      ]
    }},
    options:{{
      indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{{
        legend:{{display:false}},
        tooltip:{{callbacks:{{label:c=>c.dataset.label+': R$ '+c.parsed.x.toFixed(0)}}}}
      }},
      scales:{{
        x:{{ticks:{{callback:v=>'R$'+v}}, grid:{{color:'#131d2e'}}}},
        y:{{ticks:{{font:{{size:11}}}}, grid:{{display:false}}}}
      }}
    }}
  }});

  // ── Tab Ocupação ──
  const grpO=[...grp].sort((a,b)=>b.occ-a.occ);
  const ho=Math.max(320,grpO.length*32+80);
  sel('box-occ').style.height=ho+'px';
  mkChart('chart-occ',{{
    type:'bar',
    data:{{
      labels:grpO.map(r=>r.eixo),
      datasets:[{{
        label:'Occ %',
        data:grpO.map(r=>+(r.occ*100).toFixed(1)),
        backgroundColor:grpO.map(r=>r.occ<0.12?'#e05050':r.occ<0.20?'#d4860a':'#00c896'),
        borderRadius:3,
      }}]
    }},
    options:{{
      indexAxis:'y', responsive:true, maintainAspectRatio:false,
      plugins:{{
        legend:{{display:false}},
        tooltip:{{callbacks:{{label:c=>c.parsed.x.toFixed(1)+'%'}}}}
      }},
      scales:{{
        x:{{max:100, ticks:{{callback:v=>v+'%'}}, grid:{{color:'#131d2e'}}}},
        y:{{ticks:{{font:{{size:11}}}}, grid:{{display:false}}}}
      }}
    }}
  }});

  // ── Tabela ──
  sel('tbody').innerHTML = data.map(d=>{{
    const ratio=d.lf_proj_2026>0 ? d.lf_atual/d.lf_proj_2026 : null;
    const cls  =classifica(ratio);
    const pct  =v=>v!=null?(v*100).toFixed(1)+'%':'–';
    const brl  =v=>v!=null?'R$ '+(+v).toFixed(0):'–';
    const num  =v=>v!=null?v:'–';
    const ratioStyle=`color:${{ratioColor(ratio)}};font-weight:600;font-family:'DM Mono',monospace`;
    return `<tr>
      <td>${{badge(cls)}}</td>
      <td style="color:#c8d8f0;font-weight:500">${{d.rota_principal}}</td>
      <td>${{d.sentido||'–'}}</td>
      <td>${{d.turno||'–'}}</td>
      <td style="font-family:'DM Mono',monospace">${{d.data||'–'}}</td>
      <td style="font-family:'DM Mono',monospace">${{d.antecedencia??'–'}}</td>
      <td style="font-family:'DM Mono',monospace">${{pct(d.lf_proj_2026)}}</td>
      <td style="font-family:'DM Mono',monospace">${{pct(d.lf_atual)}}</td>
      <td style="${{ratioStyle}}">${{ratio!=null?(ratio*100).toFixed(1)+'%':'–'}}</td>
      <td>${{num(d.pax)}}</td>
      <td>${{num(d.capacidade_atual)}}</td>
      <td style="font-family:'DM Mono',monospace">${{pct(d.occ_atual)}}</td>
      <td style="font-family:'DM Mono',monospace">${{brl(d.preco_base)}}</td>
      <td style="font-family:'DM Mono',monospace">${{brl(d.preco_praticado)}}</td>
      <td style="font-family:'DM Mono',monospace">${{d.mult_final!=null?d.mult_final.toFixed(2)+'×':'–'}}</td>
      <td style="font-family:'DM Mono',monospace">${{brl(d.price_cc)}}</td>
    </tr>`;
  }}).join('');
}}

function showTab(name, el) {{
  document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.getElementById('panel-'+name).classList.add('active');
  el.classList.add('active');
  setTimeout(render,30);
}}

render();
</script>
</body>
</html>
"""

st.components.v1.html(html, height=1200, scrolling=True)
