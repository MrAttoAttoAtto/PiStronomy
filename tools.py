'''Tools for converting between units (and possibly other things)'''
import urllib.parse
import socket
import subprocess
import os
import time

if os.name == 'nt':
    WINDOWS = True
else:
    WINDOWS = False

def from_hour_rep(hours, mins, secs):
    answer = hours % 24

    answer += mins/60 % 1

    answer += secs/3600 % 1/60

    return answer

def from_min_rep(deg, mins, secs):
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
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def get_all_ssids():
    ssidList = []

    if WINDOWS:
        command = ["netsh", "wlan", "show", "networks"]
    else:
        command = ["sudo", "iw", "wlan0", "scan"]

    rawNetworkData = subprocess.check_output(command)

    ssidSplit = rawNetworkData.split(b"SSID: ")

    del ssidSplit[0]

    for ssidString in ssidSplit:
        ssid = ssidString.split(b"\n", 1)[0]

        realSSID = from_hex_unicode_rep(ssid)

        ssidList.append(realSSID)
    
    return ssidList

def mobile_connect(ssid, password):
    command = ["wpa_cli", "-i", "wlan0", "reconfigure"]
    str_to_write = '\n#mobile_connect\nnetwork={\n\tssid="%s"\n\tpsk="%s"\n\tpriority=2\n}' % (ssid, password)

    print(str_to_write)

    with open("/etc/wpa_supplicant/wpa_supplicant.conf", 'a') as f:
        f.write(str_to_write)

    time.sleep(2)

    update_wlan_config = subprocess.Popen(command)
    update_wlan_config.communicate()

    return

def delete_prior_connection():
    command = ["wpa_cli", "-i", "wlan0", "reconfigure"]
    str_to_check = "\n#mobile_connect"

    with open("/etc/wpa_supplicant/wpa_supplicant.conf", 'r') as f:
        wpa_contents = f.read()

    prior_string = wpa_contents.split(str_to_check)[0]

    print(prior_string)

    with open("/etc/wpa_supplicant/wpa_supplicant.conf", 'w') as f:
        f.write(prior_string)

    time.sleep(2)
    
    update_wlan_config = subprocess.Popen(command)
    update_wlan_config.communicate()

    return
