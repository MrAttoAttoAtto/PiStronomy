import random
from io import BytesIO

import requests
from PIL import Image

import tools

def old_get_sky_picture(param_dict={}, ra=None, de=None):
    param_dict['survey'] = 'DSS2'

    if ra != None:
        param_dict['ra'] = ra

    if de != None:
        param_dict['de'] = de

    http_response = requests.get('http://server{}.wikisky.org/imgcut'.format(random.randint(1, 9)),
                                 params=param_dict)

    image = Image.open(BytesIO(http_response.content))

    return image

    #image.show()

    #image.save('noot.png')


def get_sky_picture(base_ra, base_de, shiftx=0, shifty=0, magnification_level=0):
    param_dict = {'survey':'DSS2'}

    param_dict['angle'] = 1.25 * (0.75**magnification_level)

    param_dict['ra'] = base_ra
    param_dict['de'] = base_de

    param_dict['x_shift'] = shiftx
    param_dict['y_shift'] = shifty

    while True:
        try:
            http_response = requests.get('http://server{}.wikisky.org/imgcut'.format(random.randint(1, 9)),
                                         params=param_dict, timeout=0.5)
            break
        except (requests.exceptions.ReadTimeout, requests.exceptions.COnnectTimeout):
            continue

    image = Image.open(BytesIO(http_response.content))

    print("Pic got")

    return image

def prompt_sky_picture():
    hours = int(input('Hours: '))
    mins = int(input('Minutes: '))
    secs = int(input('Seconds: '))

    deg = int(input('Degrees: '))
    deg_min = int(input('Mins of arc: '))
    deg_sec = int(input('Secs of arc: '))

    righta = tools.from_hour_rep(hours, mins, secs)

    dec = tools.from_deg_rep(deg, deg_min, deg_sec)

    get_sky_picture(base_ra=righta, base_de=dec)

if __name__ == '__main__':
    prompt_sky_picture()
