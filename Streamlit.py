import streamlit as st
import pandas as pd

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

    # Colunas esperadas
    alarm_columns = ["E3TimeStamp", "Acked", "ActorID", "ConditionActive", "EventType", "Message", "InTime", "OutTime",
                     "AckTime", "FullAlarmSourceName", "FormattedValue", "Quality", "AlarmSourceName", "EventTime", 
                     "InTimeMS", "Source"]
    level_columns = ["TAG", "Data", "Valor"]

    # Upload dos arquivos separados para Nível do Poço e Histórico de Alarmes
    st.subheader("📂 Anexar Arquivo do Nível do Poço (CSV ou XLSX)")
    file_nivel_poco = st.file_uploader("Anexe o arquivo do Nível do Poço", type=['csv', 'xlsx'], key="nivel_poco")

    st.subheader("📂 Anexar Arquivo do Histórico de Alarmes (CSV ou XLSX)")
    file_historico_alarmes = st.file_uploader("Anexe o arquivo do Histórico de Alarmes", type=['csv', 'xlsx'], key="historico_alarmes")

    # Verificar se os arquivos foram carregados corretamente e se possuem as colunas esperadas
    nivel_poco_valid = False
    historico_alarmes_valid = False

    if file_nivel_poco:
        try:
            # Ler o arquivo do Nível do Poço
            df_nivel_poco = pd.read_csv(file_nivel_poco) if file_nivel_poco.name.endswith('.csv') else pd.read_excel(file_nivel_poco)
            # Verificar se possui as colunas necessárias
            if all(column in df_nivel_poco.columns for column in level_columns):
                nivel_poco_valid = True
            else:
                st.error("O arquivo do Nível do Poço não possui todas as colunas esperadas: TAG, Data, Valor.")
        except Exception as e:
            st.error(f"Erro ao processar o arquivo do Nível do Poço: {e}")

    if file_historico_alarmes:
        try:
            # Ler o arquivo do Histórico de Alarmes
            df_historico_alarmes = pd.read_csv(file_historico_alarmes) if file_historico_alarmes.name.endswith('.csv') else pd.read_excel(file_historico_alarmes)
            # Verificar se possui as colunas necessárias
            if all(column in df_historico_alarmes.columns for column in alarm_columns):
                historico_alarmes_valid = True
            else:
                st.error("O arquivo do Histórico de Alarmes não possui todas as colunas esperadas.")
        except Exception as e:
            st.error(f"Erro ao processar o arquivo do Histórico de Alarmes: {e}")

    # Exibir mensagem de sucesso se ambos os arquivos estiverem válidos
    if nivel_poco_valid and historico_alarmes_valid:
        st.success("✅ Ambos os arquivos foram carregados com sucesso e possuem as colunas corretas!")

        # Botão para iniciar a análise
        if st.button("🔍 Análise dos Dados"):
            st.session_state['file_nivel_poco'] = file_nivel_poco
            st.session_state['file_historico_alarmes'] = file_historico_alarmes
            st.session_state['page'] = 'analysis'
            st.rerun()
    else:
        st.warning("⚠️ Por favor, verifique se ambos os arquivos possuem as colunas esperadas para prosseguir.")

# Página de análise dos dados
def analysis_page():
    st.title("📈 Resultados da Análise de Dados")
    
    if 'file_nivel_poco' not in st.session_state or 'file_historico_alarmes' not in st.session_state:
        st.warning("Por favor, volte para a página de upload e anexe ambos os arquivos.")
        return

    # Código para análise de dados (preservado conforme a necessidade)

# Verificar qual página exibir
if 'page' not in st.session_state:
    st.session_state['page'] = 'upload'

if st.session_state['page'] == 'upload':
    upload_page()
elif st.session_state['page'] == 'analysis':
    analysis_page()
