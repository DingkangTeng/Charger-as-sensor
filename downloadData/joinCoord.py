import os
import pandas as pd

def joinCoord(rowData: str, coord: str, savePath: str, ignoreNullCoord: bool = False) -> None:
    rowDf = pd.read_csv(rowData, encoding="utf-8")
    coordDf = pd.read_csv(coord, encoding="utf-8").set_index("CPID")
    coordDf.columns = ["{}_poi".format(x) for x in coordDf.columns]

    rowDf["CPID_Num"] = rowDf["CPID"].str[-5:]
    rowDf.set_index("CPID_Num", inplace=True)
    rowDf = rowDf.join(coordDf)

    samplerate = rowDf[rowDf["lng_poi"].notna()].shape[0] / rowDf.shape[0]
    print("{:.2f}% of the origional data are joined with coordinate data.".format(samplerate * 100))

    if ignoreNullCoord:
        rowDf = rowDf[rowDf["lng_poi"].notna()]

    rowDf.to_csv(
        os.path.join(savePath, "{}_poi.csv".format(os.path.basename(rowData).split('.')[0])),
        encoding="utf-8",
        index=False
    )
    
    return

# test
if __name__ == "__main__":
    DATA_ROOT = r"C:\Users\tengd\OneDrive - The Hong Kong Polytechnic University\Student Assistant\scotland\Data"
    joinCoord(
        os.path.join(DATA_ROOT, "merge_clean.csv"),
        os.path.join(DATA_ROOT, "poi.csv"),
        DATA_ROOT
    )