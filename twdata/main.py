from twdata.twapi import TWAPI


# Create an instance of the TWAPI class
tw = TWAPI("en")
tw_nl = TWAPI("nl")
tw_us = TWAPI("us")
tw_de = TWAPI("de", "https://die-staemme.de")
tw_uk = TWAPI("uk")

# Download the files
tw.get_files()
tw_nl.get_files()
tw_us.get_files()
tw_de.get_files()
tw_uk.get_files()
