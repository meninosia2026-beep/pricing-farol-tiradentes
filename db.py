"""
db.py — Databricks SQL connection + query runner
Versão: Databricks Apps (autenticação nativa, sem .env)
"""
import os
import streamlit as st
import pandas as pd
from databricks import sql

DATABRICKS_HOST      = os.environ.get("DATABRICKS_HOST", "")
DATABRICKS_HTTP_PATH = os.environ.get("DATABRICKS_HTTP_PATH", "")
DATABRICKS_TOKEN     = os.environ.get("DATABRICKS_TOKEN", "")


def _get_connection():
    return sql.connect(
        server_hostname=DATABRICKS_HOST,
        http_path=DATABRICKS_HTTP_PATH,
        access_token=DATABRICKS_TOKEN,
    )


@st.cache_data(ttl=300, show_spinner=False)
def run_query(query: str) -> pd.DataFrame:
    with _get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query)
            cols = [d[0] for d in cursor.description]
            rows = cursor.fetchall()
    return pd.DataFrame(rows, columns=cols)


QUERY_BASE_CONSULTA = """
SELECT
  data, turno, rota_principal, sentido, antecedencia, dia_da_semana,
  pax, capacidade_atual, occ_atual, vagas_restantes,
  lf_proj_2026, lf_atual, ratio_vs_proj,
  tkm_atual, tkm_comp,
  preco_base, preco_est_draft, preco_est_novo, preco_praticado,
  mult_final, mult_flutuacao, price_cc
FROM base_consulta
WHERE data BETWEEN date('{data_ini}') AND date('{data_fim}')
"""

QUERY_ALERTAS = """
SELECT
  data, turno, rota_principal, sentido, antecedencia,
  occ_atual, lf_atual, lf_proj_2026, ratio_vs_proj,
  mult_final, mult_flutuacao, preco_praticado, price_cc,
  vagas_restantes, capacidade_atual
FROM base_consulta
WHERE ratio_vs_proj > {ratio_min}
  AND mult_final < {mult_max}
  AND occ_atual > {occ_min}
  AND data BETWEEN date('{data_ini}') AND date('{data_fim}')
ORDER BY ratio_vs_proj DESC
"""


def load_base(data_ini: str, data_fim: str) -> pd.DataFrame:
    return run_query(QUERY_BASE_CONSULTA.format(data_ini=data_ini, data_fim=data_fim))


def load_alertas(
    data_ini: str,
    data_fim: str,
    ratio_min: float = 1.30,
    mult_max: float = 1.50,
    occ_min: float = 0.33,
) -> pd.DataFrame:
    return run_query(
        QUERY_ALERTAS.format(
            data_ini=data_ini,
            data_fim=data_fim,
            ratio_min=ratio_min,
            mult_max=mult_max,
            occ_min=occ_min,
        )
    )
