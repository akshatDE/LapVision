# LapVision

LapVision is an end-to-end data pipeline that automates the process of scraping laptop data from Amazon, transforming raw HTML into structured CSV datasets, and performing machine learning predictions on laptop price and performance. This project integrates powerful tools like Apache Airflow for ETL orchestration, Docker for containerization, Selenium and BeautifulSoup for web scraping, and a Tkinter-based GUI for interactive predictions.

## Features

- **Web Scraping**: Utilizes Selenium and BeautifulSoup to extract laptop data from Amazon.
- **ETL Automation**: Schedules and executes ETL tasks using Apache Airflow.
- **Machine Learning**: Employs RandomForestRegressor (scikit-learn) with prediction metrics achieving an R² score of up to 0.92 and an RMSE as low as $150.
- **Interactive GUI**: Offers a Tkinter interface for real-time predictions and product suggestions.
- **Containerization**: Ensures consistent deployment with Docker and Docker Compose.

## Project Structure

amazon_project/
├── LapVision/
│   ├── airflow/
│   │   ├── dags/
│   │   │   └── amazon_ETL_dag.py       # ETL DAG for scraping and processing data
│   │   └── data/
│   │       └── laptop.csv              # Generated CSV data (typically excluded from VCS)
│   ├── src/
│   │   ├── init.py
│   │   └── app_final.py                # Main application with ML predictions and GUI
│   ├── requirements.txt                # Python dependencies for LapVision
│   └── README.md                       # LapVision-specific documentation
├── docker-compose.yml                  # Docker Compose configuration for the project
└── Dockerfile                          # Dockerfile to build the custom container image

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/lapvision.git
   cd lapvision

2. **Set Up Environment**:
   - Create a virtual environment (optional but recommended):
     ```bash
     python3 -m venv venv
     source venv/bin/activate  # Linux/macOS
     .\venv\Scripts\activate   # Windows
     ```
   - Install the required Python packages:
     ```bash
     pip install -r LapVision/requirements.txt
   - Ensure Docker and Docker Compose are installed on your system.

## Running the Project

1.Run the containerized application using Docker Compose:
   ```bash
   docker-compose up --build
   ```
2. Access the airflow at `http://localhost:8080`to monitor and trigger the ETL DAG.

## Running the Application

1.Navigate to the source directory and run the application:
   ```bash
   cd LapVision/src
   python app_final.py
   ```
2. Use the GUI to predict laptop prices and performance based on the trained model.

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request with your improvements.