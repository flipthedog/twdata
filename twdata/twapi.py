import requests
import logging
import boto3
from typing import List, Dict, Optional
import time
from datetime import datetime
import phpserialize
import re

class TWAPI: 

    def __init__(self, language: str, base_url: Optional[str] = None, worlds: Optional[List[int]] = None, save_local: bool = False):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        self.language = language
        self.save_local = save_local

        logging.info(f"Initializing TWAPI for language: {language}")
        
        # Define domain mapping for different languages
        self.domain_map = {
            'en': '.net',
            'nl': '.nl',
            'de': '.de',
            'fr': '.fr',
            'es': '.es',
            'pt': '.pt',
            'it': '.it',
            'pl': '.pl',
            'tr': '.com.tr',
            'cs': '.cz',
            'sk': '.sk',
            'hu': '.hu',
            'ro': '.ro',
            'fi': '.fi',
            'se': '.se',
            'no': '.no',
            'dk': '.dk',
            'us': '.us',
            'uk': '.co.uk',
            'de': '.de',
        }
        
        # Get the appropriate domain for the language
        self.domain = self.domain_map.get(language, '.net')  # Default to .net
        logging.info(f"Using domain: {self.domain} for language: {language}")
        
        if base_url is None:
            self.base_url = f"https://{language}.tribalwars{self.domain}"
        else:
            self.base_url = base_url
            
        # Set up the worlds URL first - needed for fetching active worlds
        self.worlds_url = f"{self.base_url}/backend/get_servers.php"
        
        # If worlds are not provided, fetch active worlds for the language
        if worlds is None:
            logging.info("No worlds provided, auto-detecting active worlds...")
            active_worlds = self.get_worlds_by_language(language)
            # Extract numeric world IDs from world codes (e.g., 'en144' -> 144)
            self.worlds = []
            for world_code in active_worlds:
                # Extract numbers from world code
                numbers = re.findall(r'\d+', world_code)
                if numbers:
                    self.worlds.append(int(numbers[0]))
            logging.info(f"Auto-detected {len(self.worlds)} worlds for language '{language}': {self.worlds}")
        else:
            self.worlds = worlds
            logging.info(f"Using provided worlds: {self.worlds}")
        
        # Construct URLs with the correct domain for the language
        if base_url is None:
            self.urls = [f"https://{language}{world}.tribalwars{self.domain}" for world in self.worlds]
        else:
            # For custom base URLs like "https://die-staemme.de", extract the domain and use it
            from urllib.parse import urlparse
            parsed_url = urlparse(self.base_url)
            # For "https://die-staemme.de" -> "die-staemme.de"
            custom_domain = parsed_url.netloc
            self.urls = [f"https://{language}{world}.{custom_domain}" for world in self.worlds]
        
        logging.info(f"Generated {len(self.urls)} URLs for data collection")

        self.map_files = {
            "village": "/map/village.txt",
            "player": "/map/player.txt",
            "ally": "/map/ally.txt",
            "conquer": "/map/conquer.txt",
            "killatt": "/map/kill_att.txt",
            "killdef": "/map/kill_def.txt",
            "killsup": "/map/kill_sup.txt",
            "killall": "/map/kill_all.txt",
            "killatttribe": "/map/kill_att_tribe.txt",
            "killdeftribe": "/map/kill_def_tribe.txt",
            "killalltribe": "/map/kill_all_tribe.txt",
        }

        self.s3_client = boto3.client('s3')
        self.bucket_name = 'tribalwars-scraped'

    def get_active_worlds(self) -> Dict[str, str]:
        """
        Fetch currently active worlds from the Tribal Wars API.
        
        Returns:
            Dict[str, str]: Dictionary mapping world codes to their full URLs
        """
        try:
            response = requests.get(self.worlds_url)
            response.raise_for_status()
            
            # Parse PHP serialized data
            worlds_data = phpserialize.loads(response.content)
            
            # Convert bytes keys/values to strings if needed
            if isinstance(worlds_data, dict):
                worlds_dict = {}
                for key, value in worlds_data.items():
                    # Handle both string and bytes keys/values
                    key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
                    value_str = value.decode('utf-8') if isinstance(value, bytes) else str(value)
                    worlds_dict[key_str] = value_str
                
                logging.info(f"Successfully fetched {len(worlds_dict)} active worlds")
                return worlds_dict
            else:
                logging.error("Unexpected data format from worlds API")
                return {}
                
        except requests.RequestException as e:
            logging.error(f"Failed to fetch active worlds: {e}")
            return {}
        except Exception as e:
            logging.error(f"Failed to parse worlds data: {e}")
            return {}

    def get_worlds_by_language(self, language: str) -> List[str]:
        """
        Get active worlds filtered by language code.
        
        Args:
            language (str): Language code (e.g., 'en', 'de', 'fr')
            
        Returns:
            List[str]: List of world codes for the specified language
        """
        logging.info(f"Fetching worlds for language: {language}")
        active_worlds = self.get_active_worlds()
        language_worlds = []
        
        # Define exclusion patterns for world types we don't want
        exclusion_patterns = [
            r'^[a-z]+p\d+$',  # Matches patterns like 'enp16', 'enp17', etc. (premium worlds)
            r'^[a-z]+s\d+$',  # Matches patterns like 'ens1', 'ens2', etc. (speed worlds)
            r'^[a-z]+c\d+$',  # Matches patterns like 'enc1', 'enc2', etc. (classic worlds)
        ]
        
        logging.info(f"Filtering {len(active_worlds)} active worlds for language '{language}'")
        
        for world_code in active_worlds.keys():
            # Check if this world starts with the language and is followed by digits (regular worlds)
            # This matches 'en144', 'en146' but not 'enc1', 'ens1', 'enp16'
            if re.match(f'^{language}\\d+$', world_code):
                logging.debug(f"Found regular world for language '{language}': {world_code}")
                language_worlds.append(world_code)
            elif world_code.startswith(language):
                # This world starts with our language but has additional characters
                # Check if it matches any exclusion pattern
                excluded = False
                for pattern in exclusion_patterns:
                    if re.match(pattern, world_code):
                        excluded = True
                        logging.info(f"Excluding world '{world_code}' (matches exclusion pattern)")
                        break
                
                if not excluded:
                    logging.info(f"Including special world '{world_code}' (no exclusion pattern matched)")
                    language_worlds.append(world_code)
        
        logging.info(f"Found {len(language_worlds)} valid worlds for language '{language}': {language_worlds}")
        return language_worlds

    def get_files(self):
        logging.info(f"Starting file download for {len(self.urls)} worlds")
        logging.info(f"Will download {len(self.map_files)} file types per world")
        
        for i, url in enumerate(self.urls, 1):
            world = url.split('.')[0].replace("https://", "")
            logging.info(f"Processing world {i}/{len(self.urls)}: {world}")
            
            for j, (key, value) in enumerate(self.map_files.items(), 1):
                url_get = url + value
                logging.info(f"  Downloading file {j}/{len(self.map_files)}: {key} from {url_get}")
                
                try:
                    response = requests.get(url_get)
                    response.raise_for_status()
                    
                    if not self.check_file_validity(response.text):
                        logging.warning(f"  Invalid file content for {key} from {url_get}, skipping...")
                        continue

                    logging.info(f"  Successfully downloaded {key} ({len(response.text)} characters)")
                    
                    if self.save_local:
                        # Save locally
                        self.save_locally(response.text, world, key)
                    else:
                        # Upload to S3
                        self.upload_to_s3(response.text, world, key)
                    
                except requests.RequestException as e:
                    logging.error(f"  Failed to download {key} from {url_get}: {e}")
                    continue

                # delay of 5 seconds
                logging.debug(f"  Waiting 5 seconds before next download...")
                time.sleep(5)
        
        logging.info("Completed all file downloads")

    def check_file_validity(self, file_content: str) -> bool:
        """Checks if the downloaded file content is valid.

        Args:
            file_content (str): The content of the file to check.
        Returns:
            bool: True if valid, False otherwise.
        """

        check_string = "<!DOCTYPE html>"

        if file_content.startswith(check_string):
            logging.warning("  File content appears to be HTML, indicating an error page.")
            return False
        return True

    def save_locally(self, file_content: str, world: str, key: str):
        """Saves a file locally.

        Args:
            file_content (str): The content of the file to save.
            world (str): The world the file belongs to.
            key (str): The key (filename) to use.
        """
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/{key}_{world}_{current_time}.txt"
        
        try:
            # Ensure the directory exists
            import os
            os.makedirs(os.path.dirname(filename), exist_ok=True)
        except Exception as e:
            logging.error(f"  Failed to create directory for {filename}: {e}")
            raise

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(file_content)
            logging.info(f"  Successfully saved to {filename}")
        except Exception as e:
            logging.error(f"  Failed to save file {filename}: {e}")
            raise

    def upload_to_s3(self, file_content: str, world: str, key: str):
        """Uploads a file to S3.

        Args:
            file_content (str): The content of the file to upload.
            world (str): The world the file belongs to.
            key (str): The key (filename) to use in S3.
        """

        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        s3_key = f"{world}/{key}_{world}_{current_time}.txt"
        
        try:
            logging.info(f"  Uploading to S3: {s3_key} ({len(file_content)} characters)")
            self.s3_client.put_object(Body=file_content, Bucket=self.bucket_name, Key=s3_key)
            logging.info(f"  Successfully uploaded to s3://{self.bucket_name}/{s3_key}")
        except Exception as e:
            logging.error(f"  Failed to upload to S3: {e}")
            raise


if __name__ == "__main__":
    # Configure logging first
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Example usage
    tw = TWAPI("en")
    
    print("All active worlds:")
    print(tw.get_active_worlds())
    print("\nFiltered worlds for 'en':")
    print(f"World IDs: {tw.worlds}")
    print(f"URLs: {tw.urls}")
