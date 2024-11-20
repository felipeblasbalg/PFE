import streamlit as st
import pandas as pd
from analysis import Analysis
import plotly.graph_objects as go
lista = [15,13,12,15,12,10,11,9,8,6,9,8]
# Configuração da página e inicialização do objeto de análise
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

# Dados de login (em um sistema real, estas informações deveriam estar em um banco de dados seguro)
user_credentials = {
    "admin": "senha",  # Exemplo de credencial
    "operador1": "alupar"
}

def to_days_and_hours(seconds):
    days = int(seconds // (24 * 60 * 60))
    seconds = seconds % (24 * 60 * 60)
    hours = round(seconds / (60 * 60))
    return days, hours

# Função de verificação de login
def login_page():
    st.title("🔐 Login")
    
    # Criar um formulário para capturar a entrada de usuário e senha
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

    # Mostrar o botão "Verificar Dados" apenas quando ambos os arquivos forem anexados
    if file_nivel_poco and file_historico_alarmes:
        if st.button("Verificar e Analisar Dados"):
            with st.spinner("Verificando e Analisando Dados..."):
                try:
                    # Ler os arquivos e armazenar na sessão para não repetir a leitura
                    st.session_state['df_nivel_poco'] = pd.read_csv(file_nivel_poco) if file_nivel_poco.name.endswith('.csv') else pd.read_excel(file_nivel_poco)
                    st.session_state['df_historico_alarmes'] = pd.read_csv(file_historico_alarmes) if file_historico_alarmes.name.endswith('.csv') else pd.read_excel(file_historico_alarmes)

                    # Verificar as colunas esperadas
                    colunas_nivel_poco = ["TAG", "Data", "Valor"]
                    colunas_historico_alarmes = ["E3TimeStamp", "Acked", "Area", "ActorID", "ConditionActive", "EventType",
                                                 "Message", "Severity", "InTime", "OutTime", "AckTime", 
                                                 "FullAlarmSourceName", "FormattedValue", "Quality", 
                                                 "AlarmSourceName", "EventTime", "InTimeMS", "Source"]

                    if set(colunas_nivel_poco).issubset(st.session_state['df_nivel_poco'].columns) and \
                       set(colunas_historico_alarmes).issubset(st.session_state['df_historico_alarmes'].columns):
                        
                        # análise de dados real
                        analysis_object = Analysis(st.session_state["df_nivel_poco"], st.session_state["df_historico_alarmes"])
                        print("Inicialização da análise                 OK")
                        analysis_object.preprocess()
                        print("Preprocessamento dos dados               OK")
                        analysis_object.split_cycles()
                        print("Formatação dos dados para a predição     OK")
                        analysis_object.format()
                        print("Predição                                 OK")
                        df_predictions, average_cycle_duration = analysis_object.predict()
                        st.session_state["previsoes_ultimos_ciclos"] = list(df_predictions["Prediction"])
                        st.session_state["bombas_principais_ultimos_ciclos"] = list(df_predictions["MainPump"])
                        st.session_state["proxima_falha_BOAD5_ciclos"] = list(df_predictions[df_predictions["MainPump"] == 5]["Prediction"])[-1]
                        st.session_state["proxima_falha_BOAD5_segundos"] = list(df_predictions[df_predictions["MainPump"] == 5]["Prediction"])[-1] * average_cycle_duration
                        st.session_state["proxima_falha_BOAD6_ciclos"] = list(df_predictions[df_predictions["MainPump"] == 6]["Prediction"])[-1]
                        st.session_state["proxima_falha_BOAD6_segundos"] = list(df_predictions[df_predictions["MainPump"] == 6]["Prediction"])[-1] * average_cycle_duration
                           
                        # No momento de fazer a previsão (dentro da função upload_page):
                        if 'lista_prediction_anteriores' not in st.session_state:
                            st.session_state['lista_prediction_anteriores'] = []  # Defina uma lista vazia caso não exista
                        
                        # Agora, adicione a nova previsão à lista
                        st.session_state['lista_prediction_anteriores'] = list(df_predictions["Prediction"])[-30:] if len(list(df_predictions["Prediction"])) > 30 else list(df_predictions["Prediction"])
                                               
                        print(st.session_state["previsoes_ultimos_ciclos"])

                        st.session_state['data_verificada'] = True
                        if st.session_state['data_verificada']:
                            st.session_state['current_page'] = 'results_page'
                            # Forçar a recarga da página
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
    
    # Cabeçalho visual para a página de resultados
    st.markdown("""
    <div style="background-color: #28a745; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: white; text-align: center;">📈 Análise Completa</h2>
        <p style="color: #e2f5e9; text-align: center;">Os resultados detalhados dos dados carregados estão disponíveis abaixo.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # obtendo a previsão de ciclos até a falha
    proxima_falha_BOAD5_ciclos = round(st.session_state["proxima_falha_BOAD5_ciclos"])
    proxima_falha_BOAD6_ciclos = round(st.session_state["proxima_falha_BOAD6_ciclos"])
    proxima_falha_ciclos = min(proxima_falha_BOAD5_ciclos, proxima_falha_BOAD6_ciclos)

    # obtendo a previsão de segundos até a falha
    proxima_falha_BOAD5_segundos = round(st.session_state["proxima_falha_BOAD5_segundos"])
    proxima_falha_BOAD6_segundos = round(st.session_state["proxima_falha_BOAD6_segundos"])
    proxima_falha_segundos = min(proxima_falha_BOAD5_segundos, proxima_falha_BOAD6_segundos)

    # calcula quantos em quantos dias e horas a falha deve ocorrer
    proxima_falha_BOAD5_dias, proxima_falha_BOAD5_horas = to_days_and_hours(proxima_falha_BOAD5_segundos)
    proxima_falha_BOAD6_dias, proxima_falha_BOAD6_horas = to_days_and_hours(proxima_falha_BOAD6_segundos)
    days, hours = to_days_and_hours(proxima_falha_segundos)

    st.markdown(f"""
        Bomba BOAD5 como principal: {proxima_falha_BOAD5_ciclos} ciclos, o que deve demorar aproximadamente {proxima_falha_BOAD5_dias} dias e {proxima_falha_BOAD5_horas} horas.
        
        Bomba BOAD6 como principal: {proxima_falha_BOAD6_ciclos} ciclos, o que deve demorar aproximadamente {proxima_falha_BOAD6_dias} dias e {proxima_falha_BOAD6_horas} horas.
    """, unsafe_allow_html=True)
    
    # Estilos para as mensagens
    if proxima_falha_ciclos <= 5:
        cor_fundo = "#f8d7da"  # Vermelho claro para alerta
        cor_texto = "#721c24"  # Vermelho escuro
        icone = "⚠️"
        mensagem = f"Atenção: A próxima falha ocorrerá em {proxima_falha_ciclos} ciclos!"
    elif 5 < proxima_falha_ciclos <= 10:
        cor_fundo = "#fff3cd"  # Amarelo claro para uma advertência menos crítica
        cor_texto = "#856404"  # Amarelo escuro
        icone = "🛠️"
        mensagem = f"O sistema de bombas está funcional, mas a falha está prevista em {proxima_falha_ciclos} ciclos."
    else:
        cor_fundo = "#d4edda"  # Verde claro para indicar que tudo está seguro
        cor_texto = "#155724"  # Verde escuro
        icone = "✅"
        mensagem = f"O sistema de bombas está funcionando com segurança, próxima falha em {proxima_falha_ciclos} ciclos."
    
    # Exibindo a previsão de falha e tempo estimado com a nomenclatura solicitada
    st.markdown("---")
    st.markdown(f"<h3 style='color:{cor_texto}; text-align: center; font-family: Arial, sans-serif;'>{icone} {mensagem}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{cor_texto}; text-align: center; font-size: 18px;'>Isso deve ocorrer em, aproximadamente {days} dias e {hours} horas.</p>", unsafe_allow_html=True)
    
    # Adicionando a sentença "Falha prevista para" alinhada com os visores
    st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; gap: 15px; font-size: 18px; font-weight: bold; color: {cor_texto};">
            <span>Falha prevista para:</span>
            <div style="background-color: #000000; color: #ffffff; font-size: 30px; font-weight: bold; padding: 15px; width: 160px; border-radius: 10px; text-align: center;">
                {proxima_falha_ciclos} ciclos
            </div>
            <div style="background-color: #000000; color: #ffffff; font-size: 25px; font-weight: bold; padding: 15px; width: 160px; border-radius: 10px; text-align: center;">
                {days}d {hours}h
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Adicionando um divisor visual
    st.markdown("<div style='height: 2px; background-color: #007bff; margin: 20px 0;'></div>", unsafe_allow_html=True)
    
    #num_ciclos = list(range(1, len(st.session_state['lista_prediction_anteriores']) + 1))
    num_ciclos = list(range(1, len(lista) + 1))
    # Criação do gráfico interativo
    fig = go.Figure()
    
    # Adicionando a linha ao gráfico
    #fig.add_trace(go.Scatter(x=num_ciclos, y=st.session_state['lista_prediction_anteriores'], mode='lines+markers', name='Previsão de Falha'))
    fig.add_trace(go.Scatter(x=num_ciclos, y=lista, mode='lines+markers', name='Previsão de Falha'))
    # Títulos e rótulos dos eixos
    fig.update_layout(
        title='Previsão de Falha ao Longo dos Ciclos',
        xaxis_title='Número do Ciclo',
        yaxis_title='Previsão de Falha (Ciclos)',
        template='plotly_dark',  # Usando um tema escuro para o gráfico
    )
    
    # Exibindo o gráfico no Streamlit
    st.plotly_chart(fig)

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
