import streamlit as st
import pandas as pd
from analysis import Analysis

# Configuração da página e inicialização do objeto de análise
st.set_page_config(page_title="Análise de Dados", layout="wide")
image1 = "logoInsper3.png"
image2 = "logoAlupar.png"

# Criar três colunas: uma vazia para empurrar as imagens para o canto direito
col1, col2, col3 = st.columns([6, 0.7, 0.5])

# Deixar a primeira coluna vazia para alinhamento
with col1:
    st.empty()

# Exibir as duas imagens na segunda e terceira colunas, lado a lado e alinhadas à direita
with col2:
    st.image(image1, width=88)

with col3:
    st.image(image2, width=100)

# Dados de login (em um sistema real, estas informações deveriam estar em um banco de dados seguro)
user_credentials = {
    "admin": "senha",
    "operador1": "alupar"
}

# Função de verificação de login
def login_page():
    st.title("🔐 Login")
    
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if username in user_credentials and user_credentials[username] == password:
                st.success("Login bem-sucedido!")
                st.session_state['logged_in'] = True
                st.session_state['current_page'] = 'upload_page'
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos. Tente novamente.")

# Função da página de upload
def upload_page():
    st.title("📊 Análise de Dados")
    
    st.markdown("""
    <div style="background-color: #1f77b4; padding: 20px; border-radius: 10px;">
        <h1 style="color: white; text-align: center;">Caro Operador, Bem-Vindo!</h1>
        <p style="color: #f0f0f0; text-align: center;">Anexe os arquivos necessários para começar a análise.</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📂 Anexar Arquivo do Nível do Poço (CSV ou XLSX)")
    file_nivel_poco = st.file_uploader("Anexe o arquivo do Nível do Poço", type=['csv', 'xlsx'], key="nivel_poco")

    st.subheader("📂 Anexar Arquivo do Histórico de Alarmes (CSV ou XLSX)")
    file_historico_alarmes = st.file_uploader("Anexe o arquivo do Histórico de Alarmes", type=['csv', 'xlsx'], key="historico_alarmes")

    # Inicializa a lista para armazenar as últimas 30 previsões
    if 'ultimas_previsoes' not in st.session_state:
        st.session_state['ultimas_previsoes'] = []

    # Mostrar o botão "Verificar Dados" apenas quando ambos os arquivos forem anexados
    if file_nivel_poco and file_historico_alarmes:
        if st.button("Verificar e Analisar Dados"):
            with st.spinner("Verificando e Analisando Dados..."):
                try:
                    # Ler os arquivos e armazenar na sessão
                    st.session_state['df_nivel_poco'] = pd.read_csv(file_nivel_poco) if file_nivel_poco.name.endswith('.csv') else pd.read_excel(file_nivel_poco)
                    st.session_state['df_historico_alarmes'] = pd.read_csv(file_historico_alarmes) if file_historico_alarmes.name.endswith('.csv') else pd.read_excel(file_historico_alarmes)

                    colunas_nivel_poco = ["TAG", "Data", "Valor"]
                    colunas_historico_alarmes = ["E3TimeStamp", "Acked", "Area", "ActorID", "ConditionActive", "EventType",
                                                 "Message", "Severity", "InTime", "OutTime", "AckTime", 
                                                 "FullAlarmSourceName", "FormattedValue", "Quality", 
                                                 "AlarmSourceName", "EventTime", "InTimeMS", "Source"]

                    if set(colunas_nivel_poco).issubset(st.session_state['df_nivel_poco'].columns) and \
                       set(colunas_historico_alarmes).issubset(st.session_state['df_historico_alarmes'].columns):
                        
                        # Análise e previsões
                        analysis_object = Analysis(st.session_state["df_nivel_poco"], st.session_state["df_historico_alarmes"])
                        analysis_object.preprocess()
                        analysis_object.split_cycles()
                        analysis_object.format()
                        prediction = analysis_object.predict()
                        st.session_state["previsoes_ultimos_ciclos"] = prediction[0]
                        st.session_state["proxima_falha_ciclos"] = prediction[0][-1]
                        st.session_state["proxima_falha_segundos"] = prediction[1] * prediction[0][-1]

                        # Adiciona a previsão à lista das últimas 30 previsões, convertendo para float
                        st.session_state['ultimas_previsoes'].append(float(prediction[0][-1]))  # Conversão para float
                        if len(st.session_state['ultimas_previsoes']) > 30:
                            st.session_state['ultimas_previsoes'] = st.session_state['ultimas_previsoes'][-30:]

                        st.session_state['data_verificada'] = True
                        if st.session_state['data_verificada']:
                            st.session_state['current_page'] = 'results_page'
                            st.rerun()
                    else:
                        st.session_state['data_verificada'] = False
                        st.error("⚠️ Um ou ambos os arquivos não são compatíveis com a análise!")
                except Exception as e:
                    st.session_state['data_verificada'] = False
                    st.error(f"Erro ao ler os arquivos: {e}")
    elif file_nivel_poco or file_historico_alarmes:
        st.warning("⚠️ Por favor, anexe ambos os arquivos para prosseguir.")

# Função da página de resultados
def results_page():
    st.title("Resultados da Análise dos Dados")
    
    st.markdown("""
    <div style="background-color: #28a745; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: white; text-align: center;">📈 Análise Completa</h2>
        <p style="color: #e2f5e9; text-align: center;">Os resultados detalhados dos dados carregados estão disponíveis abaixo.</p>
    </div>
    """, unsafe_allow_html=True)

    seconds = st.session_state["proxima_falha_segundos"]
    days = seconds // (24 * 60 * 60)
    seconds = seconds % (24 * 60 * 60)
    hours = round(seconds / (60 * 60))
    
    st.markdown("---")
    st.markdown("De acordo com o modelo, a próxima falha ocorrerá em %d ciclos." % st.session_state["proxima_falha_ciclos"], unsafe_allow_html=True)
    st.markdown("Isso deve ocorrer em, aproximadamente %d dias e %d horas" % (days, hours), unsafe_allow_html=True)
    
    # Exibir a lista das últimas 30 previsões
    st.write("Últimas 30 Previsões de Ciclos até a Falha:", st.session_state['ultimas_previsoes'])

    if st.button("Voltar à Página Principal"):
        st.session_state['current_page'] = 'upload_page'
        st.rerun()  # Recarrega a página para mostrar a página principal

# Controle de navegação e login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Verificar se o usuário está logado
if not st.session_state['logged_in']:
    login_page()
else:
    # Verificar qual página exibir
    if st.session_state['current_page'] == 'upload_page':
        upload_page()
    elif st.session_state['current_page'] == 'results_page':
        results_page()

# Colocar o botão de logout no final de todas as páginas
st.markdown("<hr>", unsafe_allow_html=True)
if st.session_state.get('logged_in', False):
    if st.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['current_page'] = 'login'
        st.rerun()

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
