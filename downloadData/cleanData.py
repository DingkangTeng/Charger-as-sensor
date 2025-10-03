import re
import pandas as pd
import numpy as np

TYPE_MAP = {
    "ac": "slow", "ac_controller_receiver": "slow", "type_2_plug": "slow",
    "AC": "slow", "AC Controller/Receiver": "slow", "Slow ": "slow", "slow": "slow",
    "dc_controller_receiver": "fast", "rapid": "fast", "Fast": "fast",
    "Rapid": "fast", "Fast ": "fast", "Rapid ": "fast", "FAST": "fast", "ccs": "fast", "chademo": "fast",
    "ultra_rapid": "fast", "Ultra-Rapid": "fast", "Ultra Rapid": "fast",
    np.nan: np.nan
}

def __convertDayFormat(time_str: str) -> int | float:
    """
    Convert "X day, HH:MM:SS" to seconds
    e.g.: "1 day, 1:58:55" -> 1*86400 + 1*3600 + 58*60 + 55
    """
    try:
        match = re.match(r"(\d+)\s*days?\s*,\s*(\d+):(\d+):(\d+)$", time_str)
        if match:
            days, hours, minutes, seconds = map(int, match.groups())
            return days * 86400 + hours * 3600 + minutes * 60 + seconds
    except:
        return np.nan
    return np.nan

def cleanData(path: str, savePath: str) -> None:
    df = pd.read_csv(path, encoding="utf-8")

    # Swap misplacesd connector ID and connector type
    mask = df["Connector ID"].isna() | (df["Connector ID"] =="Â£")
    df.loc[mask, "Connector ID"] = df[mask]["Connector Type"]
    df["Connector ID"] = df["Connector ID"].astype(int)

    # Fill connector type by CPID and connector ID with mode
    mask = pd.to_numeric(df["Connector Type"], errors='coerce').notna() | df["Connector Type"].isna()
    typeMapping = df[~mask].groupby(["CPID", "Connector ID"])["Connector Type"].agg(lambda x: x.value_counts().idxmax()).to_dict()
    df.loc[mask, "Connector Type"] = df[mask].apply(
        lambda row: typeMapping.get((row["CPID"], row["Connector ID"]), np.nan), 
        axis=1
    )

    # Classify connector
    df["Connector Speed"] = df["Connector Type"].map(TYPE_MAP)

    # Standardization Duration
    ## Split the duration time and time stamp in Duration colums
    df["Duration Seconds"] = np.nan
    ### HH:MM:SS
    durationMask = df["Duration"].str.match(r"^\d{1,10}:\d{2}:\d{2}$", na=False)
    df.loc[durationMask, "Duration Seconds"] = (
        df.loc[durationMask, "Duration"]
        .apply(lambda x: sum(int(t) * 60**i for i, t in enumerate(reversed(x.split(':')))))
    )
    ### X day, HH:MM:SS
    durationMask = df["Duration"].str.match(r"^(\d+)\s*days?\s*,\s*(\d+):(\d+):(\d+)$", na=False)
    df.loc[durationMask, "Duration Seconds"] = (
        df.loc[durationMask, "Duration"]
        .apply(lambda x: __convertDayFormat(x))
    )
    ### Seconds
    numericDurations = pd.to_numeric(df["Duration"], errors='coerce')
    secondMask = numericDurations.notna()
    df.loc[secondMask, "Duration Seconds"] = df.loc[secondMask, "Duration"].astype(np.float32)

    # Standerlize Start time
    df["Start"] = pd.to_datetime(df["Start"], format="mixed")

    # Standardization End (YYYY-MM-DDTHH:MM:SS or YYYY-MM-DD HH:MM:SS)
    df["End"] = pd.NaT
    timestampMask = df["Duration"].str.contains(r"^\d{4}-\d{2}-\d{2}T? ?\d", na=False)
    df.loc[timestampMask, "End"] = df.loc[timestampMask, "Start"]
    df.loc[timestampMask, "Start"] = pd.to_datetime(
        df.loc[timestampMask, "Duration"], format="mixed"
    )    

    ## Fill na in Duration Seconds and End columns
    endNaTMask = df["Start"].notna() & df["Duration Seconds"].notna() & df["End"].isna()
    df.loc[endNaTMask, "End"] = df.loc[endNaTMask, "Start"] + pd.to_timedelta(df.loc[endNaTMask, "Duration Seconds"], unit='s')
    secondNanMask = df["Start"].notna() & df["End"].notna() & df["Duration Seconds"].isna()
    df.loc[secondNanMask, "Duration Seconds"] = (df.loc[secondNanMask, "End"] - df.loc[secondNanMask, "Start"]) / pd.Timedelta(seconds=1)

    # Is weekend?
    df["isWeekend"] = df["Start"].astype("datetime64[ns]").dt.weekday >= 5  # 5=Saturday, 6=Sunday
    
    df.columns = [
        "SITE", "CPID", "ConnectorType", "ConnectorID", "Currency", "Amount", "Consum",
        "Duration", "Start", "ConnectorSpeed", "DurationSeconds", "End", "isWeekend"
    ]
    df.to_csv(savePath, encoding="utf-8", index=False)

    return

# Debug
if __name__ == "__main__":
    cleanData(r"C:\Users\tengd\OneDrive - The Hong Kong Polytechnic University\Student Assistant\scotland\Data\merge.csv",
              r"C:\Users\tengd\OneDrive - The Hong Kong Polytechnic University\Student Assistant\scotland\Data\merge_clean.csv")