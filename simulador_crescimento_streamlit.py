# -*- coding: utf-8 -*-
"""
Simulador de Ganhos e Perdas do Aviator
---------------------------------------
Agora com campos de data usando st.date_input.
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta

st.set_page_config(page_title="Simulador de Ganhos e Perdas do Aviator", page_icon="✈️", layout="wide")

# ----------------------
# Estilo Aviator (CSS)
# ----------------------
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
  background: radial-gradient(1200px 600px at 10% 10%, #1b1b1f 0%, #0f0f12 60%, #0b0b0d 100%) !important;
  color: #f0f2f6 !important;
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #111115 0%, #0b0b0d 100%) !important;
  border-right: 1px solid rgba(255, 0, 0, 0.15);
}
h1 { font-weight: 800 !important; color: #ff2d2d !important; text-shadow: 0 0 18px rgba(255,45,45,0.25); }
h2, h3 { color: #ff6961 !important; }
</style>
""", unsafe_allow_html=True)

st.title("Simulador de Ganhos e Perdas do Aviator")

with st.sidebar:
    st.header("Parâmetros gerais ✈️")
    banca_inicial = st.number_input("Banca inicial (R$)", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
    hoje = date.today()
    data_inicio = st.date_input("Data de início da operação", value=hoje, format="DD/MM/YYYY")
    data_fim = st.date_input("Data final", value=None, format="DD/MM/YYYY")

# Dias abreviados
DAYS_ABBR = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]

st.subheader("Percentuais por dia")
st.write("Preencha os campos dos dias de acordo com a simulação que queria fazer. "
         "Deixe 0 caso não queira simular o operação naquele dia. "
         "Caso queria simular apenas uma operação no dia, deixe 0 o segundo campo.")

percentuais_A = []
percentuais_B = []
cols = st.columns(7)
for i, day in enumerate(DAYS_ABBR):
    with cols[i]:
        st.markdown(f"**{day}**")
        a = st.number_input("", value=0.0, step=0.1, format="%.2f", key=f"pctA_{i}", label_visibility="collapsed")
        b = st.number_input("", value=0.0, step=0.1, format="%.2f", key=f"pctB_{i}", label_visibility="collapsed")
        percentuais_A.append(a)
        percentuais_B.append(b)

# Validação de datas
if data_fim is None:
    st.info("Informe a **Data final** para rodar a simulação.")
    st.stop()
if data_fim < data_inicio:
    st.error("A **Data final** deve ser igual ou posterior à **Data de início da operação**.")
    st.stop()

datas_periodo = pd.date_range(start=data_inicio, end=data_fim, freq="D")

# --- Simulação ---
registros = []
capital = banca_inicial
for current_date in datas_periodo:
    weekday = int(current_date.weekday())
    a = percentuais_A[weekday]
    b = percentuais_B[weekday]
    fator = (1 + a/100.0) * (1 + b/100.0)
    pct_total = (fator - 1) * 100.0
    delta = capital * (pct_total / 100.0)
    capital_final = capital + delta
    registros.append({
        "Data": current_date.strftime("%d/%m/%Y"),
        "Dia": DAYS_ABBR[weekday],
        "% 1": a,
        "% 2": b,
        "% do dia (total)": pct_total,
        "Variação (R$)": delta,
        "Capital (início do dia)": capital,
        "Capital (fim do dia)": capital_final,
    })
    capital = capital_final

df = pd.DataFrame(registros)

# Resultados principais
st.subheader("Resultados")
if len(df) > 0:
    banca_final_total = df["Capital (fim do dia)"].iloc[-1]
    retorno_acumulado_pct = ((banca_final_total / banca_inicial - 1) * 100.0) if banca_inicial > 0 else 0.0
    lucro_prejuizo = banca_final_total - banca_inicial

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Dias simulados", f"{len(df)}")
    c2.metric("Banca final", f"R$ {banca_final_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    c3.metric("Retorno acumulado", f"{retorno_acumulado_pct:.2f}%")
    lp_fmt = f"R$ {lucro_prejuizo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    lp_color = "green" if lucro_prejuizo >= 0 else "red"
    c4.markdown(f"<span style='color:{lp_color};font-weight:bold'>{lp_fmt}</span>", unsafe_allow_html=True)

    st.markdown("#### Resumo por período")
    dias_pos = int((df["Variação (R$)"] > 0).sum())
    dias_neg = int((df["Variação (R$)"] < 0).sum())
    st.write(f"Dias positivos: {dias_pos} | Dias negativos: {dias_neg}")

    st.subheader("Tabela de operações")
    st.dataframe(df, use_container_width=True)

    st.subheader("Evolução da Banca")
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(pd.to_datetime(df["Data"], format="%d/%m/%Y"), df["Capital (fim do dia)"], linewidth=2.0, color="#ff2d2d")
    ax.set_facecolor("#0f0f12")
    fig.patch.set_facecolor("#0f0f12")
    ax.tick_params(colors="#f0f2f6")
    ax.spines['bottom'].set_color("#f0f2f6")
    ax.spines['left'].set_color("#f0f2f6")
    ax.set_xlabel("Data", color="#f0f2f6")
    ax.set_ylabel("Banca (R$)", color="#f0f2f6")
    ax.set_title("Evolução da Banca", color="#ff6961")
    fig.autofmt_xdate()
    st.pyplot(fig)
else:
    st.info("Defina o período e os percentuais para visualizar resultados.")
