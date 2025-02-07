
## Requirements
- Python 3.10
- Poetry
- Docker
- AWS CLI

## Installation

1. **Clone the repository:**
    ```sh
    git clone https://github.com/yourusername/twdata.git
    cd twdata
    ```

2. **Install dependencies using Poetry:**
    ```sh
    poetry install
    ```

## Usage

1. **Run the project:**
    ```sh
    poetry run python src/main.py
    ```

2. **Build and push Docker image to ECR:**
    ```sh
    ./commands.sh
    ```

## Docker

The project includes a [Dockerfile](http://_vscodecontentref_/3) to build a Docker image. The Docker image uses Python 3.10 and installs dependencies using Poetry.

### Build Docker Image
```sh
docker build -t twdata:twdata .