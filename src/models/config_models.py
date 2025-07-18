from dataclasses import dataclass
from typing import Optional


@dataclass
class ScrapingParams:
    """Configuration parameters for scraping"""
    base_url: str = "https://stooq.com/q/i/?s=^spx"
    delay_between_requests: float = 1.0
    max_retries: int = 3
    timeout: int = 30
    user_agent: str = "Mozilla/5.0 (compatible; StooqScraper/1.0)"
    headless: bool = True
    use_selenium_fallback: bool = True
    max_pages: int = 15
    min_stocks_threshold: int = 100
    
    def __post_init__(self):
        """Validate scraping parameters"""
        self.validate()
    
    def validate(self) -> bool:
        """Validate scraping configuration"""
        if not self.base_url or not isinstance(self.base_url, str):
            raise ValueError("Base URL must be a non-empty string")
        
        if not isinstance(self.delay_between_requests, (int, float)) or self.delay_between_requests < 0:
            raise ValueError("Delay between requests must be a non-negative number")
        
        if not isinstance(self.max_retries, int) or self.max_retries < 0:
            raise ValueError("Max retries must be a non-negative integer")
        
        if not isinstance(self.timeout, int) or self.timeout <= 0:
            raise ValueError("Timeout must be a positive integer")
        
        if not self.user_agent or not isinstance(self.user_agent, str):
            raise ValueError("User agent must be a non-empty string")
        
        if not isinstance(self.headless, bool):
            raise ValueError("Headless must be a boolean")
        
        if not isinstance(self.use_selenium_fallback, bool):
            raise ValueError("Use selenium fallback must be a boolean")
        
        if not isinstance(self.max_pages, int) or self.max_pages <= 0:
            raise ValueError("Max pages must be a positive integer")
        
        if not isinstance(self.min_stocks_threshold, int) or self.min_stocks_threshold < 0:
            raise ValueError("Min stocks threshold must be a non-negative integer")
        
        return True


@dataclass
class ExportParams:
    """Configuration parameters for data export"""
    output_directory: str = "./data"
    filename_prefix: str = "sp500_data"
    include_timestamp: bool = True
    validate_output: bool = True
    
    def __post_init__(self):
        """Validate export parameters"""
        self.validate()
    
    def validate(self) -> bool:
        """Validate export configuration"""
        if not self.output_directory or not isinstance(self.output_directory, str):
            raise ValueError("Output directory must be a non-empty string")
        
        if not self.filename_prefix or not isinstance(self.filename_prefix, str):
            raise ValueError("Filename prefix must be a non-empty string")
        
        if not isinstance(self.include_timestamp, bool):
            raise ValueError("Include timestamp must be a boolean")
        
        if not isinstance(self.validate_output, bool):
            raise ValueError("Validate output must be a boolean")
        
        return True


@dataclass
class LoggingParams:
    """Configuration parameters for logging"""
    log_level: str = "INFO"
    log_file: Optional[str] = "scraper.log"
    console_output: bool = True
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    def __post_init__(self):
        """Validate logging parameters"""
        self.validate()
    
    def validate(self) -> bool:
        """Validate logging configuration"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        
        if self.log_file is not None and not isinstance(self.log_file, str):
            raise ValueError("Log file must be a string or None")
        
        if not isinstance(self.console_output, bool):
            raise ValueError("Console output must be a boolean")
        
        if not isinstance(self.log_format, str) or not self.log_format:
            raise ValueError("Log format must be a non-empty string")
        
        return True


@dataclass
class AppConfig:
    """Main application configuration"""
    scraping: ScrapingParams
    export: ExportParams
    logging: LoggingParams
    
    def __init__(self, scraping: dict = None, export: dict = None, logging: dict = None):
        """Initialize configuration with dictionaries"""
        self.scraping = ScrapingParams(**(scraping or {}))
        self.export = ExportParams(**(export or {}))
        self.logging = LoggingParams(**(logging or {}))
    
    def validate(self) -> bool:
        """Validate entire configuration"""
        self.scraping.validate()
        self.export.validate()
        self.logging.validate()
        return True