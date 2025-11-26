import matplotlib.pyplot as plt
from dataclasses import dataclass

# Fig size
LABEL_SIZE = 24
TICK_SIZE = int(LABEL_SIZE * 0.9)
@dataclass
class __FIG_SIZE:
    D: tuple[int, int] = (10,9)     # Default
    R: tuple[int, int] = (9, 10)    # Rotate
    H: tuple[int, int] = (10, 18)   # Higher
    W: tuple[int, int] = (20, 9)    # Wider
    H3W: tuple[int, int] = (20, 27)  # Higher * 3 and wider
    N: tuple[int, int] = (5, 9)     # Narrower
    S: tuple[int, int] = (10, 3)    # Shorter
FIG_SIZE = __FIG_SIZE()

# Color map
BAR_COLORS = [
    ["#436C85", "#B73F42", "#DE9960", "#82B29B", "#EEE6CB"],
    ["#DE476A", "#76AEA6", "#D79E8F", "#E5D2C4", "#F0E0D3"],
    ["#7D5A8A", "#DE7294", "#90BBAA", "#E6D2C2", "#F0E0D3"],
    ["#165188", "#BFCF61", "#9FCBC3", "#BFD3BC", "#DDDAB4"],
]

# General setting
def plotSet(scal1: float | int = 1, scal2: float | int = 1) -> None:
    labelSize = int(LABEL_SIZE * scal1)
    tickSize = int(TICK_SIZE * scal2)
    plt.style.use("seaborn-v0_8-whitegrid")
    # Font setting
    plt.rcParams["font.sans-serif"] = "Sans Serif Collection"
    plt.rcParams["font.size"] = tickSize
    plt.rcParams["xtick.labelsize"] = tickSize
    plt.rcParams["ytick.labelsize"] = tickSize
    plt.rcParams["axes.labelsize"] = labelSize
    # legend format
    plt.rcParams["legend.facecolor"] = "white"
    plt.rcParams["legend.edgecolor"] = "lightgray"
    plt.rcParams['legend.frameon'] = True
    plt.rcParams["legend.framealpha"] = 1.0
    # axes setting
    plt.rcParams["axes.formatter.use_mathtext"] = False
    plt.rcParams["axes.labelweight"] = "bold"
    # save setting
    plt.rcParams["savefig.dpi"] = 300

    return