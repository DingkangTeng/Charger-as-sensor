# It seems that popWorld do not support mutlti-thread downloading?
import os
from bs4 import BeautifulSoup as bs
from bs4 import Tag

from _crawler import crawler
from _files import mkdir, readFiles

class chargeplacescotland:
    __slots__ = ["hrefs"]
    __baseUrl = "https://chargeplacescotland.org/{}"

    def __init__(self, key: str) -> None:
        print("Getting all data metadata from chargeplacescotland...")
        self.hrefs = self.__getAllData(key)

    def __subPage(self, sub: str) -> str:
        return self.__baseUrl.format(sub)
    
    def __getAllData(self, keywords: str) -> list[str]:
        c = crawler(self.__subPage("monthly-charge-point-performance"))
        r = c.rget()
        r.encoding = "utf-8"

        soup = bs(r.text, "html.parser")
        div = soup.find("div", {"class": "page-content main-content-text"})
        if not isinstance(div, Tag):
            print("No data found")
            return []
        
        hrefs = []
        a = div.find_all("a")
        for i in a:
            if not isinstance(i, Tag):
                continue
            href = i["href"]
            if keywords not in href and keywords.upper() not in href and keywords.lower() not in href:
                continue
            if href not in hrefs:
                hrefs.append(href)

        return hrefs
    
    def downloadAll(self, savePath: str) -> None:
        mkdir(savePath)
        existFiles = readFiles(savePath).specificFile(["xls", "xlsx", "csv"])

        for i in self.hrefs:
            fileName = i.split('/')[-1]
            if fileName in existFiles:
                continue

            c = crawler(i)
            c.download(os.path.join(savePath, fileName))

        return