'''Tools for converting between units (and possibly other things)'''

def from_hour_rep(hours, mins, secs):
    answer = hours % 24

    answer += mins/60 % 1

    answer += secs/3600 % 1/60

    return answer

def from_min_rep(deg, mins, secs):
    answer = deg

    answer += mins/60

    answer += secs/3600

    return answer