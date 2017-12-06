import os
IMAGEPATH = os.path.dirname(os.path.abspath(__file__))

def get_imagepath(name):
    '''Gets the path for an image.'''
    for extension in ["gif", "png"]:
        path = os.path.join(IMAGEPATH, name+"."+extension)
        if (os.path.exists(path)):
            return path
    return False