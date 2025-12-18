import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import box
from tqdm import tqdm

from .data import Data, EPSG
from _plot import plotSet, FIG_SIZE, BAR_COLORS
from analysis.__converTime2Hrs import convertTime2Hrs

class spatialPattern(Data):

    def __init__(self, path: str | pd.DataFrame | gpd.GeoDataFrame) -> None:
        super().__init__(path)

        if not isinstance(path, gpd.GeoDataFrame): self.creatGDF()

        print(f"""
            Origional data volumns: {self.originalLength}\n
            Volumns after cleaning: {self.df.shape[0]} ({self.df.shape[0]/self.originalLength*100:.02f}%)
        """)
            
        plotSet()

        return
    
    def grid(self, savePath: str, gridSize: float = 1000, gridType: str = "allRecord", threadNum: int = 1) -> None:
        gdf = gpd.GeoDataFrame(self.cleanTime())
        gdf.to_crs(EPSG, inplace=True) # Change to planar coordinate system

        # Creat grid
        xmin, ymin, _, _ = gdf.total_bounds

        # Calculate grid number
        gdf["grid_x"] = ((gdf.geometry.x - xmin) // gridSize).astype(int)
        gdf["grid_y"] = ((gdf.geometry.y - ymin) // gridSize).astype(int)
        groupTag = ["grid_x", "grid_y"]

        if gridType == "hours":
            timeDf = convertTime2Hrs(gdf, threadNum=threadNum)[["hour"]]
            gdf = gdf.join(timeDf)
            groupTag += ["hour"]
        elif gridType == "speed":
            gdf = gdf[gdf["ConnectorSpeed"].notna()]
            groupTag += ["ConnectorSpeed"]

        grids = []
        
        # Calcualte grid
        grouped = gdf.groupby(groupTag)
        bar = tqdm(total=len(grouped), desc="Generating grids of {}".format(gridType), unit="grid")
        for tags, group in grouped:
            grids.append(
                self._calSingleCube(tags, group, xmin, ymin, gridSize, gridType)
            )
            bar.update()
        
        bar.close()
        gpd.GeoDataFrame(grids, crs=EPSG).to_file(os.path.join(savePath, "grided.gpkg"), layer=gridType)

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
            'total_amount': group["Amount"].sum(),
            'avg_duration': group["DurationSeconds"].mean(),
            'order_count': group.shape[0]
        }

        if len(tags) !=2:
            result[gridType] = tag # type: ignore

        return result
    
    def location(self, savePath: str, startAndEnd: tuple[int, int]) -> None:
        gdf = gpd.GeoDataFrame(self.cleanTime())
        gdf.to_crs(EPSG, inplace=True) # Change to planar coordinate system

        # Get the unique locations
        gdf["lcoation"] = gdf["lng_poi"].astype(str) + "-" + gdf["lat_poi"].astype(str)

        # Tag overnight
        gdf["dayOrders"] = (gdf["Start"].dt.hour < startAndEnd[0]) & (gdf["End"].dt.hour > startAndEnd[1]) # type: ignore
        gdf["overnightOrders"] = ~gdf["dayOrders"]
        # Not ruboust enough, need to be improved later
        gdf["dayOrders"] = gdf["dayOrders"].astype(int)
        gdf["overnightOrders"] = gdf["overnightOrders"].astype(int)
        
        # Calcualte location
        gdf = gdf.groupby(["lcoation", "ConnectorSpeed"]).agg({
            "geometry": "first",
            "Amount": "sum",
            "Consum": "sum",
            "DurationSeconds": "mean",
            "dayOrders": "sum",
            "overnightOrders": "sum",
        }).reset_index()
        gdf["overnightPercentage"] = gdf["overnightOrders"] / (gdf["dayOrders"] + gdf["overnightOrders"])

        gpd.GeoDataFrame(gdf).set_geometry("geometry").set_crs(EPSG).to_file(os.path.join(savePath, "location.gpkg"), layer="location")

        return