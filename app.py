import streamlit as st
import pandas as pd
from weather_logic import WeatherLogic, load_config
import os
import io
import datetime
import math
from dotenv import load_dotenv
import plotly.graph_objects as go
import base64
import requests
import folium
from streamlit_folium import st_folium

load_dotenv()

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

st.set_page_config(page_title="Weather Reporter", layout="wide")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #2A0845, #1C0770);
    color: white; /* to ensure text remains readable on dark background */
}

/* Custom Button Styles */
div.stButton > button, div.stDownloadButton > button {
    background: linear-gradient(90deg, #0072ff, #00c6ff);
    color: white;
    border: 1px solid transparent;
    transition: 0.3s;
}
div.stButton > button:hover, div.stDownloadButton > button:hover {
    background: transparent !important;
    border: 1px solid #00c6ff !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

st.title("Weather Reporter")

@st.cache_resource
def get_weather_logic():
    api_key = os.environ.get("OPENWEATHERMAP_API_KEY")
    config = load_config()
    if not api_key:
        api_key = config.get("api_keys", {}).get("openweathermap", "")
    return WeatherLogic(api_key), config

logic, config_data = get_weather_logic()

# ─── Session state init ───────────────────────────────────────────────────────
if "weather_data" not in st.session_state:
    st.session_state.weather_data = None
    st.session_state.location_info = None
    st.session_state.marine_data = None
    st.session_state.lat = None
    st.session_state.lon = None
    st.session_state.api_source = None
    st.session_state.ui_location_name = None
if "selected_lat" not in st.session_state:
    st.session_state.selected_lat = None
    st.session_state.selected_lon = None
    st.session_state.selected_location_name = None
if "geocode_results" not in st.session_state:
    st.session_state.geocode_results = []

# ─── Location Section ─────────────────────────────────────────────────────────
st.header("Search Location")

locations_dict = config_data.get("locations", {})
loc_names = list(locations_dict.keys())

tab1, tab2, tab3, tab4 = st.tabs(["📋 Danh sách", "🔍 Tìm kiếm", "🗺️ Bản đồ", "📍 Tọa độ"])

# ── Tab 1: Dropdown ────────────────────────────────────────────────────────────
with tab1:
    default_loc = "Rong Doi Platform - Block 11.2"
    default_idx = loc_names.index(default_loc) if default_loc in loc_names else 0
    selected_from_list = st.selectbox("Chọn địa điểm:", loc_names, index=default_idx)
    if st.button("Chọn địa điểm này", key="btn_list"):
        coords = locations_dict[selected_from_list]['coords']
        st.session_state.selected_lat = coords[0]
        st.session_state.selected_lon = coords[1]
        st.session_state.selected_location_name = selected_from_list
        st.success(f"✅ Đã chọn: **{selected_from_list}** ({coords[0]:.4f}, {coords[1]:.4f})")

    # Auto-select default on very first load (no location chosen yet)
    if st.session_state.selected_lat is None:
        coords = locations_dict[default_loc]['coords']
        st.session_state.selected_lat = coords[0]
        st.session_state.selected_lon = coords[1]
        st.session_state.selected_location_name = default_loc

# ── Tab 2: Geocoding Search ────────────────────────────────────────────────────
with tab2:
    search_query = st.text_input("Nhập tên địa điểm:", placeholder="Ví dụ: Vũng Tàu, Hà Nội, Ho Chi Minh City...")
    if st.button("🔍 Tìm kiếm", key="btn_search"):
        if search_query.strip():
            with st.spinner("Đang tìm kiếm..."):
                try:
                    resp = requests.get(
                        "https://geocoding-api.open-meteo.com/v1/search",
                        params={"name": search_query, "count": 5, "language": "vi", "format": "json"},
                        timeout=8
                    )
                    data = resp.json()
                    st.session_state.geocode_results = data.get("results", [])
                except Exception as e:
                    st.error(f"Lỗi tìm kiếm: {e}")
                    st.session_state.geocode_results = []
        else:
            st.warning("Vui lòng nhập tên địa điểm.")

    if st.session_state.geocode_results:
        options = [
            f"{r.get('name', '')}, {r.get('admin1', '')}, {r.get('country', '')} "
            f"({r['latitude']:.4f}, {r['longitude']:.4f})"
            for r in st.session_state.geocode_results
        ]
        chosen_idx = st.radio("Chọn kết quả phù hợp:", range(len(options)), format_func=lambda i: options[i])
        if st.button("✅ Xác nhận địa điểm này", key="btn_confirm_search"):
            r = st.session_state.geocode_results[chosen_idx]
            st.session_state.selected_lat = r["latitude"]
            st.session_state.selected_lon = r["longitude"]
            place_name = f"{r.get('name','')}, {r.get('country','')}"
            st.session_state.selected_location_name = place_name
            st.success(f"✅ Đã chọn: **{place_name}** ({r['latitude']:.4f}, {r['longitude']:.4f})")

# ── Tab 3: Interactive Map ─────────────────────────────────────────────────────
with tab3:
    st.caption("Click vào bất kỳ điểm nào trên bản đồ để lấy tọa độ địa điểm.")
    init_lat = st.session_state.selected_lat or 10.8
    init_lon = st.session_state.selected_lon or 106.7
    m = folium.Map(location=[init_lat, init_lon], zoom_start=6, tiles="OpenStreetMap")
    # Show current selection marker if exists
    if st.session_state.selected_lat:
        folium.Marker(
            [st.session_state.selected_lat, st.session_state.selected_lon],
            tooltip=st.session_state.selected_location_name or "Đã chọn",
            icon=folium.Icon(color="red", icon="info-sign")
        ).add_to(m)
    map_result = st_folium(m, height=420, width="100%", returned_objects=["last_clicked"])
    if map_result and map_result.get("last_clicked"):
        clicked = map_result["last_clicked"]
        clat = round(clicked["lat"], 5)
        clon = round(clicked["lng"], 5)
        st.info(f"📍 Vị trí vừa click: **{clat}, {clon}**")
        if st.button(f"✅ Dùng tọa độ này ({clat}, {clon})", key="btn_confirm_map"):
            st.session_state.selected_lat = clat
            st.session_state.selected_lon = clon
            st.session_state.selected_location_name = f"Tuỳ chỉnh ({clat}, {clon})"
            st.success("✅ Đã lưu tọa độ từ bản đồ!")

# ── Tab 4: Manual Coordinates ──────────────────────────────────────────────────
with tab4:
    st.caption("Nhập tọa độ thủ công (phù hợp cho các địa điểm offshore hoặc kỹ thuật).")
    mc1, mc2 = st.columns(2)
    with mc1:
        manual_lat = st.number_input("Latitude:", min_value=-90.0, max_value=90.0,
                                     value=float(st.session_state.selected_lat or 10.8),
                                     step=0.0001, format="%.5f")
    with mc2:
        manual_lon = st.number_input("Longitude:", min_value=-180.0, max_value=180.0,
                                     value=float(st.session_state.selected_lon or 106.7),
                                     step=0.0001, format="%.5f")
    manual_name = st.text_input("Tên địa điểm (tuỳ chọn):", placeholder="Ví dụ: Platform X, Block Y...")
    if st.button("✅ Xác nhận tọa độ", key="btn_manual"):
        st.session_state.selected_lat = manual_lat
        st.session_state.selected_lon = manual_lon
        st.session_state.selected_location_name = manual_name.strip() or f"({manual_lat:.5f}, {manual_lon:.5f})"
        st.success(f"✅ Đã xác nhận: **{st.session_state.selected_location_name}**")

# ── Confirmed location display + Fetch ────────────────────────────────────────
st.markdown("---")
if st.session_state.selected_lat:
    st.markdown(
        f"📍 **Địa điểm đã chọn:** {st.session_state.selected_location_name} "
        f"| Lat: `{st.session_state.selected_lat}` | Lon: `{st.session_state.selected_lon}`"
    )

col_ds, col_btn = st.columns([2, 1])
with col_ds:
    data_source = st.radio("Data Source:", ["Open-Meteo", "OpenWeatherMap"], horizontal=True)
with col_btn:
    fetch_btn = st.button("Fetch Data")

# ── Fetch Logic ────────────────────────────────────────────────────────────────
if fetch_btn or (not st.session_state.weather_data and st.session_state.selected_lat):
    lat = st.session_state.selected_lat
    lon = st.session_state.selected_lon
    location = st.session_state.selected_location_name
    with st.spinner("Fetching data..."):
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
    
    temp_b64 = get_base64_image("icons/temp.png")
    colA.markdown(f"<div style='text-align: center; margin-bottom: -15px;'><img src='data:image/png;base64,{temp_b64}' width='55'></div>", unsafe_allow_html=True)
    colA.metric("Temperature", f"{temp_min} - {temp_max}")
    
    wind_b64 = get_base64_image("icons/wind.png")
    colB.markdown(f"<div style='text-align: center; margin-bottom: -15px;'><img src='data:image/png;base64,{wind_b64}' width='55'></div>", unsafe_allow_html=True)
    colB.metric("Wind Speed", f"{wind_min} - {wind_max}")
    if st.session_state.api_source == "Open-Meteo":
        rain_vals = [item.get('rain') for item in w_data if isinstance(item.get('rain'), (int, float))]
        uv_vals = [item.get('uv_index') for item in w_data if isinstance(item.get('uv_index'), (int, float))]
        rain_max = f"{max(rain_vals):.1f} mm/h" if rain_vals else "N/A"
        uv_max = f"{max(uv_vals):.1f}" if uv_vals else "N/A"
        
        rain_b64 = get_base64_image("icons/rain.png")
        colC.markdown(f"<div style='text-align: center; margin-bottom: -15px;'><img src='data:image/png;base64,{rain_b64}' width='55'></div>", unsafe_allow_html=True)
        colC.metric("Rain (Max)", rain_max)
        
        uv_b64 = get_base64_image("icons/UV.png")
        colD.markdown(f"<div style='text-align: center; margin-bottom: -15px;'><img src='data:image/png;base64,{uv_b64}' width='55'></div>", unsafe_allow_html=True)
        colD.metric("UV Index (Max)", uv_max)
    
    current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"**Location Info:** {l_info.get('name')} | **Timezone:** {l_info.get('timezone')} | **Sunrise:** {l_info.get('sunrise')} | **Sunset:** {l_info.get('sunset')} | **Current Time:** {current_time_str}")

    # Sidebar Table
    # Bottom Section
    st.header("Charts")
    df = pd.DataFrame(w_data)

    def plot_custom_chart(df_plot, title, cols, colors, units=None):
        # Ensure datetime is parsed
        if not pd.api.types.is_datetime64_any_dtype(df_plot.index):
            df_plot.index = pd.to_datetime(df_plot.index)
        
        if units is None:
            units = [''] * len(cols)
        
        # Build traces list, then sort by descending mean y so the highest
        # line on the chart always appears first in the unified hover tooltip
        traces = []
        max_val = -float('inf')
        for col, color, unit in zip(cols, colors, units):
            if col in df_plot.columns:
                unit_str = f' {unit}' if unit else ''
                mean_y = df_plot[col].mean()
                traces.append(dict(
                    col=col, color=color, mean_y=mean_y,
                    unit_str=unit_str, data=df_plot[col]
                ))
                local_max = df_plot[col].max()
                if local_max > max_val:
                    max_val = local_max
        
        # Sort descending by mean value so hover label order matches visual order
        traces.sort(key=lambda t: t['mean_y'], reverse=True)
        
        fig = go.Figure()
        for t in traces:
            fig.add_trace(go.Scatter(
                x=df_plot.index,
                y=t['data'],
                mode='lines',
                name=t['col'],
                line=dict(color=t['color'], width=2),
                hovertemplate=f'%{{y:.1f}}{t["unit_str"]}<extra></extra>'
            ))
                    
        y_max_range = max_val * 1.1 if max_val != -float('inf') else None
        
        tickvals = df_plot.index[df_plot.index.hour.isin([7, 19])]
        ticktext = tickvals.strftime('%m-%d %H:%M')
        
        fig.update_layout(
            title=dict(text=title, font=dict(size=18)),
            xaxis=dict(
                tickmode='array',
                tickvals=tickvals,
                ticktext=ticktext,
                tickangle=-45,
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)',
                tickfont=dict(size=13),
                title_font=dict(size=14)
            ),
            yaxis=dict(
                range=[None, y_max_range] if y_max_range is not None else None,
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)',
                tickfont=dict(size=13),
                title_font=dict(size=14)
            ),
            legend=dict(font=dict(size=13)),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            hovermode="x unified",
            margin=dict(l=40, r=20, t=40, b=40)
        )
        
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Temperature & Humidity")
    plot_custom_chart(df.set_index('datetime'), "Temperature & Humidity",
        ['temperature', 'humidity'], ['#EB4C4C', 'white'],
        units=['°C', '%'])
    
    st.subheader("Wind Speed & Gust")
    plot_custom_chart(df.set_index('datetime'), "Wind Speed & Gust",
        ['wind_speed', 'wind_gust'], ['green', 'orange'],
        units=['knots', 'knots'])
    
    st.subheader("Rain & PoP")
    rain_cols = ['rain', 'pop'] if 'rain' in df.columns else ['pop']
    rain_units = ['mm/h', '%'] if 'rain' in df.columns else ['%']
    plot_custom_chart(df.set_index('datetime'), "Rain & PoP",
        rain_cols, ['blue', 'purple'],
        units=rain_units)
    
    if 'cloud_cover' in df.columns:
        st.subheader("Cloud Cover")
        plot_custom_chart(df.set_index('datetime'), "Cloud Cover",
            ['cloud_cover'], ['lightgray'], units=['%'])
        
    if 'uv_index' in df.columns:
        st.subheader("UV Index")
        plot_custom_chart(df.set_index('datetime'), "UV Index",
            ['uv_index'], ['gold'], units=[''])
        
    if st.session_state.api_source == "Open-Meteo" and st.session_state.marine_data:
        df_marine = pd.DataFrame(st.session_state.marine_data)
        st.subheader("Wave & Swell Height")
        plot_custom_chart(df_marine.set_index('datetime'), "Wave Height",
            ['wave_height', 'swell_wave_height'], ['dodgerblue', 'mediumblue'],
            units=['m', 'm'])
        
        st.subheader("Wave & Swell Period")
        plot_custom_chart(df_marine.set_index('datetime'), "Wave Period",
            ['wave_period', 'swell_wave_period'], ['magenta', 'gold'],
            units=['s', 's'])

    st.markdown("---")
    st.header("Data Table")
    if st.session_state.api_source == "Open-Meteo":
        cols = ['datetime', 'description', 'temperature', 'humidity', 'wind_speed', 'wind_gust', 'wind_direction', 'rain', 'pop', 'uv_index']
    else:
        cols = ['datetime', 'description', 'temperature', 'humidity', 'wind_speed', 'wind_gust', 'wind_direction', 'pop']
    df_display = df[[c for c in cols if c in df.columns]].copy()
    
    # Render table via HTML for complete styling control (font size + lightblue hover)
    html_table = df_display.to_html(classes="custom-table", index=False, justify='left', escape=False)
    
    html_template = f"""
<style>
.custom-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 16px; 
    margin-bottom: 2rem;
}}
.custom-table th, .custom-table td {{
    padding: 8px 12px;
    border: 1px solid #444; 
}}
.custom-table tr:hover {{
    background-color: lightgreen !important;
    color: black !important;
}}
.custom-table tr:hover td {{
    color: black !important;
}}
</style>
<div style="max-height: 400px; overflow-y: auto;">
{html_table}
</div>
"""
    st.markdown(html_template, unsafe_allow_html=True)

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
        
        df_datetime = pd.to_datetime(df['datetime'])
        import datetime
        current_date = datetime.date.today()
        default_from = current_date - datetime.timedelta(days=7)
        
        export_col1, export_col2 = st.columns(2)
        with export_col1:
            export_from = st.date_input("From (date)", max_value=current_date, value=default_from)
        with export_col2:
            export_to = st.date_input("To (date)", max_value=current_date, value=current_date)

        # Filter dataset by converting string datetimes
        mask = (df_datetime.dt.date >= export_from) & (df_datetime.dt.date <= export_to)
        export_df = df.loc[mask]
        
        export_marine_df = None
        if st.session_state.marine_data:
            marine_df = pd.DataFrame(st.session_state.marine_data)
            marine_mask = (pd.to_datetime(marine_df['datetime']).dt.date >= export_from) & (pd.to_datetime(marine_df['datetime']).dt.date <= export_to)
            export_marine_df = marine_df.loc[marine_mask]

        # Prepare Excel (remove timezones as Excel doesn't support them)
        export_df_excel = export_df.copy()
        export_df_excel['datetime'] = pd.to_datetime(export_df_excel['datetime']).dt.tz_localize(None)
        
        # Remove tzinfo from any other columns (like datetime_obj, sunrise, sunset)
        for col in export_df_excel.columns:
            if export_df_excel[col].apply(lambda x: hasattr(x, 'tzinfo') and x.tzinfo is not None).any():
                export_df_excel[col] = export_df_excel[col].apply(lambda x: x.replace(tzinfo=None) if hasattr(x, 'tzinfo') and x.tzinfo is not None else x)
        
        excel_buf = io.BytesIO()
        with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
            export_df_excel.to_excel(writer, index=False, sheet_name='Weather')
            if export_marine_df is not None:
                export_marine_df_excel = export_marine_df.copy()
                export_marine_df_excel['datetime'] = pd.to_datetime(export_marine_df_excel['datetime']).dt.tz_localize(None)
                
                for col in export_marine_df_excel.columns:
                    if export_marine_df_excel[col].apply(lambda x: hasattr(x, 'tzinfo') and x.tzinfo is not None).any():
                        export_marine_df_excel[col] = export_marine_df_excel[col].apply(lambda x: x.replace(tzinfo=None) if hasattr(x, 'tzinfo') and x.tzinfo is not None else x)
                
                export_marine_df_excel.to_excel(writer, index=False, sheet_name='Marine')
        
        # Prepare CSV
        csv_data = export_df.to_csv(index=False).encode('utf-8')
        
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            st.download_button(
                label="Download Excel (.xlsx)",
                data=excel_buf.getvalue(),
                file_name=f"Historical_Data_{st.session_state.ui_location_name}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with btn_col2:
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"Historical_Data_{st.session_state.ui_location_name}.csv",
                mime="text/csv"
            )

