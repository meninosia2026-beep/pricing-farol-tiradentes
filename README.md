# 🚌 Pricing Farol — Tiradentes 2026

Dashboard Streamlit para monitoramento de pricing em feriados.  
Conecta direto ao Databricks SQL e executa as queries do seu notebook de forma automática.

---

## 🚀 Setup rápido

### 1. Clonar / copiar os arquivos

```
pricing_dashboard/
├── app.py           ← App principal Streamlit
├── db.py            ← Conexão Databricks + queries
├── logic.py         ← Lógica de farol e scores
├── requirements.txt
├── .env             ← Credenciais (NÃO versionar!)
└── .env.example
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar credenciais

Copie o `.env.example` para `.env` e preencha:

```bash
cp .env.example .env
```

```env
DATABRICKS_HOST=adb-XXXXXXXXXXXXXXXX.X.azuredatabricks.net
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/XXXXXXXXXXXXXXXX
DATABRICKS_TOKEN=dapiXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Como encontrar esses valores no Databricks:**
- Vá em **SQL Warehouses** → selecione seu warehouse
- Aba **Connection details**
- Copie `Server hostname` → `DATABRICKS_HOST`
- Copie `HTTP Path` → `DATABRICKS_HTTP_PATH`
- Em **Settings → Developer → Access Tokens** gere um token → `DATABRICKS_TOKEN`

### 4. Rodar

```bash
streamlit run app.py
```

O app abre em `http://localhost:8501`

---

## 📊 O que o dashboard faz

### 🚨 Alertas (aba principal)
Rotas onde **demanda está acima do projetado** E o **multiplicador ainda está baixo** — oportunidade de pricing que não foi capturada.

- **Parâmetros configuráveis** na sidebar:
  - `Ratio mínimo` — quanto acima do proj considera alerta (default 1.30×)
  - `Mult máximo` — limite do mult que considera "baixo" (default 1.50×)
  - `Occ mínima` — filtro para remover ruído (default 33%)

### 🗺️ Farol por Rota
- Cards coloridos com status de cada rota (🔴🟡🟢)
- Heatmap de ratio por rota × turno (top 25 rotas por ratio médio)

### 📈 Curvas & Demanda
- Curva de booking: **LF Atual vs LF Projetado 2026** por antecedência
- Marcação de pontos onde demanda ultrapassa 130% do projetado
- Gráfico de ratio por antecedência (barras coloridas por severity)

### 💰 Preço vs Concorrência
- Gap percentual do nosso preço vs concorrência por sentido
- Série temporal de preço praticado vs CC por sentido
- Verde = mais barato que CC, vermelho = mais caro

---

## ⚙️ Lógica do Farol

| Status | Condição |
|--------|----------|
| 🔴 CRÍTICO | `ratio_vs_proj > 1.30` E `mult_final < 1.50` **OU** `occ > 85%` com `antecedência > 7d` |
| 🟡 ATENÇÃO | `ratio_vs_proj > 1.15` E `mult_final < 1.30` **OU** `price_cc < preco_praticado × 0.90` |
| 🟢 OK | Todo o resto |

---

## 🔄 Automatização

### Cache
O app tem **cache de 5 minutos** automático (`@st.cache_data(ttl=300)`).  
Para forçar refresh, clique no botão **⟳ Atualizar dados** na sidebar.

### Agendamento (opcional)
Para rodar em servidor e atualizar automaticamente:

```bash
# Com streamlit community cloud: deploy direto do GitHub
# Com servidor próprio:
nohup streamlit run app.py --server.port 8501 &
```

---

## 🛠️ Customização

### Ajustar datas do feriado
Em `db.py`, as queries já são parametrizadas por `data_ini` e `data_fim` via sidebar.

### Mudar lógica de farol
Edite a função `classify_farol()` em `logic.py`.

### Adicionar novas métricas ao base_consulta
Edite `QUERY_BASE_CONSULTA` em `db.py`.

---

## 📦 Dependências principais

| Pacote | Uso |
|--------|-----|
| `streamlit` | Framework do dashboard |
| `databricks-sql-connector` | Conexão Databricks SQL |
| `pandas` | Manipulação de dados |
| `plotly` | Gráficos interativos |
| `python-dotenv` | Gerenciamento de credenciais |
