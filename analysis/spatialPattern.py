import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
from tqdm import tqdm

from .data import Data
from _plot import plotSet, FIG_SIZE, BAR_COLORS
from analysis.__converTime2Hrs import convertTime2Hrs

EPSG = 27700 # For UK only (planar coordinate system)

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
    
    def grid(self, savePath: str, gridType: str = "all") -> None:
        gdf = gpd.GeoDataFrame(self.cleanTime())
        gdf.to_crs(EPSG, inplace=True) # Change to planar coordinate system

        # Creat grid
        xmin, ymin, _, _ = gdf.total_bounds
        gridSize = 1000  # 1km网格
        # Calculate grid number
        gdf["grid_x"] = ((gdf.geometry.x - xmin) // gridSize).astype(int)
        gdf["grid_y"] = ((gdf.geometry.y - ymin) // gridSize).astype(int)
        groupTag = ["grid_x", "grid_y"]

        if gridType == "hours":
            timeDf = convertTime2Hrs(gdf, threadNum=16)[["hour"]]
            gdf = gdf.join(timeDf)
            groupTag += ["hour"]
        elif gridType == "speed":
            gdf = gdf[gdf["ConnectorSpeed"].notna()]
            gdf["ConnectorSpeed"] = gdf["ConnectorSpeed"].map({True: "fast", False: "slow"})
            groupTag += ["ConnectorSpeed"]

        grids = []
        
        # Calcualte grid
        grouped = gdf.groupby(groupTag)
        bar = tqdm(total=len(grouped), desc="Generating grids", unit="grid")
        for tags, group in grouped:
            grids.append(
                self._calSingleCube(tags, group, xmin, ymin, gridSize, gridType)
            )
            bar.update()
        
        bar.close()
        gpd.GeoDataFrame(grids, crs=EPSG).to_file(savePath, layer=gridType)

        return
    
    @staticmethod
    def _calSingleCube(tags: tuple, group: pd.DataFrame, xmin: float, ymin: float, gridSize: float, gridType: str) -> dict:
        if len(tags) == 2:
            gx, gy = tags
        else:
            gx, gy, tag = tags

        grid_cell = box(
            xmin + gx * gridSize,
            ymin + gy * gridSize,
            xmin + (gx + 1) * gridSize,
            ymin + (gy + 1) * gridSize
        )

        result = {
            'geometry': grid_cell,
            'total_amount': group['Amount'].sum(),
            'avg_duration': group['DurationSeconds'].mean(),
            'order_count': group.shape[0]
        }

        if len(tags) !=2:
            result[gridType] = tag # type: ignore

        return result
