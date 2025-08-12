
# simulador_crescimento_streamlit.py
# Última versão consolidada do Simulador de Ganhos e Perdas
# Mantém layout e temática, otimizado para exibição no Streamlit com tabela detalhada e resumo.

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Simulador de Ganhos e Perdas", layout="wide")

# Função para calcular evolução
def calcular_evolucao(valor_inicial, data_inicio, data_fim, dias_ganho, dias_perda, pct_ganho, pct_perda):
    resultados = []
    valor = valor_inicial
    data_atual = data_inicio
    ciclo = []
    for _ in range(dias_ganho):
        ciclo.append(pct_ganho)
    for _ in range(dias_perda):
        ciclo.append(pct_perda)

    ciclo_index = 0
    while data_atual <= data_fim:
        pct = ciclo[ciclo_index % len(ciclo)]
        valor *= (1 + pct / 100)
        resultados.append({"Data": data_atual.strftime("%d/%m/%Y"), "Operação (%)": pct, "Valor (R$)": round(valor, 2)})
        ciclo_index += 1
        data_atual += timedelta(days=1)

    return pd.DataFrame(resultados)

st.title("Simulador de ganhos e perdas")

# Entrada de dados
col1, col2, col3 = st.columns(3)
with col1:
    valor_inicial = st.number_input("Valor inicial (R$)", value=200.0, step=0.01, format="%.2f")
with col2:
    data_inicio = st.date_input("Data de início", value=datetime.today())
with col3:
    data_fim = st.date_input("Data de fim", value=datetime.today() + timedelta(days=30))

col4, col5 = st.columns(2)
with col4:
    dias_ganho = st.number_input("Qtd. dias de ganho", min_value=0, max_value=10, value=2, step=1)
with col5:
    dias_perda = st.number_input("Qtd. dias de perda", min_value=0, max_value=10, value=1, step=1)

col6, col7 = st.columns(2)
with col6:
    pct_ganho = st.number_input("Percentual de ganho (%)", value=20.0, step=0.01, format="%.2f")
with col7:
    pct_perda = st.number_input("Percentual de perda (%)", value=-15.0, step=0.01, format="%.2f")

if st.button("Calcular"):
    df = calcular_evolucao(valor_inicial, data_inicio, data_fim, dias_ganho, dias_perda, pct_ganho, pct_perda)

    # Gráfico
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Data"], y=df["Valor (R$)"], mode='lines+markers', name='Evolução'))
    st.plotly_chart(fig, use_container_width=True)

    # Tabela detalhada
    st.markdown("### Tabela detalhada")
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Tabela-resumo
    valor_final = df["Valor (R$)"].iloc[-1]
    lucro_prejuizo = valor_final - valor_inicial

    resumo_df = pd.DataFrame({
        "Item": ["Valor Final (R$)", "Lucro/Prejuízo (R$)"],
        "Valor": [f"**{valor_final:,.2f}**", f"{lucro_prejuizo:,.2f}"]
    })

    st.markdown("### Resumo")
    st.dataframe(resumo_df, use_container_width=True, hide_index=True)
