import os
import pandas as pd
import matplotlib.pyplot as plt

from .data import Data
from _plot import plotSet, FIG_SIZE, BAR_COLORS

class monthPattern(Data):
    __slots__ = ["monthDf", "allMonth"]
    
    def __init__(self, path: str | pd.DataFrame) -> None:
        super().__init__(path)

        self.cleanTime(inplace=True)
        
        print(f"""
            Origional data volumns: {self.originalLength}\n
            Volumns after cleaning: {self.df.shape[0]} ({self.df.shape[0]/self.originalLength*100:.02f}%)
        """)

        self.monthDf = self.df[["CPID", "ConnectorID", "ConnectorSpeed", "Start"]]
        self.monthDf["month"] = self.monthDf["Start"].dt.to_period('M')
        self.monthDf["charger"] = self.monthDf["CPID"] + self.monthDf["ConnectorID"]
        self.allMonth: list = self.monthDf["month"].unique().tolist()
        self.allMonth.sort()
        
        plotSet()

        return
    
    def plotOrder(self, figsize: str = 'D', savePath: str = "") -> None:
        order = self.monthDf.groupby(["ConnectorSpeed", "month"]).size().unstack(fill_value=0)

        plt.figure(figsize=getattr(FIG_SIZE, figsize))
        ax = plt.subplot()
        order.T.plot(ax=ax)

        plt.tight_layout()
        if savePath == "":
            plt.show()
        else:
            plt.savefig(os.path.join(savePath, "order.jpg"))

        return
    
    def plotChargers(self, figsize: str = 'D', savePath: str = "") -> None:
        result = {}
        for month in self.allMonth:
            order: pd.DataFrame = self.monthDf[self.monthDf["month"] == month]
            order = order.drop_duplicates(subset="charger")
            result[month] = order.shape[0]

        plt.figure(figsize=getattr(FIG_SIZE, figsize))
        ax = plt.subplot()
        pd.DataFrame.from_dict(result, orient='index').plot(ax=ax)

        plt.tight_layout()
        if savePath == "":
            plt.show()
        else:
            plt.savefig(os.path.join(savePath, "order.jpg"))

        return