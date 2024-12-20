import json
import numpy      as np
import pandas     as pd
import tensorflow as tf

class Analysis:

    def __init__(self, df_levels, df_alarms):

        # amarra os dfs originais ao objeto
        self.df_levels_original = df_levels
        self.df_alarms_original = df_alarms

        # altera os formatos de data e tempo
        self.df_levels_original["Data"] = pd.to_datetime(self.df_levels_original["Data"])
        self.df_alarms_original["E3TimeStamp"] = pd.to_datetime(self.df_alarms_original["E3TimeStamp"])
        self.df_alarms_original["InTime"] = pd.to_datetime(self.df_alarms_original["InTime"])
        self.df_alarms_original["OutTime"] = pd.to_datetime(self.df_alarms_original["OutTime"])
        self.df_alarms_original["AckTime"] = pd.to_datetime(self.df_alarms_original["AckTime"])
        self.df_alarms_original["EventTime"] = pd.to_datetime(self.df_alarms_original["EventTime"])

        # cria o dataframe de referência
        self.df_reference = Analysis.make_df_reference(df_levels, df_alarms)

        # importa o modelo e variáveis necessárias
        self.model = tf.keras.models.load_model("model/model.keras")
        with open("model/variables.json", "r") as file:
            self.variables = json.load(file)


    def preprocess(self):

        # cria os dfs a serem manipulados
        self.df_levels = self.df_levels_original.copy()
        self.df_alarms = self.df_alarms_original.copy()

        # remove as colunas e entradas inúteis
        self.df_alarms = self.df_alarms.drop(columns=["E3TimeStamp", "Area", "Severity", "Quality", "ActorID", "FullAlarmSourceName", "InTimeMS", "FormattedValue"])
        self.df_alarms = self.df_alarms[self.df_alarms["ConditionActive"] == 0]
        self.df_alarms = self.df_alarms[self.df_alarms["InTime"] >= self.df_levels["Data"].min()]
        self.df_levels = self.df_levels[self.df_levels["Data"] >= self.df_alarms["InTime"].min()]

        # verifica o momento da última falha e esquece tudo que vem antes
        last_error = self.df_alarms[self.df_alarms["AlarmSourceName"].isin(["SJ40AD_BOAD5_DF", "SJ40AD_BOAD6_DF"])]["EventTime"].max()
        if pd.isna(last_error): last_error = pd.to_datetime("01/01/2000")
        self.df_levels = self.df_levels[self.df_levels["Data"] > last_error]
        self.df_alarms = self.df_alarms[self.df_alarms["EventTime"] > last_error]

        # se não houverem dados o suficiente, gera um erro
        if len(self.df_alarms) == 0 or len(self.df_levels) == 0: raise ValueError("sem dados suficientes nos arquivos")


    def split_cycles(self):
        
        # inclui o nível da água no dataframe dos alarmes por interpolação
        self.df_alarms["InLevel"] = None
        for index, row in self.df_alarms.iterrows():
            self.df_alarms.loc[index, "InLevel"] = Analysis.get_water_level(self.df_levels, row["InTime"])
        self.df_alarms = self.df_alarms.sort_values("InTime", ignore_index=True)
        self.df_alarms = self.df_alarms.reset_index()
        self.df_alarms = self.df_alarms.drop(columns=["index"])

        # definição do dataframe dos ciclos
        self.df_cycles = pd.DataFrame({"Cycle": [], "StartTime": [], "EndTime": []})

        # definição dos valores iniciais
        current_cycle = 0
        self.df_cycles.loc[0, "Cycle"] = 0
        self.df_cycles.loc[0, "StartTime"] = self.df_alarms["InTime"].min()
        self.df_cycles.loc[0, "StartLevel"] = self.df_alarms.loc[self.df_alarms["InTime"].idxmin(), "InLevel"]
        activation_times_to_levels = dict()
        main_pump = ["SJ40AD_BOAD5_DG", "SJ40AD_BOAD6_DG"]
        main_pump_running = False

        # loop de coleta dos ciclos
        for index, row in self.df_alarms.iterrows():

            # se for evento de desligamento da bomba principal e o nível da água estiver abaixo do nível de desligamento
            if row["AlarmSourceName"] in main_pump:
                if row["InLevel"] <= self.df_reference[self.df_reference["Data"] == str(row["InTime"].date())]["DesligaPrincipal"].iloc[0]:

                    main_pump_running = False

                    # valores do primeiro acionamento de bomba do ciclo (momento e nível)
                    try:
                        self.df_cycles.loc[current_cycle, "FirstActivationTime"] = min(activation_times_to_levels.keys())                               # coluna que tem o timestamp do primeiro acionamento de qualquer bomba no ciclo
                        self.df_cycles.loc[current_cycle, "FirstActivationLevel"] = activation_times_to_levels[min(activation_times_to_levels.keys())]  # coluna que tem o nível da água no momento do primeiro acionamento de qualquer bomba no ciclo
                    except ValueError:
                        self.df_cycles.loc[current_cycle, "FirstActivationTime"] = None
                        self.df_cycles.loc[current_cycle, "FirstActivationLevel"] = None
                    
                    # registra momento do final do ciclo, limpa o dicionário de acionamentos e incrementa o ID do ciclo
                    self.df_cycles.loc[current_cycle, "EndTime"] = row["InTime"]
                    activation_times_to_levels = dict()
                    current_cycle += 1

                    # registra o ID do ciclo, e o nível e momento de início
                    self.df_cycles.loc[current_cycle, "Cycle"] = current_cycle
                    self.df_cycles.loc[current_cycle, "StartTime"] = row["InTime"]
                    self.df_cycles.loc[current_cycle, "StartLevel"] = row["InLevel"]

            # se for evento de acionamento de qualquer uma das bombas e nenhuma bomba tenha sido acionada ainda
            if row["AlarmSourceName"] in ["SJ40AD_BOAD5_LG", "SJ40AD_BOAD6_LG"]:
                if not main_pump_running:

                    activation_times_to_levels[row["InTime"]] = row["InLevel"]

                    # registra qual a bomba principal do ciclo
                    if row["AlarmSourceName"] == "SJ40AD_BOAD5_LG":
                        self.df_cycles.loc[current_cycle, "MainPump"] = 5
                        self.df_cycles.loc[current_cycle, "ReservePump"] = 6
                    if row["AlarmSourceName"] == "SJ40AD_BOAD6_LG":
                        self.df_cycles.loc[current_cycle, "MainPump"] = 6
                        self.df_cycles.loc[current_cycle, "ReservePump"] = 5
                    main_pump = [row["AlarmSourceName"][:-2] + "DG"]
                    main_pump_running = True
        
        # atualiza o tipo da variável de início e fim do ciclo
        self.df_cycles["StartTime"] = pd.to_datetime(self.df_cycles["StartTime"])
        self.df_cycles["EndTime"] = pd.to_datetime(self.df_cycles["EndTime"])

        # se não houverem ciclos o suficiente, gera um erro
        if len(self.df_cycles) <= 2: raise ValueError("sem dados suficientes nos arquivos: nenhum ciclo de operação completo nos dados fornecidos")

        # remove o primeiro e o último ciclo
        self.df_cycles = self.df_cycles[self.df_cycles["Cycle"] != 0]
        self.df_cycles = self.df_cycles[self.df_cycles["Cycle"] != self.df_cycles["Cycle"].max()]

        # calcula a duração dos ciclos
        self.df_cycles["Duration"] = (self.df_cycles["EndTime"] - self.df_cycles["StartTime"]).dt.total_seconds()

        # filtra os ciclos muito longos ou muito curtos
        q2 = self.df_cycles["Duration"].quantile(0.99)
        q1 = self.df_cycles["Duration"].quantile(0.01)
        self.df_cycles = self.df_cycles[self.df_cycles["Duration"] > q1][self.df_cycles["Duration"] < q2]

        # se não houverem ciclos o suficiente, gera um erro
        if len(self.df_cycles) <= 2: raise ValueError("sem nenhum ciclo de operação completo")


    def format(self):

        # cria a coluna da derivada discreta padronizada do nível do poço
        self.df_levels["DifValor"] = self.df_levels["Valor"].diff()
        self.df_levels["DifTempo"] = self.df_levels["Data"].diff().dt.total_seconds()
        self.df_levels["Derivada"] = self.df_levels["DifValor"] / self.df_levels["DifTempo"]
        self.df_levels["DerivadaPadronizada"] = (self.df_levels["Derivada"] - self.df_levels["Derivada"].mean()) / self.df_levels["Derivada"].std()
        self.df_levels = self.df_levels.dropna()

        # cria o array das derivadas padronizadas dos ciclos
        self.cycles_array = list()
        cycle_sizes = list()
        for _, row in self.df_cycles.iterrows():
            df_cycle_levels = self.df_levels[self.df_levels["Data"] >= row["StartTime"]]
            df_cycle_levels = df_cycle_levels[df_cycle_levels["Data"] < row["EndTime"]]
            df_cycle_levels.sort_values(by="Data")
            levels_diff_list = list(df_cycle_levels["DerivadaPadronizada"])
            self.cycles_array.append(levels_diff_list)
            cycle_sizes.append(len(levels_diff_list))
        self.df_cycles["Len"] = cycle_sizes


    def predict(self):
        
        # faz o preenchimento de zeros e aumenta a dimensão do array
        X = tf.keras.preprocessing.sequence.pad_sequences(self.cycles_array, dtype="float32", padding="post", maxlen=self.df_cycles["Len"].max())
        X = np.expand_dims(X, axis=-1)

        # faz as predições
        predictions = self.model.predict(X)
        
        # analisa as predições
        predictions = np.squeeze(predictions)
        predictions = predictions * self.variables["max_cycles_without_error"] + 1

        # diferencia pela bomba principal
        self.df_cycles["Prediction"] = predictions
        print(self.df_cycles)

        return self.df_cycles, self.variables["average_cycle_duration"]


    @staticmethod
    # função que retorna o nível da água em determinado momento
    def get_water_level(df_levels, date: pd.Timestamp):

        # verifica se a data solicitada tem um valor definido
        res = df_levels.loc[df_levels["Data"] == date]
        if (len(res) != 0): return res["Valor"].iloc[0]

        # copia o dataframe original e adiciona a data à cópia
        df = df_levels.copy()
        new_row = pd.DataFrame([{"Data": date}])
        df = pd.concat([df, new_row], ignore_index=True)

        # ordena o dataframe cópia pelas datas, define o índice e interpola o valor
        df = df.sort_values("Data")
        df.set_index("Data", inplace=True)
        df["Valor"] = df["Valor"].interpolate()
        df.reset_index(inplace=True)

        return df[df["Data"] == date]["Valor"].iloc[0]
    
    @staticmethod
    def make_df_reference(df_levels, df_alarms):

        # define o intervalo de datas dos dados
        initial_date_alarms = df_alarms["InTime"].dt.normalize().min()
        final_date_alarms   = df_alarms["OutTime"].dt.normalize().max()
        initial_date_levels = df_levels["Data"].dt.normalize().min()
        final_date_levels   = df_levels["Data"].dt.normalize().max()
        initial_date = max([initial_date_alarms, initial_date_levels])
        final_date = min([final_date_alarms, final_date_levels])
        date_range = pd.date_range(start=initial_date, end=final_date)

        # cria o DataFrame
        df_reference = pd.DataFrame({
            "Data"             : date_range,
            "NivelBaixo"       : None,
            "NivelAlto"        : None,
            "LigaPrincipal"    : None,
            "LigaReserva"      : None,
            "DesligaPrincipal" : None,
            "DesligaReserva"   : None
        })

        # define os valores antes de 17/01/2024
        before_revision = df_reference["Data"] < "2024-01-17"
        df_reference.loc[before_revision, "NivelBaixo"]       = 129.35
        df_reference.loc[before_revision, "NivelAlto"]        = 132.00
        df_reference.loc[before_revision, "LigaPrincipal"]    = 131.30
        df_reference.loc[before_revision, "LigaReserva"]      = 131.80
        df_reference.loc[before_revision, "DesligaPrincipal"] = 129.95
        df_reference.loc[before_revision, "DesligaReserva"]   = 129.95

        # define os valores depois de 17/01/2024 (inclusive)
        after_revision = df_reference["Data"] >= "2024-01-17"
        df_reference.loc[after_revision, "NivelBaixo"]       = 130.50
        df_reference.loc[after_revision, "NivelAlto"]        = 133.50
        df_reference.loc[after_revision, "LigaPrincipal"]    = 132.67
        df_reference.loc[after_revision, "LigaReserva"]      = 132.90
        df_reference.loc[after_revision, "DesligaPrincipal"] = 131.26
        df_reference.loc[after_revision, "DesligaReserva"]   = 131.26

        return df_reference