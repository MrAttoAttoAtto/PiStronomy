'''Tools for converting between units (and possibly other things)'''
import urllib.parse
import socket
import subprocess

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
    ssid = ssid.decode().encode('latin-1').decode('utf8')
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

    rawNetworkData = subprocess.check_output(["sudo", "iw", "wlan0", "scan"])

    ssidSplit = rawNetworkData.split(b"SSID: ")

    del ssidSplit[0]

    for ssidString in ssidSplit:
        ssid = ssidString.split(b"\n", 1)[0]

        realSSID = from_hex_unicode_rep(ssid)

        ssidList.append(realSSID)
    
    return ssidList