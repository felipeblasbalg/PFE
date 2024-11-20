import streamlit as st
import pandas as pd
from analysis import Analysis
import plotly.graph_objects as go
#lista = [15,13,12,15,12,10,11,9,8,6,9,8]
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
                                              
                        # Verifique se a coluna "Prediction" existe e se não está vazia
                        if "Prediction" in df_predictions and not df_predictions["Prediction"].empty:
                            st.session_state["previsoes_ultimos_ciclos"] = list(df_predictions["Prediction"])
                        else:
                            st.session_state["previsoes_ultimos_ciclos"] = []
                        
                        # Verifique se a coluna "MainPump" existe e se não está vazia
                        if "MainPump" in df_predictions and not df_predictions["MainPump"].empty:
                            st.session_state["bombas_principais_ultimos_ciclos"] = list(df_predictions["MainPump"])
                        else:
                            st.session_state["bombas_principais_ultimos_ciclos"] = []
                        
                        # Verifique se há registros para MainPump == 5 antes de acessar o índice -1
                        mainpump_5_predictions = list(df_predictions[df_predictions["MainPump"] == 5]["Prediction"])
                        if mainpump_5_predictions:
                            st.session_state["proxima_falha_BOAD5_ciclos"] = mainpump_5_predictions[-1]
                            st.session_state["proxima_falha_BOAD5_segundos"] = mainpump_5_predictions[-1] * average_cycle_duration
                        else:
                            st.session_state["proxima_falha_BOAD5_ciclos"] = None
                            st.session_state["proxima_falha_BOAD5_segundos"] = None
                        
                        # Verifique se há registros para MainPump == 6 antes de acessar o índice -1
                        mainpump_6_predictions = list(df_predictions[df_predictions["MainPump"] == 6]["Prediction"])
                        if mainpump_6_predictions:
                            st.session_state["proxima_falha_BOAD6_ciclos"] = mainpump_6_predictions[-1]
                            st.session_state["proxima_falha_BOAD6_segundos"] = mainpump_6_predictions[-1] * average_cycle_duration
                        else:
                            st.session_state["proxima_falha_BOAD6_ciclos"] = None
                            st.session_state["proxima_falha_BOAD6_segundos"] = None


                        # Previsão anterior BOAD5 (dentro da função upload_page):
                        if 'lista_prediction_BOAD5' not in st.session_state:
                            st.session_state['lista_prediction_BOAD5'] = []  # Cria uma lista vazia caso não exista
                        
                        # Obter as previsões para BOAD5
                        mainpump_5_predictions = list(df_predictions[df_predictions["MainPump"] == 5]["Prediction"])
                        
                        # Verifique se há previsões para BOAD5
                        if mainpump_5_predictions:
                            # Adicione as últimas 30 previsões ou todas as previsões disponíveis
                            st.session_state['lista_prediction_BOAD5'] = mainpump_5_predictions[-30:]  # Mantém as últimas 30 previsões, se houver
                        else:
                            st.session_state['lista_prediction_BOAD5'] = []  # Lista vazia se não houver previsões
                        
                        # Previsão anterior BOAD6 (dentro da função upload_page):
                        if 'lista_prediction_BOAD6' not in st.session_state:
                            st.session_state['lista_prediction_BOAD6'] = []  # Cria uma lista vazia caso não exista
                        
                        # Obter as previsões para BOAD6
                        mainpump_6_predictions = list(df_predictions[df_predictions["MainPump"] == 6]["Prediction"])
                        
                        # Verifique se há previsões para BOAD6
                        if mainpump_6_predictions:
                            # Adicione as últimas 30 previsões ou todas as previsões disponíveis
                            st.session_state['lista_prediction_BOAD6'] = mainpump_6_predictions[-30:]  # Mantém as últimas 30 previsões, se houver
                        else:
                            st.session_state['lista_prediction_BOAD6'] = []  # Lista vazia se não houver previsões
                        
                        


                           
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

    # Função para exibir as informações de falha
    def exibir_previsao_bomba(nome_bomba, ciclos, segundos):
        if ciclos is None or segundos is None:
            return f"""
            <h3 style="color:#721c24; text-align: center; font-family: Arial, sans-serif;">
            ⚠️ Atenção: Não há dados suficientes para prever falhas na bomba {nome_bomba}.</h3>
            """
    
        # Arredonda ciclos para não mostrar casas decimais
        ciclos = int(ciclos)
    
        # Calcula os dias e horas com base nos segundos
        dias, horas = to_days_and_hours(segundos)
    
        # Define as cores e mensagens com base no número de ciclos
        if ciclos <= 5:
            cor_texto = "#721c24"  # Vermelho escuro
            icone = "⚠️"
            mensagem = f"Atenção: A próxima falha da bomba {nome_bomba} ocorrerá em {ciclos} ciclos!"
        elif 5 < ciclos <= 10:
            cor_texto = "#856404"  # Amarelo escuro
            icone = "🛠️"
            mensagem = f"A bomba {nome_bomba} está funcional, mas a falha está prevista para {ciclos} ciclos."
        else:
            cor_texto = "#155724"  # Verde escuro
            icone = "✅"
            mensagem = f"A bomba {nome_bomba} está funcionando com segurança, próxima falha em {ciclos} ciclos."
    
        # Retorna a mensagem formatada como HTML
        return f"""
        <h3 style='color:{cor_texto}; text-align: center; font-family: Arial, sans-serif;'>{icone} {mensagem}</h3>
        <p style='color:{cor_texto}; text-align: center; font-size: 18px;'>Isso deve ocorrer em, aproximadamente {dias} dias e {horas} horas.</p>
        <div style="display: flex; justify-content: center; align-items: center; gap: 15px; font-size: 18px; font-weight: bold; color: {cor_texto};">
            <span>Falha prevista para:</span>
            <div style="background-color: #000000; color: #ffffff; font-size: 30px; font-weight: bold; padding: 15px; width: 160px; border-radius: 10px; text-align: center;">
                {ciclos} ciclos
            </div>
            <div style="background-color: #000000; color: #ffffff; font-size: 25px; font-weight: bold; padding: 15px; width: 160px; border-radius: 10px; text-align: center;">
                {dias}d {horas}h
            </div>
        </div>
        """
    
    # Previsão e gráfico para BOAD5
    with st.container():
        st.markdown("""
        <div style="border: 2px solid #000000; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        """, unsafe_allow_html=True)
        
        # Exibir as informações da BOAD5 dentro do contêiner
        st.markdown(
            exibir_previsao_bomba(
                nome_bomba="BOAD5",
                ciclos=st.session_state.get("proxima_falha_BOAD5_ciclos"),
                segundos=st.session_state.get("proxima_falha_BOAD5_segundos")
            ),
            unsafe_allow_html=True
        )
        
        # Gráfico da BOAD5 dentro do mesmo contêiner
        num_ciclos5 = list(range(1, len(st.session_state['lista_prediction_BOAD5']) + 1))
        fig5 = go.Figure()
        fig5.add_trace(go.Scatter(x=num_ciclos5, y=st.session_state['lista_prediction_BOAD5'], mode='lines+markers', name='Previsão de Falha da bomba BOAD5'))
        fig5.update_layout(
            title='Previsão de Falha da bomba BOAD5 ao Longo dos Ciclos',
            xaxis_title='Número do Ciclo',
            yaxis_title='Previsão de Falha (Ciclos)',
            template='plotly_dark',
        )
        st.plotly_chart(fig5)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Previsão e gráfico para BOAD6
    with st.container():
        st.markdown("""
        <div style="border: 2px solid #000000; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        """, unsafe_allow_html=True)
        
        # Exibir as informações da BOAD6 dentro do contêiner
        st.markdown(
            exibir_previsao_bomba(
                nome_bomba="BOAD6",
                ciclos=st.session_state.get("proxima_falha_BOAD6_ciclos"),
                segundos=st.session_state.get("proxima_falha_BOAD6_segundos")
            ),
            unsafe_allow_html=True
        )
        
        # Gráfico da BOAD6 dentro do contêiner
        num_ciclos6 = list(range(1, len(st.session_state['lista_prediction_BOAD6']) + 1))
        fig6 = go.Figure()
        fig6.add_trace(go.Scatter(x=num_ciclos6, y=st.session_state['lista_prediction_BOAD6'], mode='lines+markers', name='Previsão de Falha da bomba BOAD6'))
        fig6.update_layout(
            title='Previsão de Falha da bomba BOAD6 ao Longo dos Ciclos',
            xaxis_title='Número do Ciclo',
            yaxis_title='Previsão de Falha (Ciclos)',
            template='plotly_dark',
        )
        st.plotly_chart(fig6)
        
        st.markdown("</div>", unsafe_allow_html=True)










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
