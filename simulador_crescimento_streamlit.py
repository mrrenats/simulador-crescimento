
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re

st.title("Simulador de ganhos e perdas do Aviator")

# ===== Utilidades =====
def parse_percent_br(pct_str: str) -> float:
    """Converte '20,00%' ou '-15,00%' para fator multiplicativo (1.2 ou 0.85)."""
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
    """Recebe 'dd/mm/aaaa' e retorna datetime; lança ValueError se inválida."""
    s = (txt or '').strip()
    if not re.fullmatch(r"\d{2}/\d{2}/\d{4}", s):
        raise ValueError("Use o formato dd/mm/aaaa, ex.: 07/08/2025.")
    return datetime.strptime(s, "%d/%m/%Y")

def construir_ciclo(ganho_pct_str: str, perda_pct_str: str, dias_ganho: int, dias_perda: int, comeca_por: str):
    """Monta a lista de multiplicadores do ciclo conforme parâmetros."""
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
    """Retorna SOMENTE os dias com operação aplicada; sem dias parados."""
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

def formatar_br_num(v):
    return ("{:,.2f}".format(v)).replace(",", "X").replace(".", ",").replace("X", ".")

def montar_tabela_html(df_ops: pd.DataFrame, valor_inicial: float, data_inicio: datetime) -> str:
    """Gera HTML da tabela com linha inicial + dias com operação; com cores por linha."""
    linhas = []
    # Cabeçalho
    linhas.append("""
    <thead>
      <tr>
        <th style="text-align:left;padding:6px;">Data</th>
        <th style="text-align:left;padding:6px;">Tipo</th>
        <th style="text-align:right;padding:6px;">Variação (%)</th>
        <th style="text-align:right;padding:6px;">Valor (R$)</th>
      </tr>
    </thead>
    """)
    # Linha inicial (cinza)
    linhas.append(f"""
    <tr style="background-color:#f0f0f0;">
      <td style="padding:6px;">{data_inicio.strftime('%d/%m/%Y')}</td>
      <td style="padding:6px;">Inicial</td>
      <td style="text-align:right;padding:6px;">-</td>
      <td style="text-align:right;padding:6px;">R$ {formatar_br_num(valor_inicial)}</td>
    </tr>
    """)
    # Operações
    if not df_ops.empty:
        for _, r in df_ops.iterrows():
            cor = "#e6ffe6" if r["Tipo"] == "Ganho" else ("#ffe6e6" if r["Tipo"] == "Perda" else "#ffffff")
            data_br = pd.to_datetime(r["Data"]).strftime("%d/%m/%Y")
            var_br = f"{formatar_br_num(r['Variação (%)'])}%"
            val_br = f"R$ {formatar_br_num(r['Valor (R$)'])}"
            linhas.append(f"""
            <tr style="background-color:{cor};">
              <td style="padding:6px;">{data_br}</td>
              <td style="padding:6px;">{r['Tipo']}</td>
              <td style="text-align:right;padding:6px;">{var_br}</td>
              <td style="text-align:right;padding:6px;">{val_br}</td>
            </tr>
            """)
    html = f"""
    <div style="overflow-x:auto;">
      <table style="border-collapse:collapse;width:100%;font-family:system-ui,Arial,sans-serif;font-size:14px;">
        {''.join(linhas)}
      </table>
    </div>
    """
    return html

# ===== Entradas =====
st.subheader("Parâmetros do período e valor inicial")
c_top1, c_top2, c_top3 = st.columns([1,1,1])
with c_top1:
    valor_inicial = st.number_input("Valor inicial (R$)", min_value=0.0, value=200.0, step=100.0)
with c_top2:
    data_inicio_txt = st.text_input("Data de início (dd/mm/aaaa)", value="07/08/2025")
with c_top3:
    data_fim_txt = st.text_input("Data de fim (dd/mm/aaaa)", value="31/12/2025")

# Validar datas BR
data_erro = None
try:
    data_inicio = parse_data_br(data_inicio_txt)
    data_fim = parse_data_br(data_fim_txt)
    if data_inicio > data_fim:
        data_erro = "A data de início deve ser anterior ou igual à data de fim."
except Exception as e:
    data_erro = str(e)

st.caption(f"Período selecionado: {data_inicio_txt} — {data_fim_txt}")

st.subheader("Dias com operações")
dias_ativos = []
c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
with c1:
    if st.checkbox("Seg", value=True): dias_ativos.append(0)
with c2:
    if st.checkbox("Ter", value=True): dias_ativos.append(1)
with c3:
    if st.checkbox("Qua", value=False): dias_ativos.append(2)
with c4:
    if st.checkbox("Qui", value=True): dias_ativos.append(3)
with c5:
    if st.checkbox("Sex", value=False): dias_ativos.append(4)
with c6:
    if st.checkbox("Sáb", value=False): dias_ativos.append(5)
with c7:
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

if st.button("Simular") and not (erro or data_erro):
    df_ops = simular_operacoes(valor_inicial, data_inicio, data_fim, dias_ativos, ciclo)

    if df_ops.empty:
        st.warning("Nenhum dia de operação dentro do período/dias escolhidos.")
    else:
        df_chart = df_ops[["Data", "Valor (R$)"]].copy().set_index("Data")
        st.line_chart(df_chart)

        html = montar_tabela_html(df_ops, valor_inicial, data_inicio)
        st.markdown(html, unsafe_allow_html=True)

        valor_final = df_ops["Valor (R$)"].iloc[-1]
        data_final = df_ops["Data"].iloc[-1].strftime("%d/%m/%Y")
        st.success(("Valor final em {}: R$ {}".format(
            data_final,
            ("{:,.2f}".format(valor_final)).replace(",", "X").replace(".", ",").replace("X", ".")
        )))
