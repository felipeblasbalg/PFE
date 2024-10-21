import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(page_title="Análise de Dados", layout="wide")

# Definição das páginas
def upload_page():
    st.title("📊 Análise de Dados")
    
    # Personalização do cabeçalho
    st.markdown("""
    <div style="background-color: #1f77b4; padding: 20px; border-radius: 10px;">
        <h1 style="color: white; text-align: center;">Caro Operador, Bem-Vindo!</h1>
        <p style="color: #f0f0f0; text-align: center;">Anexe seu arquivo CSV ou XLSX abaixo para começar a análise.</p>
    </div>
    """, unsafe_allow_html=True)

    # Upload do arquivo
    uploaded_file = st.file_uploader("📂 Anexar Arquivo", type=['csv', 'xlsx'])

    # Se o arquivo for carregado
    if uploaded_file is not None:
        st.success("✅ Arquivo carregado com sucesso!")
        st.write("Clique no botão abaixo para analisar os dados.")
        
        # Botão para analisar os dados
        if st.button("🔍 Analisar os Dados"):
            # Salvar o arquivo no estado da sessão
            st.session_state['uploaded_file'] = uploaded_file
            st.session_state['page'] = 'analysis'

# Página de análise dos dados
def analysis_page():
    st.title("📈 Resultados da Análise de Dados")
    
    # Verificar se o arquivo foi carregado
    if 'uploaded_file' not in st.session_state:
        st.warning("Por favor, volte para a página de upload e anexe um arquivo.")
        return

    file = st.session_state['uploaded_file']
    
    # Ler o arquivo
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    # Filtrar colunas numéricas
    df_numeric = df.select_dtypes(include=['number'])

    if df_numeric.empty:
        st.warning("O arquivo não contém colunas numéricas para análise.")
        return

    # Dashboard com Plotly
    st.subheader("📊 Dashboard de Análise")

    # Exibir algumas estatísticas básicas
    col1, col2, col3 = st.columns(3)
    col1.metric("Número de Linhas", df.shape[0])
    col2.metric("Número de Colunas", df.shape[1])
    col3.metric("Colunas Numéricas", df_numeric.shape[1])

    # Gráficos com Plotly
    st.subheader("Gráficos Interativos")

    # Gráfico de linhas - Exemplo com as duas primeiras colunas numéricas (primeiro gráfico)
    if df_numeric.shape[1] >= 2:
        line_fig = px.line(df_numeric, x=df_numeric.index, y=df_numeric.columns[:2],
                           title="Gráfico de Linhas",
                           labels={"index": "Índice", "value": "Valor"},
                           template="plotly_dark")
        st.plotly_chart(line_fig)

    # Gráfico de dispersão (Scatter plot) - Exemplo com as duas primeiras colunas numéricas
    if df_numeric.shape[1] >= 2:
        scatter_fig = px.scatter(df_numeric, x=df_numeric.columns[0], y=df_numeric.columns[1],
                                 title="Gráfico de Dispersão",
                                 labels={df_numeric.columns[0]: "Eixo X", df_numeric.columns[1]: "Eixo Y"},
                                 template="plotly_dark")
        st.plotly_chart(scatter_fig)

    # Gráfico de barras - Exemplo com a primeira coluna numérica
    bar_fig = px.bar(df_numeric, x=df_numeric.index, y=df_numeric.columns[0],
                     title="Gráfico de Barras",
                     labels={"index": "Índice", df_numeric.columns[0]: df_numeric.columns[0]},
                     template="plotly_dark")
    st.plotly_chart(bar_fig)
    
    # Adicionar funcionalidade ao botão "Voltar para a Página Principal"
    if st.button("Voltar para a Página Principal"):
        st.session_state['page'] = 'upload'

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

# Adicionar uma imagem de fundo na página de upload
st.markdown("""
    <style>
    .css-1d391kg {
        background-image: url('https://www.transparenttextures.com/patterns/cubes.png');
    }
    </style>
    """, unsafe_allow_html=True)
