# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the pyproject.toml and .gitignore files into the container
COPY pyproject.toml ./
COPY .gitignore ./

# Install Poetry
RUN pip install poetry

# Install dependencies
RUN poetry install --no-root

# Copy the rest of the application code into the container
COPY twdata/ ./twdata/

# Set the entry point for the container
CMD ["poetry", "run", "python", "twdata/main.py"]