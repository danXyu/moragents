FROM python:3.12-bullseye

# Set the working directory in the container
WORKDIR /app

# Install system dependencies and a newer SQLite3
RUN apt-get update && apt-get install -y \
    gcc g++ procps curl wget build-essential \
    libreadline-dev libncursesw5-dev libssl-dev \
    libsqlite3-dev tk-dev libgdbm-dev libc6-dev \
    libbz2-dev libffi-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# Install newer SQLite3 from source
RUN wget https://www.sqlite.org/2023/sqlite-autoconf-3410200.tar.gz && \
    tar -xf sqlite-autoconf-3410200.tar.gz && \
    cd sqlite-autoconf-3410200 && \
    ./configure --prefix=/usr/local && \
    make && \
    make install && \
    cd .. && \
    rm -rf sqlite-autoconf-3410200 sqlite-autoconf-3410200.tar.gz

# Update library path
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

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
RUN poetry install --no-interaction --no-ansi --no-root

# Chrome installation for Debian Bullseye
RUN apt-get update && apt-get install -y \
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