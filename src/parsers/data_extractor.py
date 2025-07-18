import re
from datetime import datetime
from typing import Optional, List, Dict, Any
from bs4 import Tag
from ..models.stock_data import StockData
from ..utils.errors import DataExtractionError


class DataExtractor:
    """Extract and clean stock data from HTML elements with format adaptation"""
    
    def __init__(self):
        # Common column patterns for different data types
        self.symbol_patterns = [
            r'^[A-Z]{1,5}$',  # Standard ticker symbols
            r'^[A-Z]+\.[A-Z]+$',  # Exchange notation (e.g., AAPL.US)
        ]
        
        self.price_patterns = [
            r'[\d,]+\.?\d*',  # Numbers with commas and optional decimals
            r'\d+\.?\d*',     # Simple decimal numbers
        ]
        
        self.percentage_patterns = [
            r'[+-]?\d+\.?\d*%?',  # Percentage with optional % sign
            r'[+-]?\d+\.?\d*',    # Just the number
        ]
    
    def extract_stock_data(self, row_element: Tag) -> Optional[StockData]:
        """Extract stock data from a table row element"""
        try:
            cells = row_element.find_all(['td', 'th'])
            if len(cells) < 3:
                return None
            
            # Extract text from all cells
            cell_texts = [self._clean_cell_text(cell.get_text()) for cell in cells]
            
            # Try to identify data structure
            data_map = self._identify_data_structure(cell_texts)
            
            if not data_map.get('symbol'):
                return None
            
            # Create StockData object
            stock_data = StockData(
                symbol=data_map['symbol'],
                company_name=data_map.get('company_name'),
                price=self._parse_price(data_map.get('price')),
                change_percent=self._parse_percentage(data_map.get('change_percent')),
                change_absolute=self._parse_price(data_map.get('change_absolute')),
                timestamp=datetime.now(),
                status='success' if data_map.get('price') else 'partial'
            )
            
            return stock_data
            
        except Exception as e:
            raise DataExtractionError(f"Failed to extract stock data: {e}")
    
    def _clean_cell_text(self, text: str) -> str:
        """Clean and normalize cell text"""
        if not text:
            return ""
        
        # Remove extra whitespace and special characters
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common HTML artifacts
        cleaned = re.sub(r'&nbsp;|&amp;|&lt;|&gt;', ' ', cleaned)
        
        # Remove non-printable characters
        cleaned = re.sub(r'[^\x20-\x7E]', '', cleaned)
        
        return cleaned.strip()
    
    def _identify_data_structure(self, cell_texts: List[str]) -> Dict[str, str]:
        """Identify which cell contains which type of data"""
        data_map = {}
        
        for i, text in enumerate(cell_texts):
            if not text or text == 'N/A':
                continue
            
            # Identify symbol (usually first column or matches pattern)
            if self._is_symbol(text) and 'symbol' not in data_map:
                data_map['symbol'] = text
            
            # Identify company name (usually longer text without numbers)
            elif self._is_company_name(text) and 'company_name' not in data_map:
                data_map['company_name'] = text
            
            # Identify price (number with optional currency symbols)
            elif self._is_price(text) and 'price' not in data_map:
                data_map['price'] = text
            
            # Identify percentage change
            elif self._is_percentage(text):
                if 'change_percent' not in data_map:
                    data_map['change_percent'] = text
                elif 'change_absolute' not in data_map:
                    # Sometimes absolute change is also in percentage format
                    data_map['change_absolute'] = text
            
            # Identify absolute change (number with +/- sign)
            elif self._is_absolute_change(text) and 'change_absolute' not in data_map:
                data_map['change_absolute'] = text
        
        return data_map
    
    def _is_symbol(self, text: str) -> bool:
        """Check if text looks like a stock symbol"""
        return any(re.match(pattern, text.upper()) for pattern in self.symbol_patterns)
    
    def _is_company_name(self, text: str) -> bool:
        """Check if text looks like a company name"""
        # Company names are usually longer and contain letters
        return (len(text) > 3 and 
                any(c.isalpha() for c in text) and 
                not self._is_symbol(text) and 
                not self._is_price(text) and 
                not self._is_percentage(text))
    
    def _is_price(self, text: str) -> bool:
        """Check if text looks like a price"""
        # Remove currency symbols and check if it's a number
        cleaned = re.sub(r'[$€£¥₹,\s]', '', text)
        try:
            float(cleaned)
            return True
        except ValueError:
            return False
    
    def _is_percentage(self, text: str) -> bool:
        """Check if text looks like a percentage"""
        return '%' in text or (
            any(re.match(pattern, text) for pattern in self.percentage_patterns) and
            (text.startswith(('+', '-')) or '.' in text)
        )
    
    def _is_absolute_change(self, text: str) -> bool:
        """Check if text looks like an absolute change value"""
        return (text.startswith(('+', '-')) and 
                self._is_price(text.lstrip('+-')))
    
    def clean_price_string(self, price_str: str) -> Optional[float]:
        """Clean price string and convert to float"""
        return self._parse_price(price_str)
    
    def _parse_price(self, price_str: Optional[str]) -> Optional[float]:
        """Parse price string handling different formats"""
        if not price_str:
            return None
        
        try:
            # Remove currency symbols, commas, and extra spaces
            cleaned = re.sub(r'[$€£¥₹,\s]', '', price_str)
            
            # Handle different decimal separators
            if ',' in cleaned and '.' in cleaned:
                # European format: 1.234,56 -> 1234.56
                if cleaned.rfind(',') > cleaned.rfind('.'):
                    cleaned = cleaned.replace('.', '').replace(',', '.')
            elif ',' in cleaned and cleaned.count(',') == 1:
                # Check if comma is decimal separator
                parts = cleaned.split(',')
                if len(parts) == 2 and len(parts[1]) <= 2:
                    cleaned = cleaned.replace(',', '.')
            
            # Remove any remaining non-numeric characters except decimal point and minus
            cleaned = re.sub(r'[^\d.-]', '', cleaned)
            
            if not cleaned:
                return None
            
            price = float(cleaned)
            
            # Validate reasonable price range
            if price < 0 or price > 1000000:
                return None
            
            return price
            
        except (ValueError, TypeError):
            return None
    
    def _parse_percentage(self, percent_str: Optional[str]) -> Optional[float]:
        """Parse percentage string with positive/negative detection"""
        if not percent_str:
            return None
        
        try:
            # Clean the string
            cleaned = percent_str.strip()
            
            # Detect sign
            is_negative = cleaned.startswith('-') or 'red' in cleaned.lower()
            is_positive = cleaned.startswith('+') or 'green' in cleaned.lower()
            
            # Remove non-numeric characters except decimal point
            numeric = re.sub(r'[^\d.-]', '', cleaned)
            
            if not numeric:
                return None
            
            percentage = float(numeric)
            
            # Apply sign if detected
            if is_negative and percentage > 0:
                percentage = -percentage
            elif is_positive and percentage < 0:
                percentage = abs(percentage)
            
            # Validate reasonable percentage range
            if abs(percentage) > 100:
                return None
            
            return percentage
            
        except (ValueError, TypeError):
            return None
    
    def validate_extracted_data(self, stock_data: StockData) -> bool:
        """Validate that extracted data is reasonable"""
        try:
            # Symbol validation
            if not stock_data.symbol or len(stock_data.symbol) > 10:
                return False
            
            # Price validation
            if stock_data.price is not None:
                if stock_data.price <= 0 or stock_data.price > 1000000:
                    return False
            
            # Percentage validation
            if stock_data.change_percent is not None:
                if abs(stock_data.change_percent) > 100:
                    return False
            
            # Absolute change validation
            if (stock_data.change_absolute is not None and 
                stock_data.price is not None):
                # Absolute change shouldn't be larger than the price itself
                if abs(stock_data.change_absolute) > stock_data.price:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def extract_multiple_stocks(self, row_elements: List[Tag]) -> List[StockData]:
        """Extract data from multiple table rows"""
        stocks = []
        
        for i, row in enumerate(row_elements):
            try:
                stock_data = self.extract_stock_data(row)
                if stock_data and self.validate_extracted_data(stock_data):
                    stocks.append(stock_data)
            except Exception as e:
                print(f"Warning: Failed to extract data from row {i + 1}: {e}")
                continue
        
        return stocks