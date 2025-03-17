from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import os
import time


# Define the function to extract data
def extract_data():
    # Set up Chrome options
    options = Options()
    options.add_argument("--headless")  # Ensure GUI is off
    options.add_argument("--disable-blink-features=AutomationControlled")  # Bypass bot detection
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")  # Add custom user-agent

    # Specify the path to ChromeDriver (in the Docker container)
    service = Service(executable_path="/usr/bin/chromedriver")

    # Initialize WebDriver with options and service
    driver = webdriver.Chrome(service=service, options=options)

    # Directory to save the files
    output_dir = "/opt/airflow/data"
    os.makedirs(output_dir, exist_ok=True)  # Ensure the directory exists

    file = 0

    for i in range(1, 21):
        amazon_laptop = f"https://www.amazon.com/s?k=laptop&i=electronics&rh=n%3A172282%2Cp_123%3A219979%7C308445%7C391242&dc&page={i}&crid=I8G9EC239QAO&qid=1734139461&rnid=85457740011&sprefix=lap%2Caps%2C118&ref=sr_pg_1"
        # Load the webpage
        driver.get(amazon_laptop)
        # Locate the element
        try:
            elems = driver.find_elements(By.CLASS_NAME, "puis-card-container")
            print(f"Number of elements: {len(elems)}")
            for elem in elems:
                d = elem.get_attribute("outerHTML")
                with open(f"{output_dir}/laptop_{file}.html", "w", encoding="utf-8") as f:
                    f.write(d)
                    file += 1

        except Exception as e:
            print("Error locating element:", e)

        # Wait to avoid rate-limiting issues
        time.sleep(2)
    driver.close()

def get_data():
    """
    This function reads the html files from the data folder and extracts the title, price, rating, disk_size, ram and link of the laptops.
    """
    data_dict ={'title':[],'price':[],'rating':[],'disk_size':[],'ram':[],'link':[]}

    for file in os.listdir('data'):
        try:
            with open(f'data/{file}','r') as file:
                data = file.read()
            soup = BeautifulSoup(data,'html.parser')
            title = soup.find_all('h2')[0].text
            price = soup.find_all('span',attrs={"class":'a-offscreen'})[0].text
            rating  = soup.find_all('span',attrs = { "class":"a-icon-alt"})[0].text.split()[0]
            disk_size = soup.find_all('span',attrs = {"class":"a-text-bold"})[-3].text
            ram = soup.find_all('span',attrs = {"class":"a-text-bold"})[-2].text
            tags = soup.find('a')
            link  = "https://amazon.com/" + tags['href']
            data_dict['title'].append(title)
            data_dict['price'].append(price)
            data_dict['rating'].append(rating)
            data_dict['disk_size'].append(disk_size)
            data_dict['ram'].append(ram)
            data_dict['link'].append(link)
        
        except Exception as e:
            print(e)
    print('Data extracted successfully')
    return pd.DataFrame(data_dict)

def transform_df():
    """
    This function transforms the input dataframe into a new dataframe that is ready for feature extraction
    """
    df=get_data()
    def process_data(data):
        try:
            if 'GB' in data:
                return int(data.replace('GB',''))
            elif 'TB' in data:
                return int(data.replace('TB','')) * 1024
            else:
                return data
        except:
            return data
    
    def price_process(price):
        price_str = str(price)  # Convert price to string
        if price_str.startswith('$'):
            return price_str
        else:
            return 0
    def disk_size_process(disk_size):
        if disk_size == '-':
            return 0
        else:
            return disk_size
    def ram_process(ram):
        if ram == '-':
            return 0
        else:
            return ram
    
    # Apply the process_data function to the 'disk_size' column
    df['disk_size'] = df['disk_size'].apply(process_data)
    # Apply the price_process function to the 'price' column and some transformation
    df['price'] = df['price'].apply(price_process)
    
    # Apply the disk_size_process function to the 'disk_size' column
    df['disk_size'] = df['disk_size'].apply(disk_size_process)
    # Apply the ram_process function to the 'ram' column
    df['ram'] = df['ram'].apply(ram_process)

    # Convert the 'price' column to float
    df = df.drop(df[df['price'] == 0].index)
    df['price'] = df['price'].str.replace('$','').str.replace(',','')
    # Drop rows with missing values
    df = df.dropna()
    print("Data transformed successfully")
    return df
   
def load_data():
    # Use the same folder you mounted in docker-compose: ./data -> /opt/airflow/data
    output_dir = "/opt/airflow/data"
    csv_path = os.path.join(output_dir, "laptop.csv")

    # Generate fresh data
    data = transform_df()
    print(data.head())  # Optional: To verify data is being processed
    data.to_csv(csv_path, index=False)  # Overwrite the CSV file
    print(f"Data saved to: {csv_path}")
    return data

def remove_files_with_extension(folder_loc, extension):
    """
    Remove all files with a specific extension from a given folder.

    :param folder_path: Path to the folder
    :param extension: Extension to look for (e.g., ".txt")
    """
    for filename in os.listdir(folder_loc):
        if filename.endswith(extension):  # Check if the file ends with the given extension
            file_path = os.path.join(folder_loc, filename)
            os.remove(file_path)  # Remove the file
            print(f"Removed: {file_path}")

# Example usage
folder = "/opt/airflow/data"
extension = ".html"  # Specify the extension to remove
# remove_files_with_extension(folder, extension)
    

# Define the default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 12, 29),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'data_extract',
    default_args=default_args,
    description='Extract data from Amazon',
    schedule_interval=None,
)

extract_data_task = PythonOperator(
    task_id='extract_data',
    python_callable=extract_data,
    dag=dag,
    do_xcom_push=False,
)

get_data_task = PythonOperator(
    task_id='get_data',
    python_callable=get_data,
    dag=dag,
    do_xcom_push=False,
)

transform_df_task = PythonOperator(
    task_id='transform_df',
    python_callable=transform_df,
    dag=dag,
    do_xcom_push=False,
)

load_data_task = PythonOperator(
    task_id='load_data',
    python_callable=load_data,
    dag=dag,
    do_xcom_push=False,
)

remove_files_with_extension_task = PythonOperator(
    task_id='remove_files_with_extension',
    python_callable=remove_files_with_extension,
    op_args=[folder, extension],
    dag=dag,
    do_xcom_push=False,
)

# Set the task dependencies
extract_data_task >> get_data_task >> transform_df_task >> load_data_task >> remove_files_with_extension_task