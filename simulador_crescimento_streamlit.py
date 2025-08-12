
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from datetime import datetime, timedelta
from pathlib import Path
import re

# =============================
# Config / Tema (Aviator)
# =============================
APP_TITLE = "✈️ Simulador Aviator — ganhos e perdas"
DEFAULT_BG = "/mnt/data/fundo_grafico.jpg"  # se existir, é usado no fundo do gráfico

st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)
st.caption("Simule ciclos de ganhos e perdas e veja a evolução da banca como se estivesse no Aviator.")

# =============================
# Utilidades
# =============================
def parse_data_br(txt: str) -> datetime:
    s = (txt or "").strip()
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s):
        raise ValueError("Use o formato dd/mm/aaaa, ex.: 07/08/2025.")
    return datetime.strptime(s, "%d/%m/%Y")

def construir_ciclo(ganho_pct: float, perda_pct: float, dias_ganho: int, dias_perda: int, comeca_por: str):
    if dias_ganho < 0 or dias_perda < 0:
        raise ValueError("A quantidade de dias deve ser não negativa.")
    if dias_ganho == 0 and dias_perda == 0:
        raise ValueError("Defina ao menos um dia de ganho ou de perda.")
    fator_ganho = 1 + (ganho_pct / 100.0)
    fator_perda = 1 - (perda_pct / 100.0)
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

# ----- Máscaras -----
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

def _format_pct_on_change_ganho():
    txt = st.session_state.get("ganho_pct_txt", "")
    digits = "".join(ch for ch in txt if ch.isdigit())[:6]
    st.session_state["ganho_pct_txt"] = f"{int(digits)},00" if digits else ""

def _format_pct_on_change_perda():
    txt = st.session_state.get("perda_pct_txt", "")
    digits = "".join(ch for ch in txt if ch.isdigit())[:6]
    st.session_state["perda_pct_txt"] = f"{int(digits)},00" if digits else ""

def _pct_str_br_to_float(pct_txt: str) -> float:
    s = (pct_txt or "").strip()
    if not s:
        raise ValueError("Preencha os percentuais de ganho e perda.")
    s_num = s.replace(".", "").replace(",", ".")
    return round(float(s_num), 2)

# =============================
# Entradas
# =============================
hoje = datetime.now().strftime("%d/%m/%Y")

st.subheader("🎯 Banca inicial e período", anchor=False)
c1, c2, c3 = st.columns([1,1,1])
with c1:
    valor_inicial = st.number_input("Banca inicial (R$)", min_value=0.0, value=200.0, step=100.0)
with c2:
    data_inicio_txt = st.text_input("Início (dd/mm/aaaa)", value=hoje)
with c3:
    data_fim_txt = st.text_input("Fim (dd/mm/aaaa)", value="", key="data_fim_txt", on_change=_format_data_fim_on_change)

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

st.subheader("📅 Dias com operações", anchor=False)
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

st.subheader("🧠 Estratégia (ciclo)", anchor=False)
dd1, dd2 = st.columns([1,1])
with dd1:
    dias_ganho = st.selectbox("Dias de ganho por ciclo", options=list(range(0, 11)), index=2)
with dd2:
    dias_perda = st.selectbox("Dias de perda por ciclo", options=list(range(0, 11)), index=1)

if dias_ganho == 0 and dias_perda == 0:
    st.error("O ciclo não pode ter 0 dias de ganho e 0 dias de perda ao mesmo tempo.")
    st.stop()

cc1, cc2, cc3 = st.columns([1,1,1])
with cc1:
    ganho_pct_txt = st.text_input("Ganho (%)", value="20,00", key="ganho_pct_txt", on_change=_format_pct_on_change_ganho)
with cc2:
    perda_pct_txt = st.text_input("Perda (%)", value="15,00", key="perda_pct_txt", on_change=_format_pct_on_change_perda)
with cc3:
    comeca_por = st.radio("Ciclo começa por:", options=["Ganho", "Perda"], index=0, horizontal=True)

st.caption("Dica: digite só números; a vírgula com duas casas é automática (ex.: 15 → 15,00).")

erro = None
ciclo = []
if data_erro:
    st.error(data_erro)
else:
    try:
        ganho_pct = _pct_str_br_to_float(st.session_state.get("ganho_pct_txt", ganho_pct_txt))
        perda_pct = _pct_str_br_to_float(st.session_state.get("perda_pct_txt", perda_pct_txt))
        ciclo = construir_ciclo(ganho_pct, perda_pct, dias_ganho, dias_perda, comeca_por)
        st.write("Ciclo multiplicativo:", ciclo)
    except Exception as e:
        erro = str(e)
        st.error(e)

# =============================
# Execução
# =============================
if st.button("Simular estratégia 🚀") and not (erro or data_erro) and data_fim is not None:
    df_ops = simular_operacoes(valor_inicial, data_inicio, data_fim, dias_ativos, ciclo)

    if df_ops.empty:
        st.warning("Nenhum dia de operação dentro do período/dias escolhidos.")
    else:
        container = st.container()

        # ----- Gráfico com fundo (tema Aviator) -----
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
            ax.set_facecolor("#0b0d12")
            line_color = "white"

        ax.plot(df_ops["Data"], df_ops["Valor (R$)"], linewidth=2.6, color=line_color, zorder=1)
        ax.set_xlabel("Data")
        ax.set_ylabel("Banca (R$)")
        ax.grid(True, alpha=0.25)
        fig.autofmt_xdate()

        with container:
            st.pyplot(fig, use_container_width=True)

        # ----- Tabela detalhada (rolável, sem índice, colorida por ganho/perda) -----
        df_view = df_ops.copy()
        df_view["Data"] = pd.to_datetime(df_view["Data"]).dt.strftime("%d/%m/%Y")
        df_view["Variação (%)"] = df_view["Variação (%)"].map(lambda v: f"{br_num(v)}%")
        df_view["Valor (R$)"] = df_view["Valor (R$)"].map(lambda v: f"R$ {br_num(v)}")
        df_view = df_view[["Data", "Tipo", "Variação (%)", "Valor (R$)"]]
        df_view.reset_index(drop=True, inplace=True)

        def _row_style(row):
            bg = "#063a1a" if row["Tipo"] == "Ganho" else ("#3a0b0b" if row["Tipo"] == "Perda" else "#111217")
            return [f"background-color: {bg}; color: white;" for _ in row]

        try:
            styled = df_view.style.apply(_row_style, axis=1).hide(axis="index")
        except Exception:
            styled = df_view.style.apply(_row_style, axis=1).hide_index()

        with container:
            st.dataframe(styled, use_container_width=True, height=520)

        # ----- Resumo (HTML) — Valor final como 1ª linha -----
        valor_final = df_ops["Valor (R$)"].iloc[-1]
        lucro = valor_final - valor_inicial
        retorno_pct = (valor_final / valor_inicial - 1.0) * 100.0 if valor_inicial > 0 else 0.0
        num_ops = int(len(df_ops))
        retorno_medio_op = float(df_ops["Variação (%)"].mean()) if num_ops > 0 else 0.0
        data_final = df_ops["Data"].iloc[-1].strftime("%d/%m/%Y")

        lucro_color = "#16a34a" if lucro >= 0 else "#dc2626"
        retorno_color = "#16a34a" if retorno_pct >= 0 else "#dc2626"
        retorno_medio_color = "#16a34a" if retorno_medio_op >= 0 else "#dc2626"

        resumo_html = f"""
        <div style='width:100%;'>
          <table style='width:100%; border-collapse:collapse; font-family:system-ui, -apple-system, Segoe UI, Roboto, Arial; color:#e5e7eb;'>
            <thead>
              <tr>
                <th style='text-align:left; padding:10px; background:#1f2430; font-weight:700;'>Resumo até {data_final}</th>
                <th style='text-align:right; padding:10px; background:#1f2430; font-weight:700;'></th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style='padding:10px; background:#111217;'>Valor final</td>
                <td style='padding:10px; background:#111217; text-align:right;'><span style='font-weight:800; font-size:17px;'>R$ {br_num(valor_final)}</span></td>
              </tr>
              <tr>
                <td style='padding:10px; background:#111217;'>Lucro/Prejuízo</td>
                <td style='padding:10px; background:#111217; text-align:right; color:{lucro_color};'>R$ {br_num(lucro)}</td>
              </tr>
              <tr>
                <td style='padding:10px; background:#111217;'>Retorno (%)</td>
                <td style='padding:10px; background:#111217; text-align:right; color:{retorno_color};'>{br_num(retorno_pct)}%</td>
              </tr>
              <tr>
                <td style='padding:10px; background:#111217;'>Nº de operações</td>
                <td style='padding:10px; background:#111217; text-align:right;'>{num_ops}</td>
              </tr>
              <tr>
                <td style='padding:10px; background:#111217;'>Retorno médio/operação</td>
                <td style='padding:10px; background:#111217; text-align:right; color:{retorno_medio_color};'>{br_num(retorno_medio_op)}%</td>
              </tr>
            </tbody>
          </table>
        </div>
        """
        with container:
            st.markdown(resumo_html, unsafe_allow_html=True)
