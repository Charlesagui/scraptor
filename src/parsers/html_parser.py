from bs4 import BeautifulSoup, Tag
from typing import List, Optional, Dict, Any
import re
from ..utils.errors import ParsingError


class HTMLParser:
    """HTML parser with adaptive selectors and fallback mechanisms"""
    
    def __init__(self):
        self.soup = None
        # Multiple selector strategies for different page structures
        self.table_selectors = [
            'table.tab01',  # Common Stooq table class
            'table[id*="tab"]',  # Tables with 'tab' in ID
            'table.data-table',  # Generic data table
            'table[class*="stock"]',  # Tables with 'stock' in class
            'div.table-responsive table',  # Bootstrap responsive tables
            'table',  # Fallback to any table
        ]
        
        self.row_selectors = [
            'tr[class*="row"]',  # Rows with 'row' in class
            'tr:not(:first-child)',  # All rows except header
            'tbody tr',  # Rows in tbody
            'tr',  # Fallback to any row
        ]
        
        self.pagination_selectors = [
            'a[href*="page"]',  # Links with 'page' in href
            'a[class*="page"]',  # Links with 'page' in class
            '.pagination a',  # Bootstrap pagination
            'div.pager a',  # Generic pager
            'a[href*="next"]',  # Next page links
        ]
    
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """Parse HTML content with BeautifulSoup"""
        try:
            self.soup = BeautifulSoup(html_content, 'html.parser')
            return self.soup
        except Exception as e:
            raise ParsingError(f"Failed to parse HTML content: {e}")
    
    def detect_dynamic_content(self, html_content: str) -> bool:
        """Detect if page contains JavaScript-loaded content"""
        dynamic_indicators = [
            'data-react',
            'ng-app',
            'vue-app',
            'loading...',
            'spinner',
            'skeleton',
            'placeholder',
            'data-src',  # Lazy loading
            'onload=',
            'document.ready',
            'ajax',
            'fetch(',
        ]
        
        html_lower = html_content.lower()
        return any(indicator in html_lower for indicator in dynamic_indicators)
    
    def parse_stock_table(self, html_content: str) -> List[Tag]:
        """Parse stock table with adaptive selectors"""
        soup = self.parse_html(html_content)
        
        # Try different table selectors
        table = None
        for selector in self.table_selectors:
            try:
                tables = soup.select(selector)
                if tables:
                    # Find the table with most rows (likely the data table)
                    table = max(tables, key=lambda t: len(t.find_all('tr')))
                    break
            except Exception:
                continue
        
        if not table:
            raise ParsingError("Could not find stock data table with any selector")
        
        # Extract rows using adaptive selectors
        rows = []
        for selector in self.row_selectors:
            try:
                found_rows = table.select(selector)
                if found_rows and len(found_rows) > 1:  # Need more than just header
                    rows = found_rows
                    break
            except Exception:
                continue
        
        if not rows:
            raise ParsingError("Could not find table rows with any selector")
        
        # Filter out header rows and empty rows
        data_rows = []
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 3:  # Minimum columns for stock data
                # Skip if it looks like a header
                text_content = ' '.join(cell.get_text().strip() for cell in cells)
                if not self._is_header_row(text_content):
                    data_rows.append(row)
        
        return data_rows
    
    def _is_header_row(self, text_content: str) -> bool:
        """Check if row appears to be a header"""
        header_indicators = [
            'symbol', 'ticker', 'name', 'company',
            'price', 'last', 'close',
            'change', 'chg', '%', 'percent',
            'volume', 'vol'
        ]
        
        text_lower = text_content.lower()
        # If contains multiple header indicators, likely a header
        matches = sum(1 for indicator in header_indicators if indicator in text_lower)
        return matches >= 2
    
    def extract_pagination_links(self, html_content: str) -> List[str]:
        """Extract pagination links with fallback strategies"""
        soup = self.parse_html(html_content)
        links = []
        
        for selector in self.pagination_selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    if href and self._is_valid_pagination_link(href):
                        links.append(href)
            except Exception:
                continue
        
        # Remove duplicates while preserving order
        unique_links = []
        for link in links:
            if link not in unique_links:
                unique_links.append(link)
        
        return unique_links
    
    def _is_valid_pagination_link(self, href: str) -> bool:
        """Check if link is a valid pagination link"""
        if not href:
            return False
        
        # Skip javascript links, anchors, and external links
        if href.startswith(('javascript:', '#', 'http://')) and not href.startswith('https://stooq.com'):
            return False
        
        # Look for pagination indicators
        pagination_patterns = [
            r'page=\d+',
            r'p=\d+',
            r'offset=\d+',
            r'start=\d+',
            r'next',
            r'more'
        ]
        
        return any(re.search(pattern, href.lower()) for pattern in pagination_patterns)
    
    def wait_for_element(self, selector: str, timeout: int = 10) -> bool:
        """Check if element exists (for dynamic content detection)"""
        if not self.soup:
            return False
        
        try:
            elements = self.soup.select(selector)
            return len(elements) > 0
        except Exception:
            return False
    
    def extract_text_safely(self, element: Tag, default: str = "N/A") -> str:
        """Safely extract text from element"""
        if not element:
            return default
        
        try:
            text = element.get_text(strip=True)
            return text if text else default
        except Exception:
            return default
    
    def find_element_by_multiple_selectors(self, selectors: List[str]) -> Optional[Tag]:
        """Find element using multiple selector strategies"""
        if not self.soup:
            return None
        
        for selector in selectors:
            try:
                element = self.soup.select_one(selector)
                if element:
                    return element
            except Exception:
                continue
        
        return None
    
    def get_table_structure_info(self) -> Dict[str, Any]:
        """Analyze table structure for debugging"""
        if not self.soup:
            return {}
        
        info = {
            'total_tables': len(self.soup.find_all('table')),
            'tables_with_classes': [],
            'tables_with_ids': [],
            'max_rows_in_table': 0
        }
        
        for table in self.soup.find_all('table'):
            if table.get('class'):
                info['tables_with_classes'].append(' '.join(table.get('class')))
            if table.get('id'):
                info['tables_with_ids'].append(table.get('id'))
            
            row_count = len(table.find_all('tr'))
            info['max_rows_in_table'] = max(info['max_rows_in_table'], row_count)
        
        return info