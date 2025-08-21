# -*- coding: utf-8 -*-
"""
Simulador de Ganhos e Perdas do Aviator
---------------------------------------
Regras:
- Duas entradas por dia da semana; dois campos sob cada chip (SEG a DOM).
- Período definido por "Data de início da operação" e "Data final" (dd/mm/aaaa).
- O primeiro registro da tabela é sempre a data de hoje se ela estiver no período; caso contrário, usa a data de início.
- Linhas verdes quando o resultado do dia é positivo; vermelhas quando negativo.
- Gráfico sempre exibido.
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
  font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans';
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
.metric-box {
  border-radius: 14px; padding: 12px 14px; border: 1px solid rgba(255,45,45,0.25);
  background: linear-gradient(180deg, rgba(255,45,45,0.10) 0%, rgba(255,45,45,0.02) 100%);
}
.metric-box .label { color:#b8bcc6; font-size:12px; }
.metric-box .value { font-size:22px; font-weight:800; }
.metric-green { color:#9be7a3; }
.metric-red { color:#ff9aa2; }
</style>
""", unsafe_allow_html=True)

st.title("Simulador de Ganhos e Perdas do Aviator")
st.caption("Defina duas **percentagens diárias** (positivas ou negativas) para cada dia.")

with st.sidebar:
    st.header("Parâmetros gerais ✈️")
    banca_inicial = st.number_input("Banca inicial (R$)", min_value=0.0, value=1000.0, step=100.0, format="%.2f")
    hoje = date.today()
    hoje_str = hoje.strftime("%d/%m/%Y")
    data_inicio_str = st.text_input("Data de início da operação (dd/mm/aaaa)", value=hoje_str, placeholder="dd/mm/aaaa")
    data_fim_str = st.text_input("Data final (dd/mm/aaaa)", value="", placeholder="dd/mm/aaaa")
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

# --- Parse de datas ---
def parse_date_str(s: str):
    s = (s or "").strip()
    if not s:
        return None, "Campo obrigatório."
    try:
        return datetime.strptime(s, "%d/%m/%Y").date(), None
    except ValueError:
        return None, "Formato inválido. Use dd/mm/aaaa."

data_inicio, err_inicio = parse_date_str(data_inicio_str)
data_fim, err_fim = (None, None) if data_fim_str.strip()=="" else parse_date_str(data_fim_str)

if err_inicio:
    st.error(f"Data de início: {err_inicio}")
if data_fim_str.strip()!="" and err_fim:
    st.error(f"Data final: {err_fim}")

# Bloqueia simulação até que as datas sejam válidas
if (err_inicio is not None) or (data_inicio is None) or (data_fim_str.strip()!="" and (err_fim is not None or data_fim is None)):
    st.stop()

# Se data final vazia, mostramos instrução e não simulamos ainda
if data_fim is None:
    st.info("Informe a **Data final** para rodar a simulação.")
    st.stop()

# Validação de ordem
if data_fim < data_inicio:
    st.error("A **Data final** deve ser igual ou posterior à **Data de início da operação**.")
    st.stop()

# --- Construção do calendário de simulação ---
hoje_dt = date.today()
inicio_real = hoje_dt if (data_inicio <= hoje_dt <= data_fim) else data_inicio
datas_periodo = pd.date_range(start=inicio_real, end=data_fim, freq="D")
if inicio_real > data_inicio:
    prefixo = pd.date_range(start=data_inicio, end=inicio_real - pd.Timedelta(days=1), freq="D")
    datas_periodo = prefixo.append(datas_periodo)

# --- Simulação ---
registros = []
capital = banca_inicial

for current_date in datas_periodo:
    weekday = int(current_date.weekday())  # 0=Mon ... 6=Sun
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

total_dias = len(df)
banca_final_total = df["Capital (fim do dia)"].iloc[-1] if total_dias > 0 else banca_inicial
retorno_acumulado_pct = ((banca_final_total / banca_inicial - 1) * 100.0) if banca_inicial > 0 else 0.0
lucro_prejuizo = banca_final_total - banca_inicial

c1, c2, c3, c4 = st.columns(4)

c1.metric("Dias simulados", f"{total_dias}")
c2.metric("Banca final", f"R$ {banca_final_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
c3.metric("Retorno acumulado", f"{retorno_acumulado_pct:.2f}%")

lp_fmt = f"R$ {lucro_prejuizo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
lp_class = "metric-green" if lucro_prejuizo >= 0 else "metric-red"
c4.markdown(f"""<div class="metric-box"><div class="label">Lucro/Prejuízo obtido</div>
<div class="value {lp_class}">{lp_fmt}</div></div>""", unsafe_allow_html=True)

# --- Resumo por período (dias positivos/negativos) ---
st.markdown("#### Resumo por período")
if total_dias > 0:
    dias_pos = int((df["Variação (R$)"] > 0).sum())
    dias_neg = int((df["Variação (R$)"] < 0).sum())
    r1, r2 = st.columns(2)
    r1.markdown(f"""<div class="metric-box"><div class="label">Dias positivos</div>
<div class="value metric-green">{dias_pos}</div></div>""", unsafe_allow_html=True)
    r2.markdown(f"""<div class="metric-box"><div class="label">Dias negativos</div>
<div class="value metric-red">{dias_neg}</div></div>""", unsafe_allow_html=True)
else:
    st.info("Sem dados para resumir ainda.")

# --- Tabela ---
# Cores nas linhas: verde (delta > 0), vermelho (delta < 0)
def color_rows(row):
    delta = row.get("Variação (R$)", 0.0)
    if delta > 0:
        return ["background-color: #16381b; color: #9be7a3;"] * len(row)
    elif delta < 0:
        return ["background-color: #3a0f12; color: #ff9aa2;"] * len(row)
    else:
        return [""] * len(row)

# Centralizar os títulos das colunas
table_styles = [
    {'selector': 'th.col_heading', 'props': [('text-align', 'center')]},
    {'selector': 'th.index_name', 'props': [('text-align', 'center')]},
    {'selector': 'th.blank', 'props': [('text-align', 'center')]},
]

st.subheader("Tabela de operações")
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
