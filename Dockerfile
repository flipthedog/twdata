# Use the official Python image from the Docker Hub
FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim

# Set the working directory in the container
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Ensure installed tools can be executed out of the box
ENV UV_TOOL_BIN_DIR=/usr/local/bin

# Copy the pyproject.toml and .gitignore files into the container

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY twdata/ ./twdata/
COPY pyproject.toml ./
COPY .gitignore ./
COPY uv.lock ./
COPY conf/servers.yaml ./conf/servers.yaml

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Set the entry point for the container
CMD ["python", "-m", "twdata.main"]