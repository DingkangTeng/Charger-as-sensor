import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from datetime import timedelta
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed

from .data import Data
from _plot import plotSet, FIG_SIZE, BAR_COLORS



class timeDistribution(Data):
    __slots__ = ["__path", "CHARGER_TYPES"]

    def __init__(self, path: str | pd.DataFrame) -> None:
        self.__path = ""
        if isinstance(path, str) and ".csv" not in path:
            self.__path = path
            self.CHARGER_TYPES = ["slow", "fast"]
        else:
            super().__init__(path)
            if isinstance(path, str):
                self.__path = os.path.dirname(path)

            self.cleanTime(inplace=True)
            self.cleanConSpeed(inplace=True)
            print(f"""
                Origional data volumns: {self.originalLength}\n
                Volumns after cleaning: {self.df.shape[0]} ({self.df.shape[0]/self.originalLength*100:.02f}%)
            """)
        
            self.CHARGER_TYPES = self.df["ConnectorSpeed"].unique().tolist()
            
        plotSet()

        return
    
    def cleanCacheData(self) -> None:
        timeDf = os.path.join(self.__path, "merge_time.csv")
        os.remove(timeDf) if os.path.exists(timeDf) else None

        return
    
    @staticmethod
    def _extendTime(df: pd.DataFrame) -> list[dict]:
        expandedRecords = []
        bar = tqdm(total=df.shape[0], desc="Converting Data", unit="points")

        for row in df.itertuples():
            record_type: str = getattr(row, "ConnectorSpeed")
            start_time: np.datetime64 = getattr(row, "Start")
            end_time: np.datetime64 = getattr(row, "End")
            isWeekend: bool = getattr(row, "isWeekend")
            
            current_time = start_time
            
            while current_time < end_time:
                # Calculate by one hour
                hour_end = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                if hour_end > end_time:
                    hour_end = end_time
                
                expandedRecords.append({
                    "type": record_type,
                    "hour": current_time.hour,
                    "isWeekend": isWeekend
                })
                
                current_time = hour_end
            
            bar.update()
        
        bar.close()

        return expandedRecords

    # 24 hours heatmap
    def HHeatmap(self, axs: Axes | None = None, figsize: str = 'W', threadNum: int = 1, savePath: str = "") -> None:
        if "merge_time.csv" in os.listdir(self.__path):
            timeDf = pd.read_csv(os.path.join(self.__path, "merge_time.csv"), encoding="utf-8")
        else:
            expandedRecords = []
            futures =[]
            with ProcessPoolExecutor(max_workers=threadNum) as executor:
                for i in np.array_split(self.df, threadNum):
                    futures.append(executor.submit(self._extendTime, i)) # type: ignore
                
                for future in as_completed(futures):
                    try:
                        record = future.result()
                    except Exception as e:
                        raise RuntimeError(e)
                    else:
                        expandedRecords.extend(record)
        
            timeDf = pd.DataFrame(expandedRecords)
            timeDf.to_csv(os.path.join(self.__path, "merge_time.csv"), encoding="utf-8")

        # timeDf:    
        #     type  hour  isWeekend
        # 0   fast    11     False
        hours = list(range(24))
        heatmapData = np.empty((len(self.CHARGER_TYPES) * 2, len(hours)))
        
        # Fill heatmap data
        for i, val in enumerate(self.CHARGER_TYPES):
            type_data = timeDf[timeDf["type"] == val]
            
            weekdayData: pd.DataFrame = type_data[~type_data["isWeekend"]]
            weekdayCounts = weekdayData.groupby('hour').size().T.to_numpy()
            heatmapData[i * 2] = weekdayCounts
            
            weekendData: pd.DataFrame = type_data[type_data["isWeekend"]]
            weekendCounts = weekendData.groupby("hour").size().T.to_numpy()
            heatmapData[i * 2 + 1] = weekendCounts
        
        if axs is None:
            plt.figure(figsize=getattr(FIG_SIZE, figsize))
            ax = plt.subplot()
        else:
            ax = axs
            
        sns.heatmap(
            heatmapData,
            ax=ax,
            cmap="YlOrRd",
            linewidths=0.5,
            xticklabels=[f"{h:02d}:00" for h in hours],
            yticklabels=["Weekday", "Weekend"] * len(self.CHARGER_TYPES)
        )

        # Add classify label
        for i, val in enumerate(self.CHARGER_TYPES):
            ax.text(
                -3.5,
                i * 2 + 1,
                val.capitalize(),
                ha="right", va="center", 
                rotation=0
            )
        
        ax.set_xlabel("Hour of Day")
        ax.set_xticklabels([f"{h:02d}:00" for h in hours], rotation=45)
        ax.set_ylabel("Charging Attribute", labelpad=100)
        ax.set_yticklabels(["Weekday", "Weekend"] * len(self.CHARGER_TYPES), rotation=0)
        
        plt.tight_layout()
        if axs is None and savePath == "":
            plt.show()
            plt.close()
        elif savePath !="":
            plt.savefig(os.path.join(savePath, "timeHeat.jpg"))
            plt.close()
        
        return
    
    # Time duration frequency
    def timeDuration(self, axs: list[Axes] | None = None, figsize: str = 'D', savePath: str = "") -> None:
        df = self.df[["ConnectorSpeed", "isWeekend", "DurationSeconds"]]
        df["hrs"] = df["DurationSeconds"] / 3600
        bins = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, np.inf]
        labels = ["<1", "1-2", "2-3", "3-4", "4-5", "5-6", "6-7", "7-8", "8-9", "9-10", "10-11", "11-12", ">12"]
        df["timeSegment"] = pd.cut(df["hrs"], bins=bins, labels=labels, right=False)
        df = df.groupby(["ConnectorSpeed", "isWeekend", "timeSegment"], observed=False).size().unstack(fill_value=0)

        for i, var in enumerate(self.CHARGER_TYPES):
            subdf = df.xs(var, level="ConnectorSpeed")

            if axs is None:
                plt.figure(figsize=getattr(FIG_SIZE, figsize))
                ax = plt.subplot()
            else:
                ax = axs[i]

            # Convert to daily average number
            result = subdf.T
            result[False] /= 5
            result[True] /= 2

            result.plot.bar(
                ax=ax,
                color=BAR_COLORS[i] # type: ignore
            )

            ax.set_xlabel("Charging Duration Group")
            ax.set_xticklabels(labels, rotation=45)
            ax.set_ylabel("Frequency")
            ax.legend(["Weekday", "Weekend"])

            plt.tight_layout()
            if axs is None and savePath == "":
                plt.show()
                plt.close()
            elif axs is None:
                plt.savefig(os.path.join(savePath, "duration_{}.jpg".format(var)))
                plt.close()

        return
    
    # Start hour frequency
    def startHour(self, axs: list[Axes] | None = None, figsize: str = 'D', savePath: str = "") -> None:
        df = self.df[["ConnectorSpeed", "isWeekend", "Start"]]
        df["hrs"] = df["Start"].dt.hour
        bins = list(range(0,25))
        labels = [f"{i}:00-{i+1}:00" for i in range(24)]
        df["timeSegment"] = pd.cut(df["hrs"], bins=bins, labels=labels, right=False)
        df = df.groupby(["ConnectorSpeed", "isWeekend", "timeSegment"], observed=False).size().unstack(fill_value=0)

        for i, var in enumerate(self.CHARGER_TYPES):
            subdf = df.xs(var, level="ConnectorSpeed")

            if axs is None:
                plt.figure(figsize=getattr(FIG_SIZE, figsize))
                ax = plt.subplot()
            else:
                ax = axs[i]

            # Convert to daily average number
            result = subdf.T
            result[False] /= 5
            result[True] /= 2

            result.plot.bar(
                ax=ax,
                color=BAR_COLORS[i] # type: ignore
            )

            ax.set_xlabel("Start Hour")
            ax.set_xticklabels(labels, rotation=90)
            ax.set_ylabel("Charging Events")
            ax.legend(["Weekday", "Weekend"])

            plt.tight_layout()
            if axs is None and savePath == "":
                plt.show()
                plt.close()
            elif axs is None:
                plt.savefig(os.path.join(savePath, "startHr_{}.jpg".format(var)))
                plt.close()

        return