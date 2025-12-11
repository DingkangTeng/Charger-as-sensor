import pandas as pd
from numpy import array_split, datetime64
from datetime import timedelta
from os.path import join
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed

def _extendTime(df: pd.DataFrame) -> list[dict]:
    expandedRecords = []
    bar = tqdm(total=df.shape[0], desc="Converting Data", unit="points")

    for row in df.itertuples():
        recordType: str = getattr(row, "ConnectorSpeed")
        startTime: datetime64 = getattr(row, "Start")
        endTime: datetime64 = getattr(row, "End")
        isWeekend: bool = getattr(row, "isWeekend")
        
        currentTime = startTime
        
        while currentTime < endTime:
            # Calculate by one hour
            hourEnd = currentTime.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            if hourEnd > endTime:
                hourEnd = endTime
            
            expandedRecords.append({
                "type": recordType,
                "hour": currentTime.hour,
                "isWeekend": isWeekend,
                "quarter": pd.Timestamp(currentTime).quarter
            })
            
            currentTime = hourEnd
        
        bar.update()
    
    bar.close()

    return expandedRecords

def convertTime2Hrs(df: pd.DataFrame, savePath: str = "", threadNum: int = 1) -> pd.DataFrame:
    expandedRecords = []
    futures =[]
    with ProcessPoolExecutor(max_workers=threadNum) as executor:
        for i in array_split(df, threadNum):
            futures.append(executor.submit(_extendTime, i)) # type: ignore
        
        for future in as_completed(futures):
            try:
                record = future.result()
            except Exception as e:
                raise RuntimeError(e)
            else:
                expandedRecords.extend(record)

    timeDf = pd.DataFrame(expandedRecords)
    if savePath != "":
        timeDf.to_csv(join(savePath, "merge_time.csv"), encoding="utf-8")

    return timeDf
    # timeDf:    
        #     type  hour  isWeekend
        # 0   fast    11     False