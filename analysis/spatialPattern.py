import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
from concurrent.futures import ProcessPoolExecutor, as_completed

from .data import Data
from _plot import plotSet, FIG_SIZE, BAR_COLORS
from analysis.__converTime2Hrs import convertTime2Hrs

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
        gdf = gdf[gdf["ConnectorSpeed"].notna()]

        # 空间网格化
        xmin, ymin, xmax, ymax = gdf.total_bounds
        grid_size = 0.01  # 1km网格
        rows = int((ymax - ymin) / grid_size)
        cols = int((xmax - xmin) / grid_size)

        # 时间分片
        timeDf = convertTime2Hrs(gdf, threadNum=16)[["hour"]]
        gdf = gdf.join(timeDf)

        # 创建时空立方体
        spatial_temporal_cube = []
        
        executor = ProcessPoolExecutor(max_workers=maxThreads)
        futures = []
        for i in range(cols//3):
            for j in range(rows//3):
                future = executor.submit(self._calSingleCube, gdf, xmin, ymin, grid_size, i, j)
                futures.append(future)

        for future in as_completed(futures):
            try:
                result = future.result()
            except Exception as e:
                raise RuntimeError(e)
            else:
                spatial_temporal_cube.extend(result)
        
        df = pd.DataFrame(spatial_temporal_cube)
        print(df)
        gpd.GeoDataFrame(df.drop(columns="geometry"), df["geometry"]).to_file(savePath)

        return
    
    @staticmethod
    def _calSingleCube(gdf: gpd.GeoDataFrame, xmin: float, ymin: float, grid_size: float, i: int, j: int) -> list[dict]:
        grid_cell = box(
            xmin + i*grid_size, ymin + j*grid_size,
            xmin + (i+1)*grid_size, ymin + (j+1)*grid_size
        )
        spatial_temporal_cube = []

        for hour in range(24):
            mask = gdf.within(grid_cell) & (gdf['hour'] == hour)
            if mask.any():
                cell_data = gdf[mask]
                spatial_temporal_cube.append({
                    'geometry': grid_cell,
                    'hour': hour,
                    'total_amount': cell_data['Amount'].sum(),
                    'avg_duration': cell_data['DurationSeconds'].mean(),
                    'fast_charge_ratio': (cell_data['ConnectorSpeed'] == 'fast').mean(),
                    'order_count': len(cell_data)
                })

        return spatial_temporal_cube
