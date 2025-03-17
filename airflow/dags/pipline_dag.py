from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import json
from kafka import KafkaProducer, KafkaConsumer
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

OUTPUT_DIR = "/opt/airflow/data"
TOPIC = "test"
BOOTSTRAP_SERVERS = "kafka:9092"
def produce_data():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Try to initialize ChromeDriver safely
    try:
        service = Service(executable_path="/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"ChromeDriver failed to start: {e}")
        return
        
    # Try to initialize Kafka safely
    try:
        producer = KafkaProducer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=5  # Retry sending messages
        )
    except Exception as e:
        print(f"Failed to connect to Kafka: {e}")
        driver.quit()  # Close the driver before exiting
        return
    
    def process_page(page_number):
        """Process a single page and handle any tab crashes."""
        try:
            url = f"https://www.amazon.com/s?k=laptop&i=electronics&rh=n%3A172282%2Cp_123%3A219979%7C308445%7C391242&dc&page={page_number}&crid=I8G9EC239QAO&qid=1734139461&rnid=85457740011&sprefix=lap%2Caps%2C118&ref=sr_pg_1"
            driver.get(url)
            
            elems = driver.find_elements(By.CLASS_NAME, "puis-card-container")
            print(f"Page {page_number}: Found {len(elems)} elements")
            
            for elem in elems:
                data = {"text": elem.text, "html": elem.get_attribute("outerHTML")}
                producer.send(TOPIC, value=data)
                
            return True
        except Exception as e:
            print(f"Error on page {page_number}: {e}")
            return False
    
    try:
        for i in range(1, 21):
            success = process_page(i)
            if not success:
                print(f"Skipping page {i} due to errors")
            time.sleep(2)
            
        producer.flush()  # Ensure all messages are sent
    except Exception as e:
        print(f"Unexpected error during execution: {e}")
    
    finally:
        driver.quit()  # Ensure ChromeDriver always closes
        producer.close()  # Ensure Kafka producer closes


def consume_data(timeout_sec=60):
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='airflow-consumer',
        consumer_timeout_ms=60000
    )

    data_dict = {'title': [], 'price': [], 'rating': [], 'disk_size': [], 'ram': [], 'link': []}
    message_count = 0
    expected_message_count = 480

    for message in consumer:
        message_count += 1
        data = message.value
        try:
            soup = BeautifulSoup(data['html'], 'html.parser')
            title = soup.find('h2').text.strip() if soup.find('h2') else None
            price = soup.find('span', class_='a-offscreen').text.strip() if soup.find('span', class_='a-offscreen') else None
            rating = soup.find('span', class_='a-icon-alt').text.split()[0] if soup.find('span', class_='a-icon-alt') else None
            specs = soup.find_all('span', class_='a-text-bold')
            disk_size = next((spec.text.strip() for spec in specs if any(x in spec.text.lower() for x in ['ssd', 'hdd', 'gb', 'tb'])), None)
            ram = next((spec.text.strip() for spec in specs if 'ram' in spec.text.lower() or 'memory' in spec.text.lower()), None)
            link_elem = soup.find('a', class_='a-link-normal')
            link = f"https://amazon.com{link_elem['href']}" if link_elem and 'href' in link_elem.attrs else None
        except Exception as e:
            print(f"Error processing message: {e}")
            title, price, rating, disk_size, ram, link = None, None, None, None, None, None

        data_dict['title'].append(title)
        data_dict['price'].append(price)
        data_dict['rating'].append(rating)
        data_dict['disk_size'].append(disk_size)
        data_dict['ram'].append(ram)
        data_dict['link'].append(link)
        print(f"Processed {message_count} messages. Stopping consumer.")
        if message_count >= expected_message_count:
            break
    consumer.close()
    print(f"Total message consumed: {message_count}")
    # Pushing this to next task in the pipeline

    raw_df = pd.DataFrame(data_dict)
    # Saving raw data to csv
    raw_csv_path = os.path.join(OUTPUT_DIR, "laptop_raw.csv")
    raw_df.to_csv(raw_csv_path, index=False)
    print(f"Saved raw data to {raw_csv_path}")
    return raw_csv_path

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 3, 17),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'pipeline_dag',
    default_args=default_args,
    description='Extract and process laptop data via Kafka',
    schedule_interval=None,
    catchup=False,
)

produce_data_task = PythonOperator(
    task_id='produce_data',
    python_callable=produce_data,
    dag=dag,
)

consume_data_task = PythonOperator(
    task_id='consume_data',
    python_callable=consume_data,
    dag=dag,
)

produce_data_task >> consume_data_task 