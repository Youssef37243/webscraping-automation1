from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up Selenium options
options = Options()
options.add_argument("--headless")  # Enable headless mode for GitHub Actions
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")

# Rotate User-Agent to prevent detection
ua = UserAgent()
options.add_argument(f"user-agent={ua.random}")

# Set up ChromeDriver using webdriver_manager
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Define the target website
URL = "https://www.ebay.com/globaldeals/tech"

def scrape_data():
    """Scrape details from eBay for all product titles."""
    driver.get(URL)
    time.sleep(10)  # Allow time for elements to load

    # Capture timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Scroll down to load more products
    last_height = driver.execute_script("return document.body.scrollHeight")

    # Loop to keep scrolling until no new products are loaded
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for the page to load more products
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Now scrape all the products
    try:
        # Extract all titles on the page
        titles_elements = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, '//span[@itemprop="name"]'))
        )

        # Extract prices
        prices_elements = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[@itemscope="itemscope"]//span[@itemprop="price"]'))
        )

        # Extract original prices (if available) with try-except block
        original_prices = []
        try:
            original_price_elements = driver.find_elements(By.XPATH, '//div[@class="dne-itemtile-original-price"]//span[@class="itemtile-price-strikethrough"]')
            for elem in original_price_elements:
                if elem:
                    original_prices.append(elem.text)
                else:
                    original_prices.append("no original price")
        except Exception as e:
            print(f"Error extracting original prices: {e}")
            original_prices = ["no original price"] * len(titles_elements)

        # If there are fewer original prices than titles, fill the remaining ones with "no original price"
        if len(original_prices) < len(titles_elements):
            original_prices += ["no original price"] * (len(titles_elements) - len(original_prices))

        # Extract shipping information (if available) with try-except block
        shipping_info = []
        try:
            shipping_elements = driver.find_elements(By.XPATH, '//span[@class="dne-itemtile-delivery"]')
            for elem in shipping_elements:
                if elem:
                    shipping_info.append(elem.text)
                else:
                    shipping_info.append("no free shipping")
        except Exception as e:
            print(f"Error extracting shipping information: {e}")
            shipping_info = ["no free shipping"] * len(titles_elements)

        # If there are fewer shipping elements than titles, fill the remaining ones with "no free shipping"
        if len(shipping_info) < len(titles_elements):
            shipping_info += ["no free shipping"] * (len(titles_elements) - len(shipping_info))

        # Extract Item URLs
        url_elements = WebDriverWait(driver, 15).until(
            EC.visibility_of_all_elements_located((By.XPATH, '//div[@class="dne-itemtile-detail"]//a[@itemprop="url"]'))
        )

        titles = [title.text for title in titles_elements]
        prices = [price.text for price in prices_elements]
        urls = [url.get_attribute("href") for url in url_elements]

        ebay_data = []
        for title, price, original_price, shipping, url in zip(titles, prices, original_prices, shipping_info, urls):
            ebay_data.append({
                "timestamp": timestamp,
                "title": title,
                "price": price,
                "original_price": original_price,
                "shipping": shipping,
                "url": url,
            })

        return ebay_data

    except Exception as e:
        print(f"Error: {str(e)}")
        return []

def save_to_csv(data):
    file_name = "ebay_tech_deals.csv"
    try:
        df = pd.read_csv(file_name)
    except FileNotFoundError:
        df = pd.DataFrame(columns=["title", "timestamp", "price", "original_price", "shipping", "url"])

    # Create a DataFrame for the new data rows
    new_rows = pd.DataFrame(data)

    # Concatenate the new rows to the existing DataFrame
    df = pd.concat([df, new_rows], ignore_index=True)

    # Save back to CSV
    df.to_csv(file_name, index=False)

if __name__ == "__main__":
    print("Scraping eBay Data...")
    scraped_data = scrape_data()

    if scraped_data:
        save_to_csv(scraped_data)
        print(f"Data saved to ebay_tech_deals.csv, total {len(scraped_data)} products scraped.")
    else:
        print("Failed to scrape data.")

    driver.quit()