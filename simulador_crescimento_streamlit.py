# -*- coding: utf-8 -*-
"""
Simulador de Ganhos e Perdas do Aviator
---------------------------------------
Agora com calendário (date_input) em Português do Brasil.
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta
import locale
import os

# Forçar locale pt-BR (funciona em Linux/Mac/Windows com tentativas em cascata)
_LOCALE_CANDIDATES = ["pt_BR.UTF-8", "pt_BR.utf8", "pt_BR", "Portuguese_Brazil.1252"]
_applied_locale = None
for loc in _LOCALE_CANDIDATES:
    try:
        locale.setlocale(locale.LC_TIME, loc)
        os.environ["LC_TIME"] = loc  # ajuda algumas distros
        _applied_locale = loc
        break
    except Exception:
        continue
# (Opcional) poderíamos exibir um aviso se não aplicar, mas evitamos poluir a UI.

st.set_page_config(page_title="Simulador de Ganhos e Perdas do Aviator", page_icon="✈️", layout="wide")

st.title("Simulador de Ganhos e Perdas do Aviator")

with st.sidebar:
    st.header("Parâmetros gerais ✈️")
    banca_inicial = st.number_input("Banca inicial (R$)", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
    hoje = date.today()
    # Campos de data com calendário pt-BR; usuário pode digitar 21082025 -> 21/08/2025
    data_inicio = st.date_input("Data de início da operação", value=hoje, format="DD/MM/YYYY")
    data_fim = st.date_input("Data final", value=None, format="DD/MM/YYYY")

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

# Período contínuo
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
    # Colorir linhas verde/vermelho
    def color_rows(row):
        delta = row.get("Variação (R$)", 0.0)
        if delta > 0:
            return ["background-color: #16381b; color: #9be7a3;"] * len(row)
        elif delta < 0:
            return ["background-color: #3a0f12; color: #ff9aa2;"] * len(row)
        else:
            return [""] * len(row)
    table_styles = [
        {'selector': 'th.col_heading', 'props': [('text-align', 'center')]},
        {'selector': 'th.index_name', 'props': [('text-align', 'center')]},
        {'selector': 'th.blank', 'props': [('text-align', 'center')]},
    ]
    styled = (df.style
              .set_table_styles(table_styles)
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

    st.subheader("Evolução da Banca")
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(pd.to_datetime(df["Data"], format="%d/%m/%Y"), df["Capital (fim do dia)"], linewidth=2.0, color="#ff2d2d")
    ax.set_xlabel("Data")
    ax.set_ylabel("Banca (R$)")
    ax.set_title("Evolução da Banca")
    fig.autofmt_xdate()
    st.pyplot(fig)
else:
    st.info("Defina o período e os percentuais para visualizar resultados.")
