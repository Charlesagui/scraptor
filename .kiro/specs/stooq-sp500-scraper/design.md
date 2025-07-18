# Design Document

## Overview

El scraper de Stooq S&P 500 será una aplicación Python que utiliza web scraping para extraer datos financieros en tiempo real. La arquitectura seguirá un patrón modular con separación clara de responsabilidades: extracción de datos, procesamiento, y exportación. El sistema utilizará bibliotecas como requests/httpx para HTTP, BeautifulSoup o Selenium para parsing HTML, y pandas para manipulación de datos y exportación CSV.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Config        │    │   Web Scraper    │    │   Data Export   │
│   Manager       │───▶│   Engine         │───▶│   Module        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Error Handler  │
                       │   & Logger       │
                       └──────────────────┘
```

### Technology Stack (Minimalista)

- **Python 3.8+**: Lenguaje principal
- **requests**: Cliente HTTP ligero para scraping
- **BeautifulSoup4**: Parsing HTML dinámico
- **csv** (built-in): Exportación CSV sin dependencias pesadas
- **selenium**: Para contenido JavaScript dinámico
- **json** (built-in): Configuración simple
- **logging** (built-in): Logs básicos

**Principio**: Solo dependencias esenciales, máxima efectividad con código mínimo

## Components and Interfaces

### File Structure (Compartimentado)
```
src/
├── main.py                 # Entry point (< 50 líneas)
├── config/
│   ├── __init__.py
│   ├── manager.py         # ConfigManager
│   └── settings.py        # Default settings
├── scraper/
│   ├── __init__.py
│   ├── base.py           # BaseScraper interface
│   ├── stooq_scraper.py  # StooqScraper implementation
│   └── http_client.py    # HTTP utilities
├── models/
│   ├── __init__.py
│   ├── stock_data.py     # StockData model
│   └── config_models.py  # Configuration models
├── parsers/
│   ├── __init__.py
│   ├── html_parser.py    # HTML parsing utilities
│   └── data_extractor.py # Data extraction logic
├── exporters/
│   ├── __init__.py
│   ├── base_exporter.py  # BaseExporter interface
│   └── csv_exporter.py   # CSV implementation
├── utils/
│   ├── __init__.py
│   ├── logger.py         # Logging utilities
│   ├── errors.py         # Custom exceptions
│   └── validators.py     # Data validation
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
```

### 1. Configuration Module (config/)

**config/manager.py**
```python
class ConfigManager:
    def load_config(self, config_path: str) -> dict
    def validate_config(self, config: dict) -> bool
```

**config/settings.py**
```python
DEFAULT_SETTINGS = {
    'scraping': {...},
    'export': {...}
}
```

### 2. Scraper Module (scraper/)

**scraper/base.py**
```python
class BaseScraper(ABC):
    @abstractmethod
    def fetch_data(self) -> List[StockData]
```

**scraper/stooq_scraper.py**
```python
class StooqScraper(BaseScraper):
    def fetch_data(self) -> List[StockData]
    def _get_sp500_page(self) -> str
```

**scraper/http_client.py**
```python
class HTTPClient:
    def get_with_retry(self, url: str) -> requests.Response
    def handle_rate_limit(self, response: requests.Response)
```

### 3. Models Module (models/)

**models/stock_data.py**
```python
@dataclass
class StockData:
    symbol: str
    price: float
    change_percent: float
    change_absolute: float
    timestamp: datetime
```

**models/config_models.py**
```python
@dataclass
class ScrapingParams:
    base_url: str
    delay_between_requests: float
    max_retries: int
```

### 4. Parsers Module (parsers/)

**parsers/html_parser.py**
```python
class HTMLParser:
    def parse_stock_table(self, html: str) -> List[BeautifulSoup]
    def extract_pagination_links(self, html: str) -> List[str]
```

**parsers/data_extractor.py**
```python
class DataExtractor:
    def extract_stock_data(self, element: BeautifulSoup) -> StockData
    def clean_price_string(self, price_str: str) -> float
```

### 5. Exporters Module (exporters/)

**exporters/base_exporter.py**
```python
class BaseExporter(ABC):
    @abstractmethod
    def export(self, data: List[StockData], path: str)
```

**exporters/csv_exporter.py**
```python
class CSVExporter(BaseExporter):
    def export(self, data: List[StockData], path: str)
    def _generate_filename(self) -> str
```

### 6. Utils Module (utils/)

**utils/logger.py**
```python
class ScraperLogger:
    def setup_logging(self, config: dict)
    def log_scraping_stats(self, stats: dict)
```

**utils/errors.py**
```python
class ScrapingError(Exception): pass
class DataExtractionError(ScrapingError): pass
class ExportError(Exception): pass
```

**utils/validators.py**
```python
class DataValidator:
    def validate_stock_data(self, data: StockData) -> bool
    def validate_csv_output(self, filepath: str) -> bool
```

## Data Models

### Stock Data Structure
```python
StockData = {
    'symbol': str,           # Ej: 'AAPL'
    'company_name': str,     # Ej: 'Apple Inc.'
    'price': float,          # Precio actual
    'change_percent': float, # Cambio porcentual
    'change_absolute': float,# Cambio absoluto
    'timestamp': datetime,   # Momento de extracción
    'status': str           # 'success', 'partial', 'failed'
}
```

### Configuration Structure
```ini
[scraping]
base_url = https://stooq.com/q/i/?s=^spx
delay_between_requests = 1.0
max_retries = 3
timeout = 30
user_agent = Mozilla/5.0 (compatible; StooqScraper/1.0)

[export]
output_directory = ./data
filename_prefix = sp500_data
include_timestamp = true

[logging]
log_level = INFO
log_file = scraper.log
```

## Error Handling

### Network Errors
- **Connection timeout**: Reintentar hasta max_retries
- **HTTP 429 (Rate Limited)**: Incrementar delay exponencialmente
- **HTTP 403/404**: Registrar error y continuar con siguiente elemento
- **SSL errors**: Configurar verificación SSL apropiada

### Data Parsing Errors
- **Missing elements**: Marcar campo como 'N/A' y continuar
- **Invalid data format**: Intentar conversión con fallback a None
- **Empty responses**: Registrar y reintentar

### Export Errors
- **File permission errors**: Crear directorio alternativo
- **Disk space**: Verificar espacio disponible antes de escribir
- **Data validation**: Verificar integridad antes de exportar

## Testing Strategy

### Unit Tests
- **ConfigManager**: Validación de configuración y valores por defecto
- **StockData models**: Serialización y validación de datos
- **CSVExporter**: Formato de salida y manejo de caracteres especiales
- **ErrorHandler**: Comportamiento de reintentos y logging

### Integration Tests
- **Web scraping flow**: Test con datos mock de HTML
- **End-to-end pipeline**: Desde configuración hasta CSV final
- **Error scenarios**: Simulación de fallos de red y datos faltantes

### Performance Tests
- **Rate limiting**: Verificar que se respetan los delays
- **Memory usage**: Monitorear uso de memoria con 500+ elementos
- **Execution time**: Benchmark de tiempo total de ejecución

### Manual Testing
- **Live website testing**: Verificar contra Stooq.com real
- **CSV output validation**: Verificar formato en Excel/LibreOffice
- **Configuration scenarios**: Probar diferentes configuraciones

## Implementation Notes

### Dynamic Scraping Strategy (NO APIs)
- **Pure Web Scraping**: Solo extracción directa de HTML/JavaScript, nunca APIs
- **Dynamic Content Handling**: Selenium para contenido cargado por JavaScript
- **Adaptive Selectors**: Sistema que se adapta a cambios en la estructura HTML
- **Real-time Detection**: Detectar cambios en la página y ajustar selectores automáticamente
- **Multi-page Navigation**: Manejo dinámico de paginación y navegación

### Minimalist Code Principles
- **Single Responsibility**: Cada función hace una sola cosa
- **No Over-engineering**: Código directo sin abstracciones innecesarias
- **Built-in Libraries**: Preferir bibliotecas estándar de Python
- **Essential Dependencies**: Solo requests, BeautifulSoup, selenium
- **Compact Functions**: Máximo 20 líneas por función

### Stooq.com Dynamic Scraping
- **JavaScript Detection**: Identificar si los datos se cargan dinámicamente
- **Element Waiting**: Esperar a que elementos aparezcan antes de extraer
- **Selector Fallbacks**: Múltiples selectores CSS como backup
- **Data Format Adaptation**: Detectar y adaptarse a diferentes formatos numéricos
- **Page Structure Analysis**: Analizar estructura HTML en tiempo real

### Adaptive Scraping Features
- **Auto-discovery**: Encontrar automáticamente tablas de datos
- **Selector Learning**: Aprender nuevos selectores cuando los antiguos fallan
- **Content Validation**: Verificar que los datos extraídos son válidos
- **Fallback Strategies**: Múltiples estrategias de extracción por elemento

### Performance & Efficiency
- **Minimal Memory**: Procesar datos en streaming, no cargar todo en memoria
- **Smart Delays**: Delays adaptativos basados en respuesta del servidor
- **Connection Reuse**: Reutilizar conexiones HTTP
- **Selective Scraping**: Solo extraer datos que han cambiado