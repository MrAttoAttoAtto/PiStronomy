import time

from astropy.time import Time
from astropy.coordinates import EarthLocation, get_body, solar_system_ephemeris

def get_planet_coords():
    formattedTime = time.strftime("%Y-%m-%d %H:%M")
    realTime = Time(formattedTime)

    realLocation = EarthLocation.of_site('greenwich')

    '''
    0 - Merc
    1 - Ven
    2 - Mars
    ...
    7 - Pluto
    8 - Moon
    9 - Sun
    '''

    skyCoordList = []

    with solar_system_ephemeris.set('de432s'):
        skyCoordList.append(get_body('mercury', realTime, realLocation))
        skyCoordList.append(get_body('venus', realTime, realLocation))
        skyCoordList.append(get_body('mars', realTime, realLocation))
        skyCoordList.append(get_body('jupiter', realTime, realLocation))
        skyCoordList.append(get_body('saturn', realTime, realLocation))
        skyCoordList.append(get_body('uranus', realTime, realLocation))
        skyCoordList.append(get_body('neptune', realTime, realLocation))
        skyCoordList.append(get_body('pluto', realTime, realLocation))
        skyCoordList.append(get_body('sun', realTime, realLocation))
        skyCoordList.append(get_body('moon', realTime, realLocation))

    coordinates = [(skyCoord.ra.hour, skyCoord.dec.degree) for skyCoord in skyCoordList]

    return coordinates
