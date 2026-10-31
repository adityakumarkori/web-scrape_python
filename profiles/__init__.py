from . import granit
from . import blinkit

PROFILES = {
    "granit": granit,
    "blinkit": blinkit,
}

def get_profile(name):
    return PROFILES.get(name)