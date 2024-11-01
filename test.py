import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import HeatMap, MarkerCluster
from streamlit_folium import st_folium

# Configuración de página
st.set_page_config(
    page_title="Dashboard Apagones PR",
    page_icon="⚡",
    layout="wide"
)

# Función para cargar datos


@st.cache_data
def load_data():
    df = pd.read_csv('caguas_outages.csv')
    df['outage_time_utc'] = pd.to_datetime(df['outage_time_utc'])
    # Limpiar datos de coordenadas
    df = df.dropna(subset=['lat', 'lon'])
    # Filtrar valores fuera de rango para Puerto Rico
    df = df[
        (df['lat'].between(17.5, 18.5)) &
        (df['lon'].between(-67.5, -65.5))
    ]
    return df


# Cargar datos
df = load_data()


def create_interactive_map(df_filtered):
    """Crear mapa interactivo con múltiples capas"""

    # Crear mapa base centrado en Puerto Rico
    m = folium.Map(location=[18.2208, -66.5901],
                   zoom_start=9,
                   tiles='cartodbdark_matter')  # Mapa oscuro para mejor contraste

    # Añadir controles de capas
    layer_control = folium.LayerControl()

    # Crear grupos de capas
    heatmap_layer = folium.FeatureGroup(name='Mapa de Calor')
    markers_layer = folium.FeatureGroup(name='Marcadores de Sectores')
    cluster_layer = folium.FeatureGroup(name='Clusters de Incidentes')

    # Añadir mapa de calor
    heat_data = df_filtered[['lat', 'lon']].values.tolist()
    HeatMap(heat_data,
            radius=15,
            gradient={'0.4': 'blue', '0.65': 'lime', '1': 'red'}).add_to(heatmap_layer)

    # Crear clusters de marcadores
    marker_cluster = MarkerCluster()

    # Agrupar datos por localización
    location_groups = df_filtered.groupby(
        ['orig_outage_location_name', 'lat', 'lon'])

    for (location_name, lat, lon), group in location_groups:
        if pd.notna(lat) and pd.notna(lon):
            # Crear popup con información detallada
            popup_html = f"""
                <div style='width:200px'>
                    <h4>{location_name}</h4>
                    <b>Total Apagones:</b> {len(group)}<br>
                    <b>Primer Apagón:</b> {group['outage_time_utc'].min().strftime('%Y-%m-%d')}<br>
                    <b>Último Apagón:</b> {group['outage_time_utc'].max().strftime('%Y-%m-%d')}<br>
                    <b>Municipio:</b> {group['orig_outage_location_muni'].iloc[0]}
                </div>
            """

            # Añadir marcador al cluster
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=location_name,
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(marker_cluster)

    # Añadir todas las capas al mapa
    marker_cluster.add_to(cluster_layer)
    heatmap_layer.add_to(m)
    cluster_layer.add_to(m)
    markers_layer.add_to(m)
    layer_control.add_to(m)

    # Añadir mini mapa para contexto
    minimap = folium.plugins.MiniMap(toggle_display=True)
    m.add_child(minimap)

    # Añadir herramienta de medición
    folium.plugins.MeasureControl(position='bottomleft').add_to(m)

    # Añadir búsqueda
    folium.plugins.Geocoder(position='topright').add_to(m)

    return m


def map_tab(df):
    st.header("Mapa Interactivo de Apagones")

    # Filtros en columnas
    col2, col3 = st.columns(2)

    with col2:
        # Filtro de fecha
        dates = pd.to_datetime(df['outage_time_utc']).dt.date.unique()
        start_date = st.date_input('Fecha Inicial', min(dates))

    with col3:
        end_date = st.date_input('Fecha Final', max(dates))

    # Aplicar filtros
    mask = pd.to_datetime(df['outage_time_utc']).dt.date.between(
        start_date, end_date)
    df_filtered = df[mask]

    if selected_municipio != 'Todos':
        df_filtered = df_filtered[df_filtered['orig_outage_location_muni']
                                  == selected_municipio]

    # Crear y mostrar mapa
    m = create_interactive_map(df_filtered)
    st_folium(m, width=1400, height=600)

    # Mostrar estadísticas del área seleccionada
    st.subheader("Estadísticas del Área Seleccionada")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total de Apagones", len(df_filtered))
    with col2:
        st.metric("Localizaciones Afectadas",
                  df_filtered['orig_outage_location_name'].nunique())
    with col3:
        st.metric("Promedio Diario", f"{len(df_filtered) / len(dates):.1f}")
    with col4:
        st.metric("Municipios Afectados",
                  df_filtered['orig_outage_location_muni'].nunique())


# Sidebar - Filtros Principales
with st.sidebar:
    st.header('Filtros')

    # Filtro de municipio
    municipios = ['Todos'] + \
        sorted(df['orig_outage_location_muni'].unique().tolist())
    selected_municipio = st.selectbox('Municipio', municipios)

    # Aplicar filtros
    if selected_municipio != 'Todos':
        df_filtered = df[df['orig_outage_location_muni'] == selected_municipio]
    else:
        df_filtered = df

    # Mostrar métricas en sidebar
    st.divider()
    st.metric("Total Apagones", len(df_filtered))
    st.metric("Sectores",
              df_filtered['orig_outage_location_name'].nunique())

# Contenido Principal
tab1, tab2, tab3 = st.tabs(
    ["🗺️ Mapa", "📊 Análisis por Localización", "📈 Tendencias"])

# Tab 1: Mapa
with tab1:
    # Container para el mapa
    with st.container():
        map_tab(df)
# Tab 2: Análisis por Localización
with tab2:
    # Dos columnas para gráficos
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("Top 10 Lugares más Afectados")
        # Obtener top 10 y crear dataframe con más detalles
        top_10 = (df_filtered['orig_outage_location_name']
                  .value_counts()
                  .head(10)
                  .reset_index())
        top_10.columns = ['Localización', 'Total Apagones']

        # Añadir más información al top 10
        top_10['Primer Apagón'] = [
            df_filtered[df_filtered['orig_outage_location_name']
                        == loc]['outage_time_utc'].min().strftime('%Y-%m-%d')
            for loc in top_10['Localización']
        ]
        top_10['Último Apagón'] = [
            df_filtered[df_filtered['orig_outage_location_name']
                        == loc]['outage_time_utc'].max().strftime('%Y-%m-%d')
            for loc in top_10['Localización']
        ]

        # Mostrar tabla expandida
        st.dataframe(
            top_10,
            column_config={
                "Localización": st.column_config.Column(width="medium"),
                "Total Apagones": st.column_config.NumberColumn(width="small"),
                "Primer Apagón": st.column_config.DateColumn(width="small"),
                "Último Apagón": st.column_config.DateColumn(width="small")
            },
            hide_index=True,
            height=400
        )

    with col2:
        st.subheader("Buscar Localización")
        search_term = st.text_input(
            "Buscar:", placeholder="Ejemplo: montecasino")

        if search_term:
            # Búsqueda case-insensitive
            mask = df_filtered['orig_outage_location_name'].str.contains(
                search_term, case=False, na=False)
            search_results = df_filtered[mask]

            if not search_results.empty:
                # Agrupar y agregar información relevante
                location_summary = (search_results
                                    .groupby('orig_outage_location_name')
                                    .agg({
                                        'outage_time_utc': ['count', 'min', 'max'],
                                        'orig_outage_location_muni': 'first'
                                    })
                                    .reset_index())

                # Limpiar nombres de columnas
                location_summary.columns = [
                    'Localización',
                    'Total Apagones',
                    'Primer Apagón',
                    'Último Apagón',
                    'Municipio'
                ]

                # Formatear fechas
                location_summary['Primer Apagón'] = location_summary['Primer Apagón'].dt.strftime(
                    '%Y-%m-%d')
                location_summary['Último Apagón'] = location_summary['Último Apagón'].dt.strftime(
                    '%Y-%m-%d')

                # Mostrar resultados
                st.dataframe(
                    location_summary,
                    column_config={
                        "Localización": st.column_config.Column(width="medium"),
                        "Total Apagones": st.column_config.NumberColumn(width="small"),
                        "Primer Apagón": st.column_config.DateColumn(width="small"),
                        "Último Apagón": st.column_config.DateColumn(width="small"),
                        "Municipio": st.column_config.Column(width="small")
                    },
                    hide_index=True,
                    height=400
                )

                # Mostrar detalles adicionales al seleccionar una localización
                if len(location_summary) > 0:
                    st.divider()
                    st.subheader("Detalles de Apagones")
                    selected_location = st.selectbox(
                        "Seleccionar localización para ver detalles:",
                        location_summary['Localización'].tolist()
                    )

                    if selected_location:
                        location_details = df_filtered[
                            df_filtered['orig_outage_location_name'] == selected_location
                        ].sort_values('outage_time_utc', ascending=False)

                        st.dataframe(
                            location_details[[
                                'outage_time_utc', 'orig_outage_location_name', 'orig_outage_location_muni']],
                            column_config={
                                "outage_time_utc": st.column_config.DatetimeColumn(
                                    "Fecha y Hora",
                                    format="DD/MM/YYYY HH:mm",
                                    width="medium"
                                ),
                                "orig_outage_location_name": st.column_config.Column(
                                    "Localización",
                                    width="medium"
                                ),
                                "orig_outage_location_muni": st.column_config.Column(
                                    "Municipio",
                                    width="small"
                                )
                            },
                            hide_index=True
                        )
            else:
                st.warning("No se encontraron resultados para la búsqueda.")

# Tab 3: Tendencias
with tab3:
    st.header("Análisis Temporal")

    # Selector de localización
    locations = [
        'Todas'] + list(df_filtered['orig_outage_location_name'].unique())
    locations.sort()
    selected_loc = st.selectbox('Seleccionar Localización:', locations)

    # Gráfico de tendencia
    if selected_loc != 'Todas':
        data = df_filtered[df_filtered['orig_outage_location_name']
                           == selected_loc]
    else:
        data = df_filtered

    daily_counts = data.groupby(
        data['outage_time_utc'].dt.date).size().reset_index(name='count')
    fig = px.line(daily_counts, x='outage_time_utc', y='count',
                  title=f"Tendencia de Apagones - {selected_loc}")
    st.plotly_chart(fig, use_container_width=True)

# Footer con información adicional
with st.expander("ℹ️ Acerca de los datos"):
    st.write("""
    - Datos desde septiembre 2021
    - Fuente: LUMA Energy
    """)
