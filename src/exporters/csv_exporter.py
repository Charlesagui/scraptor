import csv
import os
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from .base_exporter import BaseExporter
from ..models.stock_data import StockData
from ..utils.errors import ExportError


class CSVExporter(BaseExporter):
    """CSV exporter using built-in csv module with minimal dependencies"""
    
    def __init__(self, output_directory: str = "./data", 
                 filename_prefix: str = "sp500_data",
                 include_timestamp: bool = True):
        self.output_directory = output_directory
        self.filename_prefix = filename_prefix
        self.include_timestamp = include_timestamp
        
        # Ensure output directory exists
        self._ensure_directory_exists()
    
    def _ensure_directory_exists(self):
        """Create output directory if it doesn't exist"""
        try:
            Path(self.output_directory).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ExportError(f"Failed to create output directory {self.output_directory}: {e}")
    
    def export(self, data: List[StockData], path: str = None) -> str:
        """Export stock data to CSV file"""
        if not data:
            raise ExportError("No data provided for export")
        
        # Generate filename if not provided
        if path is None:
            path = self._generate_filename()
        
        # Validate data before export
        valid_data = self._validate_and_clean_data(data)
        if not valid_data:
            raise ExportError("No valid data to export after validation")
        
        try:
            # Write CSV file
            with open(path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self._get_csv_headers())
                
                # Write headers
                writer.writeheader()
                
                # Write data rows
                for stock in valid_data:
                    writer.writerow(self._stock_to_csv_row(stock))
            
            print(f"Successfully exported {len(valid_data)} stocks to {path}")
            return path
            
        except Exception as e:
            raise ExportError(f"Failed to write CSV file {path}: {e}")
    
    def _generate_filename(self) -> str:
        """Generate filename with timestamp"""
        timestamp_str = ""
        if self.include_timestamp:
            timestamp = datetime.now()
            timestamp_str = f"_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        filename = f"{self.filename_prefix}{timestamp_str}.csv"
        return os.path.join(self.output_directory, filename)
    
    def _get_csv_headers(self) -> List[str]:
        """Get CSV column headers"""
        return [
            'symbol',
            'company_name',
            'price',
            'change_percent',
            'change_absolute',
            'timestamp',
            'status'
        ]
    
    def _stock_to_csv_row(self, stock: StockData) -> dict:
        """Convert StockData to CSV row dictionary"""
        return {
            'symbol': stock.symbol or 'N/A',
            'company_name': stock.company_name or 'N/A',
            'price': self._format_price(stock.price),
            'change_percent': self._format_percentage(stock.change_percent),
            'change_absolute': self._format_price(stock.change_absolute),
            'timestamp': stock.timestamp.isoformat() if stock.timestamp else 'N/A',
            'status': stock.status or 'unknown'
        }
    
    def _format_price(self, price: Optional[float]) -> str:
        """Format price for CSV output"""
        if price is None:
            return 'N/A'
        
        try:
            # Format to 2 decimal places
            return f"{price:.2f}"
        except (ValueError, TypeError):
            return 'N/A'
    
    def _format_percentage(self, percentage: Optional[float]) -> str:
        """Format percentage for CSV output"""
        if percentage is None:
            return 'N/A'
        
        try:
            # Format to 2 decimal places with % sign
            return f"{percentage:.2f}%"
        except (ValueError, TypeError):
            return 'N/A'
    
    def _validate_and_clean_data(self, data: List[StockData]) -> List[StockData]:
        """Validate and clean data before export"""
        valid_data = []
        
        for i, stock in enumerate(data):
            try:
                # Basic validation
                if not stock.symbol:
                    print(f"Warning: Skipping stock at index {i} - no symbol")
                    continue
                
                # Clean symbol (remove extra whitespace, convert to uppercase)
                stock.symbol = stock.symbol.strip().upper()
                
                # Validate symbol format
                if len(stock.symbol) > 10 or not stock.symbol.replace('.', '').isalnum():
                    print(f"Warning: Skipping invalid symbol: {stock.symbol}")
                    continue
                
                # Clean company name
                if stock.company_name:
                    stock.company_name = stock.company_name.strip()
                
                # Validate price range
                if stock.price is not None:
                    if stock.price < 0 or stock.price > 100000:
                        print(f"Warning: Invalid price for {stock.symbol}: {stock.price}")
                        stock.price = None
                
                # Validate percentage range
                if stock.change_percent is not None:
                    if abs(stock.change_percent) > 1000:  # Allow for extreme cases
                        print(f"Warning: Extreme percentage change for {stock.symbol}: {stock.change_percent}%")
                
                # Ensure timestamp exists
                if not stock.timestamp:
                    stock.timestamp = datetime.now()
                
                # Ensure status is set
                if not stock.status:
                    stock.status = 'success' if stock.price is not None else 'partial'
                
                valid_data.append(stock)
                
            except Exception as e:
                print(f"Warning: Error validating stock at index {i}: {e}")
                continue
        
        return valid_data
    
    def validate_csv_output(self, filepath: str) -> bool:
        """Validate that CSV file was created correctly"""
        try:
            if not os.path.exists(filepath):
                return False
            
            # Check file size
            if os.path.getsize(filepath) == 0:
                return False
            
            # Try to read the CSV file
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Check headers
                expected_headers = set(self._get_csv_headers())
                actual_headers = set(reader.fieldnames or [])
                
                if not expected_headers.issubset(actual_headers):
                    return False
                
                # Check if we have at least one data row
                try:
                    next(reader)
                    return True
                except StopIteration:
                    return False
                    
        except Exception as e:
            print(f"CSV validation error: {e}")
            return False
    
    def get_export_summary(self, filepath: str) -> dict:
        """Get summary information about exported CSV file"""
        try:
            if not os.path.exists(filepath):
                return {'error': 'File does not exist'}
            
            file_size = os.path.getsize(filepath)
            
            # Count rows
            row_count = 0
            with open(filepath, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                row_count = sum(1 for row in reader)
            
            return {
                'filepath': filepath,
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'row_count': row_count,
                'created_at': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def export_with_summary(self, data: List[StockData], path: str = None) -> dict:
        """Export data and return summary information"""
        try:
            # Export the data
            exported_path = self.export(data, path)
            
            # Validate the export
            is_valid = self.validate_csv_output(exported_path)
            
            # Get summary
            summary = self.get_export_summary(exported_path)
            summary['validation_passed'] = is_valid
            summary['export_successful'] = True
            
            return summary
            
        except Exception as e:
            return {
                'export_successful': False,
                'error': str(e)
            }