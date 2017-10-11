from urllib.requests import urlretrieve

def get_picture(url):
    urlretrieve(url, 'cool_beans.png')
