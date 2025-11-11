from twdata.twapi import TWAPI
import logging
from datetime import datetime
import yaml

# log to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logging.info("Starting TWAPI data download script.")

with open("conf/servers.yaml", "r") as f:
    config = yaml.safe_load(f)

logging.info("Loaded server configuration.")

time_start = datetime.now()

for server in config['servers']:
    logging.info(f"Server: {server['name']}, URL: {server['url']}")
    # Create an instance of the TWAPI class
    server_name = server['name']
    server_url = server['url']
    sleep_time = server.get('sleep', 5)  # Default to 5 seconds if not specified
    tw = TWAPI(server_name, server_url, sleep_time=sleep_time, save_local=False)
    tw.get_files()
    logging.info(f"Completed data download for server: {server_name}")

time_end = datetime.now()
logging.info(f"Data download completed. Start time: {time_start}, End time: {time_end}, Duration: {time_end - time_start}")
