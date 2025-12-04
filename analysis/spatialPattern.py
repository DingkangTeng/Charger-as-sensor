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
    
    def grid(self, savePath: str, maxThreads: int = 1) -> None:
        gdf = gpd.GeoDataFrame(self.cleanTime())
        # gdf = gdf[gdf["ConnectorSpeed"].notna()]
        # Change to planar coordinate system
        gdf.to_crs(EPSG, inplace=True) 

        # 空间网格化
        xmin, ymin, _ = gdf.total_bounds
        grid_size = 1000  # 1km网格
        # 计算每个点所在的网格行列号
        gdf['grid_x'] = ((gdf.geometry.x - xmin) // grid_size).astype(int)
        gdf['grid_y'] = ((gdf.geometry.y - ymin) // grid_size).astype(int)

        # 时间分片
        timeDf = convertTime2Hrs(gdf, threadNum=16)[["hour"]]
        gdf = gdf.join(timeDf)

        # 创建时空立方体
        spatial_temporal_cube = []

        # 使用groupby进行批量计算
        grouped = gdf.groupby(['grid_x', 'grid_y', 'hour']) #这个地方可以改成chargingtype
        bar = tqdm(total=len(grouped), desc="Generating grids", unit="grid")
        for (gx, gy, hour), group in grouped:
            spatial_temporal_cube.append(
                self._calSingleCube(group, gx, gy, xmin, ymin, grid_size, hour)
            )
            bar.update()
        
        bar.close()
        gpd.GeoDataFrame(spatial_temporal_cube, crs=EPSG).to_file(savePath)

        return
    
    @staticmethod
    def _calSingleCube(group: pd.DataFrame, gx: int, gy: int, xmin: float, ymin: float, grid_size: float, hour: int) -> dict:
        grid_cell = box(
            xmin + gx * grid_size,
            ymin + gy * grid_size,
            xmin + (gx + 1) * grid_size,
            ymin + (gy + 1) * grid_size
        )

        result = {
            'geometry': grid_cell,
            'hour': hour,
            'total_amount': group['Amount'].sum(),
            'avg_duration': group['DurationSeconds'].mean(),
            'order_count': group.shape[0]
        }

        return result
