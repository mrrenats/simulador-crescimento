
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from datetime import datetime, timedelta
from pathlib import Path
import re

APP_TITLE = "Simulador de ganhos e perdas do Aviator"
DEFAULT_BG = "/mnt/data/fundo_grafico.jpg"

st.title(APP_TITLE)

# ---------- Utilidades ----------
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
    if not re.fullmatch(r"\\d{2}/\\d{2}/\\d{4}", s):
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

def montar_tabela_html(df_ops: pd.DataFrame, valor_inicial: float, data_inicio: datetime) -> str:
    linhas = []
    linhas.append(\"\"\"\
    <thead>
      <tr>
        <th style="text-align:left;padding:6px;">Data</th>
        <th style="text-align:left;padding:6px;">Tipo</th>
        <th style="text-align:right;padding:6px;">Variação (%)</th>
        <th style="text-align:right;padding:6px;">Valor (R$)</th>
      </tr>
    </thead>
    \"\"\"\
    )
    linhas.append(f\"\"\"\
    <tr style="background-color:#f0f0f0;">
      <td style="padding:6px;">{data_inicio.strftime('%d/%m/%Y')}</td>
      <td style="padding:6px;">Inicial</td>
      <td style="text-align:right;padding:6px;">-</td>
      <td style="text-align:right;padding:6px;">R$ {br_num(valor_inicial)}</td>
    </tr>
    \"\"\")
    if not df_ops.empty:
        for _, r in df_ops.iterrows():
            cor = "#e6ffe6" if r["Tipo"] == "Ganho" else ("#ffe6e6" if r["Tipo"] == "Perda" else "#ffffff")
            data_br = pd.to_datetime(r["Data"]).strftime("%d/%m/%Y")
            var_br = f"{br_num(r['Variação (%)'])}%"
            val_br = f"R$ {br_num(r['Valor (R$)'])}"
            linhas.append(f\"\"\"\
            <tr style="background-color:{cor};">
              <td style="padding:6px;">{data_br}</td>
              <td style="padding:6px;">{r['Tipo']}</td>
              <td style="text-align:right;padding:6px;">{var_br}</td>
              <td style="text-align:right;padding:6px;">{val_br}</td>
            </tr>
            \"\"\")
    html = f\"\"\"\
    <div style="overflow-x:auto;width:100%;max-width:100%;">
      <table style="border-collapse:collapse;width:100%;max-width:100%;font-family:system-ui,Arial,sans-serif;font-size:14px;">
        {''.join(linhas)}
      </table>
    </div>
    \"\"\"
    return html

# ---------- Entradas ----------
# Data atual BR como default de início; fim em branco
hoje = datetime.now().strftime("%d/%m/%Y")

st.subheader("Período e valor inicial")
c1, c2, c3 = st.columns([1,1,1])
with c1:
    valor_inicial = st.number_input("Valor inicial (R$)", min_value=0.0, value=200.0, step=100.0)
with c2:
    data_inicio_txt = st.text_input("Data de início (dd/mm/aaaa)", value=hoje)
with c3:
    data_fim_txt = st.text_input("Data de fim (dd/mm/aaaa)", value="")

data_erro = None
try:
    data_inicio = parse_data_br(data_inicio_txt)
    if not data_fim_txt.strip():
        data_erro = "Informe a data de fim no formato dd/mm/aaaa."
        data_fim = None
    else:
        data_fim = parse_data_br(data_fim_txt)
        if data_inicio > data_fim:
            data_erro = "A data de início deve ser anterior ou igual à data de fim."
except Exception as e:
    data_erro = str(e)
    data_fim = None

st.caption(f"Período selecionado: {data_inicio_txt} — {data_fim_txt or '(defina a data de fim)'}")

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

# ---------- Execução ----------
if st.button("Simular") and not (erro or data_erro) and data_fim is not None:
    df_ops = simular_operacoes(valor_inicial, data_inicio, data_fim, dias_ativos, ciclo)

    if df_ops.empty:
        st.warning("Nenhum dia de operação dentro do período/dias escolhidos.")
    else:
        container = st.container()

        # Gráfico com fundo DEFAULT_BG (se existir) e linha contrastante
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
            ax.set_facecolor("#111111")  # fundo escuro para dar contraste
            line_color = "black"         # linha preta p/ contraste no fundo escuro

        ax.plot(df_ops["Data"], df_ops["Valor (R$)"], linewidth=2.5, color=line_color, zorder=1)
        ax.set_xlabel("Data")
        ax.set_ylabel("Valor (R$)")
        ax.grid(True, alpha=0.3)
        fig.autofmt_xdate()

        with container:
            st.pyplot(fig, use_container_width=True)

        # Tabela full-width no mesmo container
        html = montar_tabela_html(df_ops, valor_inicial, data_inicio)
        with container:
            components.html(html, height=480, scrolling=True)

        valor_final = df_ops["Valor (R$)"].iloc[-1]
        data_final = df_ops["Data"].iloc[-1].strftime("%d/%m/%Y")
        st.success(f"Valor final em {data_final}: R$ {br_num(valor_final)}")
