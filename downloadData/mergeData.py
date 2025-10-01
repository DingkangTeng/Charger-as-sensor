import os
import pandas as pd
from tqdm import tqdm
from threading import Lock
from concurrent.futures import ThreadPoolExecutor, as_completed

from _files import mkdir, readFiles

def mergeData(path: str, savePath: str = "", maxThreads: int = 4) -> None:
    # Check save path
    if savePath == "":
        savePath = path
    else:
        mkdir(savePath)

    existFiles = readFiles(path, fileFilter=["merge.csv"]).specificFile(["xls", "xlsx", "csv"])
    bar = tqdm(total=len(existFiles), desc="Reading files", unit="files")

    dfs = []
    futures = []
    debugDict = {}
    with ThreadPoolExecutor(max_workers=maxThreads) as executor:
        for file in existFiles:
            future = executor.submit(read, file, path)
            futures.append(future)
            debugDict[future] = file

        for future in as_completed(futures):
            file = debugDict[future]
            try:
                df = future.result()
            except Exception as e:
                raise RuntimeError(f"{file}: {e}")
            else:
                with Lock():
                    dfs.append(df)
                    bar.update()

    df = pd.concat(dfs)
    df.to_csv(os.path.join(savePath, "merge.csv"), encoding="utf-8", index=False)

    return

def read(file: str, path: str) -> pd.DataFrame:
    filePath = os.path.join(path, file)
    if file.split('.')[-1] == "csv":
        df = pd.read_csv(filePath, encoding="latin1")
    else:
        allSheet = pd.ExcelFile(filePath)
        if len(allSheet.sheet_names) == 1:
            df = pd.read_excel(filePath)
        else:
            df = pd.read_excel(filePath, sheet_name="Public View Only")

    if len(df.columns) == 8:
        df.columns = ["SITE" ,"CPID", "Connector ID", "Currency" , "Amount", "Consum" , "Duration" ,"Start"]
    else:
        df.columns = ["SITE" ,"CPID", "Connector Type", "Connector ID", "Currency" , "Amount", "Consum" , "Duration" ,"Start"]

    return df