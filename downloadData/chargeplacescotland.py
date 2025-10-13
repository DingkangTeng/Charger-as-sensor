# It seems that popWorld do not support mutlti-thread downloading?
import os
import pandas as pd
from bs4 import BeautifulSoup as bs
from bs4 import Tag

from _crawler import crawler
from _files import mkdir, readFiles

class tableData:
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
    
class POIData:
    __slots__ = ["df"]

    def __init__(self) -> None:
        c = crawler(
            "https://account.chargeplacescotland.org/api/v3/poi/chargepoint/static",
            headers={"api-auth": "c3VwcG9ydCtjcHNhcHBAdmVyc2FudHVzLmNvLnVrOmt5YlRYJkZPJCEzcVBOJHlhMVgj"}
        )
        r = c.rget()
        features = r.json()["features"]
        # {
        #   'type': 'Feature',
        #   'geometry': {'type': 'Point', 'coordinates': ['56.4796', '-2.8384']},
        #   'properties': {
        #       'name': '70299', 'id': '12570697', 'siteID': '12551851',
        #       'connectorGroups': [
        #           {'connectorGroupID': 1, 'connectors': [
        #               {'connectorID': '1', 'connectorType': 'AC', 'connectorPlugType': 'type_2_plug',
        #               'connectorPlugTypeName': 'Type 2', 'connectorMaxChargeRate': '7'}
        #           ]},
        #           {'connectorGroupID': 2, 'connectors': [
        #               {'connectorID': '2', 'connectorType': 'AC', 'connectorPlugType': 'type_2_plug',
        #               'connectorPlugTypeName': 'Type 2', 'connectorMaxChargeRate': '7'}
        #           ]}
        #       ],
        #       'locationInfo': '', 'imageUrl': '',
        #       'tariff': {
        #           'amount': '0.60', 'currency': 'GBP', 'connectionfee': '0.00',
        #           'description': '60p/kWh. £10 overstay fee applies after 8 hours.'
        #       },
        #       'pre-select': False,
        #       'address': {
        #           'sitename': 'Monifieth Learning Campus', 'streetnumber': 'Monifieth Learning Campus',
        #           'street': 'Panmurefield Road', 'area': '', 'city': 'Dundee', 'postcode': 'DD5 4QT', 'country': 'GB'
        #       },
        #       'allowedVehicleType': 'public', 'displayCategory': 'public'
        #   }
        # }

        result = []
        for feature in features:
            coordinates: list = feature["geometry"]["coordinates"]
            properties: dict = feature["properties"]
            cpid = properties["name"]
            sitename = properties["address"]["sitename"]
            city = properties["address"]["city"]
            postcode = properties["address"]["postcode"]
            result.append([cpid, sitename, city, postcode, coordinates[0], coordinates[1]])
        
        self.df = pd.DataFrame(result, columns=["CPID", "sitename", "city", "postcode", "lat", "lng"])

    def save(self, path: str) -> None:
        self.df.to_csv(os.path.join(path, "poi.csv"), encoding="utf-8", index=False)

        return