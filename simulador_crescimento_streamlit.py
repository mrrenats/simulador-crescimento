
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

st.title("Simulador de Juros Compostos com Ciclos Personalizados")

# Entradas do usuário
valor_inicial = st.number_input("Valor inicial (R$)", min_value=0.0, value=200.0, step=100.0)
data_inicio = st.date_input("Data de início", value=datetime(2025, 8, 7))
data_fim = st.date_input("Data de fim", value=datetime(2025, 12, 31))

st.markdown("**Dias úteis com operações:**")
dias_ativos = []
if st.checkbox("Segunda-feira", value=True): dias_ativos.append(0)
if st.checkbox("Terça-feira", value=True): dias_ativos.append(1)
if st.checkbox("Quarta-feira", value=False): dias_ativos.append(2)
if st.checkbox("Quinta-feira", value=True): dias_ativos.append(3)
if st.checkbox("Sexta-feira", value=False): dias_ativos.append(4)

st.markdown("**Ciclo de operações (ex: [1.2, 1.2, 0.85]):**")
ciclo_input = st.text_input("Fatores de ganho/perda separados por vírgula", value="1.2, 1.2, 0.85")
ciclo = [float(x.strip()) for x in ciclo_input.split(",") if x.strip()]

# Simulação
def simular(valor_inicial, data_inicio, data_fim, dias_ativos, ciclo):
    valor = valor_inicial
    data_atual = data_inicio
    historico = [{"Data": data_atual, "Valor": valor}]
    ciclo_index = 0
    while data_atual <= data_fim:
        if data_atual.weekday() in dias_ativos:
            valor *= ciclo[ciclo_index]
            ciclo_index = (ciclo_index + 1) % len(ciclo)
        historico.append({"Data": data_atual, "Valor": valor})
        data_atual += timedelta(days=1)
    return pd.DataFrame(historico)

if st.button("Simular"):
    df = simular(valor_inicial, data_inicio, data_fim, dias_ativos, ciclo)
    st.line_chart(df.set_index("Data"))
    st.dataframe(df)
    st.download_button("📥 Baixar CSV", data=df.to_csv(index=False), file_name="simulacao.csv", mime="text/csv")
