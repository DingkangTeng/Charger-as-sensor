import os
import pandas as pd
import geopandas as gpd
from esda.moran import Moran
from libpysal.weights import Queen, KNN

from .data import Data
from _plot import plotSet, FIG_SIZE, BAR_COLORS



class spatialPattern(Data):
    __slots__ = ["CHARGER_TYPES"]

    def __init__(self, path: str | pd.DataFrame | gpd.GeoDataFrame) -> None:
        super().__init__(path)

        if not isinstance(path, gpd.GeoDataFrame): self.creatGDF()

        print(f"""
            Origional data volumns: {self.originalLength}\n
            Volumns after cleaning: {self.df.shape[0]} ({self.df.shape[0]/self.originalLength*100:.02f}%)
        """)
    
        self.CHARGER_TYPES = self.df["ConnectorSpeed"].unique().tolist()
            
        plotSet()

        return
    
    def moran(self, indexs: list[str], lng: str = "lng_poi", lat: str = "lat_poi") -> None:
        # w = Queen.from_dataframe(self.gdf, use_index=False)
        
        for i in indexs:
            gdf = self.gdf.loc[self.gdf[i].notna(), [i, "geometry"]]
            w = Queen.from_dataframe(gdf, use_index=False)
            moran = Moran(gdf[i], w)
            print(f"Moran's I: {moran.I}, p-value: {moran.p_sim}")
