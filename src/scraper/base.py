from abc import ABC, abstractmethod
from typing import List
from ..models.stock_data import StockData


class BaseScraper(ABC):
    """Base interface for all scrapers"""
    
    @abstractmethod
    def fetch_data(self) -> List[StockData]:
        """Fetch stock data from the source"""
        pass