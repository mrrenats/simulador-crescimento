# -*- coding: utf-8 -*-
"""
Simulador de Ganhos e Perdas do Aviator
---------------------------------------
- Tema completo estilo Aviator (escuro com detalhes em vermelho).
- Datas via st.date_input (locale pt-BR; digite números e formata em DD/MM/AAAA).
- Gráfico com fundo preto, linha vermelha, e eixos brancos; título fora do gráfico.
- Tabela esconde dias sem variação (delta == 0).
- "Resultados" como tabela uniforme; "Lucro/Prejuízo do período" colorido (verde/vermelho).
- "Resumo por período" com totais em fonte maior (verde para positivos, vermelho para negativos).
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from datetime import date, datetime, timedelta
import matplotlib as mpl
import locale
import os

# ------------- Locale pt-BR -------------
_LOCALE_CANDIDATES = ["pt_BR.UTF-8", "pt_BR.utf8", "pt_BR", "Portuguese_Brazil.1252"]
for loc in _LOCALE_CANDIDATES:
    try:
        locale.setlocale(locale.LC_TIME, loc)
        os.environ["LC_TIME"] = loc
        break
    except Exception:
        continue

st.set_page_config(page_title="Simulador de Ganhos e Perdas do Aviator", page_icon="✈️", layout="wide")

# ------------- Estilo Aviator (CSS) -------------
st.markdown("""
<style>
/* Base escura com destaque em vermelho */
html, body, [data-testid="stAppViewContainer"] {
  background: radial-gradient(1200px 600px at 10% 10%, #1b1b1f 0%, #0f0f12 60%, #0b0b0d 100%) !important;
  color: #f0f2f6 !important;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans';
}
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #111115 0%, #0b0b0d 100%) !important;
  border-right: 1px solid rgba(255, 0, 0, 0.15);
}
h1 {
  font-weight: 800 !important; letter-spacing: .3px;
  color: #ff2d2d !important; text-shadow: 0 0 18px rgba(255,45,45,.25);
}
h2, h3 { color: #ff6961 !important; }
.small-note { color: #b8bcc6; font-size: 12px; }
.day-chip {
  display:inline-block; padding:6px 10px; border:1px solid rgba(255,45,45,0.35);
  border-radius:999px; margin-bottom:6px; font-weight:700; color:#ffd6d6; background:rgba(255,45,45,0.08);
}
/* Caixas de métrica/summary */
.metric-box {
  border-radius: 14px; padding: 12px 14px; border: 1px solid rgba(255,45,45,0.25);
  background: linear-gradient(180deg, rgba(255,45,45,0.10) 0%, rgba(255,45,45,0.02) 100%);
}
.metric-green { color:#9be7a3; }
.metric-red { color:#ff9aa2; }
/* DataFrame: borda + cabeçalho centralizado */
[data-testid="stDataFrame"] {
  border: 1px solid rgba(255,45,45,0.22);
  border-radius: 12px;
  overflow: hidden;
}
</style>
""", unsafe_allow_html=True)

st.title("Simulador de Ganhos e Perdas do Aviator")

# ------------- Sidebar -------------
with st.sidebar:
    st.header("Parâmetros gerais ✈️")
    banca_inicial = st.number_input("Banca inicial (R$)", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
    hoje = date.today()
    data_inicio = st.date_input("Data de início da operação", value=hoje, format="DD/MM/YYYY")
    data_fim = st.date_input("Data final", value=None, format="DD/MM/YYYY")
    st.markdown('<div class="small-note">Dica: você pode digitar apenas números (ex.: 21082025) e apertar Tab.</div>', unsafe_allow_html=True)

# ------------- Inputs diários (dois por dia) -------------
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
        st.markdown(f'<span class="day-chip">{day}</span>', unsafe_allow_html=True)
        a = st.number_input("", value=0.0, step=0.1, format="%.2f", key=f"pctA_{i}", label_visibility="collapsed")
        b = st.number_input("", value=0.0, step=0.1, format="%.2f", key=f"pctB_{i}", label_visibility="collapsed")
        percentuais_A.append(a)
        percentuais_B.append(b)

# ------------- Validação de datas -------------
if data_fim is None:
    st.info("Informe a **Data final** para rodar a simulação.")
    st.stop()
if data_fim < data_inicio:
    st.error("A **Data final** deve ser igual ou posterior à **Data de início da operação**.")
    st.stop()

# ------------- Simulação -------------
datas_periodo = pd.date_range(start=data_inicio, end=data_fim, freq="D")

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

# ------------- Resultados (como tabela uniforme) -------------
st.subheader("Resultados")
total_dias = len(df)
banca_final_total = df["Capital (fim do dia)"].iloc[-1] if total_dias > 0 else banca_inicial
retorno_acumulado_pct = ((banca_final_total / banca_inicial - 1) * 100.0) if banca_inicial > 0 else 0.0
lucro_prejuizo = banca_final_total - banca_inicial


# Montar "Resultados" como tabela uniforme (mantendo numéricos e formatando via Styler)
resumo_dict = {
    "Dias simulados": [total_dias],
    "Banca final": [banca_final_total],
    "Retorno acumulado": [retorno_acumulado_pct],
    "Lucro/Prejuízo do período": [lucro_prejuizo],
}
resumo_df = pd.DataFrame(resumo_dict)

def fmt_real(v):
    try:
        return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return v

styled_resumo = (resumo_df.style
                 .format({
                     "Banca final": fmt_real,
                     "Retorno acumulado": lambda v: f"{v:.2f}%",
                     "Lucro/Prejuízo do período": fmt_real,
                 })
                 .applymap(lambda v: "color: #9be7a3; font-weight: 700;" if isinstance(v, (int, float)) and v > 0 else
                                   ("color: #ff9aa2; font-weight: 700;" if isinstance(v, (int, float)) and v < 0 else ""),
                           subset=["Lucro/Prejuízo do período"])
                 .set_table_styles([
                     {'selector': 'th.col_heading', 'props': [('text-align', 'center')]},
                     {'selector': 'th.index_name', 'props': [('text-align', 'center')]},
                     {'selector': 'th.blank', 'props': [('text-align', 'center')]},
                 ]))
# Mostrar sem índice
st.dataframe(styled_resumo, use_container_width=True)


# ------------- Resumo por período (positivos/negativos) -------------
st.markdown("#### Resumo por período")
if total_dias > 0:
    dias_pos = int((df["Variação (R$)"] > 0).sum())
    dias_neg = int((df["Variação (R$)"] < 0).sum())
    rp1, rp2 = st.columns(2)
    rp1.markdown(f"""
    <div class="metric-box" style="text-align:center">
      <div style="font-size:14px;color:#b8bcc6">Dias positivos</div>
      <div class="metric-green" style="font-size:34px;font-weight:900">{dias_pos}</div>
    </div>
    """, unsafe_allow_html=True)
    rp2.markdown(f"""
    <div class="metric-box" style="text-align:center">
      <div style="font-size:14px;color:#b8bcc6">Dias negativos</div>
      <div class="metric-red" style="font-size:34px;font-weight:900">{dias_neg}</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.info("Sem dados para resumir ainda.")

# ------------- Tabela de operações (sem linhas com delta=0) -------------
st.subheader("Tabela de operações")
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

if total_dias > 0:
    df_view = df[df["Variação (R$)"] != 0].copy()
    if df_view.empty:
        st.info("Não houve variações no período selecionado.")
    else:
        styled_table = (df_view.style
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
        st.dataframe(styled_table, use_container_width=True)
else:
    st.info("Defina o período e os percentuais para visualizar a tabela.")

# ------------- Gráfico (Evolução da Banca) -------------
if total_dias > 0:
    st.subheader("Evolução da Banca")
    # Preparar datas como datetime para formatação DD/MM/AAAA
    x_dates = pd.to_datetime(df["Data"], format="%d/%m/%Y")

    fig, ax = plt.subplots(figsize=(11, 5.2))
    # Fundo preto
    fig.patch.set_facecolor("#000000")
    ax.set_facecolor("#000000")
    # Linha vermelha
    ax.plot(x_dates, df["Capital (fim do dia)"], linewidth=2.2, color="#ff2d2d")
    # Eixos brancos
    ax.tick_params(colors="#ffffff")
    ax.spines['bottom'].set_color("#ffffff")
    ax.spines['left'].set_color("#ffffff")
    ax.set_xlabel("Data", color="#ffffff")
    ax.set_ylabel("Banca (R$)", color="#ffffff")
    # Formatador de data DD/MM/AAAA
    ax.xaxis.set_major_formatter(DateFormatter("%d/%m/%Y"))
    fig.autofmt_xdate()

    # Sem título dentro do gráfico (somente o subheader acima)
    # ax.set_title("")

    st.pyplot(fig)
