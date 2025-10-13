import os
ROOT = r"C:\Users\tengd\OneDrive - The Hong Kong Polytechnic University\Student Assistant\scotland"
DATA_ROOT = os.path.join(ROOT, "Data")
FIG_ROOT = os.path.join(ROOT, "fig")

# Downlaod and merge data
from downloadData import tableData, POIData, mergeData, cleanData, joinCoord
# Download
tableData("Session").downloadAll(DATA_ROOT)
POIData().save(DATA_ROOT)
## Merge
mergeData(DATA_ROOT, maxThreads=16)
## Clean data
cleanData(
    os.path.join(DATA_ROOT, "merge.csv"),
    os.path.join(DATA_ROOT, "merge_clean.csv")
)
## Join coordinate
joinCoord(
    os.path.join(DATA_ROOT, "merge_clean.csv"),
    os.path.join(DATA_ROOT, "poi.csv"),
    DATA_ROOT
)

# Analysis data
