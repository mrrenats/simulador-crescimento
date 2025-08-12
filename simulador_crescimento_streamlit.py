
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta

st.set_page_config(page_title="Simulador de Crescimento", layout="wide")

st.title("Simulador de Crescimento")

# Entrada de dados
valor_inicial = st.number_input("Valor inicial (R$)", min_value=0.0, value=200.0, step=0.01)

col1, col2 = st.columns(2)
with col1:
    data_inicio = st.date_input("Data de início", value=date.today(), format="DD/MM/YYYY")
with col2:
    data_fim = st.date_input("Data de fim", value=None, format="DD/MM/YYYY")

col3, col4 = st.columns(2)
with col3:
    dias_ganho = st.selectbox("Qtd. dias de ganho no ciclo", list(range(0, 11)), index=2)
with col4:
    dias_perda = st.selectbox("Qtd. dias de perda no ciclo", list(range(0, 11)), index=1)

col5, col6 = st.columns(2)
with col5:
    ganho_pct = st.number_input("Percentual de ganho (%)", value=20.00, step=0.01, format="%.2f")
with col6:
    perda_pct = st.number_input("Percentual de perda (%)", value=-15.00, step=0.01, format="%.2f")

ciclo_inicio = st.radio("Ciclo começa por:", ["Ganho", "Perda"], horizontal=True)

dias_semana = st.multiselect("Selecione os dias da semana com operação:",
    ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"],
    default=["Segunda", "Terça", "Quinta"]
)

dias_map = {"Segunda":0,"Terça":1,"Quarta":2,"Quinta":3,"Sexta":4,"Sábado":5,"Domingo":6}
dias_semana_idx = [dias_map[d] for d in dias_semana]

if data_fim and data_fim > data_inicio:
    datas = pd.date_range(start=data_inicio, end=data_fim, freq="D")
    valor = valor_inicial
    resultados = []
    ciclo = []
    ciclo.extend(["ganho"]*dias_ganho + ["perda"]*dias_perda)
    ciclo_idx = 0
    for d in datas:
        if d.weekday() in dias_semana_idx:
            if ciclo[ciclo_idx] == "ganho":
                valor *= (1 + ganho_pct/100)
                resultados.append([d.strftime("%d/%m/%Y"), "Ganho", valor])
            else:
                valor *= (1 + perda_pct/100)
                resultados.append([d.strftime("%d/%m/%Y"), "Perda", valor])
            ciclo_idx = (ciclo_idx + 1) % len(ciclo)
    df = pd.DataFrame(resultados, columns=["Data", "Operação", "Valor (R$)"])

    # Gráfico
    fig, ax = plt.subplots(figsize=(10,5))
    ax.plot(df["Data"], df["Valor (R$)"], marker="o", linestyle="-")
    ax.set_xlabel("Data")
    ax.set_ylabel("Valor (R$)")
    ax.set_title("Evolução do Valor")
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # Tabela detalhada rolável sem índice
    st.subheader("Tabela Detalhada")
    st.dataframe(df.style.hide(axis="index"), height=300, use_container_width=True)

    # Tabela resumo com valor final e lucro/prejuízo
    valor_final = df["Valor (R$)"].iloc[-1]
    lucro = valor_final - valor_inicial
    resumo = pd.DataFrame({
        "Descrição": ["Valor Final (R$)", "Lucro/Prejuízo (R$)"],
        "Valor": [valor_final, lucro]
    })
    resumo_style = resumo.style.format({"Valor": "R$ {:,.2f}"}).hide(axis="index")
    resumo_style = resumo_style.set_properties(**{'font-weight': ['bold', 'normal'], 'font-size': ['14px', '12px']})
    st.subheader("Resumo")
    st.table(resumo_style)

else:
    st.warning("Por favor, selecione uma data final válida.")
