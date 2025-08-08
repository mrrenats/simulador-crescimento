
import streamlit as st
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

# ---------- CSS mínimo para destaque do total ----------
st.markdown(
    """
    <style>
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

# ---------- Utilidades ----------
def parse_data_br(txt: str) -> datetime:
    s = (txt or "").strip()
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s):
        raise ValueError("Use o formato dd/mm/aaaa, ex.: 07/08/2025.")
    return datetime.strptime(s, "%d/%m/%Y")

def construir_ciclo(ganho_pct: float, perda_pct: float, dias_ganho: int, dias_perda: int, comeca_por: str):
    """ganho_pct e perda_pct são percentuais 'cheios' (ex.: 20.00 -> 20,00%)"""
    if dias_ganho < 0 or dias_perda < 0:
        raise ValueError("A quantidade de dias deve ser não negativa.")
    if dias_ganho == 0 and dias_perda == 0:
        raise ValueError("Defina ao menos um dia de ganho ou de perda.")
    fator_ganho = 1 + (ganho_pct / 100.0)
    fator_perda = 1 - (perda_pct / 100.0)  # perda aplicada como negativa
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

# ---------- Máscara automática para data fim (dd/mm/aaaa) ----------
def _format_data_fim_on_change():
    txt = st.session_state.get("data_fim_txt", "")
    digits = "".join(ch for ch in txt if ch.isdigit())[:8]
    if len(digits) == 0:
        st.session_state["data_fim_txt"] = ""
    elif len(digits) <= 2:
        st.session_state["data_fim_txt"] = digits
    elif len(digits) <= 4:
        st.session_state["data_fim_txt"] = f"{digits[:2]}/{digits[2:4]}"
    else:
        st.session_state["data_fim_txt"] = f"{digits[:2]}/{digits[2:4]}/{digits[4:]}"

# ---------- Máscara para percentuais com vírgula (interpretação 'cheia') ----------
def _format_pct_on_change_ganho():
    txt = st.session_state.get("ganho_pct_txt", "")
    digits = "".join(ch for ch in txt if ch.isdigit())[:6]
    if not digits:
        st.session_state["ganho_pct_txt"] = ""
        return
    val = int(digits)
    st.session_state["ganho_pct_txt"] = f"{val},00"

def _format_pct_on_change_perda():
    txt = st.session_state.get("perda_pct_txt", "")
    digits = "".join(ch for ch in txt if ch.isdigit())[:6]
    if not digits:
        st.session_state["perda_pct_txt"] = ""
        return
    val = int(digits)
    st.session_state["perda_pct_txt"] = f"{val},00"

def _pct_str_br_to_float(pct_txt: str) -> float:
    s = (pct_txt or "").strip()
    if not s:
        raise ValueError("Preencha os percentuais de ganho e perda.")
    s_num = s.replace(".", "").replace(",", ".")
    try:
        val = float(s_num)
    except Exception:
        raise ValueError("Percentual inválido. Digite apenas números; a vírgula entra automaticamente (ex.: 20 → 20,00).")
    return round(val, 2)

# ---------- Entradas ----------
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
dd1, dd2 = st.columns([1,1])
with dd1:
    dias_ganho = st.selectbox("Qtd. dias de ganho no ciclo", options=list(range(0, 11)), index=2)
with dd2:
    dias_perda = st.selectbox("Qtd. dias de perda no ciclo", options=list(range(0, 11)), index=1)
if dias_ganho == 0 and dias_perda == 0:
    st.error('O ciclo não pode ter 0 dias de ganho e 0 dias de perda ao mesmo tempo.')
    st.stop()


cc1, cc2, cc3 = st.columns([1,1,1])
with cc1:
    ganho_pct_txt = st.text_input("Percentual de ganho (%)", value="20,00", key="ganho_pct_txt", on_change=_format_pct_on_change_ganho)
with cc2:
    perda_pct_txt = st.text_input("Percentual de perda (%)", value="15,00", key="perda_pct_txt", on_change=_format_pct_on_change_perda)
with cc3:
    comeca_por = st.radio("Ciclo começa por:", options=["Ganho", "Perda"], index=0, horizontal=True)
st.caption("Ex.: Para 2 ganhos e 1 perda, informe ganho=2 e perda=1. Digite apenas números; a vírgula com duas casas é automática (ex.: 15 → 15,00).")

erro = None
ciclo = []
if data_erro:
    st.error(data_erro)
else:
    try:
        ganho_pct = _pct_str_br_to_float(st.session_state.get('ganho_pct_txt', ganho_pct_txt))
        perda_pct = _pct_str_br_to_float(st.session_state.get('perda_pct_txt', perda_pct_txt))
        ciclo = construir_ciclo(ganho_pct, perda_pct, dias_ganho, dias_perda, comeca_por)
        st.write("Ciclo multiplicativo:", ciclo)
    except Exception as e:
        erro = str(e)
        st.error(erro)

# ---------- Execução ----------
if st.button("Simular") and not (erro or data_erro) and data_fim is not None:
    df_ops = simular_operacoes(valor_inicial, data_inicio, data_fim, dias_ativos, ciclo)

    if df_ops.empty:
        st.warning("Nenhum dia de operação dentro do período/dias escolhidos.")
    else:
        container = st.container()

        # ----- Gráfico com fundo -----
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

        # ----- Tabela Plotly (texto preto, largura total) -----
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

        # ----- Valor final em destaque -----        # ----- Resumo final em tabela (valor final, lucro/prejuízo e retorno %) -----        # ----- Resumo final em tabela (valor final, lucro/prejuízo, retorno %, nº operações, retorno médio/operação) -----
        valor_final = df_ops["Valor (R$)"].iloc[-1]
        lucro = valor_final - valor_inicial
        retorno_pct = (valor_final / valor_inicial - 1.0) * 100.0 if valor_inicial > 0 else 0.0
        num_ops = int(len(df_ops))
        retorno_medio_op = float(df_ops["Variação (%)"].mean()) if num_ops > 0 else 0.0
        data_final = df_ops["Data"].iloc[-1].strftime("%d/%m/%Y")
        # Monta tabela 5 linhas x 2 colunas
        summary_labels = [
            "Valor final",
            "Lucro/Prejuízo",
            "Retorno (%)",
            "Nº de operações",
            "Retorno médio/operação"
        ]
        summary_vals = [
            f"R$ {br_num(valor_final)}",
            f"R$ {br_num(lucro)}",
            f"{br_num(retorno_pct)}%",
            f"{num_ops}",
            f"{br_num(retorno_medio_op)}%"
        ]
        lucro_color = '#1a7f37' if lucro >= 0 else '#b91c1c'
        retorno_color = '#1a7f37' if retorno_pct >= 0 else '#b91c1c'
        retorno_medio_color = '#1a7f37' if retorno_medio_op >= 0 else '#b91c1c'
        font_colors = [["black"]*5, ["black", lucro_color, retorno_color, "black", retorno_medio_color]]
        fig_sum = go.Figure(data=[go.Table(
            header=dict(values=[f"Resumo até {data_final}", ""], fill_color='#f0f0f0', align=['left','right'], font=dict(color='black')),
            cells=dict(values=[summary_labels, summary_vals], align=['left','right'], fill_color=[["white"]*5, ["white"]*5], font=dict(color=font_colors))
        )])
        fig_sum.update_layout(margin=dict(l=0,r=0,t=0,b=0))
        with container:
            st.plotly_chart(fig_sum, use_container_width=True)
