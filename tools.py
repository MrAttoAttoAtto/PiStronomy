'''Tools for converting between units (and possibly other things)'''
import urllib.parse

def from_hour_rep(hours, mins, secs):
    answer = hours % 24

    answer += mins/60 % 1

    answer += secs/3600 % 1/60

    return answer

def from_min_rep(deg, mins, secs):
    if abs(deg) != deg:
        negative = True
    else:
        negative = False

    answer = deg

    answer += mins/60

    answer += secs/3600

    return -answer if negative else answer

def from_hex_unicode_rep(ssid):
    ssid = ssid.encode('latin-1').decode('utf8')
    return urllib.parse.unquote(ssid)