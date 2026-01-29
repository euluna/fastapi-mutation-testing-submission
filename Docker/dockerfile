FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app/

# Install Python dependencies from pyproject.toml
RUN pip install --no-cache-dir -e .

# Install test dependencies
RUN pip install --no-cache-dir pytest pytest-cov

# Keep container running for interactive use
CMD ["/bin/bash"]