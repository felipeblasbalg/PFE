import pandas as pd

class Analysis:

    def __init__(self):
        pass

    def preprocess(self, df_levels, df_alarms):

        # amarra os dfs originais ao objeto
        self.df_levels_original = df_levels
        self.df_alarms_original = df_alarms

        # cria os dfs a serem manipulados
        self.df_levels = self.df_levels_original.copy()
        self.df_alarms = self.df_alarms_original.copy()

        # altera os formatos de data e tempo
        self.df_levels["Data"] = pd.to_datetime(self.df_levels["Data"])
        self.df_alarms["E3TimeStamp"] = pd.to_datetime(self.df_alarms["E3TimeStamp"])
        self.df_alarms["InTime"] = pd.to_datetime(self.df_alarms["InTime"])
        self.df_alarms["OutTime"] = pd.to_datetime(self.df_alarms["OutTime"])
        self.df_alarms["AckTime"] = pd.to_datetime(self.df_alarms["AckTime"])
        self.df_alarms["EventTime"] = pd.to_datetime(self.df_alarms["EventTime"])

        # remove as colunas e entradas inúteis
        self.df_alarms = self.df_alarms.drop(columns=["E3TimeStamp", "Area", "Severity", "Quality", "ActorID", "FullAlarmSourceName", "InTimeMS", "FormattedValue"])
        self.df_alarms = self.df_alarms[self.df_alarms["ConditionActive"] == 0]
        self.df_alarms = self.df_alarms[self.df_alarms["InTime"] >= self.df_levels["Data"].min()]

        # verifica o momento da última falha
        self.last_error = self.df_alarms[self.df_alarms["AlarmSourceName"].isin(["SJ40AD_BOAD5_DF", "SJ40AD_BOAD6_DF"])]["EventTime"].max()
        print(self.last_error)

    def predict(self):

        return 0