# ✈️ Simulador de Crescimento — Tema Aviator

**Arquivo principal:** `simulador_crescimento_streamlit.py`  
**Objetivo:** simular evolução da banca aplicando ciclos de **ganhos** e **perdas** em dias selecionados, com **máscaras BR** para datas e percentuais.

## 🔧 Como rodar
```bash
# clone o repositório
git clone <SEU_REPO.git>
cd <SEU_REPO>

# (opcional) crie e ative um ambiente virtual
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# instale as dependências
pip install -r requirements.txt

# execute
streamlit run simulador_crescimento_streamlit.py
```

## 🧠 Funcionalidades principais
- **Entrada**: banca inicial, data início/fim (formato `dd/mm/aaaa`), dias da semana, dias de ganho/perda, percentuais (mascara automática `15` → `15,00%`), ordem de início do ciclo (ganho/perda).
- **Processamento**: ciclo multiplicativo com validações fortes (perda < 100%, sem negativos, limites de ganho razoáveis).
- **Saída**: KPIs (`st.metric`), gráfico com **tema escuro** (usa `fundo_grafico.jpg` se presente), tabela detalhada **colorida** por ganho/perda e **exportações** (CSV e XLSX).

## 🎨 Tema Aviator
- Se o arquivo `fundo_grafico.jpg` estiver na raiz do projeto, ele é usado como **fundo do gráfico**.
- Já incluímos um `fundo_grafico.jpg` placeholder. Você pode substituí-lo por outro de sua preferência (mesmo nome).

## 📦 Estrutura
```
.
├─ simulador_crescimento_streamlit.py
├─ requirements.txt
├─ .gitignore
├─ .streamlit/
│  └─ config.toml
└─ fundo_grafico.jpg
```

## ⚠️ Avisos
- Este app **não** conecta com sites de apostas e serve **somente** para simulação/educação financeira.
- Percentuais irreais geram resultados enganosos — use com parcimônia.
