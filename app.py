import streamlit as st
import pandas as pd
from weather_logic import WeatherLogic, load_config
import os
import io
import datetime
import math
from dotenv import load_dotenv
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

load_dotenv()

st.set_page_config(page_title="Weather Reporter", layout="wide")

st.title("Weather Reporter")

@st.cache_resource
def get_weather_logic():
    api_key = os.environ.get("OPENWEATHERMAP_API_KEY")
    config = load_config()
    if not api_key:
        api_key = config.get("api_keys", {}).get("openweathermap", "")
    return WeatherLogic(api_key), config

logic, config_data = get_weather_logic()

# Top Section
st.header("Search Location")

# Read locations from config
locations_dict = config_data.get("locations", {})
loc_names = list(locations_dict.keys())

default_loc = "Rong Doi Platform - Block 11.2"
default_idx = loc_names.index(default_loc) if default_loc in loc_names else 0

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    location = st.selectbox("Select Location:", loc_names, index=default_idx)
with col2:
    data_source = st.radio("Data Source:", ["Open-Meteo", "OpenWeatherMap"], horizontal=True)
with col3:
    fetch_btn = st.button("Fetch Data")

if "weather_data" not in st.session_state:
    st.session_state.weather_data = None
    st.session_state.location_info = None
    st.session_state.marine_data = None
    st.session_state.lat = None
    st.session_state.lon = None
    st.session_state.api_source = None
    st.session_state.ui_location_name = None

# Auto-fetch on first load if not in session state, or when fetch_btn is clicked
if fetch_btn or not st.session_state.weather_data:
    with st.spinner("Fetching data..."):
        # get coordinates from our loaded config dictionary
        if location in locations_dict:
            lat, lon = locations_dict[location]['coords']
        else:
            lat, lon = None, None
            
        w_data, l_info, m_data = None, None, None
        if data_source == "OpenWeatherMap":
            if lat is not None and lon is not None:
                w_data, l_info = logic._fetch_weather_data_owm(lat, lon)
                m_data = None
        else:
            if lat is not None and lon is not None:
                w_data, l_info = logic._fetch_weather_data_openmeteo(lat, lon)
                m_data = logic._fetch_marine_data_openmeteo(lat, lon, l_info['timezone'])
        
        if lat and lon and w_data:
            st.session_state.weather_data = w_data
            st.session_state.location_info = l_info
            st.session_state.marine_data = m_data
            st.session_state.lat = lat
            st.session_state.lon = lon
            st.session_state.api_source = data_source
            st.session_state.ui_location_name = location
            st.success("Data fetched successfully!")
        else:
            st.error("Failed to fetch data or location not found.")

if st.session_state.weather_data:
    w_data = st.session_state.weather_data
    l_info = st.session_state.location_info
    
    # Middle Section
    st.header("Current Weather Summary")
    
    # Calculate summary
    temp_vals = [item.get('temperature') for item in w_data if isinstance(item.get('temperature'), (int, float))]
    wind_vals = [item.get('wind_speed') for item in w_data if isinstance(item.get('wind_speed'), (int, float))]
    
    temp_min = f"{min(temp_vals):.1f}°C" if temp_vals else "N/A"
    temp_max = f"{max(temp_vals):.1f}°C" if temp_vals else "N/A"
    wind_min = f"{min(wind_vals):.1f} knots" if wind_vals else "N/A"
    wind_max = f"{max(wind_vals):.1f} knots" if wind_vals else "N/A"
    
    colA, colB, colC, colD = st.columns(4)
    colA.metric("Temperature", f"{temp_min} - {temp_max}")
    colB.metric("Wind Speed", f"{wind_min} - {wind_max}")
    if st.session_state.api_source == "Open-Meteo":
        rain_vals = [item.get('rain') for item in w_data if isinstance(item.get('rain'), (int, float))]
        uv_vals = [item.get('uv_index') for item in w_data if isinstance(item.get('uv_index'), (int, float))]
        rain_max = f"{max(rain_vals):.1f} mm/h" if rain_vals else "N/A"
        uv_max = f"{max(uv_vals):.1f}" if uv_vals else "N/A"
        colC.metric("Rain (Max)", rain_max)
        colD.metric("UV Index (Max)", uv_max)
    
    st.markdown(f"**Location Info:** {l_info.get('name')} | **Timezone:** {l_info.get('timezone')} | **Sunrise:** {l_info.get('sunrise')} | **Sunset:** {l_info.get('sunset')}")

    # Sidebar Table
    # Bottom Section
    st.header("Charts")

    def plot_custom_chart(df_plot, title, cols, colors):
        fig, ax = plt.subplots(figsize=(10, 4))
        
        # Ensure datetime is parsed
        if not pd.api.types.is_datetime64_any_dtype(df_plot.index):
            df_plot.index = pd.to_datetime(df_plot.index)
            
        max_val = -float('inf')
        for col, color in zip(cols, colors):
            if col in df_plot.columns:
                ax.plot(df_plot.index, df_plot[col], label=col, color=color, marker='o')
                local_max = df_plot[col].max()
                if local_max > max_val:
                    max_val = local_max
                    
        # Y-axis padding (max >= max plot point)
        # Add 10% padding to max_val
        y_min, _ = ax.get_ylim()
        if max_val != -float('inf'):
            ax.set_ylim(y_min, max_val * 1.1)

        # X-axis formatting: show only 07:00 and 19:00
        ax.xaxis.set_major_locator(mdates.HourLocator(byhour=[7, 19]))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        ax.set_title(title)
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)
        fig.tight_layout()
        st.pyplot(fig)

    st.subheader("Temperature & Humidity")
    plot_custom_chart(df.set_index('datetime'), "Temperature & Humidity", ['temperature', 'humidity'], ['red', 'blue'])
    
    st.subheader("Wind Speed & Gust")
    plot_custom_chart(df.set_index('datetime'), "Wind Speed & Gust", ['wind_speed', 'wind_gust'], ['green', 'orange'])
    
    st.subheader("Rain & PoP")
    rain_cols = ['rain', 'pop'] if 'rain' in df.columns else ['pop']
    plot_custom_chart(df.set_index('datetime'), "Rain & PoP", rain_cols, ['purple', 'cyan'])
        
    if st.session_state.api_source == "Open-Meteo" and st.session_state.marine_data:
        df_marine = pd.DataFrame(st.session_state.marine_data)
        st.subheader("Wave & Swell Height")
        plot_custom_chart(df_marine.set_index('datetime'), "Wave Height", ['wave_height', 'swell_wave_height'], ['dodgerblue', 'mediumblue'])
        
        st.subheader("Wave & Swell Period")
        plot_custom_chart(df_marine.set_index('datetime'), "Wave Period", ['wave_period', 'swell_wave_period'], ['purple', 'darkviolet'])

    st.markdown("---")
    st.header("Data Table")
    if st.session_state.api_source == "Open-Meteo":
        cols = ['datetime', 'description', 'temperature', 'humidity', 'wind_speed', 'wind_gust', 'wind_direction', 'rain', 'pop', 'uv_index']
    else:
        cols = ['datetime', 'description', 'temperature', 'humidity', 'wind_speed', 'wind_gust', 'wind_direction', 'pop']
    df_display = df[[c for c in cols if c in df.columns]]
    st.dataframe(df_display, use_container_width=True)

    st.markdown("---")
    st.header("Export Reports")
    colA, colB = st.columns(2)
    
    with colA:
        st.subheader("PDF Report")
        pdf_lang = st.radio("PDF Language", ["English", "Vietnamese"], horizontal=True)
        if st.button("Generate PDF Report"):
            with st.spinner("Generating PDF..."):
                if pdf_lang == "Vietnamese":
                    logic.generate_vietnamese_pdf_report(
                        st.session_state.lat, st.session_state.lon, w_data, l_info, 
                        st.session_state.ui_location_name, st.session_state.api_source, st.session_state.marine_data
                    )
                else:
                    logic.generate_pdf_report(
                        st.session_state.lat, st.session_state.lon, w_data, l_info, 
                        st.session_state.ui_location_name, st.session_state.api_source, st.session_state.marine_data
                    )
                import glob
                pdfs = glob.glob("Weather_Report_*.pdf")
                if pdfs:
                    latest_pdf = max(pdfs, key=os.path.getctime)
                    with open(latest_pdf, "rb") as f:
                        pdf_bytes = f.read()
                    st.download_button("Download Current PDF", data=pdf_bytes, file_name=latest_pdf, mime="application/pdf")
                    st.success("PDF generated!")
                else:
                    st.error("Failed to generate PDF.")
                    
    with colB:
        st.subheader("Historical Data Export")
        if st.button("Export Excel / CSV"):
            with st.spinner("Preparing export files..."):
                excel_buf = io.BytesIO()
                with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Weather')
                    if st.session_state.marine_data:
                        pd.DataFrame(st.session_state.marine_data).to_excel(writer, index=False, sheet_name='Marine')
                
                st.download_button(
                    label="Download Excel (.xlsx)",
                    data=excel_buf.getvalue(),
                    file_name=f"Historical_Data_{st.session_state.ui_location_name}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name=f"Historical_Data_{st.session_state.ui_location_name}.csv",
                    mime="text/csv"
                )

