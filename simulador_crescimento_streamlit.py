# -*- coding: utf-8 -*-
"""
Simulador de Crescimento por Dia da Semana (sem ciclos fixos)
----------------------------------------------------------------
Este app substitui a lógica de ciclos de ganho/perda.
Agora você define livremente a % (positiva ou negativa) para cada dia da semana.

Como usar:
- Preencha o capital inicial, quantidade de semanas e, se quiser, marque "apenas dias úteis".
- Informe a % de cada dia da semana (ex.: 7,12 para +7,12% | -15,2 para -15,2%).
- O app compõe o capital aplicando a % de cada dia ao longo das semanas.
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Simulador de Crescimento", page_icon="📈", layout="centered")

st.title("📈 Simulador de Crescimento por Dia da Semana")
st.caption("Defina livremente a **percentagem diária** (positiva ou negativa) para cada dia da semana. Sem ciclos fixos.")

with st.sidebar:
    st.header("Parâmetros gerais")
    capital_inicial = st.number_input("Capital inicial (R$)", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
    semanas = st.number_input("Quantas semanas?", min_value=1, value=4, step=1)
    dias_uteis_apenas = st.checkbox("Apenas dias úteis (seg–sex)?", value=True)
    reiniciar_a_cada_semana = st.checkbox("Reiniciar capital a cada semana?", value=False, help="Se ligado, cada semana começa com o capital inicial. Se desligado, o capital é composto ao longo de todas as semanas.")
    mostrar_grafico = st.checkbox("Mostrar gráfico de evolução", value=True)
    st.markdown("---")
    st.caption("Dica: use `,` como separador decimal (ex.: 7,12) ou `.` (ex.: 7.12).")

st.subheader("Percentuais por dia da semana")
st.write("Insira a variação diária em **%**. Ex.: `7,12` => **+7,12%**; `-15,2` => **-15,2%**.")

DAYS_PT = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
DAYS_ABBR = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

# Inputs de percentuais por dia
cols = st.columns(7)
percentuais = []
for i, day in enumerate(DAYS_PT):
    with cols[i]:
        if dias_uteis_apenas and i >= 5:
            pct = st.number_input(day, value=0.0, step=0.1, format="%.2f", key=f"pct_{i}", disabled=True)
        else:
            pct = st.number_input(day, value=0.0, step=0.1, format="%.2f", key=f"pct_{i}")
        percentuais.append(pct)

if dias_uteis_apenas:
    percentuais[5] = 0.0
    percentuais[6] = 0.0

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
        pct = percentuais[dia_semana]
        delta = capital * (pct / 100.0)
        capital_final = capital + delta
        registros.append({
            "Semana": semana,
            "Dia #": dia_global + 1,
            "Dia da semana": DAYS_PT[dia_semana],
            "% do dia": pct,
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

if total_dias > 0:
    st.dataframe(
        df.style.format({
            "% do dia": "{:.2f}%",
            "Variação (R$)": "R$ {:,.2f}",
            "Capital (início do dia)": "R$ {:,.2f}",
            "Capital (fim do dia)": "R$ {:,.2f}",
        }).highlight_null(props="opacity: 0.6;"),
        use_container_width=True
    )
else:
    st.info("Configure os percentuais e as semanas para visualizar a tabela.")

# --- Gráfico ---
if mostrar_grafico and total_dias > 0:
    st.subheader("Evolução do capital")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(df["Dia #"], df["Capital (fim do dia)"])
    ax.set_xlabel("Dia")
    ax.set_ylabel("Capital (R$)")
    ax.set_title("Evolução do capital ao longo dos dias")
    st.pyplot(fig)

# --- Exportação ---
st.subheader("Exportar dados")
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("Baixar CSV", data=csv, file_name="simulacao_por_dia_da_semana.csv", mime="text/csv")

st.caption("ⓘ Este simulador não é recomendação financeira. Use para estudos e planejamento.")
