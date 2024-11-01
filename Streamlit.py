import streamlit as st
import pandas as pd
import plotly.express as px
#
# Configuração da página
st.set_page_config(page_title="Análise de Dados", layout="wide")
image1 = "logoInsper3.png"
image2 = "logoAlupar.png"

# Criar três colunas: uma vazia para empurrar as imagens para o canto direito
col1, col2, col3 = st.columns([6, 0.7, 0.5])  # Ajuste as proporções conforme necessário

# Deixar a primeira coluna vazia para alinhamento
with col1:
    st.empty()

# Exibir as duas imagens na segunda e terceira colunas, lado a lado e alinhadas à direita
with col2:
    st.image(image1, width=88)

with col3:
    st.image(image2, width=100)
    
# Definição das páginas
def upload_page():
    st.title("📊 Análise de Dados")
    
    # Personalização do cabeçalho
    st.markdown("""
    <div style="background-color: #1f77b4; padding: 20px; border-radius: 10px;">
        <h1 style="color: white; text-align: center;">Caro Operador, Bem-Vindo!</h1>
        <p style="color: #f0f0f0; text-align: center;">Anexe os arquivos necessários para começar a análise.</p>
    </div>
    """, unsafe_allow_html=True)

    # Upload dos arquivos separados para Nível do Poço e Histórico de Alarmes
    st.subheader("📂 Anexar Arquivo do Nível do Poço (CSV ou XLSX)")
    file_nivel_poco = st.file_uploader("Anexe o arquivo do Nível do Poço", type=['csv', 'xlsx'], key="nivel_poco")

    st.subheader("📂 Anexar Arquivo do Histórico de Alarmes (CSV ou XLSX)")
    file_historico_alarmes = st.file_uploader("Anexe o arquivo do Histórico de Alarmes", type=['csv', 'xlsx'], key="historico_alarmes")

    # Verificar se os arquivos foram carregados corretamente
    if file_nivel_poco and file_historico_alarmes:
        st.success("✅ Ambos os arquivos foram carregados com sucesso!")
    elif file_nivel_poco or file_historico_alarmes:
        st.warning("⚠️ Por favor, anexe ambos os arquivos para prosseguir.")
    
    # Botão para iniciar a análise (visível apenas quando ambos os arquivos estão carregados)
    if file_nivel_poco and file_historico_alarmes:
        # Botão "Análise das Bombas de Drenagem e Esgotamento UHE SJO"
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🔍 Análisar os Dados"):
            try:
                # Salvar os arquivos no estado da sessão
                st.session_state['file_nivel_poco'] = file_nivel_poco
                st.session_state['file_historico_alarmes'] = file_historico_alarmes
                st.session_state['page'] = 'analysis'
                st.rerun()
            except Exception as e:
                st.error(f"Erro inesperado ao processar os arquivos: {e}")

# Página de análise dos dados
def analysis_page():
    st.title("📈 Resultados da Análise de Dados")
    
    # Verificar se os arquivos foram carregados
    if 'file_nivel_poco' not in st.session_state or 'file_historico_alarmes' not in st.session_state:
        st.warning("Por favor, volte para a página de upload e anexe ambos os arquivos.")
        return

    file1 = st.session_state['file_nivel_poco']
    file2 = st.session_state['file_historico_alarmes']
    
    try:
        # Ler os arquivos
        if file1.name.endswith('.csv'):
            df1 = pd.read_csv(file1)
        else:
            df1 = pd.read_excel(file1)
        
        if file2.name.endswith('.csv'):
            df2 = pd.read_csv(file2)
        else:
            df2 = pd.read_excel(file2)
        
        # Verificar se ambos os arquivos contêm dados
        if df1.empty or df2.empty:
            st.warning("Um ou ambos os arquivos estão vazios ou mal formatados.")
            return

        # Concatenar os dataframes
        combined_df = pd.concat([df1, df2], axis=0)

        # Filtrar colunas numéricas
        df_numeric = combined_df.select_dtypes(include=['number'])

        if df_numeric.empty:
            st.warning("Os arquivos não contêm colunas numéricas para análise.")
            return

        # Dashboard com Plotly
        st.subheader("📊 Dashboard de Análise")

        # Exibir algumas estatísticas básicas
        col1, col2, col3 = st.columns(3)
        col1.metric("Número de Linhas", combined_df.shape[0])
        col2.metric("Número de Colunas", combined_df.shape[1])
        col3.metric("Colunas Numéricas", df_numeric.shape[1])

        # Gráficos com Plotly (comentados)
        # st.subheader("Gráficos Interativos")

        # # Gráfico de linhas - Exemplo com as duas primeiras colunas numéricas
        # if df_numeric.shape[1] >= 2:
        #     line_fig = px.line(df_numeric, x=df_numeric.index, y=df_numeric.columns[:2],
        #                        title="Gráfico de Linhas",
        #                        labels={"index": "Índice", "value": "Valor"},
        #                        template="plotly_dark")
        #     st.plotly_chart(line_fig)

        # # Gráfico de dispersão
        # if df_numeric.shape[1] >= 2:
        #     scatter_fig = px.scatter(df_numeric, x=df_numeric.columns[0], y=df_numeric.columns[1],
        #                              title="Gráfico de Dispersão",
        #                              labels={df_numeric.columns[0]: "Eixo X", df_numeric.columns[1]: "Eixo Y"},
        #                              template="plotly_dark")
        #     st.plotly_chart(scatter_fig)

        # # Gráfico de barras
        # bar_fig = px.bar(df_numeric, x=df_numeric.index, y=df_numeric.columns[0],
        #                  title="Gráfico de Barras",
        #                  labels={"index": "Índice", df_numeric.columns[0]: df_numeric.columns[0]},
        #                  template="plotly_dark")
        # st.plotly_chart(bar_fig)
    
    except Exception as e:
        st.error(f"Erro durante a análise dos dados: {e}")

    # Adicionar funcionalidade ao botão "Voltar para a Página Principal"
    if st.button("Voltar para a Página Principal"):
        st.session_state['page'] = 'upload'
        st.rerun()

# Verificar qual página exibir
if 'page' not in st.session_state:
    st.session_state['page'] = 'upload'

if st.session_state['page'] == 'upload':
    upload_page()
elif st.session_state['page'] == 'analysis':
    analysis_page()

# Configuração de cores e estilo
st.markdown("""
    <style>
    .css-18e3th9 {
        padding: 2rem;
    }
    .css-1d391kg {
        background-color: #f4f4f4;
        border-radius: 10px;
        padding: 1rem;
    }
    .css-145kmo2 {
        color: #6c757d;
    }
    .css-1vbd788 {
        background-color: #007bff;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        margin-top: 2rem;
    }
    .css-1vbd788:hover {
        background-color: #0056b3;
        color: white;
    }
    .css-1q8dd3e p {
        font-size: 18px;
    }
    </style>
    """, unsafe_allow_html=True)
