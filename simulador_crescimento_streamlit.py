import re
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import streamlit as st

# cfg
T="✈️ Simulador Aviator — ganhos e perdas"; B="fundo_grafico.jpg"
st.set_page_config(page_title=T, layout="wide"); st.title(T); st.caption("Simule ciclos de ganhos e perdas e veja a evolução da banca como se estivesse no Aviator.")

# utils
f=lambda v:("{:,.2f}".format(v)).replace(",", "X").replace(".", ",").replace("X",".")
okd=lambda s: bool(re.fullmatch(r"\d{2}/\d{2}/\d{4}", (s or "").strip()))
pdt=lambda s: datetime.strptime(s.strip(),"%d/%m/%Y")
pp=lambda s: round(float((s or "").strip().replace(".","").replace(",", ".")),2) if (s or "").strip() else (_ for _ in ()).throw(ValueError("Preencha os percentuais de ganho e perda."))
def cy(g,p,dg,dp,ini):
    if dg<0 or dp<0: raise ValueError("Dias devem ser não negativos.")
    if dg==0 and dp==0: raise ValueError("Defina ao menos um dia de ganho ou de perda.")
    if g<0 or p<0: raise ValueError("Percentuais não podem ser negativos.")
    if p>=100: raise ValueError("Perda (%) deve ser < 100.")
    if g>500: raise ValueError("Ganho (%) muito alto (≤ 500%).")
    fg,fp=1+g/100,1-p/100; G,P=[fg]*dg,[fp]*dp
    return (G+P) if ini=="Ganho" else (P+G)
def sim(v0,di,df,act,cyc):
    v,i,d,h=v0,0,di,[]
    while d<=df:
        if d.weekday() in act and cyc:
            fct=cyc[i]; v*=fct; i=(i+1)%len(cyc)
            h.append({"Data":d,"Tipo":"Ganho"if fct>1 else("Perda"if fct<1 else"Neutro"),"Variação (%)":(fct-1)*100,"Valor (R$)":v})
        d+=timedelta(days=1)
    return pd.DataFrame(h)
def mdf():
    t=st.session_state.get("data_fim_txt",""); d="".join(ch for ch in t if ch.isdigit())[:8]
    st.session_state["data_fim_txt"]="" if not d else d if len(d)<=2 else f"{d[:2]}/{d[2:4]}" if len(d)<=4 else f"{d[:2]}/{d[2:4]}/{d[4:]}"
def mpc(k):
    t=st.session_state.get(k,""); d="".join(ch for ch in t if ch.isdigit())[:6]; st.session_state[k]=(f"{int(d)},00" if d else "")
def sty(df):
    def rs(r):
        bg = "#063a1a" if r["Tipo"] == "Ganho" else ("#3a0b0b" if r["Tipo"] == "Perda" else "#111217")
        return [f"background-color:{bg};color:white;" for _ in r]

    base_styles = [
        {"selector": "table", "props": [("width", "100%"), ("table-layout", "fixed"), ("border-collapse", "collapse"),
                                        ("font-family", "system-ui,-apple-system,Segoe UI,Roboto,Arial"), ("color", "#e5e7eb")]},
        {"selector": "th", "props": [("background", "#1f2430"), ("color", "white"), ("text-align", "left"), ("padding", "8px 10px")]},
        {"selector": "td", "props": [("padding", "6px 8px")]},
        {"selector": "td:nth-child(3)", "props": [("text-align", "right")]},
        {"selector": "td:nth-child(4)", "props": [("text-align", "right")]},
        {"selector": "td:nth-child(2)", "props": [("text-align", "center")]},
        # Hide index via CSS for maximum compatibility
        {"selector": ".row_heading, .blank", "props": [("display", "none")]},
    ]

    styler = df.style.apply(rs, axis=1).set_table_styles(base_styles)

    # Try native hide if available (newer pandas)
    try:
        styler = styler.hide(axis="index")
    except Exception:
        pass  # CSS above already hides index in most versions

    html = styler.to_html()
    colgroup = "<colgroup><col style='width:18%'><col style='width:22%'><col style='width:30%'><col style='width:30%'></colgroup>"
    html = html.replace("<table", "<table>" + colgroup, 1)
    return html
# inputs
hj=datetime.now().strftime("%d/%m/%Y")
c1,c2,c3=st.columns(3)
with c1: v0=st.number_input("Banca inicial (R$)", min_value=0.0, value=200.0, step=100.0)
with c2: di_txt=st.text_input("Início (dd/mm/aaaa)", value=hj)
with c3: df_txt=st.text_input("Fim (dd/mm/aaaa)", value="", key="data_fim_txt", on_change=mdf)
df_txt=st.session_state.get("data_fim_txt", df_txt)

err=None; di=df=None
if not okd(di_txt): err="Use dd/mm/aaaa, ex.: 07/08/2025."
elif not df_txt.strip(): err="Informe a data de fim no formato dd/mm/aaaa."
elif not okd(df_txt): err="Use dd/mm/aaaa, ex.: 07/08/2025."
else:
    di, df = pdt(di_txt), pdt(df_txt)
    if di>df: err="A data de início deve ser anterior ou igual à data de fim."
st.caption(f"Período selecionado: {di_txt} — {df_txt or '(defina a data de fim)'}")

st.subheader("📅 Dias com operações", anchor=False)
labs=["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"]; defs=[True,True,False,True,False,False,False]
cols=st.columns(7); acts=[]
for i,(lb,dv) in enumerate(zip(labs,defs)):
    with cols[i]:
        if st.checkbox(lb,value=dv): acts.append(i)
if not acts: st.warning("Selecione pelo menos um dia da semana para operar.")

st.subheader("🧠 Estratégia (ciclo)", anchor=False)
d1,d2=st.columns(2)
with d1: dg=st.selectbox("Dias de ganho por ciclo", list(range(11)), index=2)
with d2: dp=st.selectbox("Dias de perda por ciclo", list(range(11)), index=1)
if dg==0 and dp==0: st.error("O ciclo não pode ter 0 dias de ganho e 0 dias de perda ao mesmo tempo."); st.stop()
c1,c2,c3=st.columns(3)
with c1: g_txt=st.text_input("Ganho (%)", value="20,00", key="ganho_pct_txt", on_change=lambda: mpc("ganho_pct_txt"))
with c2: p_txt=st.text_input("Perda (%)", value="15,00", key="perda_pct_txt", on_change=lambda: mpc("perda_pct_txt"))
with c3: ini=st.radio("Ciclo começa por:", ["Ganho","Perda"], index=0, horizontal=True)
st.caption("Dica: digite só números; a vírgula com duas casas é automática (ex.: 15 → 15,00).")

if err: st.error(err); cyc=[]
else:
    try: g,p=pp(st.session_state.get("ganho_pct_txt", g_txt)), pp(st.session_state.get("perda_pct_txt", p_txt)); cyc=cy(g,p,dg,dp,ini)
    except Exception as e: st.error(e); cyc=[]

# run
if st.button("Simular estratégia 🚀") and not err and df is not None:
    d=sim(v0,di,df,acts,cyc)
    if d.empty: st.warning("Nenhum dia de operação dentro do período/dias escolhidos.")
    else:
        vf=d["Valor (R$)"].iloc[-1]; l=vf-v0; rt=(vf/v0-1)*100 if v0>0 else 0.0; n=len(d); rm=float(d["Variação (%)"].mean()) if n>0 else 0.0
        k1,k2,k3,k4=st.columns(4); k1.metric("Valor final (R$)",f(vf)); k2.metric("Lucro/Prejuízo (R$)",f(l)); k3.metric("Retorno (%)",f"{f(rt)}%"); k4.metric("Operações",f"{n}")
        v=d.copy(); v["Data"]=pd.to_datetime(v["Data"]).dt.strftime("%d/%m/%Y"); v["Variação (%)"]=v["Variação (%)"].map(lambda x:f"{f(x)}%"); v["Valor (R$)"]=v["Valor (R$)"].map(lambda x:f"R$ {f(x)}"); v=v[["Data","Tipo","Variação (%)","Valor (R$)"]].reset_index(drop=True)
        st.markdown("<div style='width:100%'>" + sty(v) + "</div>", unsafe_allow_html=True)
        st.markdown(rhtml(d,vf,l,rt,n,rm), unsafe_allow_html=True)