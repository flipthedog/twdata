import boto3
import pytest
import yaml
from tests.test_api import config
from twdata import TWAPI
import logging

logging.basicConfig(level=logging.INFO)

class TestS3FileValidity:

    def __init__(self):
        self.s3_client = boto3.client("s3")
        self.bucket_name = 'tribalwars-scraped'
        self.config_file = 'conf/servers.yaml'

        self.servers_config = self.load_server_config()

        self.files = [
            "ally_"
        ]

    def load_server_config(self):
        with open(self.config_file, 'r') as file:
            return yaml.safe_load(file)
    
    def check_s3_files(self, server, world):
        
        for server in config['servers']:
            logging.info(f"Server: {server['name']}, URL: {server['url']}")
            # Create an instance of the TWAPI class
            server_name = server['name']
            server_url = server['url']
            sleep_time = server.get('sleep', 5)  # Default to 5 seconds if not specified
            tw = TWAPI(server_name, server_url, sleep_time=sleep_time, save_local=True)
            active_worlds = tw.get_active_worlds()
            logging.info(f"Active worlds for {server_name}: {active_worlds}")


