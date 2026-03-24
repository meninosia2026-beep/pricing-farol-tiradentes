"""
logic.py — Classificações, scores e derivados do base_consulta
"""
import pandas as pd
import numpy as np


# ──────────────────────────────────────────────────────────────
# 1. Farol por rota
# ──────────────────────────────────────────────────────────────

def classify_farol(row: pd.Series) -> dict:
    """
    Retorna dict com status, cor e motivo para uma linha do base_consulta.

    Lógica:
      🔴 CRÍTICO   — ratio_vs_proj > 1.3  E  mult_final < 1.5  (demanda alta, mult baixo)
                   — occ_atual > 0.85  E  antecedencia > 7     (muito cheio ainda cedo)
      🟡 ATENÇÃO   — ratio_vs_proj > 1.15 E mult_final < 1.3
                   — price_cc < preco_praticado * 0.9           (mais barato que CC)
      🟢 OK        — todo o resto
    """
    ratio = row.get("ratio_vs_proj", 0) or 0
    mult  = row.get("mult_final", 1)    or 1
    occ   = row.get("occ_atual", 0)     or 0
    ant   = row.get("antecedencia", 99) or 99
    preco = row.get("preco_praticado", None)
    pcc   = row.get("price_cc", None)

    motivos = []

    # Demanda alta, multiplicador subestimado
    if ratio > 1.30 and mult < 1.50:
        motivos.append(f"Demanda +{round((ratio-1)*100)}% acima do proj. | mult {mult:.2f}")

    # Lotação antecipada
    if occ > 0.85 and ant > 7:
        motivos.append(f"Occ {round(occ*100)}% com {ant}d de antecedência")

    if motivos:
        return {"status": "🔴 CRÍTICO", "cor": "#FF4136", "nivel": 2, "motivos": " · ".join(motivos)}

    if (ratio > 1.15 and mult < 1.30):
        motivos.append(f"Demanda +{round((ratio-1)*100)}% acima do proj. | mult {mult:.2f}")

    if preco and pcc and pcc < preco * 0.90:
        motivos.append(f"CC {round(pcc,0):.0f} < nosso {round(preco,0):.0f} (−{round((1-pcc/preco)*100)}%)")

    if motivos:
        return {"status": "🟡 ATENÇÃO", "cor": "#FFDC00", "nivel": 1, "motivos": " · ".join(motivos)}

    return {"status": "🟢 OK", "cor": "#2ECC40", "nivel": 0, "motivos": "—"}


def enrich_farol(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona colunas de farol ao DataFrame."""
    if df.empty:
        return df
    farois = df.apply(classify_farol, axis=1, result_type="expand")
    return pd.concat([df, farois], axis=1)


# ──────────────────────────────────────────────────────────────
# 2. Resumo por rota (para o painel farol)
# ──────────────────────────────────────────────────────────────

def resumo_por_rota(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega por rota_principal: pega o pior farol do dia,
    métricas médias e counts.
    """
    if df.empty:
        return pd.DataFrame()

    df = enrich_farol(df)

    agg = (
        df.groupby("rota_principal")
        .agg(
            nivel_max       = ("nivel", "max"),
            ratio_medio     = ("ratio_vs_proj", "mean"),
            lf_atual_medio  = ("lf_atual", "mean"),
            lf_proj_medio   = ("lf_proj_2026", "mean"),
            mult_medio      = ("mult_final", "mean"),
            occ_medio       = ("occ_atual", "mean"),
            price_cc_medio  = ("price_cc", "mean"),
            preco_prat_medio= ("preco_praticado", "mean"),
            n_sentidos      = ("sentido", "nunique"),
            n_linhas        = ("rota_principal", "count"),
        )
        .reset_index()
    )

    nivel_map = {0: "🟢 OK", 1: "🟡 ATENÇÃO", 2: "🔴 CRÍTICO"}
    cor_map   = {0: "#2ECC40", 1: "#FFDC00", 2: "#FF4136"}
    agg["status"] = agg["nivel_max"].map(nivel_map)
    agg["cor"]    = agg["nivel_max"].map(cor_map)

    return agg.sort_values("nivel_max", ascending=False)


# ──────────────────────────────────────────────────────────────
# 3. Alertas formatados
# ──────────────────────────────────────────────────────────────

def fmt_pct(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{v*100:.1f}%"

def fmt_brl(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"R$ {v:.2f}"

def fmt_x(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{v:.2f}×"
