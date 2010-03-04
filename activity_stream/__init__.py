VERSION = (0, 2, 8)

def get_version():
    return "%s.%s.%s" % (VERSION[0], VERSION[1], VERSION[2])

__version__ = get_version()