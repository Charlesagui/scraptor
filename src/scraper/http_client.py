import requests
import time
import random
from typing import Optional, Dict, List
from ..utils.errors import ScrapingError


class HTTPClient:
    """HTTP client with retry mechanism and anti-bot measures"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, timeout: int = 30):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.timeout = timeout
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Configure session with headers and settings"""
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (compatible; StooqScraper/1.0)"
        ]
        
        # Default headers
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def _rotate_user_agent(self):
        """Rotate user agent to avoid detection"""
        self.session.headers['User-Agent'] = random.choice(self.user_agents)
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay"""
        return self.base_delay * (2 ** attempt) + random.uniform(0, 1)
    
    def get_with_retry(self, url: str, headers: Optional[Dict] = None) -> requests.Response:
        """Make GET request with retry mechanism and exponential backoff"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Rotate user agent for each attempt
                self._rotate_user_agent()
                
                # Merge custom headers with session headers
                request_headers = self.session.headers.copy()
                if headers:
                    request_headers.update(headers)
                
                # Make the request
                response = self.session.get(
                    url, 
                    headers=request_headers, 
                    timeout=self.timeout,
                    allow_redirects=True
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    self.handle_rate_limit(response, attempt)
                    continue
                
                # Check for successful response
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    delay = self._calculate_delay(attempt)
                    print(f"Request failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}")
                    print(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                else:
                    break
        
        # All retries failed
        raise ScrapingError(f"Failed to fetch {url} after {self.max_retries + 1} attempts. Last error: {last_exception}")
    
    def handle_rate_limit(self, response: requests.Response, attempt: int = 0):
        """Handle rate limiting with exponential backoff"""
        # Check for Retry-After header
        retry_after = response.headers.get('Retry-After')
        
        if retry_after:
            try:
                delay = int(retry_after)
            except ValueError:
                delay = self._calculate_delay(attempt)
        else:
            # Use exponential backoff if no Retry-After header
            delay = self._calculate_delay(attempt)
        
        print(f"Rate limited (HTTP 429). Waiting {delay} seconds before retry...")
        time.sleep(delay)
    
    def add_delay(self, custom_delay: Optional[float] = None):
        """Add delay between requests to be respectful"""
        delay = custom_delay if custom_delay is not None else self.base_delay
        # Add some randomness to avoid predictable patterns
        actual_delay = delay + random.uniform(0, delay * 0.5)
        time.sleep(actual_delay)
    
    def close(self):
        """Close the session"""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()