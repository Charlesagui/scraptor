import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class ScraperLogger:
    """Logging system using built-in logging module"""
    
    def __init__(self, name: str = "StooqScraper"):
        self.name = name
        self.logger = None
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_stocks_extracted': 0,
            'pages_scraped': 0,
            'errors': [],
            'warnings': []
        }
    
    def setup_logging(self, config: Dict[str, Any]):
        """Setup logging configuration"""
        try:
            # Create logger
            self.logger = logging.getLogger(self.name)
            self.logger.setLevel(getattr(logging, config.get('log_level', 'INFO')))
            
            # Clear existing handlers
            self.logger.handlers.clear()
            
            # Setup file handler if log_file is specified
            if config.get('log_file'):
                self._setup_file_handler(config)
            
            # Setup console handler if enabled
            if config.get('console_output', True):
                self._setup_console_handler(config)
            
            # Prevent duplicate logs
            self.logger.propagate = False
            
            self.info("Logging system initialized")
            
        except Exception as e:
            print(f"Failed to setup logging: {e}")
            # Fallback to basic logging
            self._setup_fallback_logging()
    
    def _setup_file_handler(self, config: Dict[str, Any]):
        """Setup file logging handler"""
        log_file = config['log_file']
        
        try:
            # Ensure log directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create file handler
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(getattr(logging, config.get('log_level', 'INFO')))
            
            # Set formatter
            formatter = logging.Formatter(
                config.get('log_format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
            
        except Exception as e:
            print(f"Failed to setup file logging: {e}")
    
    def _setup_console_handler(self, config: Dict[str, Any]):
        """Setup console logging handler"""
        try:
            # Create console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, config.get('log_level', 'INFO')))
            
            # Set formatter (simpler for console)
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(console_handler)
            
        except Exception as e:
            print(f"Failed to setup console logging: {e}")
    
    def _setup_fallback_logging(self):
        """Setup basic fallback logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.name)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        if self.logger:
            self.logger.debug(self._format_message(message, **kwargs))
        else:
            print(f"DEBUG: {message}")
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        if self.logger:
            self.logger.info(self._format_message(message, **kwargs))
        else:
            print(f"INFO: {message}")
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        if self.logger:
            self.logger.warning(self._format_message(message, **kwargs))
        else:
            print(f"WARNING: {message}")
        
        # Track warning
        self.stats['warnings'].append({
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': kwargs
        })
    
    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log error message"""
        full_message = self._format_message(message, **kwargs)
        
        if exception:
            full_message += f" | Exception: {str(exception)}"
        
        if self.logger:
            self.logger.error(full_message)
        else:
            print(f"ERROR: {full_message}")
        
        # Track error
        self.stats['errors'].append({
            'message': message,
            'exception': str(exception) if exception else None,
            'timestamp': datetime.now().isoformat(),
            'details': kwargs
        })
    
    def critical(self, message: str, exception: Optional[Exception] = None, **kwargs):
        """Log critical message"""
        full_message = self._format_message(message, **kwargs)
        
        if exception:
            full_message += f" | Exception: {str(exception)}"
        
        if self.logger:
            self.logger.critical(full_message)
        else:
            print(f"CRITICAL: {full_message}")
        
        # Track critical error
        self.stats['errors'].append({
            'message': message,
            'exception': str(exception) if exception else None,
            'timestamp': datetime.now().isoformat(),
            'level': 'CRITICAL',
            'details': kwargs
        })
    
    def _format_message(self, message: str, **kwargs) -> str:
        """Format log message with additional context"""
        if kwargs:
            context_parts = [f"{k}={v}" for k, v in kwargs.items()]
            return f"{message} | {' | '.join(context_parts)}"
        return message
    
    def start_scraping_session(self):
        """Start a new scraping session"""
        self.stats['start_time'] = datetime.now()
        self.info("Scraping session started")
    
    def end_scraping_session(self):
        """End scraping session"""
        self.stats['end_time'] = datetime.now()
        self.info("Scraping session ended")
        self.log_scraping_stats(self.stats)
    
    def log_request(self, url: str, success: bool, response_time: float = None):
        """Log HTTP request"""
        self.stats['total_requests'] += 1
        
        if success:
            self.stats['successful_requests'] += 1
            self.debug(f"Request successful", url=url, response_time=response_time)
        else:
            self.stats['failed_requests'] += 1
            self.warning(f"Request failed", url=url)
    
    def log_page_scraped(self, page_url: str, stocks_found: int):
        """Log page scraping result"""
        self.stats['pages_scraped'] += 1
        self.stats['total_stocks_extracted'] += stocks_found
        self.info(f"Page scraped", url=page_url, stocks_found=stocks_found)
    
    def log_scraping_stats(self, stats: Dict[str, Any]):
        """Log comprehensive scraping statistics"""
        if not stats.get('start_time'):
            return
        
        # Calculate duration
        end_time = stats.get('end_time') or datetime.now()
        duration = end_time - stats['start_time']
        
        self.info("="*60)
        self.info("SCRAPING SESSION STATISTICS")
        self.info("="*60)
        
        # Time statistics
        self.info(f"Session duration: {duration}")
        self.info(f"Start time: {stats['start_time'].isoformat()}")
        self.info(f"End time: {end_time.isoformat()}")
        
        # Request statistics
        self.info(f"Total requests: {stats['total_requests']}")
        self.info(f"Successful requests: {stats['successful_requests']}")
        self.info(f"Failed requests: {stats['failed_requests']}")
        
        if stats['total_requests'] > 0:
            success_rate = (stats['successful_requests'] / stats['total_requests']) * 100
            self.info(f"Request success rate: {success_rate:.1f}%")
        
        # Scraping statistics
        self.info(f"Pages scraped: {stats['pages_scraped']}")
        self.info(f"Total stocks extracted: {stats['total_stocks_extracted']}")
        
        if stats['pages_scraped'] > 0:
            avg_stocks_per_page = stats['total_stocks_extracted'] / stats['pages_scraped']
            self.info(f"Average stocks per page: {avg_stocks_per_page:.1f}")
        
        # Performance statistics
        total_seconds = duration.total_seconds()
        if total_seconds > 0:
            stocks_per_second = stats['total_stocks_extracted'] / total_seconds
            self.info(f"Extraction rate: {stocks_per_second:.2f} stocks/second")
        
        # Error statistics
        self.info(f"Errors encountered: {len(stats['errors'])}")
        self.info(f"Warnings encountered: {len(stats['warnings'])}")
        
        # Log recent errors
        if stats['errors']:
            self.info("Recent errors:")
            for error in stats['errors'][-5:]:  # Last 5 errors
                self.info(f"  - {error['message']} ({error['timestamp']})")
        
        self.info("="*60)
    
    def log_export_result(self, filepath: str, stock_count: int, file_size: int):
        """Log CSV export result"""
        self.info(f"Data exported successfully", 
                 filepath=filepath, 
                 stock_count=stock_count, 
                 file_size_mb=round(file_size / (1024*1024), 2))
    
    def log_validation_result(self, passed: bool, details: Dict[str, Any]):
        """Log data validation result"""
        if passed:
            self.info("Data validation passed", **details)
        else:
            self.warning("Data validation failed", **details)
    
    def log_configuration(self, config_summary: Dict[str, Any]):
        """Log configuration summary"""
        self.info("Configuration loaded:")
        for key, value in config_summary.items():
            self.info(f"  {key}: {value}")
    
    def log_selenium_action(self, action: str, success: bool, details: Dict[str, Any] = None):
        """Log Selenium actions"""
        if success:
            self.debug(f"Selenium action successful: {action}", **(details or {}))
        else:
            self.warning(f"Selenium action failed: {action}", **(details or {}))
    
    def log_parsing_result(self, element_type: str, found_count: int, expected_min: int = None):
        """Log HTML parsing results"""
        if expected_min and found_count < expected_min:
            self.warning(f"Found fewer {element_type} than expected", 
                        found=found_count, expected_min=expected_min)
        else:
            self.debug(f"Parsing successful", element_type=element_type, found=found_count)
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """Get current statistics summary"""
        stats = self.stats.copy()
        
        # Add calculated fields
        if stats['start_time']:
            end_time = stats.get('end_time') or datetime.now()
            stats['duration_seconds'] = (end_time - stats['start_time']).total_seconds()
        
        if stats['total_requests'] > 0:
            stats['success_rate'] = (stats['successful_requests'] / stats['total_requests']) * 100
        
        return stats
    
    def reset_stats(self):
        """Reset statistics for new session"""
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_stocks_extracted': 0,
            'pages_scraped': 0,
            'errors': [],
            'warnings': []
        }