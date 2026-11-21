# Inventario de Tecnología · versión Streamlit

El mismo caso de negocio que el dashboard de Power BI, hecho en Python con Streamlit + Plotly.

## Qué demuestra
- **pandas**: carga, limpieza (tildes), joins tipo modelo en estrella y columnas calculadas (edad, depreciación, SLA).
- **Plotly**: barras, mapas de calor, combo con doble eje y medidor.
- **Streamlit**: filtros en la barra lateral, pestañas, KPIs con `st.metric`, tablas con barras de progreso y caché de datos.
- **Títulos dinámicos**: los títulos de los gráficos cambian con los filtros («Lima es la sede más lenta…»).

## Ejecutar en local
```bash
cd streamlit_app
python -m venv .venv
.venv\Scripts\activate          # en Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
> En Windows, si `import pandas` falla con «El nombre del archivo o la extensión es demasiado largo», la ruta de la carpeta supera los 260 caracteres: crea el entorno en una ruta corta (por ejemplo `python -m venv C:\venvs\itam`) o mueve el proyecto a algo como `C:\proyectos\itam`.

La app busca los CSV en `streamlit_app/datos` o en `datos` junto a la carpeta `streamlit_app`.

## Publicar gratis (Streamlit Community Cloud)
1. Sube el repositorio a GitHub (con la carpeta `datos`).
2. Entra en share.streamlit.io con tu cuenta de GitHub → **Create app**.
3. Repositorio, rama y archivo principal `streamlit_app/app.py` → **Deploy**.
4. Pega el enlace público en tu README y en LinkedIn.
