# -*- coding: utf-8 -*-
"""
Simulador de Ganhos e Perdas do Aviator
---------------------------------------
Regras:
- Duas entradas por dia da semana (sem rótulos A/B); apenas dois campos sob cada dia (SEG a DOM).
- Período definido por "Data de início da operação" e "Data final".
- O primeiro registro da tabela é sempre a **data de hoje** se ela estiver dentro do período. Caso contrário, será a data de início.
- Linhas verdes quando o resultado do dia é positivo; vermelhas quando negativo.
- Gráfico sempre exibido.
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import date, datetime

st.set_page_config(page_title="Simulador de Ganhos e Perdas do Aviator", page_icon="✈️", layout="wide")

# ----------------------
# Estilo Aviator (CSS)
# ----------------------
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
  background: radial-gradient(1200px 600px at 10% 10%, #1b1b1f 0%, #0f0f12 60%, #0b0b0d 100%) !important;
  color: #f0f2f6 !important;
  font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji';
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #111115 0%, #0b0b0d 100%) !important;
  border-right: 1px solid rgba(255, 0, 0, 0.15);
}
h1 { font-weight: 800 !important; letter-spacing: 0.3px; color: #ff2d2d !important; text-shadow: 0 0 18px rgba(255,45,45,0.25); }
h2, h3 { color: #ff6961 !important; }
[data-testid="stMetric"] { border-radius: 14px; padding: 8px 12px;
  background: linear-gradient(180deg, rgba(255,45,45,0.10) 0%, rgba(255,45,45,0.02) 100%);
  border: 1px solid rgba(255,45,45,0.25);
}
[data-baseweb="input"] input { color: #f0f2f6 !important; }
[data-testid="stDataFrame"] { border: 1px solid rgba(255,45,45,0.22); border-radius: 12px; overflow: hidden; }
.small-note { color: #b8bcc6; font-size: 12px; margin-top: 4px; }
.day-chip { display:inline-block; padding:6px 10px; border:1px solid rgba(255,45,45,0.35);
  border-radius: 999px; margin-bottom: 6px; font-weight: 700; color:#ffd6d6; background: rgba(255,45,45,0.08);
}
</style>
""", unsafe_allow_html=True)

st.title("Simulador de Ganhos e Perdas do Aviator")
st.caption("Defina duas **percentagens diárias** (positivas ou negativas) para cada dia. Sem ciclos fixos.")

with st.sidebar:
    st.header("Parâmetros gerais ✈️")
    capital_inicial = st.number_input("Capital inicial (R$)", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
    hoje = date.today()
    data_inicio = st.date_input("Data de início da operação", value=hoje)
    data_fim = st.date_input("Data final", value=hoje)
    st.markdown('<div class="small-note">Use vírgula ou ponto como separador decimal. Ex.: 7,12 ou 7.12.</div>', unsafe_allow_html=True)

# Dias abreviados
DAYS_ABBR = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]

st.subheader("Percentuais por dia")
st.write("Preencha os campos dos dias de acordo com a simulação que queria fazer. "
         "Deixe 0 caso não queira simular o operação naquele dia. "
         "Caso queria simular apenas uma operação no dia, deixe 0 o segundo campo.")

# Inputs: duas entradas numéricas por dia sem rótulos, apenas sob o chip do dia
percentuais_A = []
percentuais_B = []
cols = st.columns(7)
for i, day in enumerate(DAYS_ABBR):
    with cols[i]:
        st.markdown(f'<span class="day-chip">{day}</span>', unsafe_allow_html=True)
        a = st.number_input("", value=0.0, step=0.1, format="%.2f", key=f"pctA_{i}", label_visibility="collapsed")
        b = st.number_input("", value=0.0, step=0.1, format="%.2f", key=f"pctB_{i}", label_visibility="collapsed")
        percentuais_A.append(a)
        percentuais_B.append(b)

# --- Validação de datas ---
if data_fim < data_inicio:
    st.error("A **Data final** deve ser igual ou posterior à **Data de início da operação**.")
    st.stop()

# --- Construção do calendário de simulação ---
# Se "hoje" estiver dentro do período, o primeiro dia será hoje; caso contrário, começa em data_inicio.
inicio_real = hoje if (data_inicio <= hoje <= data_fim) else data_inicio
# Conjunto de datas do período
datas_periodo = pd.date_range(start=inicio_real, end=data_fim, freq="D")

# Caso o início_real seja posterior a data_inicio, oferecemos também as datas entre data_inicio e ontem após o período principal
if inicio_real > data_inicio:
    prefixo = pd.date_range(start=data_inicio, end=inicio_real - pd.Timedelta(days=1), freq="D")
    datas_periodo = prefixo.append(datas_periodo)

# --- Simulação ---
registros = []
capital = capital_inicial

for current_date in datas_periodo:
    weekday = int(current_date.weekday())  # 0=Mon ... 6=Sun
    # Mapear para nossas labels: 0->SEG ... 6->DOM
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

# --- Resultados ---
st.subheader("Resultados")
col1, col2, col3 = st.columns(3)
total_dias = len(df)
capital_final_total = df["Capital (fim do dia)"].iloc[-1] if total_dias > 0 else capital_inicial
retorno_acumulado_pct = ((capital_final_total / capital_inicial - 1) * 100.0) if capital_inicial > 0 else 0.0

col1.metric("Dias simulados", f"{total_dias}")
col2.metric("Banca final", f"R$ {capital_final_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
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

# Centralizar os títulos das colunas da tabela
table_styles = [
    {'selector': 'th.col_heading', 'props': [('text-align', 'center')]},
    {'selector': 'th.index_name', 'props': [('text-align', 'center')]},
    {'selector': 'th.blank', 'props': [('text-align', 'center')]},
]

if total_dias > 0:
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
else:
    st.info("Defina o período e os percentuais para visualizar a tabela.")

# --- Gráfico (sempre exibido) ---
if total_dias > 0:
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

st.caption("ⓘ Este simulador não é recomendação financeira. Use para estudos e planejamento.")
