from twapi import TWAPI

# List of world numbers to download
worlds = [143, 144, 145]

# Create an instance of the TWAPI class
tw = TWAPI(worlds, "en")

# Download the files
tw.get_files()
