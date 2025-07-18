#!/usr/bin/env python3
"""
Stooq S&P 500 Scraper - Main Application Entry Point

This script scrapes S&P 500 stock data from Stooq.com and exports it to CSV format.
"""

import argparse
import sys
import signal
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.config.manager import ConfigManager
from src.scraper.stooq_scraper import StooqScraper
from src.exporters.csv_exporter import CSVExporter
from src.utils.logger import ScraperLogger
from src.utils.errors import ScrapingError, ConfigurationError, ExportError


class StooqScraperApp:
    """Main application class for Stooq S&P 500 scraper"""
    
    def __init__(self):
        self.config_manager = None
        self.logger = None
        self.scraper = None
        self.exporter = None
        self.shutdown_requested = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print(f"\nReceived signal {signum}. Initiating graceful shutdown...")
        self.shutdown_requested = True
        
        if self.logger:
            self.logger.warning("Shutdown signal received", signal=signum)
        
        self._cleanup()
        sys.exit(0)
    
    def run(self, args):
        """Main application entry point"""
        try:
            # Initialize components
            self._initialize_config(args)
            self._initialize_logger()
            self._initialize_components()
            
            # Log startup information
            self._log_startup_info(args)
            
            # Start scraping session
            self.logger.start_scraping_session()
            
            # Perform scraping
            stock_data = self._scrape_data()
            
            if not stock_data:
                self.logger.error("No stock data was scraped")
                return 1
            
            # Export data
            export_result = self._export_data(stock_data, args.output)
            
            # End session and show results
            self.logger.end_scraping_session()
            self._show_final_results(stock_data, export_result)
            
            return 0
            
        except KeyboardInterrupt:
            self.logger.warning("Operation cancelled by user")
            return 130
        except ConfigurationError as e:
            print(f"Configuration error: {e}")
            return 2
        except ScrapingError as e:
            if self.logger:
                self.logger.error("Scraping failed", exception=e)
            else:
                print(f"Scraping error: {e}")
            return 3
        except ExportError as e:
            if self.logger:
                self.logger.error("Export failed", exception=e)
            else:
                print(f"Export error: {e}")
            return 4
        except Exception as e:
            if self.logger:
                self.logger.critical("Unexpected error", exception=e)
            else:
                print(f"Unexpected error: {e}")
            return 5
        finally:
            self._cleanup()
    
    def _initialize_config(self, args):
        """Initialize configuration manager"""
        try:
            self.config_manager = ConfigManager(
                config_path=args.config,
                environment=args.environment
            )
            
            # Load configuration
            config_data = self.config_manager.load_config()
            
            # Apply command line overrides
            self._apply_cli_overrides(args)
            
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize configuration: {e}")
    
    def _apply_cli_overrides(self, args):
        """Apply command line argument overrides to configuration"""
        # Override scraping parameters
        if args.url:
            self.config_manager.set_config_value('scraping.base_url', args.url)
        
        if args.delay:
            self.config_manager.set_config_value('scraping.delay_between_requests', args.delay)
        
        if args.retries:
            self.config_manager.set_config_value('scraping.max_retries', args.retries)
        
        if args.timeout:
            self.config_manager.set_config_value('scraping.timeout', args.timeout)
        
        if args.headless is not None:
            self.config_manager.set_config_value('scraping.headless', args.headless)
        
        # Override export parameters
        if args.output_dir:
            self.config_manager.set_config_value('export.output_directory', args.output_dir)
        
        if args.filename_prefix:
            self.config_manager.set_config_value('export.filename_prefix', args.filename_prefix)
        
        # Override logging parameters
        if args.log_level:
            self.config_manager.set_config_value('logging.log_level', args.log_level.upper())
        
        if args.log_file:
            self.config_manager.set_config_value('logging.log_file', args.log_file)
    
    def _initialize_logger(self):
        """Initialize logging system"""
        try:
            self.logger = ScraperLogger("StooqScraper")
            
            # Get logging configuration
            app_config = self.config_manager.get_app_config()
            logging_config = {
                'log_level': app_config.logging.log_level,
                'log_file': app_config.logging.log_file,
                'console_output': True,  # Always enable console for main app
                'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
            
            self.logger.setup_logging(logging_config)
            
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize logging: {e}")
    
    def _initialize_components(self):
        """Initialize scraper and exporter components"""
        try:
            app_config = self.config_manager.get_app_config()
            
            # Initialize scraper
            self.scraper = StooqScraper(
                base_url=app_config.scraping.base_url,
                headless=getattr(app_config.scraping, 'headless', True),
                timeout=app_config.scraping.timeout
            )
            
            # Initialize exporter
            self.exporter = CSVExporter(
                output_directory=app_config.export.output_directory,
                filename_prefix=app_config.export.filename_prefix,
                include_timestamp=app_config.export.include_timestamp
            )
            
            self.logger.info("Components initialized successfully")
            
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize components: {e}")
    
    def _log_startup_info(self, args):
        """Log startup information"""
        self.logger.info("="*60)
        self.logger.info("STOOQ S&P 500 SCRAPER STARTED")
        self.logger.info("="*60)
        
        # Log configuration summary
        config_summary = self.config_manager.get_config_summary()
        self.logger.log_configuration(config_summary)
        
        # Log command line arguments
        self.logger.info("Command line arguments:")
        for key, value in vars(args).items():
            if value is not None:
                self.logger.info(f"  {key}: {value}")
    
    def _scrape_data(self):
        """Perform the scraping operation"""
        self.logger.info("Starting data scraping...")
        
        try:
            # Check for shutdown signal
            if self.shutdown_requested:
                self.logger.warning("Shutdown requested before scraping")
                return []
            
            # Perform scraping
            stock_data = self.scraper.fetch_data()
            
            self.logger.info(f"Scraping completed", stocks_found=len(stock_data))
            return stock_data
            
        except Exception as e:
            raise ScrapingError(f"Data scraping failed: {e}")
    
    def _export_data(self, stock_data, output_path=None):
        """Export scraped data to CSV"""
        self.logger.info("Starting data export...")
        
        try:
            # Export with summary
            export_result = self.exporter.export_with_summary(stock_data, output_path)
            
            if export_result.get('export_successful'):
                self.logger.log_export_result(
                    filepath=export_result.get('filepath', 'unknown'),
                    stock_count=export_result.get('row_count', 0),
                    file_size=export_result.get('file_size_bytes', 0)
                )
            else:
                raise ExportError(f"Export failed: {export_result.get('error', 'Unknown error')}")
            
            return export_result
            
        except Exception as e:
            raise ExportError(f"Data export failed: {e}")
    
    def _show_final_results(self, stock_data, export_result):
        """Show final results summary"""
        print("\n" + "="*60)
        print("SCRAPING COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Stocks scraped: {len(stock_data)}")
        print(f"Export file: {export_result.get('filepath', 'N/A')}")
        print(f"File size: {export_result.get('file_size_mb', 0):.2f} MB")
        print(f"Validation: {'PASSED' if export_result.get('validation_passed') else 'FAILED'}")
        
        # Show statistics summary
        stats = self.logger.get_stats_summary()
        if stats.get('duration_seconds'):
            print(f"Total time: {stats['duration_seconds']:.1f} seconds")
        if stats.get('success_rate'):
            print(f"Success rate: {stats['success_rate']:.1f}%")
        
        print("="*60)
    
    def _cleanup(self):
        """Clean up resources"""
        try:
            if self.scraper:
                self.scraper.close()
            
            if self.logger:
                self.logger.info("Application cleanup completed")
                
        except Exception as e:
            print(f"Warning: Cleanup error: {e}")


def create_argument_parser():
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description="Scrape S&P 500 stock data from Stooq.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Use default settings
  python main.py --headless false --delay 2.0      # Run with browser visible, 2s delay
  python main.py --config my_config.json           # Use custom config file
  python main.py --output-dir ./results            # Custom output directory
  python main.py --log-level DEBUG                 # Enable debug logging
        """
    )
    
    # Configuration options
    parser.add_argument('--config', '-c', 
                       help='Configuration file path (default: config.json)')
    parser.add_argument('--environment', '-e', 
                       choices=['development', 'production'], 
                       default='production',
                       help='Environment mode (default: production)')
    
    # Scraping options
    parser.add_argument('--url', '-u', 
                       help='Base URL to scrape (overrides config)')
    parser.add_argument('--delay', '-d', type=float,
                       help='Delay between requests in seconds (overrides config)')
    parser.add_argument('--retries', '-r', type=int,
                       help='Maximum number of retries (overrides config)')
    parser.add_argument('--timeout', '-t', type=int,
                       help='Request timeout in seconds (overrides config)')
    parser.add_argument('--headless', type=lambda x: x.lower() == 'true',
                       help='Run browser in headless mode (true/false)')
    
    # Export options
    parser.add_argument('--output', '-o',
                       help='Output CSV file path (overrides auto-generation)')
    parser.add_argument('--output-dir',
                       help='Output directory (overrides config)')
    parser.add_argument('--filename-prefix',
                       help='Output filename prefix (overrides config)')
    
    # Logging options
    parser.add_argument('--log-level', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Logging level (overrides config)')
    parser.add_argument('--log-file',
                       help='Log file path (overrides config)')
    
    # Utility options
    parser.add_argument('--create-config', action='store_true',
                       help='Create default configuration file and exit')
    parser.add_argument('--version', action='version', version='Stooq Scraper 1.0.0')
    
    return parser


def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Handle special commands
    if args.create_config:
        try:
            config_manager = ConfigManager()
            config_path = config_manager.create_default_config_file(args.config)
            print(f"Default configuration file created: {config_path}")
            return 0
        except Exception as e:
            print(f"Failed to create config file: {e}")
            return 1
    
    # Run main application
    app = StooqScraperApp()
    return app.run(args)


if __name__ == "__main__":
    sys.exit(main())