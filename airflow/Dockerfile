FROM apache/airflow:2.10.4-python3.9

USER root

# Install Chromium and dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        unzip \
        chromium \
        chromium-driver \
        libglib2.0-0 \
        libnss3 \
        libx11-xcb1 \
        libxcb-dri3-0 \
        libxtst6 \
        libgbm1 \
        libasound2 \
        xvfb \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set Chromium binary location
ENV CHROME_BIN=/usr/bin/chromium

USER airflow

# Copy and install Python requirements
COPY requirements.txt /opt/airflow/requirements.txt
RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt

WORKDIR /opt/airflow