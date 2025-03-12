FROM --platform=linux/arm64 python:3.12-bullseye

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc g++ procps curl && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Copy pyproject.toml first for lock file generation
COPY pyproject.toml ./

# Generate lock file if it doesn't exist
RUN poetry lock --no-update || true

# Copy lock file and install dependencies
COPY poetry.lock* ./

# Install Python dependencies using Poetry
# Remove the virtualenvs.create false line and let Poetry use its default virtualenv
RUN poetry install --no-interaction --no-ansi --no-root

# Chrome installation for Debian Bullseye
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    apt-transport-https \
    ca-certificates \
    unzip \
    xvfb \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1

# Install ChromiumDriver instead of Chrome
RUN apt-get install -y chromium chromium-driver

# Set environment variables for Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

COPY . .

# Expose the port your application listens on
EXPOSE 5000

# Use the full path to the virtualenv's uvicorn
WORKDIR /app/src
CMD ["poetry", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]