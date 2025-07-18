import time
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
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
    """Intensive Selenium-based scraper for complete S&P 500 data from Stooq"""
    
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
        """Fetch S&P 500 stock data from Stooq with intensive search"""
        try:
            # First try with simple HTTP request
            stocks = self._try_simple_scraping()
            if stocks and len(stocks) >= 100:
                return stocks
            
            # If simple scraping fails or finds too few, use intensive Selenium
            return self._selenium_scraping_intensive()
            
        except Exception as e:
            raise ScrapingError(f"Failed to fetch data: {e}")
    
    def _try_simple_scraping(self) -> Optional[List[StockData]]:
        """Try simple HTTP scraping first (faster)"""
        try:
            print("🚀 Attempting simple HTTP scraping...")
            response = self.http_client.get_with_retry(self.base_url)
            
            # Check if content is dynamic
            if self.html_parser.detect_dynamic_content(response.text):
                print("⚡ Dynamic content detected, will use intensive Selenium")
                return None
            
            # Parse with simple HTML parser
            rows = self.html_parser.parse_stock_table(response.text)
            if len(rows) < 50:  # Need more rows for S&P 500
                print(f"📊 Only {len(rows)} rows found, switching to intensive Selenium")
                return None
            
            stocks = self.data_extractor.extract_multiple_stocks(rows)
            if len(stocks) >= 100:  # Good threshold for S&P 500
                print(f"✅ Simple scraping successful: {len(stocks)} stocks found")
                return stocks
            
            return None
            
        except Exception as e:
            print(f"❌ Simple scraping failed: {e}")
            return None
    
    def _selenium_scraping_intensive(self) -> List[StockData]:
        """Use intensive Selenium scraping for complete S&P 500 data"""
        print("🚀 Starting INTENSIVE Selenium-based S&P 500 scraping...")
        
        try:
            self.driver = self._setup_driver()
            return self._scrape_intensive()
            
        finally:
            if self.driver:
                self.driver.quit()
    
    def _scrape_intensive(self) -> List[StockData]:
        """Main intensive scraping logic to find all S&P 500 stocks"""
        all_stocks = []
        scraping_stats = {
            'pages_scraped': 0,
            'urls_tried': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'start_time': time.time()
        }
        
        try:
            print("🎯 Target: Find all ~500 S&P 500 stocks")
            
            # Try multiple S&P 500 URLs
            sp500_urls = self._get_sp500_urls()
            
            for i, url in enumerate(sp500_urls):
                try:
                    print(f"\n--- 🔍 Trying S&P 500 source {i+1}/{len(sp500_urls)} ---")
                    print(f"URL: {url}")
                    
                    stocks = self._scrape_url_intensive(url, scraping_stats)
                    
                    if stocks:
                        # Remove duplicates before adding
                        new_stocks = self._filter_new_stocks(stocks, all_stocks)
                        all_stocks.extend(new_stocks)
                        
                        print(f"✅ Found {len(stocks)} stocks ({len(new_stocks)} new)")
                        print(f"📊 Total unique stocks so far: {len(all_stocks)}")
                        
                        # If we found a good source, try to get more from it
                        if len(stocks) >= 50:
                            print("🔥 Good source found! Trying pagination...")
                            more_stocks = self._scrape_pagination_intensive(url, scraping_stats)
                            new_more = self._filter_new_stocks(more_stocks, all_stocks)
                            all_stocks.extend(new_more)
                            print(f"📄 Pagination added {len(new_more)} more stocks")
                    
                    # Stop if we have enough stocks
                    if len(all_stocks) >= 450:
                        print(f"🎯 TARGET REACHED! Found {len(all_stocks)} stocks!")
                        break
                        
                except Exception as e:
                    print(f"❌ Failed to scrape {url}: {e}")
                    scraping_stats['failed_extractions'] += 1
                    continue
            
            # Final cleanup and validation
            final_stocks = self._cleanup_and_validate_stocks(all_stocks)
            
            # Log final statistics
            self._log_intensive_stats(scraping_stats, len(final_stocks))
            
            return final_stocks
            
        except Exception as e:
            self._log_intensive_stats(scraping_stats, len(all_stocks), error=str(e))
            raise ScrapingError(f"Intensive S&P 500 scraping failed: {e}")
    
    def _get_sp500_urls(self) -> List[str]:
        """Get multiple potential S&P 500 URLs to try"""
        urls = [
            # Original URL with different parameters
            self.base_url,
            "https://stooq.com/q/i/?s=^spx&c=0&t=l&a=lg&b=0",
            "https://stooq.com/q/i/?s=^spx&f=1",
            "https://stooq.com/q/i/?s=^spx&c=1&t=c",
            "https://stooq.com/q/i/?s=^spx&t=c&i=d",
            
            # Alternative S&P 500 symbols
            "https://stooq.com/q/i/?s=spy",  # SPDR S&P 500 ETF
            "https://stooq.com/q/i/?s=^gspc", # Alternative S&P 500 symbol
            
            # Try different views and formats
            "https://stooq.com/q/i/?s=^spx&t=l&i=d&v=1",
            "https://stooq.com/q/i/?s=^spx&t=c&v=2",
        ]
        
        return urls
    
    def _scrape_url_intensive(self, url: str, stats: dict) -> List[StockData]:
        """Intensively scrape a single URL"""
        try:
            print(f"🌐 Navigating to: {url}")
            self.driver.get(url)
            stats['urls_tried'] += 1
            
            # Wait for page to load with multiple strategies
            self._wait_for_page_load_intensive()
            
            # Try multiple extraction strategies
            all_stocks = []
            
            print("📊 Strategy 1: Extract from all tables...")
            table_stocks = self._extract_from_all_tables()
            all_stocks.extend(table_stocks)
            print(f"   Found {len(table_stocks)} stocks from tables")
            
            print("🔍 Strategy 2: Look for S&P 500 patterns...")
            pattern_stocks = self._extract_sp500_patterns()
            all_stocks.extend(pattern_stocks)
            print(f"   Found {len(pattern_stocks)} stocks from patterns")
            
            print("🔗 Strategy 3: Extract from stock links...")
            link_stocks = self._extract_from_stock_links()
            all_stocks.extend(link_stocks)
            print(f"   Found {len(link_stocks)} stocks from links")
            
            # Remove duplicates from this URL
            unique_stocks = self._remove_duplicate_stocks(all_stocks)
            
            stats['pages_scraped'] += 1
            stats['successful_extractions'] += len(unique_stocks)
            
            return unique_stocks
            
        except Exception as e:
            print(f"❌ Failed to scrape URL {url}: {e}")
            return []
    
    def _wait_for_page_load_intensive(self):
        """Wait for page to load with multiple strategies"""
        try:
            wait = WebDriverWait(self.driver, self.timeout)
            
            # Try multiple selectors
            selectors_to_try = [
                "table", "tbody tr", "[class*='table']", "[id*='table']",
                "[class*='stock']", "[class*='symbol']", "[class*='price']",
                "a[href*='q/']", ".tab01", "#tab01", "tr td"
            ]
            
            element_found = False
            for selector in selectors_to_try:
                try:
                    elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
                    if len(elements) > 5:
                        print(f"✅ Page loaded - found {len(elements)} elements")
                        element_found = True
                        break
                except TimeoutException:
                    continue
            
            if not element_found:
                print("⚠️ No expected elements found, proceeding anyway")
            
            # Additional strategies
            time.sleep(3)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
        except Exception as e:
            print(f"⚠️ Page load wait failed: {e}")
    
    def _extract_from_all_tables(self) -> List[StockData]:
        """Extract data from all tables on the page"""
        stocks = []
        
        try:
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            print(f"   🔍 Found {len(tables)} tables")
            
            for i, table in enumerate(tables):
                try:
                    table_html = table.get_attribute('outerHTML')
                    rows = self.html_parser.parse_stock_table(table_html)
                    
                    if rows and len(rows) > 1:
                        table_stocks = self.data_extractor.extract_multiple_stocks(rows)
                        if table_stocks:
                            stocks.extend(table_stocks)
                            print(f"     📊 Table {i+1}: {len(table_stocks)} stocks")
                
                except Exception as e:
                    continue
            
            return stocks
            
        except Exception as e:
            return []
    
    def _extract_sp500_patterns(self) -> List[StockData]:
        """Look for S&P 500 specific patterns"""
        stocks = []
        
        try:
            # Look for stock symbols in various elements
            symbol_selectors = [
                "a[href*='/q/']", "[class*='symbol']", "[class*='ticker']",
                "td:first-child", "strong", ".symbol"
            ]
            
            for selector in symbol_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements[:200]:  # Reasonable limit
                        text = element.text.strip().upper()
                        
                        if self._looks_like_stock_symbol(text):
                            stock_data = self._create_stock_from_element(element, text)
                            if stock_data:
                                stocks.append(stock_data)
                
                except Exception:
                    continue
            
            return stocks
            
        except Exception:
            return []
    
    def _extract_from_stock_links(self) -> List[StockData]:
        """Extract from individual stock links"""
        stocks = []
        
        try:
            stock_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/q/']")
            
            for link in stock_links[:100]:  # Reasonable limit
                try:
                    text = link.text.strip().upper()
                    
                    if self._looks_like_stock_symbol(text):
                        stock_data = StockData(
                            symbol=text,
                            company_name=None,
                            price=None,
                            change_percent=None,
                            change_absolute=None,
                            timestamp=datetime.now(),
                            status='partial'
                        )
                        stocks.append(stock_data)
                
                except Exception:
                    continue
            
            return stocks
            
        except Exception:
            return []
    
    def _looks_like_stock_symbol(self, text: str) -> bool:
        """Check if text looks like a stock symbol"""
        if not text or len(text) > 10 or len(text) < 1:
            return False
        
        # Stock symbol patterns
        patterns = [
            r'^[A-Z]{1,5}$',
            r'^[A-Z]{1,5}\.[A-Z]+$',
            r'^[A-Z]{1,5}-[A-Z]$',
        ]
        
        return any(re.match(pattern, text) for pattern in patterns)
    
    def _create_stock_from_element(self, element, symbol: str) -> Optional[StockData]:
        """Create stock data from element"""
        try:
            parent = element.find_element(By.XPATH, "./..")
            row_text = parent.text
            
            price = self._extract_price_from_text(row_text)
            change_percent = self._extract_percentage_from_text(row_text)
            
            return StockData(
                symbol=symbol,
                company_name=None,
                price=price,
                change_percent=change_percent,
                change_absolute=None,
                timestamp=datetime.now(),
                status='success' if price else 'partial'
            )
            
        except Exception:
            return None
    
    def _extract_price_from_text(self, text: str) -> Optional[float]:
        """Extract price from text"""
        try:
            price_patterns = [
                r'\$?(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)',
                r'(\d+\.\d{2})',
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    try:
                        clean_price = match.replace(',', '')
                        price = float(clean_price)
                        if 0.01 <= price <= 10000:
                            return price
                    except:
                        continue
            
            return None
            
        except Exception:
            return None
    
    def _extract_percentage_from_text(self, text: str) -> Optional[float]:
        """Extract percentage from text"""
        try:
            percent_patterns = [
                r'([+-]?\d+\.\d+)%',
                r'([+-]?\d+)%',
            ]
            
            for pattern in percent_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    try:
                        percent = float(match)
                        if -100 <= percent <= 100:
                            return percent
                    except:
                        continue
            
            return None
            
        except Exception:
            return None
    
    def _scrape_pagination_intensive(self, base_url: str, stats: dict) -> List[StockData]:
        """Scrape pagination pages"""
        all_stocks = []
        
        try:
            # Look for pagination
            pagination_selectors = [
                "a[href*='page']", "a[href*='p=']", ".pagination a",
                "a[href*='next']", "a[href*='more']"
            ]
            
            pagination_links = []
            for selector in pagination_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        href = element.get_attribute('href')
                        if href and href not in pagination_links:
                            pagination_links.append(href)
                except:
                    continue
            
            print(f"   🔗 Found {len(pagination_links)} pagination links")
            
            for i, link in enumerate(pagination_links[:5]):  # Limit pages
                try:
                    print(f"   📄 Page {i+1}: {link}")
                    
                    self.driver.get(link)
                    self._wait_for_page_load_intensive()
                    
                    page_stocks = self._extract_from_all_tables()
                    if page_stocks:
                        all_stocks.extend(page_stocks)
                        print(f"     ✅ Got {len(page_stocks)} stocks")
                    
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"     ❌ Page {i+1} failed: {e}")
                    continue
            
            return all_stocks
            
        except Exception:
            return []
    
    def _filter_new_stocks(self, new_stocks: List[StockData], existing_stocks: List[StockData]) -> List[StockData]:
        """Filter out stocks that already exist"""
        existing_symbols = {stock.symbol for stock in existing_stocks if stock.symbol}
        return [stock for stock in new_stocks if stock.symbol and stock.symbol not in existing_symbols]
    
    def _remove_duplicate_stocks(self, stocks: List[StockData]) -> List[StockData]:
        """Remove duplicates within a list"""
        seen_symbols = set()
        unique_stocks = []
        
        for stock in stocks:
            if stock.symbol and stock.symbol not in seen_symbols:
                seen_symbols.add(stock.symbol)
                unique_stocks.append(stock)
        
        return unique_stocks
    
    def _cleanup_and_validate_stocks(self, stocks: List[StockData]) -> List[StockData]:
        """Final cleanup and validation"""
        print(f"\n🧹 Cleaning up {len(stocks)} stocks...")
        
        # Remove duplicates
        unique_stocks = self._remove_duplicate_stocks(stocks)
        print(f"   Removed {len(stocks) - len(unique_stocks)} duplicates")
        
        # Validate and clean
        valid_stocks = []
        for stock in unique_stocks:
            if self._is_valid_sp500_stock(stock):
                valid_stocks.append(stock)
        
        print(f"   {len(valid_stocks)} stocks passed validation")
        return valid_stocks
    
    def _is_valid_sp500_stock(self, stock: StockData) -> bool:
        """Validate stock data"""
        try:
            if not stock.symbol or len(stock.symbol) > 10:
                return False
            
            if stock.price is not None:
                if stock.price <= 0 or stock.price > 10000:
                    return False
            
            if not re.match(r'^[A-Z]{1,5}(\.[A-Z]+)?$', stock.symbol.upper()):
                return False
            
            return True
            
        except Exception:
            return False
    
    def _log_intensive_stats(self, stats: dict, total_stocks: int, error: str = None):
        """Log intensive scraping statistics"""
        elapsed_time = time.time() - stats['start_time']
        
        print("\n" + "="*60)
        print("🚀 INTENSIVE S&P 500 SCRAPING RESULTS")
        print("="*60)
        print(f"📊 Total unique stocks found: {total_stocks}")
        print(f"🌐 URLs tried: {stats['urls_tried']}")
        print(f"📄 Pages scraped: {stats['pages_scraped']}")
        print(f"✅ Successful extractions: {stats['successful_extractions']}")
        print(f"❌ Failed extractions: {stats['failed_extractions']}")
        print(f"⏱️ Total time: {elapsed_time:.2f} seconds")
        
        if error:
            print(f"🚨 Error: {error}")
        
        # Coverage assessment
        if total_stocks >= 400:
            print("🎯 EXCELLENT: Found most of S&P 500!")
        elif total_stocks >= 200:
            print("👍 GOOD: Found significant portion")
        elif total_stocks >= 50:
            print("⚠️ PARTIAL: Found some stocks")
        else:
            print("❌ LIMITED: Found few stocks")
        
        print("="*60 + "\n")
    
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