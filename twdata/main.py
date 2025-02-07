from twapi import TWAPI

worlds = [143, 144, 145]

tw = TWAPI(worlds, "en")

tw.get_files()
