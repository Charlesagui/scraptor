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
        
        return True


@dataclass
class ExportParams:
    """Configuration parameters for data export"""
    output_directory: str = "./data"
    filename_prefix: str = "sp500_data"
    include_timestamp: bool = True
    
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
        
        return True


@dataclass
class LoggingParams:
    """Configuration parameters for logging"""
    log_level: str = "INFO"
    log_file: Optional[str] = "scraper.log"
    
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