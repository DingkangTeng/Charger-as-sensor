# Downlaod and merge data
from downloadData import chargeplacescotland, mergeData, cleanData
# Download
chargeplacescotland("Session").downloadAll(r"C:\Users\tengd\OneDrive - The Hong Kong Polytechnic University\Student Assistant\scotland\Data")
## Merge
mergeData(r"C:\Users\tengd\OneDrive - The Hong Kong Polytechnic University\Student Assistant\scotland\Data", maxThreads=16)
## Clean data
cleanData(
    r"C:\Users\tengd\OneDrive - The Hong Kong Polytechnic University\Student Assistant\scotland\Data\merge.csv",
    r"C:\Users\tengd\OneDrive - The Hong Kong Polytechnic University\Student Assistant\scotland\Data\merge_clean.csv"
)
## Join coordinate
...

# Analysis data
