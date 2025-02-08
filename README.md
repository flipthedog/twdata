# Tribal Wars Data Downloader
[Tribal Wars](www.tribalwars.net) is a popular real-time online browser strategy game that takes place over the course of several months. This project is a data downloader that fetches data from the game's API and stores it. The data can be used for analysis and visualizations.

# Disclaimer
Tribal Wars is a registered trademark of InnoGames GmbH. This project is not affiliated with InnoGames GmbH. Accessing and using the game's API should be severely limited to avoid any potential issues with the game's developers.

## Requirements
- Python 3.10
- Poetry
- Docker
- AWS CLI (for optional deployment to AWS)

## Installation

1. **Clone the repository:**
    ```sh
    git clone https://github.com/flipthedog/twdata.git
    cd twdata
    ```

2. **Install dependencies using Poetry:**
    ```sh
    poetry install
    ```

## Usage

1.a. **Run the project with Docker:**
    ```sh
    docker build -t twdata:twdata .
    docker run twdata:twdata
    ```

1.b. **Run the project through CLI:**
    ```sh
    poetry run python src/main.py
    ```

## AWS Credentials
This project stores data within S3 buckets. To use this feature, you must have an AWS account and configure your AWS CLI with your credentials.

## Docker

The project includes a Dockerfile to build a Docker image. The Docker image uses Python 3.10 and installs dependencies using Poetry.

### Build Docker Image
```sh
docker build -t twdata:twdata .