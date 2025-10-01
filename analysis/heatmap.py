import pandas as pd

from .data import Data

CHARGER_TYPES = ["slow", "fast", "ultra fast"]

class heatmap(Data):
    __slots__ = []

    def __init__(self, path: str) -> None:
        super().__init__(path)
        self.cleanTime()

        print(self.df)
        print(self.originalLength)
        df = self.df.dropna(subset="Connector Speed")

        print(df["Duration Seconds"].unique())
        # weekday, weekend
        # fast, slow