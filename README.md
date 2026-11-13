# SIMTELE-RISK

Proyecto final de Métodos Numéricos. Simulación educativa inspirada en un sistema
de transporte por cable (La Paz). Los datos son sintéticos y no hay conexión con
equipos de control reales.

## Integrantes
- Belen ...
- ... (compañera)
Mención: Ingeniería de Sistemas

## Módulos
1. Detención de emergencia
2. Deterioro mecánico y mantenimiento (sistemas lineales activos)
3. Oscilaciones por viento
4. Reconstrucción de sensores

## Métodos implementados (Semana 1)
Errores (absoluto, relativo, porcentual, residual, sensibilidad), Jacobi,
Gauss-Seidel, LU (Doolittle), Gradiente Conjugado y solución directa de referencia.

## Escenarios
NORMAL, ESTRÉS y MAL CONDICIONADO (matriz de Hilbert).

## Ejecución
pip install -r requirements.txt
streamlit run app.py

## Estructura
- app.py: interfaz Streamlit
- metodos_lineales.py: algoritmos y teoría de errores
- docs/: DER y script SQL (próximamente)
