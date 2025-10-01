import os

def mkdir(savePath: str) -> None:
    if not os.path.exists(savePath):
        os.mkdir(savePath)

    return