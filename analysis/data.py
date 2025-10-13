import pandas as pd
import numpy as np
from typing import overload, Literal

MIN = 60
HRS = MIN * 60
DAYS = HRS * 24

class Data:
    __slots__ = ["__df", "originalLength"]
    
    def __init__(self, path: str | pd.DataFrame) -> None:
        if isinstance(path, str):
            self.__df = pd.read_csv(path, encoding="utf-8")
        else:
            self.__df = path
        self.originalLength = self.__df.shape[0]
        self.__df["Start"] = self.__df["Start"].astype("datetime64[ns]")
        self.__df["End"] = self.__df["End"].astype("datetime64[ns]")
        self.__df["CPID"] = self.__df["CPID"].astype(str)
        self.__df["ConnectorID"] = self.__df["ConnectorID"].astype(str)

        # Clean invaild data
        ...

        return
    
    @property
    def df(self) -> pd.DataFrame:
        return self.__df.copy()
    
    def __modify(self, mask: pd.Series, inplace: bool) -> None | pd.DataFrame:
        if inplace:
            self.__df = self.__df[mask]
            return
        else:
            return self.__df[mask].copy()
    
    @overload
    def cleanTime(self, inplace: Literal[False] = False) -> pd.DataFrame: ...
    @overload
    def cleanTime(self, inplace: Literal[True]) -> None: ...
    def cleanTime(self, inplace: bool = False) -> None | pd.DataFrame:
        mask = (
            self.__df["Start"].notna() &                    # Clean invaild time data
            self.__df["End"].notna() &                      # Clean invaild time data
            self.__df["DurationSeconds"].notna() &         # Clean invaild time data
            (self.__df["DurationSeconds"] > 5 * MIN) &     # Too short duration
            (self.__df["DurationSeconds"] < 10 * DAYS)     # Too long duration
        )
        
        return self.__modify(mask, inplace)

    @overload
    def cleanConSpeed(self, inplace: Literal[False] = False) -> pd.DataFrame: ...
    @overload
    def cleanConSpeed(self, inplace: Literal[True]) -> None: ...    
    def cleanConSpeed(self, inplace: bool = False) -> None | pd.DataFrame:
        mask = self.__df["ConnectorSpeed"].notna()

        return self.__modify(mask, inplace)