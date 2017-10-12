import requests
from PIL import Image
from io import BytesIO

def get_sky_picture(paramDict=None):
    paramDict['survey'] = 'DSS2'

    httpResponse = requests.get('http://server4.wikisky.org/imgcut', params=paramDict)

    image = Image.open(BytesIO(httpResponse.content))

    image.show()
