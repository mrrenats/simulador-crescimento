
# simulador_crescimento_streamlit.py
# -*- coding: utf-8 -*-
# App Streamlit: Simulador de banca por ciclos de ganhos e perdas (tema Aviator)
# Agosto/2025 — mantém: sem gráficos; colgroup fixo; resumo HTML; tema Aviator; formatação BR; mesmas validações
# Acrescentado: badge de streak, barra de progresso do ciclo e som opcional de decolagem

import math
import base64
import io
from datetime import datetime, timedelta, date
from typing import List, Tuple, Dict, Any

import numpy as np
import pandas as pd
import streamlit as st

# =========================
# --------- CSS -----------
# =========================

CSS = """
<style>
:root{
  --avi-bg:#0b0d12;
  --avi-bg-2:#12151d;
  --avi-red:#ff2a2a;
  --avi-red-2:#c81818;
  --avi-green:#27d17f;
  --avi-green-2:#0fb96a;
  --avi-text:#e7e9ee;
  --avi-muted:#9aa2b1;
  --avi-yellow:#ffd166;
}
html,body,[data-testid="stAppViewContainer"]{
  background: radial-gradient(1200px 500px at 20% -10%, rgba(255,42,42,0.12), transparent 40%),
              radial-gradient(900px 400px at 120% 10%, rgba(255,42,42,0.08), transparent 50%),
              linear-gradient(180deg, var(--avi-bg), var(--avi-bg-2));
  color: var(--avi-text);
}
h1,h2,h3,h4,h5{ color: var(--avi-text); }
a{ color: var(--avi-yellow); }

/* Ribbon Aviator */
.ribbon{
  position: relative;
  padding: 14px 18px 14px 56px;
  margin: 6px 0 18px 0;
  background: linear-gradient(90deg, rgba(255,42,42,0.25), rgba(255,42,42,0.05));
  border: 1px solid rgba(255,42,42,0.35);
  border-radius: 14px;
  box-shadow: 0 0 32px rgba(255,42,42,0.18) inset, 0 6px 18px rgba(0,0,0,0.35);
}
.ribbon:before{
  content:"✈️";
  position:absolute;
  left:14px; top:10px;
  font-size:28px;
  filter: drop-shadow(0 0 6px rgba(255,42,42,0.5));
}
.badge{
  display:inline-block;
  padding:4px 10px;
  border-radius:999px;
  font-weight:700;
  font-size:12px;
  border:1px solid rgba(255,255,255,0.12);
  background:linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
  margin-left:8px;
}
.badge.red { color:#fff; background:linear-gradient(180deg, rgba(255,42,42,0.65), rgba(200,24,24,0.45)); border-color:rgba(255,42,42,0.65); }
.badge.green { color:#062e1b; background:linear-gradient(180deg, rgba(39,209,127,0.85), rgba(15,185,106,0.75)); border-color:rgba(39,209,127,0.9); }
.badge.yellow { color:#2a1e00; background:linear-gradient(180deg, rgba(255,209,102,0.85), rgba(190,150,60,0.75)); border-color:rgba(255,209,102,0.9); }

/* Botões com gradiente Aviator */
button[kind="secondary"]{ color: var(--avi-text) !important; }
.stButton>button{
  background: linear-gradient(180deg, #ff4747, #c81818);
  border: none;
  color: #fff;
  font-weight: 700;
  padding: 10px 16px;
  border-radius: 12px;
  box-shadow: 0 4px 18px rgba(255,42,42,0.35);
}
.stButton>button:hover{ filter:brightness(1.05); }

/* Tabela */
.table-wrap{
  width:100%;
}
.table-wrap table{
  width:100%;
  border-collapse:separate;
  border-spacing:0;
  background:rgba(255,255,255,0.02);
  border:1px solid rgba(255,255,255,0.08);
  border-radius:12px;
  overflow:hidden;
}
.table-wrap th, .table-wrap td{
  padding:10px 12px;
  font-size:14px;
}
.table-wrap thead th{
  background:rgba(255,255,255,0.04);
  color:var(--avi-muted);
  text-transform:uppercase;
  letter-spacing:.06em;
  font-size:12px;
}
.table-wrap tbody tr:nth-child(even){ background: rgba(255,255,255,0.02); }
.table-wrap .g{ color: var(--avi-green); font-weight:700; }
.table-wrap .r{ color: var(--avi-red); font-weight:700; }
.table-wrap .n{ color: var(--avi-muted); }

/* Resumo */
.resumo{
  margin-top: 14px;
  display:grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.card{
  padding:12px 14px;
  border:1px solid rgba(255,255,255,0.08);
  border-radius:12px;
  background:linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
  box-shadow: 0 4px 18px rgba(0,0,0,0.25);
}
.card h4{ margin:0; font-size:12px; color:var(--avi-muted); text-transform:uppercase; letter-spacing:.06em; }
.card .v{ font-weight:800; font-size:20px; margin-top:6px; }
.card .v.g{ color:var(--avi-green); }
.card .v.r{ color:var(--avi-red); }

/* Barra de progresso do ciclo */
.progress{
  margin: 12px 0 8px 0;
  width:100%;
}
.progress .label{
  display:flex; justify-content:space-between; font-size:12px; color:var(--avi-muted); margin-bottom:6px;
}
.progress .bar{
  width:100%; height:12px; background:rgba(255,255,255,0.06); border-radius:999px; overflow:hidden; border:1px solid rgba(255,255,255,0.08);
}
.progress .bar .fill{
  height:100%;
  background: linear-gradient(90deg, rgba(39,209,127,0.9), rgba(255,42,42,0.9));
  box-shadow: 0 0 12px rgba(255,42,42,0.35);
}

.small-note{ font-size:12px; color:var(--avi-muted); }

</style>
"""

# =========================
# ----- Utilitários -------
# =========================

def br_money(x: float) -> str:
    try:
        s = f"{x:,.2f}"
    except Exception:
        return "R$ 0,00"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

def br_percent(x: float) -> str:
    s = f"{x:.2f}".replace(".", ",")
    return f"{s}%"

def parse_float_br(s: str, default: float = 0.0) -> float:
    if s is None: return default
    s = str(s).strip()
    if s == "": return default
    # aceita apenas números; vírgula como decimal
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return default

def pdt(s: str):
    return datetime.strptime(s, "%d/%m/%Y").date()

def fmt_date(d):
    return d.strftime("%d/%m/%Y")

def okd(dini, dfim) -> bool:
    return dini <= dfim

def cy(ganhos:int, perdas:int, ganho_pct:float, perda_pct:float, start_ganho:bool):
    """Retorna lista do ciclo como [(fator, tipo), ...]"""
    if ganhos < 0 or perdas < 0: raise ValueError("Ganhos/Perdas não podem ser negativos.")
    if ganhos == 0 and perdas == 0: raise ValueError("Ciclo não pode ter 0 ganhos e 0 perdas ao mesmo tempo.")
    if not (0 <= perda_pct < 100): raise ValueError("Perda (%) deve ser >=0 e < 100.")
    if not (0 <= ganho_pct <= 500): raise ValueError("Ganho (%) deve ser >=0 e <= 500.")
    fg = 1 + ganho_pct/100.0
    fp = 1 - perda_pct/100.0
    bloco_g = [(fg,"Ganho")]*ganhos
    bloco_p = [(fp,"Perda")]*perdas
    ordem = []
    if ganhos == 0: ordem = bloco_p
    elif perdas == 0: ordem = bloco_g
    else:
        if start_ganho:
            ordem = bloco_g + bloco_p
        else:
            ordem = bloco_p + bloco_g
    return ordem

def dias_ativos_map(sel):
    # Seg=0 ... Dom=6
    order = ["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"]
    idx = set()
    for i, k in enumerate(order):
        if sel.get(k, False):
            idx.add(i)
    return idx

def sim(banca_inicial: float,
        dini,
        dfim,
        ativos_idx,
        ciclo):
    """Percorre as datas; aplica fator nos dias ativos; retorna df e kpis"""
    rows = []
    banca = banca_inicial
    if not ciclo:
        ciclo = [(1.0,"Neutro")]
    c_len = len(ciclo)
    c_i = -1  # começará em 0 na primeira operação
    total_ops = 0

    d = dini
    while d <= dfim:
        dow = d.weekday()  # 0 seg ... 6 dom
        if dow in ativos_idx:
            c_i = (c_i + 1) % c_len
            fator, tipo = ciclo[c_i]
            banca = banca * fator
            variacao = (fator - 1.0) * 100.0
            total_ops += 1
            rows.append({
                "Data": fmt_date(d),
                "Tipo": tipo,
                "Variação (%)": variacao,
                "Valor (R$)": banca,
                "Fator": fator,
                "CicloIndex": c_i,
                "CicloLen": c_len
            })
        d += timedelta(days=1)

    df = pd.DataFrame(rows, columns=["Data","Tipo","Variação (%)","Valor (R$)","Fator","CicloIndex","CicloLen"])
    val_final = banca if len(rows)>0 else banca_inicial
    lucro = val_final - banca_inicial
    retorno = ( (val_final / banca_inicial) - 1.0 ) * 100.0 if banca_inicial>0 else 0.0
    kpis = {
        "valor_final": val_final,
        "lucro": lucro,
        "retorno_pct": retorno,
        "operacoes": total_ops,
        "ciclo_len": c_len
    }
    return df, kpis

# =========================
# ---- Renderizadores ------
# =========================

def sty(df: pd.DataFrame) -> str:
    """Retorna HTML (pandas.Styler) com colgroup fixo, alinhamentos e cores por Tipo"""
    df2 = df.copy()
    # Formatação BR
    if "Variação (%)" in df2.columns:
        df2["Variação (%)"] = df2["Variação (%)"].apply(br_percent)
    if "Valor (R$)" in df2.columns:
        df2["Valor (R$)"] = df2["Valor (R$)"].apply(br_money)

    # Estilos por linha com base em Tipo (classes g/r/n)
    def _row_cls(row):
        t = str(row.get("Tipo",""))
        if t == "Ganho": return ['g','g','g','g']
        if t == "Perda": return ['r','r','r','r']
        return ['n','n','n','n']

    styler = (df2.style
                .hide(axis="index")
                .set_table_attributes('class="table-wrap"')
                .set_table_styles([
                    {"selector":"th.col_heading","props":"text-align:left;"},
                ])
                .set_properties(subset=["Tipo"], **{"text-align":"center"})
                .set_properties(subset=["Variação (%)","Valor (R$)"], **{"text-align":"right"})
                .apply(_row_cls, axis=1)
            )
    html = styler.to_html()

    # Injeta colgroup com larguras fixas: 18%, 22%, 30%, 30%
    colgroup = '<colgroup><col style="width:18%"><col style="width:22%"><col style="width:30%"><col style="width:30%"></colgroup>'
    html = html.replace("<table ", f"<table {colgroup} ", 1)
    return html

def rhtml(valor_final: float, lucro: float, retorno_pct: float, operacoes: int) -> str:
    """Resumo HTML com mesma paleta/estilo"""
    cls_lp = "g" if lucro >= 0 else "r"
    cls_rt = "g" if retorno_pct >= 0 else "r"
    return f'''
<div class="resumo">
  <div class="card">
    <h4>Valor Final</h4>
    <div class="v">{br_money(valor_final)}</div>
  </div>
  <div class="card">
    <h4>Lucro / Prejuízo</h4>
    <div class="v {cls_lp}">{br_money(lucro)}</div>
  </div>
  <div class="card">
    <h4>Retorno (%)</h4>
    <div class="v {cls_rt}">{br_percent(retorno_pct)}</div>
  </div>
  <div class="card">
    <h4>Operações</h4>
    <div class="v">{operacoes}</div>
  </div>
</div>
'''

def current_streak(df: pd.DataFrame):
    """Calcula o streak atual (sequência do mesmo Tipo no final)"""
    if df is None or df.empty: return {"tipo": "Neutro", "tamanho": 0}
    tipos = df["Tipo"].tolist()
    last = tipos[-1]
    n = 0
    for t in reversed(tipos):
        if t == last: n += 1
        else: break
    return {"tipo": last, "tamanho": n}

def cycle_progress_html(df: pd.DataFrame) -> str:
    """Barra de progresso do ciclo, baseada no último registro"""
    if df is None or df.empty:
        return """
        <div class="progress">
          <div class="label"><span>Ciclo</span><span>0/0</span></div>
          <div class="bar"><div class="fill" style="width:0%"></div></div>
          <div class="small-note">Sem operações no período.</div>
        </div>"""
    last = df.iloc[-1]
    idx = int(last.get("CicloIndex", 0))
    length = int(last.get("CicloLen", max(1, idx+1)))
    pct = int(round(((idx+1)/max(1,length))*100))
    tipo = last.get("Tipo","");
    return f"""
    <div class="progress">
      <div class="label"><span>Progresso do ciclo</span><span>{idx+1}/{length} — {tipo}</span></div>
      <div class="bar"><div class="fill" style="width:{pct}%"></div></div>
    </div>
    """

def beep_data_uri() -> str:
    """Gera um beep curto (WAV) embutido em data URI"""
    import struct, math, io, base64
    fr = 44100
    dur = 0.15
    freq = 880.0
    n = int(fr*dur)
    amp = 16000
    buf = io.BytesIO()

    data = bytearray()
    for i in range(n):
        t = i / fr
        sample = int(amp * math.sin(2*math.pi*freq*t) * (0.5 + 0.5*math.sin(2*math.pi*5*t)))
        data.extend(struct.pack('<h', sample))

    datasize = len(data)
    # RIFF header
    buf.write(b'RIFF')
    buf.write(struct.pack('<I', 36 + datasize))
    buf.write(b'WAVE')
    # fmt chunk
    buf.write(b'fmt ')
    buf.write(struct.pack('<I', 16))
    buf.write(struct.pack('<H', 1))
    buf.write(struct.pack('<H', 1))
    buf.write(struct.pack('<I', fr))
    buf.write(struct.pack('<I', fr*2))
    buf.write(struct.pack('<H', 2))
    buf.write(struct.pack('<H', 16))
    # data chunk
    buf.write(b'data')
    buf.write(struct.pack('<I', datasize))
    buf.write(data)

    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    return f"data:audio/wav;base64,{b64}"

# =========================
# --------- UI ------------
# =========================

def main():
    st.set_page_config(page_title="Simulador Aviator — Ciclos", page_icon="✈️", layout="centered")
    st.markdown(CSS, unsafe_allow_html=True)

    st.markdown('<div class="ribbon"><div style="font-weight:900;font-size:20px;">Simulador Aviator — Ciclos</div><div style="font-size:12px;color:var(--avi-muted)">Disciplina e previsibilidade • sem integração com apostas</div></div>', unsafe_allow_html=True)

    # Entradas
    col1, col2 = st.columns([1,1])
    with col1:
        banca_inicial = st.number_input("Banca inicial (R$)", min_value=0.0, value=1000.0, step=10.0, format="%.2f")
    with col2:
        st.write("")

    # Datas com máscara BR via text_input
    today = datetime.today().date()
    dini_str = st.text_input("Início (dd/mm/aaaa)", value=today.strftime("%d/%m/%Y"), help="Formato BR: dia/mês/ano")
    dfim_str = st.text_input("Fim (dd/mm/aaaa)", value=(today + timedelta(days=30)).strftime("%d/%m/%Y"), help="Formato BR: dia/mês/ano")

    # Dias com operações
    st.markdown("**Dias com operações**")
    c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
    dias_sel = {}
    with c1: dias_sel["Seg"] = st.checkbox("Seg", value=True)
    with c2: dias_sel["Ter"] = st.checkbox("Ter", value=True)
    with c3: dias_sel["Qua"] = st.checkbox("Qua", value=True)
    with c4: dias_sel["Qui"] = st.checkbox("Qui", value=True)
    with c5: dias_sel["Sex"] = st.checkbox("Sex", value=True)
    with c6: dias_sel["Sáb"] = st.checkbox("Sáb", value=False)
    with c7: dias_sel["Dom"] = st.checkbox("Dom", value=False)

    st.markdown("---")

    # Estratégia (ciclo)
    st.markdown("**Estratégia (ciclo)**")
    cA, cB, cC, cD = st.columns([1,1,1,1])
    with cA:
        dias_g = st.number_input("Dias de ganho por ciclo", min_value=0, max_value=10, value=2, step=1)
    with cB:
        dias_p = st.number_input("Dias de perda por ciclo", min_value=0, max_value=10, value=1, step=1)
    with cC:
        ganho_in = st.text_input("Ganho (%)", value="10,00", help="Digite só números; formata em 2 casas (ex.: 15,00)")
    with cD:
        perda_in = st.text_input("Perda (%)", value="5,00", help="Digite só números; formata em 2 casas (ex.: 15,00)")

    start_ganho = st.radio("Ciclo começa por", options=["Ganho","Perda"], index=0, horizontal=True)

    som_check = st.checkbox("Som de decolagem ao simular")

    # Botão simular
    simular = st.button("Simular estratégia 🚀")

    # Validações
    erros = []
    # datas
    try:
        dini = pdt(dini_str)
        dfim = pdt(dfim_str)
        if not okd(dini, dfim):
            erros.append("Data inicial não pode ser maior que a data final.")
    except Exception:
        erros.append("Datas inválidas. Use o formato dd/mm/aaaa.")
        dini = today
        dfim = today

    # dias ativos
    if not any(dias_sel.values()):
        erros.append("Selecione pelo menos um dia da semana para operar.")

    # percentuais
    ganho_pct = parse_float_br(ganho_in, 0.0)
    perda_pct = parse_float_br(perda_in, 0.0)
    if perda_pct >= 100 or perda_pct < 0:
        erros.append("Perda (%) deve ser >= 0 e < 100.")
    if ganho_pct < 0 or ganho_pct > 500:
        erros.append("Ganho (%) deve ser >= 0 e <= 500.")
    # ciclo não nulo
    if dias_g == 0 and dias_p == 0:
        erros.append("Ciclo não pode ter 0 ganhos e 0 perdas ao mesmo tempo.")

    if simular:
        if erros:
            for e in erros:
                st.error(e)
        else:
            try:
                ciclo = cy(dias_g, dias_p, ganho_pct, perda_pct, start_ganho=="Ganho")
                ativos_idx = dias_ativos_map(dias_sel)
                df, kpis = sim(banca_inicial, dini, dfim, ativos_idx, ciclo)

                # Badge de streak
                stks = current_streak(df)
                if stks["tamanho"] > 0 and stks["tipo"] in ("Ganho","Perda"):
                    bcls = "green" if stks["tipo"]=="Ganho" else "red"
                    sinal = "+" if stks["tipo"]=="Ganho" else "−"
                    st.markdown(f'<div class="badge {bcls}">Streak: {sinal}{stks["tamanho"]} {stks["tipo"].lower()}(s)</div>', unsafe_allow_html=True)

                # Barra de progresso do ciclo
                st.markdown(cycle_progress_html(df), unsafe_allow_html=True)

                # KPIs e resumo
                st.markdown(rhtml(kpis["valor_final"], kpis["lucro"], kpis["retorno_pct"], kpis["operacoes"]), unsafe_allow_html=True)

                # Tabela
                if df.empty:
                    st.info("Nenhuma operação no período com a configuração atual.")
                else:
                    st.markdown(sty(df), unsafe_allow_html=True)

                # Som opcional
                if som_check:
                    data_uri = beep_data_uri()
                    st.markdown(f'<audio autoplay style="display:none"><source src="{data_uri}" type="audio/wav"></audio>', unsafe_allow_html=True)

                # Notas
                st.markdown('<div class="small-note">Sem gráficos, colunas com larguras fixas e formatação BR preservadas.</div>', unsafe_allow_html=True)

            except Exception as ex:
                st.error(f"Erro durante a simulação: {ex}")

    else:
        if erros:
            for e in erros:
                st.warning(e)

    st.caption("Tema Aviator — disciplina e previsibilidade. Este simulador não integra com casas de aposta.")

if __name__ == "__main__":
    main()
