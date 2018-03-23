'''Tools for converting between units (and possibly other things)'''
import os
import queue
import requests
import socket
import subprocess
import time
import urllib.parse

from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time

if os.name == 'nt':
    WINDOWS = True
else:
    import RPi.GPIO as GPIO
    WINDOWS = False

def from_hour_rep(hours, mins, secs):
    """
    Converts a human hour min sec representation to one number of hours
    """
    answer = hours

    answer += mins/60

    answer += secs/3600

    return answer

def from_deg_rep(deg, mins, secs):
    """
    Converts a human degree min sec representation to one number of degrees
    """
    if abs(deg) != deg:
        negative = True
        deg = abs(deg)
    else:
        negative = False

    answer = deg

    answer += mins/60

    answer += secs/3600

    return -answer if negative else answer

def from_hex_unicode_rep(ssid):
    """
    Converts a hexadecimal unicode code to real python chars
    """
    ssid = ssid.decode('unicode-escape')
    ssid = ssid.encode('latin-1').decode('utf8')
    return urllib.parse.unquote(ssid)

def get_ip():
    """
    Gets the current internal IP of the pi
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('8.8.8.8', 80))
        current_ip = s.getsockname()[0]
    except:
        current_ip = '127.0.0.1'
    finally:
        s.close()
    return current_ip

def get_all_ssids(block=True):
    """
    Gets all ssids in range
    """
    ssid_list = []

    if WINDOWS:
        command = ["netsh", "wlan", "show", "networks"]
    else:
        command = ["sudo", "iw", "wlan0", "scan"]

    while block:
        try:
            raw_network_data = subprocess.check_output(command)
            break
        except subprocess.CalledProcessError:
            time.sleep(0.5)

    if not WINDOWS:
        ssid_split = raw_network_data.split(b"SSID: ")

        del ssid_split[0]

        for ssid_string in ssid_split:
            ssid = ssid_string.split(b"\n", 1)[0]

            real_ssid = from_hex_unicode_rep(ssid)

            ssid_list.append(real_ssid)
    else:
        ssid_split = raw_network_data.split(b"SSID ")
        del ssid_split[0]

        for ssid_string in ssid_split:
            ssid = ssid_string.split(b"\r\n", 1)[0].split(b": ")[1]

            ssid_list.append(ssid.decode())
    
    return ssid_list

def get_current_ssid(block=True):
    """
    Gets the ssid of the currently connected network
    """
    if WINDOWS:
        command = ['netsh', 'wlan', 'show', 'interfaces']
        return "NOT CONNECTED"
    else:
        command = ['iwgetid', '-r']
    
    while block:
        try:
            raw_connection_data = subprocess.check_output(command)
            break
        except subprocess.CalledProcessError:
            time.sleep(0.5)

    return from_hex_unicode_rep(raw_connection_data)[:-1]

def mobile_connect(ssid, password):
    """
    Connects to a wifi based on ssid and password
    """
    command = ["wpa_cli", "-i", "wlan0", "reconfigure"]
    str_to_write = '\n#mobile_connect\nnetwork={\n\tssid="%s"\n\tpsk="%s"\n\tpriority=2\n}' % (ssid, password)

    print(str_to_write)

    with open("/etc/wpa_supplicant/wpa_supplicant.conf", 'a') as fil:
        fil.write(str_to_write)

    time.sleep(2)

    update_wlan_config = subprocess.Popen(command)
    update_wlan_config.communicate()

    return

def delete_prior_connection():
    """
    Deletes the mobile connection that was made that session
    """
    if WINDOWS:
        return

    command = ["wpa_cli", "-i", "wlan0", "reconfigure"]
    str_to_check = "\n#mobile_connect"

    with open("/etc/wpa_supplicant/wpa_supplicant.conf", 'r') as fil:
        wpa_contents = fil.read()

    prior_string = wpa_contents.split(str_to_check)[0]

    print(prior_string)

    if prior_string == wpa_contents:
        return

    with open("/etc/wpa_supplicant/wpa_supplicant.conf", 'w') as fil:
        fil.write(prior_string)

    time.sleep(2)
    
    update_wlan_config = subprocess.Popen(command)
    update_wlan_config.communicate()

def get_constellation(righta, dec):
    """
    Gets the constellation an RA and DEC is in
    """
    return SkyCoord(righta, dec, unit=("hour", "deg")).get_constellation()

def get_coordinates_from_observer(righta, dec, location, obstime):
    """
    Gets the Alt and Az of an Ra and Dec from a location and time 
    """
    real_time = Time(obstime)
    real_location = EarthLocation.of_site(location)

    real_coordinates = SkyCoord(righta, dec, unit=("hour", "deg"))

    alt_az = real_coordinates.transform_to(AltAz(obstime=real_time, location=real_location))

    return alt_az.az.deg, alt_az.alt.deg

def convert_altaz_to_radec(az, alt, location, obstime):
    """
    Converts AltAz coords to RaDec coords
    """
    real_time = Time(obstime)
    real_location = EarthLocation.of_site(location)

    altaz_coords = SkyCoord(az=az, alt=alt, unit=("deg", "deg"), frame=AltAz(obstime=real_time, location=real_location))
    radec_coords = altaz_coords.transform_to("icrs")

    return radec_coords.ra.hour, radec_coords.dec.deg

def get_earth_location_coordinates(location):
    """
    Gets the Lat and Long on earth from a location (Site)
    """
    real_location = EarthLocation.of_site(location)

    long_lat_repr = real_location.to_geodetic()
    longi = long_lat_repr.lon.deg
    lat = long_lat_repr.lat.deg

    return lat, longi

def get_object_coordinates(obj):
    """
    Get coordinates from an object name
    """
    coordinates = SkyCoord.from_name(obj)

    return coordinates.ra.hour, coordinates.dec.deg

def get_magnitude(obj):
    """
    Gets the magnitude of an object (if it exists)
    """
    param_dict = {
        "request":"doQuery",
        "lang":"adql",
        "format":"text",
        "query":"SELECT V from allfluxes JOIN ident USING(oidref) WHERE id = '{}';".format(obj.replace("'", "''"))
    }

    http_response = requests.get("http://simbad.u-strasbg.fr/simbad/sim-tap/sync", params=param_dict, timeout=3)

    mag = http_response.content.split(b"\n")[2].decode()

    if mag == ' ' or mag == '':
        return None

    return float(mag)

def safe_put(q, item):
    """
    Puts an item into a queue safely (yay)
    """
    try:
        q.put(item, block=False)
    except queue.Full:
        q.get()
        q.put(item, block=False)

def setup_gpio():
    '''Sets up the joystick GPIO'''
    GPIO.setmode(GPIO.BCM)
    
    GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)