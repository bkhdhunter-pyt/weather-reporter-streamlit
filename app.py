import streamlit as st
import pandas as pd
from weather_logic import WeatherLogic, load_config
import os
import io
import datetime
import math
from dotenv import load_dotenv
import os

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
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    location = st.text_input("Enter city name or coordinates (lat, lon):", "Hanoi")
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

if fetch_btn and location:
    with st.spinner("Fetching data..."):
        # geocode
        def resolve_location(loc_str, api_key=None, use_owm=False):
            import requests
            # Check if lat, lon
            parts = loc_str.split(',')
            if len(parts) == 2:
                try:
                    return float(parts[0].strip()), float(parts[1].strip())
                except ValueError:
                    pass
            # Geocode
            if use_owm and api_key:
                resp = requests.get(f"http://api.openweathermap.org/geo/1.0/direct?q={loc_str}&limit=1&appid={api_key}")
                if resp.status_code == 200 and resp.json():
                    return resp.json()[0]['lat'], resp.json()[0]['lon']
            # Fallback to open-meteo
            resp = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={loc_str}&count=1")
            if resp.status_code == 200 and resp.json().get('results'):
                return resp.json()['results'][0]['latitude'], resp.json()['results'][0]['longitude']
            return None, None

        lat, lon = resolve_location(location, logic.api_key, data_source == "OpenWeatherMap")
        
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
    st.sidebar.header("Data Table")
    df = pd.DataFrame(w_data)
    # filter columns and reorder
    if st.session_state.api_source == "Open-Meteo":
        cols = ['datetime', 'description', 'temperature', 'humidity', 'wind_speed', 'wind_gust', 'wind_direction', 'rain', 'pop', 'uv_index']
    else:
        cols = ['datetime', 'description', 'temperature', 'humidity', 'wind_speed', 'wind_gust', 'wind_direction', 'pop']
    df_display = df[[c for c in cols if c in df.columns]]
    st.sidebar.dataframe(df_display, use_container_width=True)
    
    # PDF Export
    st.sidebar.header("Export")
    pdf_lang = st.sidebar.radio("PDF Language", ["English", "Vietnamese"])
    if st.sidebar.button("Generate PDF Report"):
        with st.spinner("Generating PDF..."):
            cur_dir = os.getcwd()
            # The logic expects to save to standard path then we could read it
            # Or we can just let it save and then provide download link
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
            # Find the latest generated pdf
            import glob
            pdfs = glob.glob("Weather_Report_*.pdf")
            if pdfs:
                latest_pdf = max(pdfs, key=os.path.getctime)
                with open(latest_pdf, "rb") as f:
                    pdf_bytes = f.read()
                st.sidebar.download_button("Download PDF", data=pdf_bytes, file_name=latest_pdf, mime="application/pdf")
                st.sidebar.success("PDF generated!")
            else:
                st.sidebar.error("Failed to generate PDF.")

    # Bottom Section
    st.header("Charts")
    chart_opts = ["Temperature & Humidity", "Wind Speed & Gust", "Rain & PoP"]
    if st.session_state.api_source == "Open-Meteo" and st.session_state.marine_data:
        chart_opts.append("Wave & Swell Height")
        chart_opts.append("Wave & Swell Period")
        
    chart_sel = st.selectbox("Select Chart to View", chart_opts)
    
    if chart_sel == "Temperature & Humidity":
        st.line_chart(df.set_index('datetime')[['temperature', 'humidity']])
    elif chart_sel == "Wind Speed & Gust":
        st.line_chart(df.set_index('datetime')[['wind_speed', 'wind_gust']])
    elif chart_sel == "Rain & PoP":
        # Streamlit doesn't support dual axis directly via line_chart easily but we can just use matplotlib or simple line chart
        if 'rain' in df.columns and 'pop' in df.columns:
            st.line_chart(df.set_index('datetime')[['rain', 'pop']])
        else:
            st.line_chart(df.set_index('datetime')[['pop']])
    elif chart_sel == "Wave & Swell Height":
        df_marine = pd.DataFrame(st.session_state.marine_data)
        st.line_chart(df_marine.set_index('datetime')[['wave_height', 'swell_wave_height']])
    elif chart_sel == "Wave & Swell Period":
        df_marine = pd.DataFrame(st.session_state.marine_data)
        st.line_chart(df_marine.set_index('datetime')[['wave_period', 'swell_wave_period']])

