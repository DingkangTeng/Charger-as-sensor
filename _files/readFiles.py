import os

# data structure method
## list
class newList(list):
    def set(self):
        return set(self)

class readFiles:
    __slots__ = ["path", "fileFilter", "typeFilter", "files"]

    def __init__(self, path: str = "", fileFilter: list[str] = [], typeFilter: list[str] = []):
        self.path = path
        self.files = os.listdir(path)
        typeFilter += ["py"]
        for i in range(len(self.files) - 1, -1, -1):
            file = self.files[i]
            if file.split(".")[-1] in typeFilter or file in fileFilter:
                self.files.pop(i)
    
    def specificFloder(self, contains: list[str] = []) -> list[str]:
        allFolder = [x for x in self.files if len(x.split(".")) == 1]
        result = set(allFolder)
        if contains != []:
            for contain in contains:
                result = result & set(x for x in allFolder if contain in x)
        result = newList(result)
        result.sort()
    
        return result
    
    def specificFile(self, suffix: list[str] = [], contains: list[str] = []) -> list[str]:
        files = set(self.files)
        if suffix != []:
            files = files & set(x for x in files if x.split(".")[-1] in suffix)
        if contains != []:
            for contain in contains:
                files = files & set(x for x in files if contain in x)
        files = newList(files)
        files.sort()
                
        return files