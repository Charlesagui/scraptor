"""Default configuration settings for the Stooq S&P 500 scraper"""

DEFAULT_SETTINGS = {
    "scraping": {
        "base_url": "https://stooq.com/q/i/?s=^spx",
        "delay_between_requests": 1.0,
        "max_retries": 3,
        "timeout": 30,
        "user_agent": "Mozilla/5.0 (compatible; StooqScraper/1.0)",
        "headless": True,
        "use_selenium_fallback": True,
        "max_pages": 15,
        "min_stocks_threshold": 100
    },
    "export": {
        "output_directory": "./data",
        "filename_prefix": "sp500_data",
        "include_timestamp": True,
        "validate_output": True
    },
    "logging": {
        "log_level": "INFO",
        "log_file": "scraper.log",
        "console_output": True,
        "log_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    },
    "validation": {
        "min_price": 0.01,
        "max_price": 100000.0,
        "max_percentage_change": 1000.0,
        "max_symbol_length": 10,
        "required_fields": ["symbol"]
    }
}

# Environment-specific overrides
DEVELOPMENT_OVERRIDES = {
    "scraping": {
        "delay_between_requests": 0.5,
        "max_pages": 3,
        "headless": False
    },
    "logging": {
        "log_level": "DEBUG"
    }
}

PRODUCTION_OVERRIDES = {
    "scraping": {
        "delay_between_requests": 2.0,
        "max_retries": 5,
        "headless": True
    },
    "logging": {
        "log_level": "WARNING",
        "console_output": False
    }
}