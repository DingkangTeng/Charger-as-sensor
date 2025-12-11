# grided.gpkg
# -allRecord
# --total_amount
# --avg_duration
# --order_count
# -hours
# -- +hours (1-23)
# -speed
# -- +speed (fast, slow)
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from shapely.geometry.base import BaseGeometry
from shapely.affinity import scale

from _plot import plotSet, FIG_SIZE

class gridPattern:
    __slots__ = ["gdf", "layer"]

    def __init__(self, path: str, layer: str) -> None:
        self.gdf = gpd.read_file(path, layer=layer)
        self.layer = layer
        plotSet()

        return
    
    @staticmethod
    def scale_geometry(geom: BaseGeometry, scale_factor: int):
        """将几何图形以其中心点为中心进行缩放"""
        centroid = geom.centroid
        # 平移至原点 -> 缩放 -> 平移回原位置
        return scale(geom, xfact=scale_factor, yfact=scale_factor, origin=centroid)
    
    def cal(self, colum: str, figsize: str = "HU") -> None:
        fig = plt.figure(figsize=getattr(FIG_SIZE, figsize))
        gs = gridspec.GridSpec(4, 6, figure=fig, wspace=0.1, hspace=0.25)
        gdf = self.gdf.copy()
        # gdf["geometry"] = gdf["geometry"].map(
        #     lambda geom: self.scale_geometry(geom, 5) if geom else geom
        # )

        # # IQR
        # Q1 = gdf[colum].quantile(0.25)
        # Q3 = gdf[colum].quantile(0.75)
        # IQR = Q3 - Q1
        # # 定义正常值范围
        # lower_bound = Q1 - 1.5 * IQR
        # upper_bound = Q3 + 1.5 * IQR
        # # 剔除离群值
        # gdf = gdf[(gdf[colum] >= lower_bound) & (gdf[colum] <= upper_bound)]

        global_min = gdf[colum].min()
        global_max = gdf[colum].max()

        from shapely.geometry import box
        bbox_polygon = box(248000, 657000, 278000, 687000) #glasow
        
        # 裁剪数据，只保留在边界框内的要素
        gdf = gdf[gdf.intersects(bbox_polygon)].copy()

        series: list = gdf[self.layer].unique().tolist()
        series.sort()
        for i, layer in enumerate(series):
            ax = fig.add_subplot(gs[i])
            subData: gpd.GeoDataFrame = gdf[gdf[self.layer] == layer]

            ax.set_facecolor('#CCCCCC') 

            subData.plot(
                column=colum, 
                cmap='YlOrRd',
                ax=ax,
                # categorical=True,
                legend=False,
                vmin=global_min,
                vmax=global_max
            )
            
            ax.set_title(layer, y=-0.3)
            ax.set_axis_off()

        fig.patch.set_facecolor('#CCCCCC')
        plt.tight_layout()
        plt.show()


