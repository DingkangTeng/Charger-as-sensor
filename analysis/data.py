import pandas as pd

MIN = 60
HRS = MIN * 60
DAYS = HRS * 24

class Data:
    __slots__ = ["__df", "originalLength"]
    
    def __init__(self, path: str) -> None:
        self.__df = pd.read_csv(path, encoding="utf-8")
        self.originalLength = self.__df.shape[0]

        return
    
    @property
    def df(self) -> pd.DataFrame:
        return self.__df.copy()

    def cleanTime(self) -> None:
        # Clean invaild time data
        self.__df.dropna(subset=["Start", "End", "Duration Seconds"], inplace=True)
        # Too short duration
        self.__df = self.__df[self.__df["Duration Seconds"] > 5 * MIN]
        # Too long duration
        self.__df = self.__df[self.__df["Duration Seconds"] < 10 * DAYS]

        return