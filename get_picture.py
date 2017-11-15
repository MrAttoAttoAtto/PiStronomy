import requests
from PIL import Image
from io import BytesIO

import tools

def get_sky_picture(paramDict={}, ra=None, de=None):
    paramDict['survey'] = 'DSS2'

    if ra != None:
        paramDict['ra'] = ra
    
    if de != None:
        paramDict['de'] = de

    httpResponse = requests.get('http://server4.wikisky.org/imgcut', params=paramDict)

    image = Image.open(BytesIO(httpResponse.content))

    image.show()

    image.save('noot.png')

if __name__ == '__main__':
    hours = int(input('Hours: '))
    mins = int(input('Minutes: '))
    secs = int(input('Seconds: '))
    
    deg = int(input('Degrees: '))
    deg_min = int(input('Mins of arc: '))
    deg_sec = int(input('Secs of arc: '))

    ra = tools.from_hour_rep(hours, mins, secs)

    dec = tools.from_min_rep(deg, deg_min, deg_sec)

    get_sky_picture({}, ra, dec)