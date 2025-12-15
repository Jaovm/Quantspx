import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_ta as ta
import numpy as np

# --- 1. CONFIGURAÇÃO E UNIVERSO DE AÇÕES ---
# Universo de Ações Brasileiras (Apenas um exemplo ilustrativo e líquido)
TICKERS = [
    'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA',
    'WEGE3.SA', 'EGIE3.SA', 'RDOR3.SA', 'RENT3.SA', 'HAPV3.SA'
]
DIAS_HISTORICO = 365 # 1 ano de dados

@st.cache_data
def buscar_dados_e_analisar(tickers, dias_historico, roe_minimo, pl_maximo, ma_periodo):
    """
    Função principal que busca dados e aplica as estratégias Fundamentalista e Quantitativa.
    """
    st.info("Buscando dados de mercado e fundamentos... Isso pode levar alguns segundos.")
    resultados = []

    for ticker in tickers:
        try:
            # --- Busca de Dados (YFinance) ---
            
            # Dados de Preço para Análise Quantitativa
            dados_historicos = yf.download(ticker, period=f'{dias_historico}d', progress=False)
            
            # Dados Fundamentais para Análise Fundamentalista
            info = yf.Ticker(ticker).info
            
            # --- 2. ANÁLISE FUNDAMENTALISTA (Stock-Picking) ---
            # Uso de valores estimados ou disponíveis.
            roe = info.get('returnOnEquity', np.nan) 
            pl = info.get('trailingPE', np.nan)

            # Aplicação dos Filtros Fundamentais (Critérios do usuário)
            passa_fundamental = (roe >= roe_minimo) and (pl <= pl_maximo) if not np.isnan(roe) and not np.isnan(pl) else False

            # --- 3. ANÁLISE QUANTITATIVA (Market Timing) ---
            sinal_quant = "Dados históricos insuficientes"
            passa_quant = False
            ultimo_preco = np.nan
            
            if not dados_historicos.empty:
                # Calcula Média Móvel Simples (SMA)
                dados_historicos.ta.sma(length=ma_periodo, append=True)
                
                # Pega o último preço e a última média móvel
                ultimo_preco = dados_historicos['Close'].iloc[-1]
                ultima_ma = dados_historicos[f'SMA_{ma_periodo}'].iloc[-1]
                
                # Sinais Quantitativos
                if ultimo_preco > ultima_ma:
                    sinal_quant = "COMPRA (Tendência de Alta)"
                    passa_quant = True
                elif ultimo_preco < ultima_ma:
                    sinal_quant = "VENDA (Tendência de Baixa)"
                    passa_quant = False
                else:
                    sinal_quant = "NEUTRO"
                    passa_quant = False
            
            # --- 4. RESULTADO HÍBRIDO (Quantamental) ---
            # A ação é ideal se Passa no Fundamental E Passa no Quantitativo
            score_final = passa_fundamental + passa_quant
            status_estrategia = "IDEAL (Alinhamento Total)" if score_final == 2 else ("Em Análise (Falta Timing ou Fundamento)" if score_final == 1 else "Fora dos Critérios")

            resultados.append({
                "Ticker": ticker,
                "Preço Atual (R$)": f"{ultimo_preco:.2f}" if not np.isnan(ultimo_preco) else "N/A",
                
                # Colunas Fundamentais
                "ROE": f"{roe*100:.2f}%" if not np.isnan(roe) else "N/A",
                "P/L": f"{pl:.2f}" if not np.isnan(pl) else "N/A",
                "Passa Fund.": "Sim" if passa_fundamental else "Não",
                
                # Colunas Quantitativas
                f"Sinal MA({ma_periodo})": sinal_quant,
                "Passa Quant.": "Sim" if passa_quant else "Não",
                
                # Coluna Final
                "Status Estratégia": status_estrategia,
                "Score Híbrido": score_final
            })

        except Exception as e:
            # Em caso de erro na busca de dados (pode acontecer com tickers menos líquidos)
            # st.warning(f"Erro ao processar {ticker}: {e}") 
            resultados.append({
                "Ticker": ticker,
                "Preço Atual (R$)": "Erro",
                "ROE": "Erro",
                "P/L": "Erro",
                "Passa Fund.": "Não",
                f"Sinal MA({ma_periodo})": "Erro",
                "Passa Quant.": "Não",
                "Status Estratégia": "Erro de Conexão/Dados",
                "Score Híbrido": 0
            })

    df_final = pd.DataFrame(resultados)
    # Ordenar por Score, mostrando os melhores no topo
    df_final = df_final.sort_values(by="Score Híbrido", ascending=False)
    return df_final.drop(columns=["Score Híbrido"])

# --- 5. INTERFACE STREAMLIT ---
st.set_page_config(layout="wide", page_title="Clone Quantamental SPX - Python/Streamlit")
st.title("Sistema Quantamental Híbrido (Falcon/Patriot)")
st.caption("Automatizando Stock-Picking e Market Timing em Python.")
st.markdown("---")
# 

# Sidebar para Inputs do Usuário (Simula o controle do Gestor)
st.sidebar.header("Definição da Estratégia")

# Filtros Fundamentalistas (Stock-Picking)
st.sidebar.subheader("1. Critérios Fundamentalistas (Stock-Picking)")
roe_min = st.sidebar.slider("ROE Mínimo (%)", min_value=0.0, max_value=30.0, value=15.0, step=1.0) / 100
pl_max = st.sidebar.slider("P/L Máximo", min_value=5.0, max_value=50.0, value=25.0, step=1.0)

# Filtros Quantitativos (Market Timing)
st.sidebar.subheader("2. Critérios Quantitativos (Market Timing)")
ma_period = st.sidebar.slider("Período da Média Móvel (dias)", min_value=20, max_value=200, value=200, step=10)
st.sidebar.markdown(f"**Sinal de Compra:** Preço > MA({ma_period})")

st.sidebar.markdown("---")
st.sidebar.info(f"Analisando o universo de {len(TICKERS)} ações.")

# Botão para executar a análise
if st.button('EXECUTAR ANÁLISE HÍBRIDA'):
    with st.spinner('Processando dados...'):
        df_resultados = buscar_dados_e_analisar(TICKERS, DIAS_HISTORICO, roe_min, pl_max, ma_period)
    
    st.header("Resultados da Triagem Quantamental")
    
    # Destaque para as ações que passaram nos dois critérios
    melhores = df_resultados[df_resultados["Status Estratégia"] == "IDEAL (Alinhamento Total)"]
    
    if not melhores.empty:
        st.success(f"**{len(melhores)} Ações selecionadas!** - Alinhamento Total de Fundamento e Timing.")
        st.dataframe(melhores.set_index('Ticker'))
    else:
        st.warning("Nenhuma ação passou em *todos* os critérios definidos.")

    # Exibe a tabela completa
    st.markdown("### Ranking Completo dos Ativos")
    
    # Adiciona cores para facilitar a visualização
    def color_status(val):
        color = 'background-color: #d4edda' if 'IDEAL' in val else ('background-color: #fff3cd' if 'Em Análise' in val else '')
        return color
    
    def color_passa(val):
        color = 'background-color: #d4edda' if 'Sim' in val else 'background-color: #f8d7da'
        return color

    # Aplica o set_index no DataFrame ANTES de aplicar o estilo (CORREÇÃO)
    df_para_exibir = df_resultados.set_index('Ticker') 
    
    # Aplica o estilo no DataFrame que já tem o índice correto
    styled_df = df_para_exibir.style.applymap(color_status, subset=['Status Estratégia']) \
                                   .applymap(color_passa, subset=['Passa Fund.', 'Passa Quant.'])

    # Exibe o objeto Styler
    st.dataframe(styled_df, use_container_width=True)
    
    st.markdown("---")
    st.info("**Nota sobre dados:** Este script utiliza dados gratuitos do Yahoo Finance, que podem ter atrasos ou erros em dados fundamentais. Em um sistema profissional, APIs pagas e mais robustas seriam utilizadas.")

