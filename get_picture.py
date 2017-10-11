import requests
from PIL import Image
from io import BytesIO

def get_sky_picture(paramDict=None):
    httpResponse = requests.get('http://server4.wikisky.org/map', params=paramDict)

    image = Image.open(BytesIO(httpResponse.content))

    image.show()
