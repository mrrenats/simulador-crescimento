
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re

st.title("Simulador de Juros Compostos • Ciclos Personalizados (v3)")

# ===== Utilidades =====
def parse_percent_br(pct_str: str) -> float:
    \"\\"Converte '20,00%' ou '-15,00%' para fator multiplicativo (1.2 ou 0.85).\\"\\"
    if not isinstance(pct_str, str):
        raise ValueError("Percentual inválido: informe texto como '12,34%'.")
    s = pct_str.strip().replace(" ", "")
    if not re.fullmatch(r"-?\d{1,3},\d{2}%", s):
        raise ValueError("Formato inválido. Use algo como '20,00%' ou '-15,00%'.")
    negativo = s.startswith("-")
    s_num = s.replace("%", "").replace("-", "")
    valor = float(s_num.replace(",", "."))
    if negativo:
        valor = -valor
    fator = 1 + (valor / 100.0)
    return fator

def construir_ciclo(ganho_pct_str: str, perda_pct_str: str, dias_ganho: int, dias_perda: int, comeca_por: str):
    \"\\"Monta a lista de multiplicadores do ciclo conforme parâmetros.\\"\\"
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

def simular(valor_inicial, data_inicio, data_fim, dias_ativos, ciclo):
    # Retorna apenas os dias com operação aplicada
    valor = valor_inicial
    data_atual = data_inicio
    historico = []
    ciclo_index = 0

    while data_atual <= data_fim:
        if data_atual.weekday() in dias_ativos and len(ciclo) > 0:
            fator = ciclo[ciclo_index]
            valor_ant = valor
            valor = valor * fator
            ciclo_index = (ciclo_index + 1) % len(ciclo)

            variacao_pct = (fator - 1.0) * 100.0
            tipo = "Ganho" if variacao_pct > 0 else ("Perda" if variacao_pct < 0 else "Neutro")

            historico.append({
                "Data": data_atual,  # manter datetime para gráfico; formatar para tabela depois
                "Tipo": tipo,
                "Variação (%)": variacao_pct,
                "Valor (R$)": valor
            })
        data_atual += timedelta(days=1)

    df = pd.DataFrame(historico)
    return df

def formatar_df_br(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    # Formatar data no padrão brasileiro para a tabela
    out["Data"] = out["Data"].dt.strftime("%d/%m/%Y")
    # Formatar variação e valor em PT-BR
    out["Variação (%)"] = out["Variação (%)"].map(lambda v: f"{v:,.2f}%".replace(",", "X").replace(".", ",").replace("X", "."))
    out["Valor (R$)"] = out["Valor (R$)"].map(lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    return out

def colorir_linhas(row):
    # Recebe linha com colunas formatadas; usa 'Tipo'
    if row.get("Tipo") == "Ganho":
        return ["background-color: #e6ffe6"] * len(row)  # verde claro
    if row.get("Tipo") == "Perda":
        return ["background-color: #ffe6e6"] * len(row)  # vermelho claro
    return [""] * len(row)

# ===== Entradas =====
col1, col2 = st.columns(2)
with col1:
    valor_inicial = st.number_input("Valor inicial (R$)", min_value=0.0, value=200.0, step=100.0)
    data_inicio = st.date_input("Data de início", value=datetime(2025, 8, 7))
with col2:
    data_fim = st.date_input("Data de fim", value=datetime(2025, 12, 31))

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
ciclo_col1, ciclo_col2, ciclo_col3 = st.columns([1,1,1])
with ciclo_col1:
    ganho_pct_str = st.text_input("Percentual de ganho (ex.: 20,00%)", value="20,00%")
with ciclo_col2:
    perda_pct_str = st.text_input("Percentual de perda (ex.: -15,00%)", value="-15,00%")
with ciclo_col3:
    comeca_por = st.radio("Ciclo começa por:", options=["Ganho", "Perda"], index=0, horizontal=True)

dias_ganho = st.number_input("Quantidade de dias de ganho no ciclo", min_value=0, value=2, step=1)
dias_perda = st.number_input("Quantidade de dias de perda no ciclo", min_value=0, value=1, step=1)

st.caption("Monte o ciclo livremente. Ex.: 2 ganhos e 1 perda, iniciando por 'Ganho'.")

erro = None
ciclo = []
try:
    ciclo = construir_ciclo(ganho_pct_str, perda_pct_str, dias_ganho, dias_perda, comeca_por)
    st.write("Ciclo multiplicativo:", ciclo)
except Exception as e:
    erro = str(e)
    st.error(erro)

if st.button("Simular") and not erro:
    df_ops = simular(valor_inicial, data_inicio, data_fim, dias_ativos, ciclo)

    if df_ops.empty:
        st.warning("Nenhum dia de operação dentro do período/dias escolhidos.")
    else:
        # Gráfico: usar apenas dias com operação
        df_chart = df_ops[["Data", "Valor (R$)"]].copy().set_index("Data")
        st.line_chart(df_chart)

        # Tabela formatada em PT-BR e colorida por linha
        df_br = formatar_df_br(df_ops)
        styler = df_br.style.apply(colorir_linhas, axis=1)
        st.dataframe(styler, use_container_width=True)

        # Resumo final
        valor_final = df_ops["Valor (R$)"].iloc[-1]
        data_final = df_ops["Data"].iloc[-1].strftime("%d/%m/%Y")
        st.success(f"Valor final em {data_final}: R$ {valor_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
