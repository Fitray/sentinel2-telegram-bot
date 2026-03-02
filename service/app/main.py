import os
import requests
from dotenv import load_dotenv
from sentinelhub import (
    SHConfig,
    SentinelHubRequest,
    DataCollection,
    MimeType,
    CRS,
    BBox
)

class Handler():
    @staticmethod
    def GetConfig():
        load_dotenv()
        config = SHConfig()
        config.sh_client_id = os.getenv("CLIENT_ID")
        config.sh_client_secret = os.getenv("CLIENT_SECRET")
        return config

    @staticmethod
    def CreateBBox(lat, lon, delta=0.05):
        return BBox(
            bbox=[
                lon - delta,
                lat - delta,
                lon + delta,
                lat + delta
            ],
            crs=CRS.WGS84
        )
    
    @staticmethod
    def GetCoordinates(city_name):
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": city_name,
            "format": "json",
            "limit": 1
        }

        headers = {
            "User-Agent": "satellite-bot-coursework" 
        }

        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 200:
            raise ValueError("Не удалось получить ответ")
        data = response.json()

        if not data:
            raise ValueError("Населённый пункт не найден")

        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])

        return lat, lon

class Service():
    def __init__(self, data_folder=None, evalscript=None, input_data=None, responses=None, bbox=None, size=None, config=None):
        self.data_folder = data_folder
        self.evalscript = evalscript
        self.input_data = input_data
        self.responses = responses
        self.bbox = bbox
        self.size = size
        self.config = config
    
    def DoRequest(self, save_data=True):
        request = SentinelHubRequest(
            data_folder=self.data_folder,
            evalscript=self.evalscript,
            input_data=self.input_data,
            responses=self.responses,
            bbox=self.bbox,
            size=self.size,
            config=self.config,
        )
        image = request.get_data(save_data=save_data)


Config = Handler.GetConfig()
lat, lon = Handler.GetCoordinates(input("Укажите территорию: "))
bbox = Handler.CreateBBox(lat, lon)
evalscript = """
//VERSION=3
function setup() {
  return {
    input: ["B04", "B03", "B02"],
    output: { bands: 3 }
  };
}

function evaluatePixel(sample) {
  return [sample.B04, sample.B03, sample.B02];
}
"""
input_data = [
    SentinelHubRequest.input_data(
        data_collection=DataCollection.SENTINEL2_L2A,
        time_interval=("2024-06-01", "2024-06-30"),
        maxcc=0.2
    )
]

responses = [
    SentinelHubRequest.output_response("default", MimeType.PNG)
]
size = (512, 512)

service = Service(
    config=Config,
    bbox=bbox,
    evalscript=evalscript,
    input_data=input_data,
    responses=responses,
    size=size,
    data_folder="data_folder"
)
service.DoRequest(save_data=True)