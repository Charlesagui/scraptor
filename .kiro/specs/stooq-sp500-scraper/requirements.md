# Requirements Document

## Introduction

Este proyecto consiste en desarrollar un scraper web que extraiga datos financieros de las 500 empresas del S&P 500 desde el sitio web Stooq.com. El scraper debe recopilar información de precios actuales y cambios porcentuales, y exportar estos datos a un archivo CSV para análisis posterior. La solución debe ser robusta, eficiente y capaz de manejar la estructura específica de datos de Stooq.

## Requirements

### Requirement 1

**User Story:** Como analista financiero, quiero extraer datos de precios de todas las empresas del S&P 500 desde Stooq, para poder realizar análisis de mercado actualizados.

#### Acceptance Criteria

1. WHEN el scraper se ejecuta THEN el sistema SHALL acceder a la página de Stooq que contiene datos del S&P 500
2. WHEN se accede a los datos THEN el sistema SHALL extraer el precio actual de cada una de las 500 empresas
3. WHEN se extraen los precios THEN el sistema SHALL capturar también el símbolo/ticker de cada empresa
4. IF una empresa no tiene datos disponibles THEN el sistema SHALL registrar este caso y continuar con las demás

### Requirement 2

**User Story:** Como analista financiero, quiero obtener información sobre los cambios porcentuales de las acciones, para poder identificar tendencias y movimientos significativos del mercado.

#### Acceptance Criteria

1. WHEN el scraper extrae datos de precios THEN el sistema SHALL también capturar el cambio porcentual de cada acción
2. WHEN se captura el cambio porcentual THEN el sistema SHALL identificar si es positivo o negativo
3. WHEN los datos están disponibles THEN el sistema SHALL extraer el cambio absoluto en valor monetario
4. IF el cambio porcentual no está disponible THEN el sistema SHALL marcar el campo como "N/A"

### Requirement 3

**User Story:** Como usuario del sistema, quiero que los datos extraídos se guarden en formato CSV, para poder importarlos fácilmente en herramientas de análisis como Excel o Python.

#### Acceptance Criteria

1. WHEN el scraping se completa THEN el sistema SHALL generar un archivo CSV con todos los datos extraídos
2. WHEN se crea el archivo CSV THEN el sistema SHALL incluir headers descriptivos (símbolo, precio, cambio_porcentual, cambio_absoluto, timestamp)
3. WHEN se guarda el archivo THEN el sistema SHALL usar un nombre que incluya la fecha y hora de extracción
4. WHEN se escriben los datos THEN el sistema SHALL usar formato estándar CSV con comas como separadores

### Requirement 4

**User Story:** Como desarrollador, quiero que el scraper sea robusto y maneje errores apropiadamente, para asegurar que funcione de manera confiable en diferentes condiciones.

#### Acceptance Criteria

1. WHEN ocurre un error de conexión THEN el sistema SHALL reintentar la conexión hasta 3 veces antes de fallar
2. WHEN se encuentra un elemento faltante en la página THEN el sistema SHALL registrar el error y continuar con el siguiente elemento
3. WHEN el scraper se ejecuta THEN el sistema SHALL implementar delays apropiados para evitar ser bloqueado por rate limiting
4. WHEN se completa la ejecución THEN el sistema SHALL generar un log con estadísticas de éxito y errores encontrados

### Requirement 5

**User Story:** Como usuario técnico, quiero poder configurar parámetros del scraper, para adaptarlo a diferentes necesidades y condiciones de uso.

#### Acceptance Criteria

1. WHEN se ejecuta el scraper THEN el sistema SHALL permitir configurar el delay entre requests
2. WHEN se configura la salida THEN el sistema SHALL permitir especificar el directorio de destino para el archivo CSV
3. WHEN se ejecuta THEN el sistema SHALL permitir configurar el número máximo de reintentos
4. IF se proporciona configuración inválida THEN el sistema SHALL mostrar mensajes de error claros y usar valores por defecto