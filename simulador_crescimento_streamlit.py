# -*- coding: utf-8 -*-
"""
Simulador e ganhos e perdas do Aviator
--------------------------------------
- Duas entradas por dia (sem rótulos A/B; apenas dois campos sob cada dia).
- Dias exibidos como: SEG, TER, QUA, QUI, SEX, SÁB, DOM.
- Tema visual escuro com detalhes em vermelho (estilo Aviator).
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Simulador e ganhos e perdas do Aviator", page_icon="✈️", layout="wide")

# ----------------------
# Estilo Aviator (CSS)
# ----------------------
st.markdown("""
<style>
/* Fonte e base escura */
html, body, [data-testid="stAppViewContainer"] {
  background: radial-gradient(1200px 600px at 10% 10%, #1b1b1f 0%, #0f0f12 60%, #0b0b0d 100%) !important;
  color: #f0f2f6 !important;
  font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji';
}
/* Sidebar */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #111115 0%, #0b0b0d 100%) !important;
  border-right: 1px solid rgba(255, 0, 0, 0.15);
}
/* Título */
h1 {
  font-weight: 800 !important;
  letter-spacing: 0.3px;
  color: #ff2d2d !important;
  text-shadow: 0 0 18px rgba(255,45,45,0.25);
}
/* Subtítulos */
h2, h3 {
  color: #ff6961 !important;
}
/* Cards de métricas */
[data-testid="stMetric"] {
  border-radius: 14px;
  padding: 8px 12px;
  background: linear-gradient(180deg, rgba(255,45,45,0.10) 0%, rgba(255,45,45,0.02) 100%);
  border: 1px solid rgba(255,45,45,0.25);
}
/* Botões */
.stButton>button, [data-testid="stDownloadButton"]>button {
  background: #ff2d2d !important;
  color: white !important;
  border: 0 !important;
  border-radius: 12px !important;
  box-shadow: 0 6px 16px rgba(255,45,45,0.28);
}
/* Inputs numéricos */
[data-baseweb="input"] input {
  color: #f0f2f6 !important;
}
/* Dataframe */
[data-testid="stDataFrame"] {
  border: 1px solid rgba(255,45,45,0.22);
  border-radius: 12px;
  overflow: hidden;
}
/* Legendas pequenas */
.small-note { color: #b8bcc6; font-size: 12px; margin-top: 4px; }
.day-chip {
  display:inline-block; padding:6px 10px; border:1px solid rgba(255,45,45,0.35);
  border-radius: 999px; margin-bottom: 6px; font-weight: 700; color:#ffd6d6; background: rgba(255,45,45,0.08);
}
</style>
""", unsafe_allow_html=True)

st.title("Simulador e ganhos e perdas do Aviator")
st.caption("Defina duas **percentagens diárias** (positivas ou negativas) para cada dia. Sem ciclos fixos.")

with st.sidebar:
    st.header("Parâmetros gerais ✈️")
    capital_inicial = st.number_input("Capital inicial (R$)", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
    semanas = st.number_input("Quantas semanas?", min_value=1, value=4, step=1)
    dias_uteis_apenas = st.checkbox("Apenas dias úteis (SEG–SEX)?", value=True)
    reiniciar_a_cada_semana = st.checkbox("Reiniciar capital a cada semana?", value=False, help="Se ligado, cada semana começa com o capital inicial. Se desligado, o capital é composto ao longo de todas as semanas.")
    mostrar_grafico = st.checkbox("Mostrar gráfico de evolução", value=True)
    st.markdown('<div class="small-note">Use vírgula ou ponto como separador decimal. Ex.: 7,12 ou 7.12.</div>', unsafe_allow_html=True)

# Dias abreviados
DAYS_ABBR = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]

st.subheader("Percentuais por dia")
st.write("Preencha **dois campos por dia**. Deixe 0 se não quiser usar o segundo.")

# Inputs: duas entradas numéricas por dia sem rótulos, apenas sob o chip do dia
percentuais_A = []
percentuais_B = []
cols = st.columns(7)
for i, day in enumerate(DAYS_ABBR):
    with cols[i]:
        st.markdown(f'<span class="day-chip">{day}</span>', unsafe_allow_html=True)
        disabled = bool(dias_uteis_apenas and i >= 5)
        a = st.number_input("", value=0.0, step=0.1, format="%.2f", key=f"pctA_{i}", disabled=disabled, label_visibility="collapsed")
        b = st.number_input("", value=0.0, step=0.1, format="%.2f", key=f"pctB_{i}", disabled=disabled, label_visibility="collapsed")
        percentuais_A.append(0.0 if disabled else a)
        percentuais_B.append(0.0 if disabled else b)

# --- Simulação ---
registros = []
capital = capital_inicial
dia_global = 0

for semana in range(1, int(semanas) + 1):
    if reiniciar_a_cada_semana and semana > 1:
        capital = capital_inicial
    for dia_semana in range(7):
        if dias_uteis_apenas and dia_semana >= 5:
            continue
        a = percentuais_A[dia_semana]
        b = percentuais_B[dia_semana]
        fator = (1 + a/100.0) * (1 + b/100.0)
        pct_total = (fator - 1) * 100.0
        delta = capital * (pct_total / 100.0)
        capital_final = capital + delta
        registros.append({
            "Dia #": dia_global + 1,
            "Dia": DAYS_ABBR[dia_semana],
            "% 1": a,
            "% 2": b,
            "% do dia (total)": pct_total,
            "Variação (R$)": delta,
            "Capital (início do dia)": capital,
            "Capital (fim do dia)": capital_final,
        })
        capital = capital_final
        dia_global += 1

df = pd.DataFrame(registros)

# --- Resultados ---
st.subheader("Resultados")
col1, col2, col3 = st.columns(3)
total_dias = len(df)
capital_final_total = df["Capital (fim do dia)"].iloc[-1] if total_dias > 0 else capital_inicial
retorno_acumulado_pct = ((capital_final_total / capital_inicial - 1) * 100.0) if capital_inicial > 0 else 0.0

col1.metric("Dias simulados", f"{total_dias}")
col2.metric("Capital final", f"R$ {capital_final_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col3.metric("Retorno acumulado", f"{retorno_acumulado_pct:.2f}%")

# Cores nas linhas: verde (delta > 0), vermelho (delta < 0)
def color_rows(row):
    delta = row.get("Variação (R$)", 0.0)
    if delta > 0:
        return ["background-color: #16381b; color: #9be7a3;"] * len(row)  # verde escuro + texto verde claro
    elif delta < 0:
        return ["background-color: #3a0f12; color: #ff9aa2;"] * len(row)  # vermelho escuro + texto rosa claro
    else:
        return [""] * len(row)

if total_dias > 0:
    styled = (df.style
              .apply(color_rows, axis=1)
              .format({
                  "% 1": "{:.2f}%",
                  "% 2": "{:.2f}%",
                  "% do dia (total)": "{:.2f}%",
                  "Variação (R$)": "R$ {:,.2f}",
                  "Capital (início do dia)": "R$ {:,.2f}",
                  "Capital (fim do dia)": "R$ {:,.2f}",
              }))
    st.dataframe(styled, use_container_width=True)
else:
    st.info("Configure os percentuais e as semanas para visualizar a tabela.")

# --- Gráfico ---
if mostrar_grafico and total_dias > 0:
    st.subheader("Evolução do capital")
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(df["Dia #"], df["Capital (fim do dia)"], linewidth=2.0, color="#ff2d2d")
    ax.set_facecolor("#0f0f12")
    fig.patch.set_facecolor("#0f0f12")
    ax.tick_params(colors="#f0f2f6")
    ax.spines['bottom'].set_color("#f0f2f6")
    ax.spines['left'].set_color("#f0f2f6")
    ax.set_xlabel("Dia", color="#f0f2f6")
    ax.set_ylabel("Capital (R$)", color="#f0f2f6")
    ax.set_title("Evolução do capital", color="#ff6961")
    st.pyplot(fig)

st.caption("ⓘ Este simulador não é recomendação financeira. Use para estudos e planejamento.")
