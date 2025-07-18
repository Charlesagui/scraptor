from abc import ABC, abstractmethod
from typing import List
from ..models.stock_data import StockData


class BaseExporter(ABC):
    """Base interface for all data exporters"""
    
    @abstractmethod
    def export(self, data: List[StockData], path: str) -> None:
        """Export stock data to specified path"""
        pass