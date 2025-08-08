
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from PIL import Image
from datetime import datetime, timedelta
from pathlib import Path
import re

APP_TITLE = "Simulador de ganhos e perdas do Aviator"
DEFAULT_BG = "/mnt/data/fundo_grafico.jpg"

st.title(APP_TITLE)

st.markdown(
    """
    <style>
      div[data-testid='stIFrame']{width:100% !important;}
      div[data-testid='stIFrame'] > iframe{width:100% !important;}
      .total-highlight {
          background:#eef8ff;
          border:1px solid #cce6ff;
          padding:14px 16px;
          border-radius:8px;
          margin-top:8px;
      }
      .total-highlight .label { font-size:1rem; color:#1b4d8a; font-weight:600; }
      .total-highlight .value { font-size:2rem; font-weight:800; color:#0b2e59; }
    </style>
    """,
    unsafe_allow_html=True
)

def parse_percent_br(pct_str: str) -> float:
    if not isinstance(pct_str, str):
        raise ValueError("Percentual inválido: informe texto como '12,34%'.")
    s = pct_str.strip().replace(" ", "")
    if not re.fullmatch(r"-?\d{1,3},\d{2}%", s):
        raise ValueError("Formato inválido. Use '20,00%' ou '-15,00%'.")
    negativo = s.startswith("-")
    s_num = s.replace("%", "").replace("-", "")
    valor = float(s_num.replace(",", "."))
    if negativo:
        valor = -valor
    return 1 + (valor / 100.0)

def parse_data_br(txt: str) -> datetime:
    s = (txt or "").strip()
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s):
        raise ValueError("Use o formato dd/mm/aaaa, ex.: 07/08/2025.")
    return datetime.strptime(s, "%d/%m/%Y")

def construir_ciclo(ganho_pct_str: str, perda_pct_str: str, dias_ganho: int, dias_perda: int, comeca_por: str):
    fator_ganho = parse_percent_br(ganho_pct_str)
    fator_perda = parse_percent_br(perda_pct_str)
    if dias_ganho < 0 or dias_perda < 0:
        raise ValueError("A quantidade de dias deve ser não negativa.")
    if dias_ganho == 0 and dias_perda == 0:
        raise ValueError("Defina ao menos um dia de ganho ou de perda.")
    bloco_ganhos = [fator_ganho] * dias_ganho
    bloco_perdas = [fator_perda] * dias_perda
    if comeca_por == "Ganho":
        ciclo = bloco_ganhos + bloco_perdas
    else:
        ciclo = bloco_perdas + bloco_ganhos
    return ciclo

def simular_operacoes(valor_inicial, data_inicio, data_fim, dias_ativos, ciclo):
    valor = valor_inicial
    data_atual = data_inicio
    historico = []
    ciclo_index = 0
    while data_atual <= data_fim:
        if data_atual.weekday() in dias_ativos and len(ciclo) > 0:
            fator = ciclo[ciclo_index]
            valor = valor * fator
            ciclo_index = (ciclo_index + 1) % len(ciclo)
            variacao_pct = (fator - 1.0) * 100.0
            tipo = "Ganho" if variacao_pct > 0 else ("Perda" if variacao_pct < 0 else "Neutro")
            historico.append({
                "Data": data_atual,
                "Tipo": tipo,
                "Variação (%)": variacao_pct,
                "Valor (R$)": valor
            })
        data_atual += timedelta(days=1)
    return pd.DataFrame(historico)

def br_num(v: float) -> str:
    return ("{:,.2f}".format(v)).replace(",", "X").replace(".", ",").replace("X", ".")

# Máscara automática para data fim
def _format_data_fim_on_change():
    txt = st.session_state.get("data_fim_txt", "")
    digits = "".join(ch for ch in txt if ch.isdigit())[:8]
    if len(digits) >= 5:
        st.session_state["data_fim_txt"] = f"{digits[:2]}/{digits[2:4]}/{digits[4:]}"
    elif len(digits) >= 3:
        st.session_state["data_fim_txt"] = f"{digits[:2]}/{digits[2:4]}"
    else:
        st.session_state["data_fim_txt"] = digits

hoje = datetime.now().strftime("%d/%m/%Y")

st.subheader("Período e valor inicial")
c1, c2, c3 = st.columns([1,1,1])
with c1:
    valor_inicial = st.number_input("Valor inicial (R$)", min_value=0.0, value=200.0, step=100.0)
with c2:
    data_inicio_txt = st.text_input("Data de início (dd/mm/aaaa)", value=hoje)
with c3:
    data_fim_txt = st.text_input("Data de fim (dd/mm/aaaa)", value="", key="data_fim_txt", on_change=_format_data_fim_on_change)

fim_txt = st.session_state.get("data_fim_txt", data_fim_txt)

data_erro = None
try:
    data_inicio = parse_data_br(data_inicio_txt)
    if not fim_txt.strip():
        data_erro = "Informe a data de fim no formato dd/mm/aaaa."
        data_fim = None
    else:
        data_fim = parse_data_br(fim_txt)
        if data_inicio > data_fim:
            data_erro = "A data de início deve ser anterior ou igual à data de fim."
except Exception as e:
    data_erro = str(e)
    data_fim = None

st.caption(f"Período selecionado: {data_inicio_txt} — {fim_txt or '(defina a data de fim)'}")

st.subheader("Dias com operações")
dias_ativos = []
d1, d2, d3, d4, d5, d6, d7 = st.columns(7)
with d1:
    if st.checkbox("Seg", value=True): dias_ativos.append(0)
with d2:
    if st.checkbox("Ter", value=True): dias_ativos.append(1)
with d3:
    if st.checkbox("Qua", value=False): dias_ativos.append(2)
with d4:
    if st.checkbox("Qui", value=True): dias_ativos.append(3)
with d5:
    if st.checkbox("Sex", value=False): dias_ativos.append(4)
with d6:
    if st.checkbox("Sáb", value=False): dias_ativos.append(5)
with d7:
    if st.checkbox("Dom", value=False): dias_ativos.append(6)

st.subheader("Ciclo de ganhos e perdas")
cc1, cc2, cc3 = st.columns([1,1,1])
with cc1:
    ganho_pct_str = st.text_input("Percentual de ganho (ex.: 20,00%)", value="20,00%")
with cc2:
    perda_pct_str = st.text_input("Percentual de perda (ex.: -15,00%)", value="-15,00%")
with cc3:
    comeca_por = st.radio("Ciclo começa por:", options=["Ganho", "Perda"], index=0, horizontal=True)

dias_ganho = st.number_input("Qtd. dias de ganho no ciclo", min_value=0, value=2, step=1)
dias_perda = st.number_input("Qtd. dias de perda no ciclo", min_value=0, value=1, step=1)

st.caption("Ex.: Para 2 ganhos e 1 perda, informe ganho=2 e perda=1. Percentuais no formato BR.")

erro = None
ciclo = []
if data_erro:
    st.error(data_erro)
else:
    try:
        ciclo = construir_ciclo(ganho_pct_str, perda_pct_str, dias_ganho, dias_perda, comeca_por)
        st.write("Ciclo multiplicativo:", ciclo)
    except Exception as e:
        erro = str(e)
        st.error(erro)

if st.button("Simular") and not (erro or data_erro) and data_fim is not None:
    df_ops = simular_operacoes(valor_inicial, data_inicio, data_fim, dias_ativos, ciclo)

    if df_ops.empty:
        st.warning("Nenhum dia de operação dentro do período/dias escolhidos.")
    else:
        container = st.container()

        # Gráfico
        fig, ax = plt.subplots(figsize=(10, 4))

        bg_img = None
        try:
            if Path(DEFAULT_BG).exists():
                bg_img = Image.open(DEFAULT_BG)
        except Exception:
            bg_img = None

        if bg_img is not None:
            ax.imshow(bg_img, extent=(0, 1, 0, 1), transform=ax.transAxes, zorder=0)
            line_color = "white"
        else:
            ax.set_facecolor("#111111")
            line_color = "white"

        ax.plot(df_ops["Data"], df_ops["Valor (R$)"], linewidth=2.5, color=line_color, zorder=1)
        ax.set_xlabel("Data")
        ax.set_ylabel("Valor (R$)")
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()

        with container:
            st.pyplot(fig, use_container_width=True)

        # Tabela Plotly
        df_tbl = df_ops.copy()
        df_tbl["Data"] = pd.to_datetime(df_tbl["Data"]).dt.strftime("%d/%m/%Y")
        df_tbl["Variação (%)"] = df_tbl["Variação (%)"].map(lambda v: f"{br_num(v)}%")
        df_tbl["Valor (R$)"] = df_tbl["Valor (R$)"].map(lambda v: f"R$ {br_num(v)}")
        header_vals = list(df_tbl.columns)
        cells_vals = [df_tbl[c].tolist() for c in header_vals]
        row_colors = ['#e6ffe6' if t=='Ganho' else ('#ffe6e6' if t=='Perda' else '#ffffff') for t in df_ops['Tipo']]
        fig_tbl = go.Figure(data=[go.Table(
            header=dict(values=header_vals, fill_color='#f0f0f0', align=['left','left','right','right'], font=dict(color='black')),
            cells=dict(values=cells_vals, fill_color=[row_colors]*len(header_vals), align=['left','left','right','right'], font=dict(color='black'))
        )])
        fig_tbl.update_layout(margin=dict(l=0,r=0,t=0,b=0))
        with container:
            st.plotly_chart(fig_tbl, use_container_width=True)

        valor_final = df_ops["Valor (R$)"].iloc[-1]
        data_final = df_ops["Data"].iloc[-1].strftime("%d/%m/%Y")
        st.markdown(
            f"<div class='total-highlight'><span class='label'>Valor final em {data_final}:</span> "
            f"<span class='value'>R$ {br_num(valor_final)}</span></div>",
            unsafe_allow_html=True
        )
