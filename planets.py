import time
import threading
from queue import Queue, Full
from collections import OrderedDict

from astropy.time import Time
from astropy.coordinates import EarthLocation, get_body, solar_system_ephemeris

PLANET_COORDINATES = Queue(1)
PLANET_COORDINATES.put([])

MAPPING_DICT = [
    ['Mercury', 0],
    ['Venus', 1],
    ['Mars', 2],
    ['Jupiter', 3],
    ['Saturn', 4],
    ['Uranus', 5],
    ['Neptune', 6],
    ['Pluto', 7],
    ['Moon', 8],
    ['Sun', 9]
]
MAPPING_DICT = OrderedDict(MAPPING_DICT)

def get_planet_coords():
    formatted_time = time.strftime("%Y-%m-%d %H:%M")
    real_time = Time(formatted_time)

    real_location = EarthLocation.of_site('greenwich')

    '''
    0 - Merc
    1 - Ven
    2 - Mars
    ...
    7 - Pluto
    8 - Moon
    9 - Sun
    '''

    sky_coord_list = []

    with solar_system_ephemeris.set('de432s'):
        sky_coord_list.append(get_body('mercury', real_time, real_location))
        sky_coord_list.append(get_body('venus', real_time, real_location))
        sky_coord_list.append(get_body('mars', real_time, real_location))
        sky_coord_list.append(get_body('jupiter', real_time, real_location))
        sky_coord_list.append(get_body('saturn', real_time, real_location))
        sky_coord_list.append(get_body('uranus', real_time, real_location))
        sky_coord_list.append(get_body('neptune', real_time, real_location))
        sky_coord_list.append(get_body('pluto', real_time, real_location))
        sky_coord_list.append(get_body('sun', real_time, real_location))
        sky_coord_list.append(get_body('moon', real_time, real_location))

    coordinates = [(sky_coord.ra.hour, sky_coord.dec.degree) for sky_coord in sky_coord_list]

    return coordinates

def constant_planet_update(fake=False):
    new_coords = get_planet_coords()

    try:
        PLANET_COORDINATES.put(new_coords, block=False)
    except Full:
        PLANET_COORDINATES.get()
        PLANET_COORDINATES.put(new_coords)

    if not fake:
        time.sleep(10)

        planet_update_thread = threading.Thread(None, constant_planet_update)
        planet_update_thread.setDaemon(True)
        planet_update_thread.start()

def start_planet_update():
    planet_update_thread = threading.Thread(None, constant_planet_update)
    planet_update_thread.setDaemon(True)
    planet_update_thread.start()

if __name__ == '__main__':
    print(get_planet_coords())
