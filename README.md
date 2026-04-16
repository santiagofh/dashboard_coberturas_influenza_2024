# Dashboard Campana Influenza 2024

Aplicacion en Streamlit para visualizar la cobertura de vacunacion contra influenza 2024 en la Region Metropolitana.

## Contenido

- Pagina principal con cobertura por grupo objetivo.
- Una pagina por campana con:
  - listado comunal de cobertura;
  - grafico de poblacion objetivo total vs vacunas administradas;
  - resumen textual;
  - descarga a Excel con hojas de indicadores, datos y totales.

## Estructura minima para ejecutar

- `streamlit_dashboard.py`: punto de entrada de la app.
- `dashboard_influenza_pages.py`: logica de carga, visualizacion y exportacion.
- `output/cobertura_influenza_2024_rm.csv`: datos usados por el dashboard.
- `assets/`: logo e icono para la barra lateral.

## Instalacion local

```bash
pip install -r requirements.txt
streamlit run streamlit_dashboard.py
```

## Despliegue en Streamlit Community Cloud

1. Sube este proyecto a un repositorio publico en GitHub.
2. En Streamlit Community Cloud, crea una nueva app desde ese repositorio.
3. Usa `streamlit_dashboard.py` como archivo principal.

## Nota sobre archivos pesados

El repositorio excluye archivos de trabajo grandes y auxiliares que no son necesarios para ejecutar la app publicada.
