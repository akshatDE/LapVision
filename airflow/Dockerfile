# Use an ARM-compatible base image
FROM arm64v8/ubuntu:20.04

# Install required packages for Chromium and Selenium
RUN apt-get update && \
    apt-get install -y \
        wget \
        unzip \
        python3 \
        python3-pip \
        chromium-browser && \
    apt-get clean

# Set Chrome options
ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROME_DRIVER=/usr/local/bin/chromedriver

# Download ChromeDriver
# Ensure the version matches the installed Chromium version
RUN wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/116.0.5845.96/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip

# Install Python libraries
RUN pip3 install \
        selenium \
        pandas \
        beautifulsoup4

# Use a non-root user (optional, for security)
RUN useradd -ms /bin/bash airflow
USER airflow

# Working directory
WORKDIR /home/airflow

# Copy your Airflow DAGs or Python files if needed
# COPY your_script.py /home/airflow/your_script.py

# Set entrypoint (optional, adapt as needed)
# ENTRYPOINT ["python3", "/home/airflow/your_script.py"]