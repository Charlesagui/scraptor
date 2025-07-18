import time
import re
from typing import List, Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from .base import BaseScraper
from .http_client import HTTPClient
from ..models.stock_data import StockData
from ..parsers.html_parser import HTMLParser
from ..parsers.data_extractor import DataExtractor
from ..utils.errors import ScrapingError, NetworkError


class StooqScraper(BaseScraper):
    """Selenium-based scraper for Stooq S&P 500 data with dynamic content handling"""
    
    def __init__(self, base_url: str = "https://stooq.com/q/i/?s=^spx", 
                 headless: bool = True, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.driver = None
        self.html_parser = HTMLParser()
        self.data_extractor = DataExtractor()
        self.http_client = HTTPClient()
        
        # Chrome options for headless browsing
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument('--headless')
        
        # Anti-detection options
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        self.chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver with anti-detection measures"""
        try:
            driver = webdriver.Chrome(options=self.chrome_options)
            
            # Execute script to remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set window size to appear more human-like
            driver.set_window_size(1920, 1080)
            
            return driver
            
        except WebDriverException as e:
            raise ScrapingError(f"Failed to setup Chrome WebDriver: {e}")
    
    def fetch_data(self) -> List[StockData]:
        """Fetch S&P 500 stock data from Stooq"""
        try:
            # First try with simple HTTP request
            stocks = self._try_simple_scraping()
            if stocks:
                return stocks
            
            # If simple scraping fails, use Selenium
            return self._selenium_scraping()
            
        except Exception as e:
            raise ScrapingError(f"Failed to fetch data: {e}")
    
    def _try_simple_scraping(self) -> Optional[List[StockData]]:
        """Try simple HTTP scraping first (faster)"""
        try:
            print("Attempting simple HTTP scraping...")
            response = self.http_client.get_with_retry(self.base_url)
            
            # Check if content is dynamic
            if self.html_parser.detect_dynamic_content(response.text):
                print("Dynamic content detected, will use Selenium")
                return None
            
            # Parse with simple HTML parser
            rows = self.html_parser.parse_stock_table(response.text)
            if len(rows) < 10:  # Expect many rows for S&P 500
                print("Too few rows found, switching to Selenium")
                return None
            
            stocks = self.data_extractor.extract_multiple_stocks(rows)
            if len(stocks) >= 100:  # Reasonable threshold for S&P 500
                print(f"Simple scraping successful: {len(stocks)} stocks found")
                return stocks
            
            return None
            
        except Exception as e:
            print(f"Simple scraping failed: {e}")
            return None
    
    def _selenium_scraping(self) -> List[StockData]:
        """Use Selenium for dynamic content scraping"""
        print("Starting Selenium-based scraping...")
        
        try:
            self.driver = self._setup_driver()
            return self._scrape_with_selenium()
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def _scrape_with_selenium(self) -> List[StockData]:
        """Main Selenium scraping logic"""
        all_stocks = []
        
        try:
            # Navigate to the page
            print(f"Navigating to: {self.base_url}")
            self.driver.get(self.base_url)
            
            # Wait for page to load
            time.sleep(5)
            
            # Extract data from current page
            html_content = self.driver.page_source
            rows = self.html_parser.parse_stock_table(html_content)
            stocks = self.data_extractor.extract_multiple_stocks(rows)
            all_stocks.extend(stocks)
            
            print(f"Extracted {len(stocks)} stocks from page")
            return all_stocks
            
        except Exception as e:
            raise ScrapingError(f"Selenium scraping failed: {e}")
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        if self.http_client:
            self.http_client.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()