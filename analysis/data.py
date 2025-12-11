import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pyproj import CRS
from typing import overload, Literal

MIN = 60
HRS = MIN * 60
DAYS = HRS * 24
EPSG = 27700 # For UK only (planar coordinate system)

class Data:
    __slots__ = ["__df", "originalLength"]
    
    def __init__(self, path: str | pd.DataFrame | gpd.GeoDataFrame) -> None:
        if isinstance(path, str):
            self.__df = pd.read_csv(path, encoding="utf-8") if "csv" in path else gpd.read_file(path, encoding="utf-8")
        else:
            self.__df = path
        self.originalLength = self.__df.shape[0]
        self.__df["Start"] = self.__df["Start"].astype("datetime64[ns]")
        self.__df["End"] = self.__df["End"].astype("datetime64[ns]")
        self.__df["CPID"] = self.__df["CPID"].astype(str)
        self.__df["ConnectorID"] = self.__df["ConnectorID"].astype(str)

        return
    
    @property
    def df(self) -> pd.DataFrame:
        return self.__df.copy()
    
    @property
    def gdf(self, lng: str = "lng_poi", lat: str = "lat_poi") -> gpd.GeoDataFrame:
        if not isinstance(self.__df, gpd.GeoDataFrame):
            self.creatGDF(lng, lat)

        assert isinstance(self.__df, gpd.GeoDataFrame)
        return self.__df.copy()
    
    @property
    def crs(self, lng: str = "lng_poi", lat: str = "lat_poi") -> CRS:
        if not isinstance(self.__df, gpd.GeoDataFrame):
            self.creatGDF(lng, lat)

        assert isinstance(self.__df, gpd.GeoDataFrame) and self.__df.crs is not None
        return self.__df.crs
    
    def __modify(self, mask: pd.Series, inplace: bool) -> None | pd.DataFrame:
        if inplace:
            self.__df = self.__df[mask]
            return
        else:
            return self.__df[mask].copy()
        
    def creatGDF(self, lng: str = "lng_poi", lat: str = "lat_poi") -> gpd.GeoDataFrame:
        if lng not in self.__df.columns or lat not in self.__df.columns:
            raise RuntimeError("Do not have {} or {} in the dataframe".format(lng, lat))
        
        self.cleanPOI(lng, lat, inplace=True)
        self.__df = gpd.GeoDataFrame(
            self.__df,
            geometry=[Point(xy) for xy in zip(self.__df[lng], self.__df[lat])],
            crs=4326
        )

        return self.__df.copy()
    
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
    
    @overload
    def cleanPOI(self, lng: str, lat: str, inplace: Literal[False] = False) -> pd.DataFrame: ...
    @overload
    def cleanPOI(self, lng: str, lat: str, inplace: Literal[True]) -> None: ...    

    def cleanPOI(self, lng: str = "lng_poi", lat: str = "lat_poi", inplace: bool = False) -> None | pd.DataFrame:
        mask = self.__df[lng].notna() & self.__df[lat].notna()

        return self.__modify(mask, inplace)