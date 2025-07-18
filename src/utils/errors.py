"""Custom exception classes for the scraper"""


class ScrapingError(Exception):
    """Base exception for scraping-related errors"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} | Details: {details_str}"
        return self.message


class DataExtractionError(ScrapingError):
    """Exception raised when data extraction fails"""
    pass


class ExportError(Exception):
    """Exception raised during data export operations"""
    
    def __init__(self, message: str, filepath: str = None):
        super().__init__(message)
        self.message = message
        self.filepath = filepath


class ConfigurationError(Exception):
    """Exception raised for configuration-related issues"""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message)
        self.message = message
        self.config_key = config_key


class NetworkError(ScrapingError):
    """Exception raised for network-related issues"""
    
    def __init__(self, message: str, url: str = None, status_code: int = None):
        super().__init__(message)
        self.message = message
        self.url = url
        self.status_code = status_code


class ParsingError(ScrapingError):
    """Exception raised when HTML parsing fails"""
    
    def __init__(self, message: str, selector: str = None, page_url: str = None):
        super().__init__(message)
        self.message = message
        self.selector = selector
        self.page_url = page_url


class ValidationError(ScrapingError):
    """Exception raised when data validation fails"""
    
    def __init__(self, message: str, field: str = None, value: str = None):
        super().__init__(message)
        self.message = message
        self.field = field
        self.value = value


class SeleniumError(ScrapingError):
    """Exception raised for Selenium-related issues"""
    
    def __init__(self, message: str, action: str = None, element: str = None):
        super().__init__(message)
        self.message = message
        self.action = action
        self.element = element


class RateLimitError(NetworkError):
    """Exception raised when rate limited by server"""
    
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.message = message
        self.retry_after = retry_after


class TimeoutError(ScrapingError):
    """Exception raised when operations timeout"""
    
    def __init__(self, message: str, timeout_seconds: int = None):
        super().__init__(message)
        self.message = message
        self.timeout_seconds = timeout_seconds