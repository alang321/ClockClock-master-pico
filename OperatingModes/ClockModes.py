from Stealth import Stealth
from Visual import Visual
from ShortestPath import ShortestPath
from NightDay import NightDay
from Analog import Analog
from Sleep import Sleep
from Settings import Settings

def get_mode_list():
    return [NightDay, Visual, ShortestPath, Stealth, Analog, Sleep, Settings]

def get_mode_by_idx(mode_id):
    return get_mode_list()[mode_id]

def get_mode_idx(mode):
    if type(mode) == type:
        return get_mode_list().index(mode)
    else:
        return get_mode_list().index(type(mode))