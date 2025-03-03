from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Set up Chrome options
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument('--headless')
options.add_argument("--disable-blink-features=AutomationControlled")  # Bypass bot detection
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36")  # Add custom user-agent(Pretend to be a normal chrome user on Windows

# Initialize WebDriver with options
driver = webdriver.Chrome(options=options)
file = 0

# Load the webpage
for i in range(1, 21):
    driver.get("https://www.amazon.com/s?k=laptop&i=electronics&rh=n%3A172282%2Cp_123%3A219979%7C308445%7C391242&dc&page={i}&crid=I8G9EC239QAO&qid=1734139461&rnid=85457740011&sprefix=lap%2Caps%2C118&ref=sr_pg_1")
    # Locate the element
    try:
        elems = driver.find_elements(By.CLASS_NAME, "puis-card-container")
        print(f"Number of elements: {len(elems)}")
        for elem in elems:
            d = elem.get_attribute("outerHTML")
            with open(f"data/laptop_{file}.html","w",encoding="utf-8") as f:
                f.write(d)
                file += 1

    except Exception as e:
        print("Error locating element:", e)

    # Keep the browser open for observation
    time.sleep(2)
driver.close()