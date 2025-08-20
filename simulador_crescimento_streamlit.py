# -*- coding: utf-8 -*-
"""
Simulador de Crescimento por Dia da Semana — com duas entradas por dia
-----------------------------------------------------------------------
Mudanças solicitadas:
- Duas entradas por dia (A e B), aplicadas na sequência (compostas dentro do dia).
- Linhas da tabela em **verde** quando há aumento (delta > 0) e **vermelho** quando há diminuição (delta < 0).
- Removida a coluna "Semana".
- Removida a exportação CSV.

Como usar:
- Preencha o capital inicial, quantidade de semanas e, se quiser, marque "apenas dias úteis".
- Informe as duas % de cada dia (podem ser positivas ou negativas). Se não quiser usar, deixe 0.
- O app compõe o capital aplicando %A e depois %B dentro de cada dia.
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Simulador de Crescimento", page_icon="📈", layout="centered")

st.title("📈 Simulador de Crescimento por Dia da Semana")
st.caption("Defina duas **percentagens diárias** (positivas ou negativas) para cada dia da semana. Sem ciclos fixos.")

with st.sidebar:
    st.header("Parâmetros gerais")
    capital_inicial = st.number_input("Capital inicial (R$)", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
    semanas = st.number_input("Quantas semanas?", min_value=1, value=4, step=1)
    dias_uteis_apenas = st.checkbox("Apenas dias úteis (seg–sex)?", value=True)
    reiniciar_a_cada_semana = st.checkbox("Reiniciar capital a cada semana?", value=False, help="Se ligado, cada semana começa com o capital inicial. Se desligado, o capital é composto ao longo de todas as semanas.")
    mostrar_grafico = st.checkbox("Mostrar gráfico de evolução", value=True)
    st.markdown("---")
    st.caption("Dica: use `,` como separador decimal (ex.: 7,12) ou `.` (ex.: 7.12).")

st.subheader("Percentuais por dia da semana (A e B)")
st.write("Insira as duas variações em **%** para cada dia. Ex.: `7,12` => **+7,12%**; `-15,2` => **-15,2%**. "
         "O cálculo diário será composto: primeiro A, depois B.")

DAYS_PT = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
DAYS_ABBR = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

# Inputs: duas colunas por dia (A e B)
percentuais_A = []
percentuais_B = []
cols = st.columns(7)
for i, day in enumerate(DAYS_PT):
    with cols[i]:
        disabled = bool(dias_uteis_apenas and i >= 5)
        pct_a = st.number_input(f"{day} — A", value=0.0, step=0.1, format="%.2f", key=f"pctA_{i}", disabled=disabled)
        pct_b = st.number_input(f"{day} — B", value=0.0, step=0.1, format="%.2f", key=f"pctB_{i}", disabled=disabled)
        percentuais_A.append(0.0 if disabled else pct_a)
        percentuais_B.append(0.0 if disabled else pct_b)

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
            "Dia da semana": DAYS_PT[dia_semana],
            "% A": a,
            "% B": b,
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

def color_rows(row):
    delta = row.get("Variação (R$)", 0.0)
    if delta > 0:
        return ["background-color: #e8f5e9; color: #1b5e20;"] * len(row)  # verde suave
    elif delta < 0:
        return ["background-color: #ffebee; color: #b71c1c;"] * len(row)  # vermelho suave
    else:
        return [""] * len(row)

if total_dias > 0:
    styled = (df.style
              .apply(color_rows, axis=1)
              .format({
                  "% A": "{:.2f}%",
                  "% B": "{:.2f}%",
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
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(df["Dia #"], df["Capital (fim do dia)"])
    ax.set_xlabel("Dia")
    ax.set_ylabel("Capital (R$)")
    ax.set_title("Evolução do capital ao longo dos dias")
    st.pyplot(fig)

st.caption("ⓘ Este simulador não é recomendação financeira. Use para estudos e planejamento.")
