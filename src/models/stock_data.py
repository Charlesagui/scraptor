from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class StockData:
    """Data model for stock information"""
    symbol: str
    company_name: Optional[str]
    price: Optional[float]
    change_percent: Optional[float]
    change_absolute: Optional[float]
    timestamp: datetime
    status: str = "success"
    
    def __post_init__(self):
        """Validate data after initialization"""
        self.validate()
    
    def validate(self) -> bool:
        """Validate stock data using built-in Python functions"""
        if not self.symbol or not isinstance(self.symbol, str):
            raise ValueError("Symbol must be a non-empty string")
        
        if self.price is not None and (not isinstance(self.price, (int, float)) or self.price < 0):
            raise ValueError("Price must be a positive number")
        
        if self.change_percent is not None and not isinstance(self.change_percent, (int, float)):
            raise ValueError("Change percent must be a number")
        
        if self.change_absolute is not None and not isinstance(self.change_absolute, (int, float)):
            raise ValueError("Change absolute must be a number")
        
        if not isinstance(self.timestamp, datetime):
            raise ValueError("Timestamp must be a datetime object")
        
        if self.status not in ["success", "partial", "failed"]:
            raise ValueError("Status must be 'success', 'partial', or 'failed'")
        
        return True
    
    def is_valid_data(self) -> bool:
        """Check if stock has valid price data"""
        return self.price is not None and self.price > 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for export"""
        return {
            'symbol': self.symbol,
            'company_name': self.company_name or 'N/A',
            'price': self.price if self.price is not None else 'N/A',
            'change_percent': self.change_percent if self.change_percent is not None else 'N/A',
            'change_absolute': self.change_absolute if self.change_absolute is not None else 'N/A',
            'timestamp': self.timestamp.isoformat(),
            'status': self.status
        }