import requests
import logging
import boto3
from typing import List
import time
from datetime import datetime

class TWAPI: 

    def __init__(self, worlds: List[int], language: str):
        
        self.language = language
        self.worlds = worlds

        self.urls = [f"https://{language}{world}.tribalwars.net" for world in worlds]

        self.map_files = {
            "village": "/map/village.txt",
            "player": "/map/player.txt",
            "ally": "/map/ally.txt",
            "conquer": "/map/conquer.txt",
            "kill_att": "/map/kill_att.txt",
            "kill_def": "/map/kill_def.txt",
            "kill_sup": "/map/kill_sup.txt",
            "kill_all": "/map/kill_all.txt",
            "kill_att_tribe": "/map/kill_att_tribe.txt",
            "kill_def_tribe": "/map/kill_def_tribe.txt",
            "kill_all_tribe": "/map/kill_all_tribe.txt",
        }

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        self.s3_client = boto3.client('s3')
        self.bucket_name = 'tribalwars-scraped'

    def get_files(self):
        for url in self.urls:
            world = url.split('.')[0].replace("https://", "")
            for key, value in self.map_files.items():
                url_get = url + value
                response = requests.get(url_get)

                # Upload to S3
                self.upload_to_s3(response.text, world, key)

                # delay of 10 seconds
                time.sleep(5)

    def upload_to_s3(self, file_content: str, world: str, key: str):
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3_key = f"{world}/{key}_{world}_{current_time}.txt"
        self.s3_client.put_object(Body=file_content, Bucket=self.bucket_name, Key=s3_key)
        logging.info(f"Uploaded content to s3://{self.bucket_name}/{s3_key}")
