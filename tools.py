'''Tools for converting between units (and possibly other things)'''
import urllib.parse
import socket
import subprocess
import os
import time

from astropy.coordinates import SkyCoord, AltAz, EarthLocation
from astropy.time import Time

if os.name == 'nt':
    WINDOWS = True
else:
    WINDOWS = False

def from_hour_rep(hours, mins, secs):
    answer = hours

    answer += mins/60

    answer += secs/3600

    return answer

def from_deg_rep(deg, mins, secs):
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
    ssid = ssid.decode('unicode-escape')
    ssid = ssid.encode('latin-1').decode('utf8')
    return urllib.parse.unquote(ssid)

def get_ip():
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
    return SkyCoord(righta, dec, unit=("hour", "deg")).get_constellation()

def coordinates_from_observer(righta, dec, location, obstime):
    real_time = Time(obstime)
    real_location = EarthLocation.of_site(location)

    real_coordinates = SkyCoord(righta, dec, unit=("hour", "deg"))

    alt_az = real_coordinates.transform_to(AltAz(obstime=real_time, location=real_location))

    return alt_az.az.deg, alt_az.alt.deg

def get_earth_location_coordinates(location):
    real_location = EarthLocation.of_site(location)

    long_lat_repr = real_location.to_geodetic()
    longi = long_lat_repr.lon.deg
    lat = long_lat_repr.lat.deg

    return lat, longi
