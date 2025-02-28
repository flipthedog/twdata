from twapi import TWAPI

# List of world numbers to download
worlds = [142, 143, 144, 145, 146]

# Create an instance of the TWAPI class
tw = TWAPI(worlds, "en")

tw_classic = TWAPI([1, 2], "enc")

# Download the files
tw.get_files()
tw_classic.get_files()
