from __future__ import annotations

import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
from tqdm import tqdm

from .data import Data, EPSG

class emergePattern(Data):
    __slots__ = ["emerge", "minM", "maxM", "spatial"]

    def __init__(self, path: str | pd.DataFrame | gpd.GeoDataFrame | None = None, spatial: bool = False) -> None:
        self.spatial = spatial
        if path is None: return

        super().__init__(path)

        if not isinstance(path, gpd.GeoDataFrame) and spatial: self.creatGDF()
        self.cleanTime(inplace=True)

        print(f"""
            Origional data volumns: {self.originalLength}\n
            Volumns after cleaning: {self.df.shape[0]} ({self.df.shape[0]/self.originalLength*100:.02f}%)
        """)

        # Group start
        if spatial:
            emerge = self.gdf.groupby("CPID").agg({
                "Start": "min",
                "End": "max",
                "SITE": "count",
                "geometry": "first"
            }).reset_index()
            emerge.columns = ["CPID", "first", "last", "orders", "geometry"]
            self.emerge = gpd.GeoDataFrame(emerge, crs=self.crs)
        else:
            self.emerge = self.gdf.groupby("CPID").agg({
                "Start": "min",
                "End": "max",
                "SITE": "count"
            }).reset_index()
            self.emerge.columns = ["CPID", "first", "last", "orders"]

        self.minM = pd.Timestamp(self.emerge["first"].min().date().replace(day=1))
        self.maxM = pd.Timestamp(self.emerge["last"].max().date().replace(day=1))

        return
    
    def grid(self, savePath: str, gridSize: float = 1000, gridType: str = "all") -> None | _emergeUnspatialPattern:
        if self.spatial:
            assert isinstance(self.emerge, gpd.GeoDataFrame)
            gdf = self.emerge.to_crs(EPSG) # Change to planar coordinate system

            # Creat grid
            xmin, ymin, _, _ = gdf.total_bounds

            # Calculate grid number
            gdf["grid_x"] = ((gdf.geometry.x - xmin) // gridSize).astype(int)
            gdf["grid_y"] = ((gdf.geometry.y - ymin) // gridSize).astype(int)
            groupby = ["grid_x", "grid_y"]
        else:
            savePath = os.path.join(savePath, "emerge_{}.csv".format(gridType))
            if os.path.exists(savePath): return _emergeUnspatialPattern(savePath)
            gdf = self.emerge
            groupby = ["CPID"]
            xmin = None
            ymin = None

        if gridType == "month":
            allM = pd.date_range(start=self.minM, end=self.maxM, freq="MS") # MS=Month Start
        elif gridType == "year":
            allM = pd.date_range(start=self.minM, end=self.maxM, freq="YS") # YS=Year Start
        else:
            gridType = "all"
            allM = [self.minM, self.maxM]

        grids = []
        
        # Calcualte grid
        grouped = gdf.groupby(groupby)
        bar = tqdm(total=len(grouped), desc="Generating grids for {}".format(gridType), unit="grid")
        for tags, group in grouped:
            for month in allM:
                group = group[(group["first"] - pd.DateOffset(months=1) <= month) & (group["last"] + pd.DateOffset(months=1) >= month)] # One month tolerance
                grids.append(
                    self._calSingleCube(tags, group, xmin, ymin, gridSize, month)
                )
            bar.update()
        
        bar.close()

        result = pd.DataFrame(grids)
        result = result[result["station_count"] != 0]
        if self.spatial:
            gpd.GeoDataFrame(result, crs=EPSG).to_file(savePath, layer="emerge_{}".format(gridType))
            return
        
        else:
            result.to_csv(savePath, encoding="utf-8", index=False)
            return _emergeUnspatialPattern(result)
    
    @staticmethod
    def _calSingleCube(tags: tuple, group: pd.DataFrame, xmin: float | None, ymin: float | None, gridSize: float, agg: pd.Timestamp) -> dict:
        if xmin is not None:
            gx, gy = tags

            grid_cell = box(
                xmin + gx * gridSize,
                ymin + gy * gridSize,
                xmin + (gx + 1) * gridSize,
                ymin + (gy + 1) * gridSize
            )

            result = {
                "geometry": grid_cell,
                "station_count": group.shape[0],
                "order_count": group["orders"].sum()
            }
        else:
            result = {
                "CPID": tags[0],
                "station_count": group.shape[0],
                "order_count": group["orders"].sum()
            }

        result["emerge"] = agg

        return result
    
class _emergeUnspatialPattern:
    __slots__ = ["df"]

    def __init__(self, path: str | pd.DataFrame) -> None:
        if isinstance(path, pd.DataFrame):
            self.df = path
        else:
            self.df = pd.read_csv(path, parse_dates=["emerge"])

        self.df = self.df.groupby("emerge").agg({
            "station_count": "sum",
            "order_count": "sum"
        }).sort_values("emerge", ascending=False)

    def plot(self, figsize: str = "D") -> None:
        import matplotlib.pyplot as plt
        from _plot import plotSet, FIG_SIZE
        plotSet()

        fig = plt.figure(figsize=getattr(FIG_SIZE, figsize))
        ax = plt.subplot()

        self.df["order_count"].plot(ax=ax)

        plt.xticks(rotation=45)

        plt.show()

        return