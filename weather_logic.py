import sys
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from PIL import Image as PLImage, ImageDraw, ImageFont
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Paragraph,
                                Spacer, Image)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import requests
import pytz
import xlsxwriter
import json
import re
import traceback
import math
from io import BytesIO
from datetime import datetime, timedelta, timezone
import matplotlib
UNITS = {'precipitation': 'mm'}
VIETNAMESE_FONT_NAME, VIETNAMESE_FONT_NAME_BOLD = 'Helvetica', 'Helvetica-Bold'
LOCATION_TIMEZONES = {'VN': 'Asia/Ho_Chi_Minh', 'ID': 'Asia/Jakarta', 'MY': 'Asia/Kuala_Lumpur', 'SG': 'Asia/Singapore', 'TH': 'Asia/Bangkok', 'PH': 'Asia/Manila', 'CN': 'Asia/Shanghai', 'JP': 'Asia/Tokyo', 'KR': 'Asia/Seoul', 'TW': 'Asia/Taipei', 'HK': 'Asia/Hong_Kong', 'IN': 'Asia/Kolkata', 'PK': 'Asia/Karachi', 'BD': 'Asia/Dhaka', 'LK': 'Asia/Colombo', 'NP': 'Asia/Kathmandu', 'AE': 'Asia/Dubai', 'SA': 'Asia/Riyadh', 'QA': 'Asia/Qatar', 'IL': 'Asia/Jerusalem', 'TR': 'Europe/Istanbul', 'GB': 'Europe/London', 'DE': 'Europe/Berlin', 'FR': 'Europe/Paris', 'IT': 'Europe/Rome', 'ES': 'Europe/Madrid', 'PT': 'Europe/Lisbon', 'NL': 'Europe/Amsterdam', 'BE': 'Europe/Brussels', 'CH': 'Europe/Zurich', 'SE': 'Europe/Stockholm',
                      'NO': 'Europe/Oslo', 'DK': 'Europe/Copenhagen', 'FI': 'Europe/Helsinki', 'PL': 'Europe/Warsaw', 'AT': 'Europe/Vienna', 'GR': 'Europe/Athens', 'IE': 'Europe/Dublin', 'RU': 'Europe/Moscow', 'US': 'America/New_York', 'CA': 'America/Toronto', 'MX': 'America/Mexico_City', 'PA': 'America/Panama', 'CR': 'America/Costa_Rica', 'GT': 'America/Guatemala', 'BR': 'America/Sao_Paulo', 'AR': 'America/Buenos_Aires', 'CL': 'America/Santiago', 'CO': 'America/Bogota', 'PE': 'America/Lima', 'VE': 'America/Caracas', 'AU': 'Australia/Sydney', 'NZ': 'Pacific/Auckland', 'FJ': 'Pacific/Fiji', 'ZA': 'Africa/Johannesburg', 'EG': 'Africa/Cairo', 'MA': 'Africa/Casablanca', 'NG': 'Africa/Lagos', 'KE': 'Africa/Nairobi', 'ET': 'Africa/Addis_Ababa'}
DEFAULT_TIMEZONE = 'Asia/Ho_Chi_Minh'
WEATHER_DESC_VIET = {'Clear sky': 'Trời quang', 'Few clouds': 'Ít mây', 'Scattered clouds': 'Mây rải rác', 'Broken clouds': 'Nhiều mây', 'Overcast clouds': 'Trời u ám', 'Light rain': 'Mưa nhẹ', 'Moderate rain': 'Mưa vừa', 'Heavy intensity rain': 'Mưa to', 'Very heavy rain': 'Mưa rất to', 'Extreme rain': 'Mưa cực lớn', 'Freezing rain': 'Mưa đông đá', 'Light intensity shower rain': 'Mưa rào nhẹ', 'Shower rain': 'Mưa rào', 'Heavy intensity shower rain': 'Mưa rào nặng hạt', 'Ragged shower rain': 'Mưa rào không đều', 'Thunderstorm with light rain': 'Dông kèm mưa nhẹ', 'Thunderstorm with rain': 'Dông kèm mưa', 'Thunderstorm with heavy rain': 'Dông kèm mưa to', 'Light thunderstorm': 'Dông nhẹ', 'Thunderstorm': 'Dông', 'Heavy thunderstorm': 'Dông mạnh', 'Ragged thunderstorm': 'Dông không đều', 'Thunderstorm with light drizzle': 'Dông kèm mưa phùn nhẹ', 'Thunderstorm with drizzle': 'Dông kèm mưa phùn', 'Thunderstorm with heavy drizzle': 'Dông kèm mưa phùn nặng hạt',
                     'Light intensity drizzle': 'Mưa phùn nhẹ', 'Drizzle': 'Mưa phùn', 'Heavy intensity drizzle': 'Mưa phùn nặng hạt', 'Light intensity drizzle rain': 'Mưa phùn/mưa nhẹ', 'Drizzle rain': 'Mưa phùn/mưa', 'Heavy intensity drizzle rain': 'Mưa phùn/mưa nặng hạt', 'Shower rain and drizzle': 'Mưa rào và mưa phùn', 'Heavy shower rain and drizzle': 'Mưa rào to và mưa phùn', 'Shower drizzle': 'Mưa phùn dạng mưa rào', 'Light snow': 'Tuyết nhẹ', 'Snow': 'Tuyết', 'Heavy snow': 'Tuyết dày', 'Sleet': 'Mưa tuyết', 'Light shower sleet': 'Mưa tuyết nhẹ', 'Shower sleet': 'Mưa tuyết', 'Light rain and snow': 'Mưa và tuyết nhẹ', 'Rain and snow': 'Mưa và tuyết', 'Light shower snow': 'Tuyết rơi nhẹ', 'Shower snow': 'Tuyết rơi', 'Heavy shower snow': 'Tuyết rơi dày', 'Mist': 'Sương mù nhẹ', 'Smoke': 'Khói', 'Haze': 'Bụi mù', 'Sand/ dust whirls': 'Xoáy cát/bụi', 'Fog': 'Sương mù', 'Sand': 'Cát', 'Dust': 'Bụi', 'Volcanic ash': 'Tro núi lửa', 'Squalls': 'Gió giật mạnh', 'Tornado': 'Lốc xoáy', 'N/A': 'Không xác định'}
WIND_DIR_VIET = {'N': 'B', 'NNE': 'BĐB', 'NE': 'ĐB', 'ENE': 'ĐĐB', 'E': 'Đ', 'ESE': 'ĐĐN', 'SE': 'ĐN', 'SSE': 'NĐN',
                 'S': 'N', 'SSW': 'NTN', 'SW': 'TN', 'WSW': 'TTN', 'W': 'T', 'WNW': 'TTB', 'NW': 'TB', 'NNW': 'BTB', 'N/A': 'N/A'}
WMO_WEATHER_CODES_EN = {0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle", 56: "Light freezing drizzle", 57: "Dense freezing drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain", 66: "Light freezing rain",
                        67: "Heavy freezing rain", 71: "Light snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall", 77: "Snow grains", 80: "Slight showers", 81: "Moderate showers", 82: "Violent showers", 85: "Slight snow showers", 86: "Heavy snow showers", 95: "Thunderstorm (slight/moderate)", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"}
WMO_WEATHER_CODES_VIET = {0: "Trời quang", 1: "Chủ yếu quang mây", 2: "Mây rải rác", 3: "Trời nhiều mây", 45: "Sương mù", 48: "Sương mù có sương giá", 51: "Mưa phùn nhẹ", 53: "Mưa phùn vừa", 55: "Mưa phùn nặng hạt", 56: "Mưa phùn nhẹ kèm đông đá", 57: "Mưa phùn nặng hạt kèm đông đá", 61: "Mưa nhẹ", 63: "Mưa vừa",
                          65: "Mưa to", 66: "Mưa nhẹ kèm đông đá", 67: "Mưa to kèm đông đá", 71: "Tuyết rơi nhẹ", 73: "Tuyết rơi vừa", 75: "Tuyết rơi dày", 77: "Hạt tuyết", 80: "Mưa rào nhẹ", 81: "Mưa rào vừa", 82: "Mưa rào dữ dội", 85: "Mưa tuyết nhẹ", 86: "Mưa tuyết dày", 95: "Dông (nhẹ/vừa)", 96: "Dông kèm mưa đá nhỏ", 99: "Dông kèm mưa đá lớn"}
OPENMETEO_API_URL = "https://api.open-meteo.com/v1/forecast"
OPENMETEO_MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"
OPENMETEO_ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"
APP_STYLESHEET = """
    QWidget {
        font-family: Arial, sans-serif;
    }
    QGroupBox {
        font-size: 11pt;
        font-weight: bold;
        border: 1px solid #CCC;
        border-radius: 5px;
        margin-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
    }
    QPushButton {
        font-size: 10pt;
        font-weight: bold;
        padding: 8px;
        background-color: #a7fcfd;
        color: black;
        border: 1px solid #888;
        border-radius: 4px;
    }
    QPushButton:hover {
        background-color: #90e0e1;
    }
    QPushButton:pressed {
        background-color: #79c6c7;
    }
"""
COLOR_SCALES = {
    'precipitation': {
        'min': 0,
        'max': 20,
        'colors': [
            (214, 236, 255), (0, 191, 255), (0, 255, 0),
            (255, 255, 0), (255, 215, 0), (255, 165, 0),
            (255, 69, 0), (255, 0, 0), (211, 0, 148),
            (255, 0, 255), (148, 0, 211)
        ]
    }
}

def resource_path(relative_path):
    """Return path to a bundled read-only asset (icons, Pictures, fonts).
    When frozen by PyInstaller the assets live in sys._MEIPASS (_internal/).
    When running normally, they live beside this script."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)

def user_data_path(relative_path):
    """Return path for user-writable files (config.json, output reports).
    Always resolved beside the executable (or script when not frozen)."""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)

def load_config():
    cfg_path = user_data_path('config.json')
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading config.json: {e}")
    
    # Return default empty config if file doesn't exist or is invalid
    # Avoid creating/writing the file automatically to support read-only environments
    return {"api_key_openweathermap": "YOUR_API_KEY_HERE",
            "dashboard_locations": [], "locations": {}}

class WeatherLogic:
    def __init__(self, api_key):
        self.api_key = api_key
        self.session = requests.Session()

    def _fetch_weather_data_owm(self, lat, lon):
            base_url = "https://api.openweathermap.org/data/2.5/"
            params = {'lat': lat, 'lon': lon,
                      'appid': self.api_key, 'units': 'metric'}
            try:
                current_response = self.session.get(
                    f"{base_url}weather", params=params, timeout=20)
                current_response.raise_for_status()
                current_data = current_response.json()

                forecast_response = self.session.get(f"{base_url}forecast", params={
                                                     **params, 'cnt': 40}, timeout=20)
                forecast_response.raise_for_status()
                forecast_data = forecast_response.json()

                # Robust timezone handling
                timezone_str = DEFAULT_TIMEZONE
                local_tz = None
                country_code = current_data.get('sys', {}).get('country')
                if country_code and country_code in LOCATION_TIMEZONES:
                    timezone_str = LOCATION_TIMEZONES[country_code]
                elif 'timezone' in current_data:
                    try:
                        offset_sec = int(current_data['timezone'])
                        now_utc = datetime.now(timezone.utc)
                        for tz_name in pytz.common_timezones:
                            tz = pytz.timezone(tz_name)
                            if now_utc.astimezone(tz).utcoffset() == timedelta(seconds=offset_sec):
                                timezone_str = tz_name
                                break
                        else:
                            local_tz = timezone(timedelta(seconds=offset_sec))
                            timezone_str = f"UTC{offset_sec/3600:+03.0f}:00"
                    except Exception as tz_err:
                        print(f"Could not process OWM timezone offset: {tz_err}")

                if local_tz is None:
                    try:
                        local_tz = pytz.timezone(timezone_str)
                    except pytz.exceptions.UnknownTimeZoneError:
                        print(
                            f"pytz unknown timezone '{timezone_str}', falling back to default.")
                        timezone_str = DEFAULT_TIMEZONE
                        local_tz = pytz.timezone(timezone_str)

                location_info = {
                    'name': current_data.get('name', f"Coords ({lat:.4f}, {lon:.4f})"),
                    'country': current_data.get('sys', {}).get('country', 'N/A'),
                    'timezone': timezone_str,
                    'sunrise': datetime.fromtimestamp(current_data['sys']['sunrise'], tz=timezone.utc).astimezone(local_tz).strftime('%H:%M'),
                    'sunset': datetime.fromtimestamp(current_data['sys']['sunset'], tz=timezone.utc).astimezone(local_tz).strftime('%H:%M')
                }

                processed_forecast = self._process_forecast_data_owm(
                    forecast_data, local_tz)
                return processed_forecast, location_info
            except Exception as e:
                print(f"Error in _fetch_weather_data_owm: {e}")
                return None, None

    def _fetch_weather_data_openmeteo(self, lat, lon):
            params = {
                "latitude": lat,
                "longitude": lon,
                "hourly": "apparent_temperature,temperature_2m,relative_humidity_2m,precipitation,rain,showers,snowfall,weather_code,wind_speed_10m,wind_gusts_10m,wind_direction_10m,cloud_cover,pressure_msl,uv_index",
                "daily": "apparent_temperature_max,apparent_temperature_min,temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,weather_code",
                "timezone": "auto",
                "forecast_days": 14,
                "temperature_unit": "celsius",
                "wind_speed_unit": "kn",
                "precipitation_unit": "mm"
            }
            try:
                response = self.session.get(
                    OPENMETEO_API_URL, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                location_info = {'name': f"Coords ({lat:.4f}, {lon:.4f})", 'country': 'N/A',
                                 'timezone': data.get('timezone', DEFAULT_TIMEZONE)}
                local_tz = pytz.timezone(location_info['timezone'])
                daily_data = data.get('daily', {})
                if daily_data.get('sunrise') and daily_data['sunrise']:
                    location_info['sunrise'] = datetime.fromisoformat(
                        daily_data['sunrise'][0]).astimezone(local_tz).strftime('%H:%M')
                if daily_data.get('sunset') and daily_data['sunset']:
                    location_info['sunset'] = datetime.fromisoformat(
                        daily_data['sunset'][0]).astimezone(local_tz).strftime('%H:%M')
                processed_data = self._process_forecast_data_openmeteo(
                    data.get('hourly', {}), local_tz)
                return processed_data, location_info
            except Exception as e:
                print(f"Error in _fetch_weather_data_openmeteo: {e}")
                return None, {}

    def _fetch_marine_data_openmeteo(self, lat, lon, timezone_str):
            params = {"latitude": lat, "longitude": lon, "hourly": "wave_height,wave_direction,wave_period,wind_wave_height,wind_wave_direction,wind_wave_period,swell_wave_height,swell_wave_direction,swell_wave_period",
                      "timezone": timezone_str, "forecast_days": 14}
            try:
                response = self.session.get(
                    OPENMETEO_MARINE_API_URL, params=params, timeout=30)
                response.raise_for_status()
                data = response.json().get('hourly', {})
                processed_data = []
                local_tz = pytz.timezone(timezone_str)
                for i in range(len(data.get('time', []))):
                    dt_obj = datetime.fromisoformat(
                        data['time'][i]).astimezone(local_tz)
                    processed_data.append({
                        'datetime_obj': dt_obj,
                        'datetime': dt_obj.strftime('%Y-%m-%d %H:%M'),
                        'wave_height': data['wave_height'][i],
                        'wave_direction': self._degrees_to_direction(data['wave_direction'][i]),
                        'wave_period': data['wave_period'][i],
                        'sea_level': data.get('sea_level', [None]*len(data.get('time', [])))[i],
                        'wind_wave_height': data['wind_wave_height'][i],
                        'wind_wave_direction': self._degrees_to_direction(data['wind_wave_direction'][i]),
                        'wind_wave_period': data['wind_wave_period'][i],
                        'swell_wave_height': data['swell_wave_height'][i],
                        'swell_wave_direction': self._degrees_to_direction(data['swell_wave_direction'][i]),
                        'swell_wave_period': data['swell_wave_period'][i],
                    })
                return processed_data
            except Exception as e:
                print(f"Error in _fetch_marine_data_openmeteo: {e}")
                return None

    def _process_forecast_data_owm(self, data, local_tz):
            processed = []
            now_local = datetime.now(local_tz)
            for item in data.get('list', []):
                local_time = datetime.fromtimestamp(
                    item['dt'], tz=timezone.utc).astimezone(local_tz)
                if now_local - timedelta(hours=3) <= local_time <= now_local + timedelta(days=5, hours=3):
                    # Use 'feels_like' as apparent temperature if available, else fallback to 'temp'
                    main_data = item.get('main', {})
                    apparent_temp = main_data.get(
                        'feels_like', main_data.get('temp'))
                    processed.append({
                        'datetime_obj': local_time, 'datetime': local_time.strftime('%Y-%m-%d %H:%M'),
                        'description': item.get('weather', [{}])[0].get('description', 'N/A').capitalize(),
                        'temperature': apparent_temp,  # Apparent temperature
                        'humidity': main_data.get('humidity'),
                        'pressure': main_data.get('pressure'),
                        'wind_speed': round(item.get('wind', {}).get('speed', 0) * 1.94384, 1),
                        'wind_gust': round(item.get('wind', {}).get('gust', 0) * 1.94384, 1),
                        'wind_direction': self._degrees_to_direction(item.get('wind', {}).get('deg')),
                        'rain': item.get('rain', {}).get('3h', 0.0), 'visibility': item.get('visibility'),
                        'pop': round(item.get('pop', 0.0) * 100), 'cloud_cover': item.get('clouds', {}).get('all')
                    })
            return processed

    def _process_forecast_data_openmeteo(self, hourly_data, local_tz):
            processed = []
            now_local = datetime.now(local_tz)
            times = hourly_data.get('time', [])
            for i in range(len(times)):
                local_time = datetime.fromisoformat(times[i]).astimezone(local_tz)
                if now_local - timedelta(hours=1) <= local_time <= now_local + timedelta(days=14, hours=1):
                    # Use apparent_temperature if available, else fallback to temperature_2m
                    apparent_temp = hourly_data.get(
                        'apparent_temperature', [None]*len(times))[i]
                    if apparent_temp is None:
                        apparent_temp = hourly_data.get(
                            'temperature_2m', [None]*len(times))[i]
                    rain = (hourly_data.get('rain', [])[i] or 0) + (hourly_data.get('showers',
                                                                                    [])[i] or 0) + (hourly_data.get('snowfall', [])[i] or 0)
                    processed.append({
                        'datetime_obj': local_time, 'datetime': local_time.strftime('%Y-%m-%d %H:%M'),
                        'description': WMO_WEATHER_CODES_EN.get(hourly_data.get('weather_code', [])[i], 'N/A'),
                        'temperature': apparent_temp,  # Apparent temperature
                        'humidity': hourly_data.get('relative_humidity_2m', [])[i],
                        'pressure': hourly_data.get('pressure_msl', [])[i],
                        'wind_speed': hourly_data.get('wind_speed_10m', [])[i], 'wind_gust': hourly_data.get('wind_gusts_10m', [])[i],
                        'wind_direction': self._degrees_to_direction(hourly_data.get('wind_direction_10m', [])[i]),
                        'rain': rain, 'uv_index': hourly_data.get('uv_index', [])[i],
                        'pop': 100 if rain > 0 else 0, 'cloud_cover': hourly_data.get('cloud_cover', [])[i]
                    })
            return processed

    def _degrees_to_direction(self, degrees):
            if degrees is None or degrees == 'N/A':
                return 'N/A'
            try:
                directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE',
                              'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
                return directions[round(float(degrees) / (360 / len(directions))) % len(directions)]
            except (ValueError, TypeError):
                return 'N/A'

    def create_chart(self, data, param_name, ylabel, title, date_key='datetime_obj', xlabel_text='Date/Time', color='tab:blue'):
            if not data:
                return None
            plt.figure(figsize=(9.0, 2.8))
            dates, values = [], []
            for item in data:
                val = item.get(param_name)
                if val is not None and val != 'N/A' and isinstance(item.get(date_key), datetime):
                    dates.append(item[date_key])
                    values.append(float(val))
            if not dates or not values:
                plt.close()
                return None
            plt.plot(dates, values, marker='.', linestyle='-',
                     markersize=4, linewidth=1, color=color)
            plt.title(title, fontsize=10)
            plt.xlabel(xlabel_text, fontsize=9)
            plt.ylabel(ylabel, fontsize=9)
            plt.xticks(rotation=30, ha='right', fontsize=9)
            plt.yticks(fontsize=9)
            plt.gca().xaxis.set_major_locator(mdates.HourLocator(
                byhour=[7], tz=dates[0].tzinfo if dates else None))
            plt.gca().xaxis.set_major_formatter(
                mdates.DateFormatter('%m-%d %H:%M', tz=dates[0].tzinfo if dates else None))
            plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
            plt.tight_layout(pad=0.5)
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=150)
            plt.close()
            buf.seek(0)
            return Image(buf, width=9.6*inch, height=3.0*inch)

    def create_wind_chart(self, data, date_key='datetime_obj',
                              xlabel_text='Date/Time', ylabel_text='Speed (knots)',
                              title_text='Wind Speed and Gust Trend',
                              speed_label='Wind Speed', gust_label='Wind Gust', limit_xticks=False):
            if not data:
                print("Warning: No data provided for wind chart.")
                return None

            plt.figure(figsize=(9.0, 2.8))
            dates = []
            speeds = []
            gusts = []

            for item in data:
                item_date = item.get(date_key)
                speed_val = item.get('wind_speed')
                gust_val = item.get('wind_gust')

                if isinstance(item_date, datetime):
                    dates.append(item_date)
                    try:
                        speeds.append(float(speed_val) if speed_val not in [
                                      None, 'N/A'] else math.nan)
                    except (ValueError, TypeError):
                        speeds.append(math.nan)
                    try:
                        gusts.append(float(gust_val) if gust_val not in [
                                     None, 'N/A'] else math.nan)
                    except (ValueError, TypeError):
                        gusts.append(math.nan)

            if not dates or (all(math.isnan(s) for s in speeds) and all(math.isnan(g) for g in gusts)):
                print("Warning: No valid numeric data points found for wind chart.")
                plt.close()
                return None

            try:
                line1, = plt.plot(dates, speeds, marker='.', linestyle='-',
                                  markersize=4, linewidth=1, label=speed_label)
                line2, = plt.plot(dates, gusts, marker='.', linestyle='-', markersize=4,
                                  linewidth=1, color='orange', label=gust_label)

                plt.title(title_text, fontsize=10)
                plt.xlabel(xlabel_text, fontsize=9)
                plt.ylabel(ylabel_text, fontsize=9)
                plt.xticks(rotation=30, ha='right', fontsize=9)
                plt.yticks(fontsize=9)
                plt.legend(fontsize=8)

                plt.gca().xaxis.set_major_locator(mdates.HourLocator(
                    byhour=[7], tz=dates[0].tzinfo if dates else None))
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter(
                    '%m-%d %H:%M', tz=dates[0].tzinfo if dates else None))

                plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
                plt.tight_layout(pad=0.5)

                img_buffer = BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                plt.close()
                img_buffer.seek(0)

                img = Image(img_buffer, width=9.6*inch, height=3.6*inch)
                img.hAlign = 'CENTER'
                return img

            except Exception as chart_err:
                print(f"Error during wind chart plotting: {chart_err}")
                print(traceback.format_exc())
                plt.close()
                return None

    def create_temp_humidity_chart(self, data, date_key='datetime_obj',
                                       xlabel_text='Date/Time', temp_ylabel='Temperature (°C)',
                                       hum_ylabel='Humidity (%)', title_text='Temperature and Humidity Trend',
                                       temp_label='Temperature', hum_label='Humidity', limit_xticks=False):
            if not data:
                print("Warning: No data provided for Temp/Humidity chart.")
                return None

            fig, ax1 = plt.subplots(figsize=(9.0, 2.8))

            dates = []
            temps = []
            humidity = []

            for item in data:
                item_date = item.get(date_key)
                temp_val = item.get('temperature')
                hum_val = item.get('humidity')

                if isinstance(item_date, datetime):
                    dates.append(item_date)
                    try:
                        temps.append(float(temp_val) if temp_val not in [
                                     None, 'N/A'] else math.nan)
                    except (ValueError, TypeError):
                        temps.append(math.nan)
                    try:
                        humidity.append(float(hum_val) if hum_val not in [
                                        None, 'N/A'] else math.nan)
                    except (ValueError, TypeError):
                        humidity.append(math.nan)

            if not dates or (all(math.isnan(t) for t in temps) and
                             all(math.isnan(h) for h in humidity)):
                print("Warning: No valid numeric data points found for Temp/Humidity chart.")
                plt.close(fig)
                return None

            try:
                color_temp = 'tab:blue'
                ax1.set_xlabel(xlabel_text, fontsize=9)
                ax1.set_ylabel(temp_ylabel, color=color_temp,
                               fontsize=9)
                ax1.tick_params(axis='x', rotation=30, labelsize=9)

                ax1.xaxis.set_major_locator(mdates.HourLocator(
                    byhour=[7], tz=dates[0].tzinfo if dates else None))
                ax1.xaxis.set_major_formatter(mdates.DateFormatter(
                    '%m-%d %H:%M', tz=dates[0].tzinfo if dates else None))

                line1, = ax1.plot(dates, temps, marker='.', linestyle='-',
                                  markersize=4, linewidth=1, color=color_temp, label=temp_label)

                ax2 = ax1.twinx()
                color_hum = 'orange'
                ax2.set_ylabel(hum_ylabel, color=color_hum,
                               fontsize=9)
                line2, = ax2.plot(dates, humidity, marker='.', linestyle='-',
                                  markersize=4, linewidth=1, color=color_hum, label=hum_label)
                ax2.tick_params(axis='y', labelcolor=color_hum, labelsize=9)

                lines = [line1, line2]
                ax1.legend(lines, [l.get_label()
                           for l in lines], loc='upper left', fontsize=8)

                plt.title(title_text, fontsize=10)
                ax1.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)

                fig.tight_layout(pad=0.5)

                for label in ax1.get_xticklabels():
                    label.set_horizontalalignment('right')

                img_buffer = BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                plt.close(fig)
                img_buffer.seek(0)

                img = Image(img_buffer, width=9.6*inch, height=3.6*inch)
                img.hAlign = 'CENTER'
                return img
            except Exception as chart_err:
                print(f"Error during Temp/Humidity chart plotting: {chart_err}")
                print(traceback.format_exc())
                plt.close(fig)
                return None

    def create_rain_pop_chart(self, data, date_key='datetime_obj',
                                  xlabel_text='Date/Time', rain_ylabel='Rainfall (mm/h)',
                                  pop_ylabel='Probability of Precipitation (%)',
                                  title_text='Rainfall and Precipitation Probability Trend',
                                  rain_label='Rainfall', pop_label='PoP'):
            if not data:
                print("Warning: No data provided for Rain/PoP chart.")
                return None

            fig, ax1 = plt.subplots(figsize=(9.0, 2.8))

            dates = []
            rains = []
            pops = []

            for item in data:
                item_date = item.get(date_key)
                rain_val = item.get('rain')
                pop_val = item.get('pop')

                if isinstance(item_date, datetime):
                    dates.append(item_date)
                    try:
                        rains.append(float(rain_val) if rain_val not in [
                                     None, 'N/A'] else math.nan)
                    except (ValueError, TypeError):
                        rains.append(math.nan)
                    try:
                        pops.append(float(pop_val) if pop_val not in [
                                    None, 'N/A'] else math.nan)
                    except (ValueError, TypeError):
                        pops.append(math.nan)

            if not dates or (all(math.isnan(r) for r in rains) and all(math.isnan(p) for p in pops)):
                print("Warning: No valid numeric data points found for Rain/PoP chart.")
                plt.close(fig)
                return None

            try:
                color_rain = 'tab:blue'
                ax1.set_xlabel(xlabel_text, fontsize=9)
                ax1.set_ylabel(rain_ylabel, color=color_rain,
                               fontsize=9)
                ax1.tick_params(axis='y', labelcolor=color_rain, labelsize=9)
                ax1.tick_params(axis='x', rotation=30, labelsize=9)

                ax1.xaxis.set_major_locator(mdates.HourLocator(
                    byhour=[7], tz=dates[0].tzinfo if dates else None))
                ax1.xaxis.set_major_formatter(mdates.DateFormatter(
                    '%m-%d %H:%M', tz=dates[0].tzinfo if dates else None))

                line1, = ax1.plot(dates, rains, marker='.', linestyle='-',
                                  markersize=4, linewidth=1, color=color_rain, label=rain_label)

                ax2 = ax1.twinx()
                color_pop = 'orange'
                ax2.set_ylabel(pop_ylabel, color=color_pop,
                               fontsize=9)
                line2, = ax2.plot(dates, pops, marker='.', linestyle='-',
                                  markersize=4, linewidth=1, color=color_pop, label=pop_label)
                ax2.tick_params(axis='y', labelcolor=color_pop, labelsize=9)
                ax2.set_ylim(0, 105)

                lines = [line1, line2]
                ax1.legend(lines, [l.get_label()
                           for l in lines], loc='upper left', fontsize=8)

                plt.title(title_text, fontsize=10)
                ax1.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)

                fig.tight_layout(pad=0.5)

                for label in ax1.get_xticklabels():
                    label.set_horizontalalignment('right')

                img_buffer = BytesIO()
                plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
                plt.close(fig)
                img_buffer.seek(0)

                img = Image(img_buffer, width=9.6*inch, height=3.6*inch)
                img.hAlign = 'CENTER'
                return img

            except Exception as chart_err:
                print(f"Error during Rain/PoP chart plotting: {chart_err}")
                print(traceback.format_exc())
                plt.close(fig)
                return None

    def create_combined_wave_chart(self, data, date_key='datetime_obj',
                                       xlabel_text='Date/Time',
                                       height_ylabel='Height (m)',
                                       period_ylabel='Period (s)',
                                       height_title='Wave & Swell Height Trend',
                                       period_title='Wave & Swell Period Trend',
                                       wave_height_label='Wave Height',
                                       swell_height_label='Swell Height',
                                       wave_period_label='Wave Period',
                                       swell_period_label='Swell Period'):
            if not data:
                print("Warning: No data provided for combined wave chart.")
                return None, None

            # Prepare data
            dates = []
            wave_heights = []
            swell_heights = []
            wave_periods = []
            swell_periods = []

            for item in data:
                item_date = item.get(date_key)
                if isinstance(item_date, datetime):
                    dates.append(item_date)
                    try:
                        wave_heights.append(float(item.get('wave_height')) if item.get(
                            'wave_height') not in [None, 'N/A'] else math.nan)
                    except (ValueError, TypeError):
                        wave_heights.append(math.nan)
                    try:
                        swell_heights.append(float(item.get('swell_wave_height')) if item.get(
                            'swell_wave_height') not in [None, 'N/A'] else math.nan)
                    except (ValueError, TypeError):
                        swell_heights.append(math.nan)
                    try:
                        wave_periods.append(float(item.get('wave_period')) if item.get(
                            'wave_period') not in [None, 'N/A'] else math.nan)
                    except (ValueError, TypeError):
                        wave_periods.append(math.nan)
                    try:
                        swell_periods.append(float(item.get('swell_wave_period')) if item.get(
                            'swell_wave_period') not in [None, 'N/A'] else math.nan)
                    except (ValueError, TypeError):
                        swell_periods.append(math.nan)

            # --- Height Chart ---
            height_img = None
            if dates and (any(not math.isnan(h) for h in wave_heights) or any(not math.isnan(h) for h in swell_heights)):
                plt.figure(figsize=(9.0, 2.8))
                plt.plot(dates, wave_heights, marker='.', linestyle='-', markersize=4,
                         linewidth=1.8, color='#0077be', label=wave_height_label)
                plt.plot(dates, swell_heights, marker='.', linestyle='-', markersize=4,
                         linewidth=1.8, color='orange', label=swell_height_label)
                plt.title(height_title, fontsize=10)
                plt.xlabel(xlabel_text, fontsize=9)
                plt.ylabel(height_ylabel, fontsize=9)
                plt.xticks(rotation=30, ha='right', fontsize=9)
                plt.yticks(fontsize=9)
                plt.legend(fontsize=8)
                plt.gca().xaxis.set_major_locator(mdates.HourLocator(
                    byhour=[7], tz=dates[0].tzinfo if dates else None))
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter(
                    '%m-%d %H:%M', tz=dates[0].tzinfo if dates else None))
                plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
                plt.tight_layout(pad=0.5)
                buf = BytesIO()
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                plt.close()
                buf.seek(0)
                height_img = Image(buf, width=9.6*inch, height=3.0*inch)
                height_img.hAlign = 'CENTER'

            # --- Period Chart ---
            period_img = None
            if dates and (any(not math.isnan(p) for p in wave_periods) or any(not math.isnan(p) for p in swell_periods)):
                plt.figure(figsize=(9.0, 2.8))
                plt.plot(dates, wave_periods, marker='.', linestyle='-', markersize=4,
                         linewidth=1.8, color='#0077be', label=wave_period_label)
                plt.plot(dates, swell_periods, marker='.', linestyle='-', markersize=4,
                         linewidth=1.8, color='orange', label=swell_period_label)
                plt.title(period_title, fontsize=10)
                plt.xlabel(xlabel_text, fontsize=9)
                plt.ylabel(period_ylabel, fontsize=9)
                plt.xticks(rotation=30, ha='right', fontsize=9)
                plt.yticks(fontsize=9)
                plt.legend(fontsize=8)
                plt.gca().xaxis.set_major_locator(mdates.HourLocator(
                    byhour=[7], tz=dates[0].tzinfo if dates else None))
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter(
                    '%m-%d %H:%M', tz=dates[0].tzinfo if dates else None))
                plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
                plt.tight_layout(pad=0.5)
                buf = BytesIO()
                plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                plt.close()
                buf.seek(0)
                period_img = Image(buf, width=9.6*inch, height=3.0*inch)
                period_img.hAlign = 'CENTER'

            return height_img, period_img

    def generate_pdf_report(self, lat, lon, weather_data, location_info, ui_location_name, api_source, marine_data=None, precipitation_map=None):
            page_width, page_height = landscape(letter)

            file_name_location = re.sub(
                r'[\\/*?:"<>|()]+', "", ui_location_name).replace(' ', '_')
            file_name = f"Weather_Report_{api_source}_{file_name_location}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

            doc = SimpleDocTemplate(
                file_name,
                pagesize=(page_width, page_height),
                topMargin=0.5*inch, bottomMargin=0.4*inch,
                leftMargin=0.5*inch, rightMargin=0.5*inch
            )

            elements = []
            styles = getSampleStyleSheet()

            title_style = styles['h1']
            title_style.alignment = 1
            title_style.fontSize = 18
            h2_style = styles['h2']
            h2_style.alignment = 0
            h2_style.fontSize = 14
            h2_style.spaceBefore = 15
            h2_style.spaceAfter = 4
            normal_style = styles['Normal']
            normal_style.leading = 15
            normal_style.fontSize = 11
            small_note_style = styles['Normal'].clone('SmallNote')
            small_note_style.fontSize = 9
            small_note_style.leading = 10
            small_note_style.textColor = colors.dimgray
            footer_style = small_note_style.clone('Footer')
            footer_style.alignment = 1
            footer_style.fontSize = 8

            elements.append(Paragraph("Weather Forecast Report", title_style))
            elements.append(Spacer(1, 0.2*inch))

            # Add location image if available (for dashboard locations)
            image_path = resource_path(os.path.join(
                "Pictures", ui_location_name.replace(" ", "_") + ".png"))
            if os.path.exists(image_path):
                try:
                    img = Image(image_path, width=5.6*inch, height=2.8*inch)
                    img.hAlign = 'CENTER'
                    elements.append(img)
                    elements.append(Spacer(1, 0.08*inch))
                except Exception as img_err:
                    print(f"Could not add image for {ui_location_name}: {img_err}")

            elements.append(Spacer(1, 0.1*inch))
            api_name = location_info.get('name', '')
            country_code = location_info.get('country', 'N/A')

            api_details_parts = []
            if api_name and api_name != ui_location_name and not api_name.startswith("Coords ("):
                api_details_parts.append(api_name)
            if country_code and country_code != 'N/A':
                api_details_parts.append(country_code)

            location_string = f"<b>Location:</b> {ui_location_name}"
            if api_details_parts:
                api_details = ", ".join(api_details_parts)
                location_string += f" ({api_details})"

            elements.append(Paragraph(location_string, normal_style))
            elements.append(
                Paragraph(f"<b>Coordinates:</b> Lat: {lat:.4f}, Lon: {lon:.4f}", normal_style))
            elements.append(Paragraph(
                f"<b>Timezone:</b> {location_info.get('timezone', DEFAULT_TIMEZONE)}", normal_style))
            elements.append(Paragraph(
                f"<b>Sunrise:</b> {location_info.get('sunrise', 'N/A')}, <b>Sunset:</b> {location_info.get('sunset', 'N/A')}", normal_style))
            elements.append(Paragraph(
                f"<b>Report Generated:</b> {datetime.now(pytz.timezone(location_info.get('timezone', DEFAULT_TIMEZONE))).strftime('%Y-%m-%d %H:%M:%S %Z')}", normal_style))
            elements.append(
                Paragraph(f"<b>Data Source:</b> {api_source}", normal_style))
            elements.append(Spacer(1, 0.2*inch))

            if weather_data:
                # Set forecast section header based on data source
                if api_source == "OpenMeteo":
                    forecast_header = "Weather Forecast (Next 14 Days Hourly)"
                else:
                    forecast_header = "Weather Forecast (Next 5 Days 03-Hourly)"
                elements.append(
                    Paragraph(forecast_header, h2_style))

                # --- BEGIN: Add summary section ---
                temp_vals = [item.get('temperature') for item in weather_data if isinstance(
                    item.get('temperature'), (int, float))]
                wind_vals = [item.get('wind_speed') for item in weather_data if isinstance(
                    item.get('wind_speed'), (int, float))]
                rain_vals = [item.get('rain') for item in weather_data if isinstance(
                    item.get('rain'), (int, float))]
                uv_vals = [item.get('uv_index') for item in weather_data if isinstance(
                    item.get('uv_index'), (int, float))]

                temp_min = f"{min(temp_vals):.1f}°C" if temp_vals else "N/A"
                temp_max = f"{max(temp_vals):.1f}°C" if temp_vals else "N/A"
                wind_min = f"{min(wind_vals):.1f} knots" if wind_vals else "N/A"
                wind_max = f"{max(wind_vals):.1f} knots" if wind_vals else "N/A"
                rain_max = f"{max(rain_vals):.1f} mm/h" if rain_vals else "N/A"
                uv_max = f"{max(uv_vals):.1f}" if uv_vals else "N/A"

                summary_text = (
                    f"<b>Summary:</b><br/>"
                    f"<b>Temperature</b>: {temp_min} - {temp_max}<br/>"
                    f"<b>Wind Speed</b>: {wind_min} - {wind_max}<br/>"
                    f"<b>Rain</b>: Max {rain_max}<br/>"
                    f"<b>UV Index</b>: Max {uv_max}"
                )
                elements.append(Paragraph(summary_text, normal_style))
                elements.append(Spacer(1, 0.08*inch))
                # --- END: Add summary section ---

                col_params = {
                    'datetime': {'header': "Date/Time", 'format': lambda x: x, 'width': 1.28*inch, 'align': 'CENTER'},
                    'description': {'header': "Description", 'format': lambda x: x, 'width': 2.1*inch, 'align': 'CENTER'},
                    'temperature': {'header': "Temp\n(°C)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.72*inch, 'align': 'RIGHT'},
                    'humidity': {'header': "Humidity\n(%)", 'format': lambda x: f"{x:.0f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.8*inch, 'align': 'RIGHT'},
                    'wind_speed': {'header': "Wind Speed\n(knots)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1*inch, 'align': 'RIGHT'},
                    'wind_gust': {'header': "Wind Gust\n(knots)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.96*inch, 'align': 'RIGHT'},
                    'wind_direction': {'header': "Wind\nDir", 'format': lambda x: x, 'width': 0.72*inch, 'align': 'CENTER'},
                    'rain': {'header': "Rain\n(mm/h)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.75*inch, 'align': 'RIGHT'},
                    'pop': {'header': "PoP\n(%)", 'format': lambda x: f"{x:.0f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.72*inch, 'align': 'RIGHT'},
                    'uv_index': {'header': "UV\nIndex", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 0.72*inch, 'align': 'RIGHT'},
                }

                weather_headers = ["Date/Time", "Description", "Temp\n(°C)", "Humidity\n(%)",
                                   "Wind Speed\n(knots)", "Wind Gust\n(knots)", "Wind\nDir",
                                   "Rain\n(mm/h)", "PoP\n(%)", "UV\nIndex"]
                weather_col_widths = [1.28*inch, 2.1*inch, 0.72*inch, 0.8*inch,
                                      1*inch, 0.96*inch, 0.72*inch, 0.75*inch, 0.72*inch, 0.72*inch]

                param_to_col_index = {
                    'temperature': 2, 'humidity': 3, 'wind_speed': 4, 'wind_gust': 5,
                    'rain': 7, 'pop': 8, 'uv_index': 9
                }
                numeric_data_for_highlight = {p: []
                                              for p in param_to_col_index.keys()}

                weather_table_data = [weather_headers]

                max_entries_for_table = 14 * 24

                for row_idx, item in enumerate(weather_data[:max_entries_for_table]):
                    uv_index_formatted = col_params['uv_index']['format'](
                        item.get('uv_index'))
                    temp_formatted = col_params['temperature']['format'](
                        item.get('temperature'))
                    hum_formatted = col_params['humidity']['format'](
                        item.get('humidity'))
                    wind_formatted = col_params['wind_speed']['format'](
                        item.get('wind_speed'))
                    gust_formatted = col_params['wind_gust']['format'](
                        item.get('wind_gust'))
                    rain_formatted = col_params['rain']['format'](item.get('rain'))
                    pop_formatted = col_params['pop']['format'](item.get('pop'))

                    row = [
                        item['datetime'],
                        item['description'],
                        temp_formatted,
                        hum_formatted,
                        wind_formatted,
                        gust_formatted,
                        item['wind_direction'],
                        rain_formatted,
                        pop_formatted,
                        uv_index_formatted
                    ]
                    weather_table_data.append(row)

                    table_row_index = row_idx + 1
                    for param, value in [('temperature', item.get('temperature')),
                                         ('humidity', item.get('humidity')),
                                         ('wind_speed', item.get('wind_speed')),
                                         ('wind_gust', item.get('wind_gust')),
                                         ('rain', item.get('rain')),
                                         ('pop', item.get('pop')),
                                         ('uv_index', item.get('uv_index'))]:
                        if param in numeric_data_for_highlight and isinstance(value, (int, float)) and not math.isnan(value):
                            numeric_data_for_highlight[param].append(
                                (value, table_row_index))

                weather_table = Table(weather_table_data,
                                      repeatRows=1, colWidths=weather_col_widths)
                weather_style_cmds = [('BACKGROUND', (0, 0), (-1, 0), colors.darkblue), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 11), ('BOTTOMPADDING', (0, 0), (-1, 0), 8), ('TOPPADDING', (0, 0), (-1, 0), 6), ('FONTNAME',
                                                                                                                                                                                                                                                                                                                                                                                          (0, 1), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 1), (-1, -1), 9.5), ('TOPPADDING', (0, 1), (-1, -1), 5), ('BOTTOMPADDING', (0, 1), (-1, -1), 5), ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('ALIGN', (2, 1), (3, -1), 'RIGHT'), ('ALIGN', (4, 1), (5, -1), 'RIGHT'), ('ALIGN', (7, 1), (9, -1), 'RIGHT'), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightblue])]
                for param, data_points in numeric_data_for_highlight.items():
                    if data_points:
                        col_idx = param_to_col_index[param]
                        min_val, min_row_idx = min(data_points, key=lambda x: x[0])
                        max_val, max_row_idx = max(data_points, key=lambda x: x[0])
                        weather_style_cmds.append(
                            ('BACKGROUND', (col_idx, min_row_idx), (col_idx, min_row_idx), colors.cyan))
                        weather_style_cmds.append(
                            ('BACKGROUND', (col_idx, max_row_idx), (col_idx, max_row_idx), colors.pink))
                weather_table.setStyle(TableStyle(weather_style_cmds))
                elements.append(weather_table)
                elements.append(Spacer(1, 0.1*inch))
                note_text = "Note: 1 knot = 1.85 km/h; Wind Dir = Wind Direction; PoP = Probability of Precipitation (hourly)."
                elements.append(Paragraph(note_text, small_note_style))
                elements.append(Spacer(1, 0.15*inch))
            else:
                elements.append(
                    Paragraph("Weather Forecast Data Not Available", h2_style))
                elements.append(Spacer(1, 0.15*inch))

            if weather_data:
                elements.append(Paragraph("Weather Parameter Charts", h2_style))

                temp_hum_chart = self.create_temp_humidity_chart(
                    weather_data)
                if temp_hum_chart:
                    elements.append(temp_hum_chart)
                    elements.append(Spacer(1, 0.1*inch))

                wind_chart = self.create_wind_chart(weather_data)
                if wind_chart:
                    elements.append(wind_chart)
                    elements.append(Spacer(1, 0.1*inch))

                rain_pop_chart = self.create_rain_pop_chart(
                    weather_data)
                if rain_pop_chart:
                    elements.append(rain_pop_chart)
                    elements.append(Spacer(1, 0.1*inch))

                cloud_chart = self.create_chart(
                    weather_data, 'cloud_cover', 'Cloud Cover (%)', 'Cloud Cover Trend')
                if cloud_chart:
                    elements.append(cloud_chart)
                    elements.append(Spacer(1, 0.1*inch))

                uv_chart = self.create_chart(
                    weather_data, 'uv_index', 'UV Index', 'UV Index Trend')
                if uv_chart:
                    elements.append(uv_chart)
                    elements.append(Spacer(1, 0.1*inch))

                charts_added = sum(1 for chart in [
                                   temp_hum_chart, wind_chart, rain_pop_chart,
                                   cloud_chart, uv_chart] if chart)  # Updated sum
                if charts_added == 0:
                    elements.append(
                        Paragraph("No data available to generate weather charts.", normal_style))
                elements.append(Spacer(1, 0.1*inch))

            # --- NEW: Marine Forecast Section (for Open-Meteo only, specific locations) ---
            if api_source == "OpenMeteo" and marine_data:
                elements.append(
                    Paragraph("Marine Forecast (Next 14 Days Hourly)", h2_style))

                # --- BEGIN: Marine summary section (English) ---
                wave_heights = [item.get('wave_height') for item in marine_data if isinstance(
                    item.get('wave_height'), (int, float))]
                wave_periods = [item.get('wave_period') for item in marine_data if isinstance(
                    item.get('wave_period'), (int, float))]
                swell_heights = [item.get('swell_wave_height') for item in marine_data if isinstance(
                    item.get('swell_wave_height'), (int, float))]
                swell_periods = [item.get('swell_wave_period') for item in marine_data if isinstance(
                    item.get('swell_wave_period'), (int, float))]
                wave_min = f"{min(wave_heights):.2f} m" if wave_heights else "N/A"
                wave_max = f"{max(wave_heights):.2f} m" if wave_heights else "N/A"
                wave_period_min = f"{min(wave_periods):.2f} s" if wave_periods else "N/A"
                wave_period_max = f"{max(wave_periods):.2f} s" if wave_periods else "N/A"
                swell_min = f"{min(swell_heights):.2f} m" if swell_heights else "N/A"
                swell_max = f"{max(swell_heights):.2f} m" if swell_heights else "N/A"
                swell_period_min = f"{min(swell_periods):.2f} s" if swell_periods else "N/A"
                swell_period_max = f"{max(swell_periods):.2f} s" if swell_periods else "N/A"
                marine_summary = (
                    f"<b>Summary:</b><br/> "
                    f"<b>Wave height</b>: {wave_min} - {wave_max}<br/>"
                    f"<b>Swell wave height</b>: {swell_min} - {swell_max}<br/>"
                    f"<b>Wave period</b>: {wave_period_min} - {wave_period_max}<br/>"
                    f"<b>Swell wave period</b>: {swell_period_min} - {swell_period_max}"
                )
                elements.append(Paragraph(marine_summary, normal_style))
                elements.append(Spacer(1, 0.08*inch))

                # Remove sea level, wind wave height, wind wave direction, wind wave period
                marine_col_params = {
                    'datetime': {'header': "Date/Time", 'format': lambda x: x, 'width': 1.5*inch, 'align': 'CENTER'},
                    'wave_height': {'header': "Wave Height\n(m)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1*inch, 'align': 'RIGHT'},
                    'wave_direction': {'header': "Wave Dir", 'format': lambda x: x, 'width': 0.9*inch, 'align': 'CENTER'},
                    'wave_period': {'header': "Wave Period\n(s)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1*inch, 'align': 'RIGHT'},
                    'swell_wave_height': {'header': "Swell Wave Height\n(m)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1*inch, 'align': 'RIGHT'},
                    'swell_wave_direction': {'header': "Swell Wave Dir", 'format': lambda x: x, 'width': 0.9*inch, 'align': 'CENTER'},
                    'swell_wave_period': {'header': "Swell Wave Period\n(s)", 'format': lambda x: f"{x:.1f}" if isinstance(x, (int, float)) else 'N/A', 'width': 1*inch, 'align': 'RIGHT'},
                }
                marine_headers = [
                    "Date/Time", "Wave Height\n(m)", "Wave\nDir", "Wave Period\n(s)",
                    "Swell Wave Height\n(m)", "Swell Wave\nDir", "Swell Wave Period\n(s)"
                ]
                marine_col_widths = [1.5*inch, 1.1*inch, 0.9 *
                                     inch, 1.1*inch, 1.5*inch, 1.1*inch, 1.5*inch]

                marine_table_data = [marine_headers]
                marine_numeric_data_for_highlight = {
                    'wave_height': [], 'wave_period': [],
                    'swell_wave_height': [], 'swell_wave_period': []
                }
                marine_param_to_col_index = {
                    'wave_height': 1, 'wave_period': 3,
                    'swell_wave_height': 4, 'swell_wave_period': 6
                }

                for row_idx, item in enumerate(marine_data):
                    row = [
                        item['datetime'],
                        marine_col_params['wave_height']['format'](
                            item.get('wave_height')),
                        marine_col_params['wave_direction']['format'](
                            item.get('wave_direction')),
                        marine_col_params['wave_period']['format'](
                            item.get('wave_period')),
                        marine_col_params['swell_wave_height']['format'](
                            item.get('swell_wave_height')),
                        marine_col_params['swell_wave_direction']['format'](
                            item.get('swell_wave_direction')),
                        marine_col_params['swell_wave_period']['format'](
                            item.get('swell_wave_period')),
                    ]
                    marine_table_data.append(row)

                    table_row_index = row_idx + 1
                    for param in marine_numeric_data_for_highlight.keys():
                        value = item.get(param)
                        if isinstance(value, (int, float)) and not math.isnan(value):
                            marine_numeric_data_for_highlight[param].append(
                                (value, table_row_index))

                if len(marine_table_data) > 1:
                    marine_table = Table(
                        marine_table_data, repeatRows=1, colWidths=marine_col_widths)
                    marine_style_cmds = [
                        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 11),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('TOPPADDING', (0, 0), (-1, 0), 6),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 9.5),
                        ('TOPPADDING', (0, 1), (-1, -1), 5),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                         [colors.whitesmoke, colors.lightblue])
                    ]
                    for param, data_points in marine_numeric_data_for_highlight.items():
                        if data_points:
                            col_idx = marine_param_to_col_index[param]
                            min_val, min_row_idx = min(
                                data_points, key=lambda x: x[0])
                            max_val, max_row_idx = max(
                                data_points, key=lambda x: x[0])
                            marine_style_cmds.append(
                                ('BACKGROUND', (col_idx, min_row_idx), (col_idx, min_row_idx), colors.cyan))
                            marine_style_cmds.append(
                                ('BACKGROUND', (col_idx, max_row_idx), (col_idx, max_row_idx), colors.pink))
                    marine_table.setStyle(TableStyle(marine_style_cmds))
                    elements.append(marine_table)
                    elements.append(Spacer(1, 0.1*inch))
                    elements.append(Paragraph(
                        "Note: Wave Dir = Direction waves are coming from.", small_note_style))
                    elements.append(Spacer(1, 0.15*inch))

                    elements.append(Paragraph("Marine Parameter Charts", h2_style))

                    # Combined Wave & Swell Height Chart
                    height_img, period_img = self.create_combined_wave_chart(
                        marine_data,
                        xlabel_text='Date/Time',
                        height_ylabel='Height (m)',
                        period_ylabel='Period (s)',
                        height_title='Wave & Swell Height Trend',
                        period_title='Wave & Swell Period Trend',
                        wave_height_label='Wave Height',
                        swell_height_label='Swell Height',
                        wave_period_label='Wave Period',
                        swell_period_label='Swell Period'
                    )
                    if height_img:
                        elements.append(height_img)
                        elements.append(Spacer(1, 0.1*inch))
                    if period_img:
                        elements.append(period_img)
                        elements.append(Spacer(1, 0.1*inch))
                else:
                    elements.append(Paragraph(
                        "Marine Forecast Data Not Available for this location or period.", normal_style))
                elements.append(Spacer(1, 0.1*inch))
            # --- END Marine Forecast Section ---

            # --- Precipitation Map Section ---
            if precipitation_map:
                elements.append(Spacer(1, 0.2*inch))
                elements.append(Paragraph("Precipitation Map",
                                getSampleStyleSheet()['h2']))
                elements.append(precipitation_map)

            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("--- End of Report ---", footer_style))
            if api_source == "OWM":
                elements.append(
                    Paragraph("Weather data © OpenWeatherMap", footer_style))
            elif api_source == "OpenMeteo":
                elements.append(
                    Paragraph("Weather data, Marine data © Open-Meteo.com", footer_style))  # Updated footer
            elements.append(
                Paragraph("Generated by Weather Reporter Tool | 2025 © TungTT", footer_style))

            try:
                doc.build(elements)
                print(f"PDF report generated: {file_name}")
            except Exception as build_err:
                print(f"Error building PDF: {build_err}")
                print(traceback.format_exc())
                print(
                    self, "PDF Error", f"Could not build PDF report:\n{build_err}")

    def generate_vietnamese_pdf_report(self, lat, lon, weather_data, location_info, ui_location_name, api_source, marine_data=None, precipitation_map=None):
            page_width, page_height = landscape(letter)

            name_map = {'Đ': 'D', 'đ': 'd'}
            safe_name = ui_location_name
            for k, v in name_map.items():
                safe_name = safe_name.replace(k, v)
            file_name_location = re.sub(
                r'[\\/*?:"<>|()]+', "", safe_name).replace(' ', '_')
            file_name = f"BaoCao_ThoiTiet_{api_source}_{file_name_location}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

            doc = SimpleDocTemplate(
                file_name,
                pagesize=(page_width, page_height),
                topMargin=0.5*inch, bottomMargin=0.4*inch,
                leftMargin=0.5*inch, rightMargin=0.5*inch
            )

            elements = []
            styles = getSampleStyleSheet()

            title_style = styles['h1']
            h2_style = styles['h2']
            normal_style = styles['Normal']
            small_note_style = styles['Normal'].clone('SmallNote')
            footer_style = small_note_style.clone('Footer')

            title_style.fontName = VIETNAMESE_FONT_NAME_BOLD
            title_style.alignment = 1
            title_style.fontSize = 18

            h2_style.fontName = VIETNAMESE_FONT_NAME_BOLD
            h2_style.alignment = 0
            h2_style.fontSize = 14
            h2_style.spaceBefore = 15
            h2_style.spaceAfter = 4

            normal_style.fontName = VIETNAMESE_FONT_NAME
            normal_style.leading = 15
            normal_style.fontSize = 11

            small_note_style.fontName = VIETNAMESE_FONT_NAME
            small_note_style.fontSize = 9
            small_note_style.leading = 10
            small_note_style.textColor = colors.dimgray

            footer_style.fontName = VIETNAMESE_FONT_NAME
            footer_style.alignment = 1
            footer_style.fontSize = 8

            elements.append(Paragraph("Báo Cáo Dự Báo Thời Tiết",
                            title_style))
            elements.append(Spacer(1, 0.2*inch))

            image_path = os.path.join(
                "Pictures", ui_location_name.replace(" ", "_") + ".png")
            if os.path.exists(image_path):
                try:
                    img = Image(image_path, width=5.6*inch, height=2.8*inch)
                    img.hAlign = 'CENTER'
                    elements.append(img)
                    elements.append(Spacer(1, 0.08*inch))
                except Exception as img_err:
                    print(f"Could not add image for {ui_location_name}: {img_err}")

            elements.append(Spacer(1, 0.1*inch))
            api_name = location_info.get('name', '')
            country_code = location_info.get('country', 'N/A')

            api_details_parts = []
            if api_name and api_name != ui_location_name and not api_name.startswith("Coords ("):
                api_details_parts.append(api_name)
            if country_code and country_code != 'N/A':
                api_details_parts.append(country_code)

            location_string = f'<font name="{VIETNAMESE_FONT_NAME_BOLD}">Vị trí:</font> {ui_location_name}'
            if api_details_parts:
                api_details = ", ".join(api_details_parts)
                location_string += f" ({api_details})"

            elements.append(Paragraph(location_string, normal_style))

            elements.append(Paragraph(
                f'<font name="{VIETNAMESE_FONT_NAME_BOLD}">Tọa độ:</font> Vĩ độ: {lat:.4f}, Kinh độ: {lon:.4f}', normal_style))
            elements.append(Paragraph(
                f'<font name="{VIETNAMESE_FONT_NAME_BOLD}">Múi giờ:</font> {location_info.get("timezone", DEFAULT_TIMEZONE)}', normal_style))
            elements.append(Paragraph(
                f'<font name="{VIETNAMESE_FONT_NAME_BOLD}">Mặt trời mọc:</font> {location_info.get("sunrise", "N/A")}, <font name="{VIETNAMESE_FONT_NAME_BOLD}">Mặt trời lặn:</font> {location_info.get("sunset", "N/A")}', normal_style))
            elements.append(Paragraph(
                f'<font name="{VIETNAMESE_FONT_NAME_BOLD}">Báo cáo tạo lúc:</font> {datetime.now(pytz.timezone(location_info.get("timezone", DEFAULT_TIMEZONE))).strftime("%Y-%m-%d %H:%M:%S %Z")}', normal_style))
            elements.append(Paragraph(
                f'<font name="{VIETNAMESE_FONT_NAME_BOLD}">Nguồn dữ liệu:</font> {api_source}', normal_style))
            elements.append(Spacer(1, 0.2*inch))

            if weather_data:
                # Set forecast section header based on data source
                if api_source == "OpenMeteo":
                    forecast_header_vn = "Dự Báo Thời Tiết (7 Ngày Tới Theo Giờ)"
                else:
                    forecast_header_vn = "Dự Báo Thời Tiết (5 Ngày Tới, Mỗi 3 Giờ)"
                elements.append(
                    Paragraph(forecast_header_vn, h2_style))

                # --- BEGIN: Add summary section (Vietnamese) ---
                temp_vals = [item.get('temperature') for item in weather_data if isinstance(
                    item.get('temperature'), (int, float))]
                wind_vals = [item.get('wind_speed') for item in weather_data if isinstance(
                    item.get('wind_speed'), (int, float))]
                rain_vals = [item.get('rain') for item in weather_data if isinstance(
                    item.get('rain'), (int, float))]
                uv_vals = [item.get('uv_index') for item in weather_data if isinstance(
                    item.get('uv_index'), (int, float))]

                temp_min = f"{min(temp_vals):.1f}°C" if temp_vals else "N/A"
                temp_max = f"{max(temp_vals):.1f}°C" if temp_vals else "N/A"
                wind_min = f"{min(wind_vals):.1f} knots" if wind_vals else "N/A"
                wind_max = f"{max(wind_vals):.1f} knots" if wind_vals else "N/A"
                rain_max = f"{max(rain_vals):.1f} mm/h" if rain_vals else "N/A"
                uv_max = f"{max(uv_vals):.1f}" if uv_vals else "N/A"

                summary_text_vn = (
                    f'<font name="{VIETNAMESE_FONT_NAME_BOLD}">Tóm tắt:</font><br/> '
                    f'Nhiệt độ: {temp_min} - {temp_max}<br/>'
                    f'Tốc độ gió: {wind_min} - {wind_max}<br/>'
                    f'Lượng mưa: lớn nhất {rain_max}<br/>'
                    f'Chỉ số UV: lớn nhất {uv_max}'
                )
                elements.append(Paragraph(summary_text_vn, normal_style))
                elements.append(Spacer(1, 0.08*inch))
                # --- END: Add summary section (Vietnamese) ---

                weather_headers = ["Ngày/Giờ", "Mô Tả", "Nhiệt Độ\n(°C)", "Độ Ẩm\n(%)", "Tốc độ gió\n(knots)",
                                   "Gió giật\n(knots)", "Hướng\ngió", "Lượng mưa\n(mm/h)", "XS mưa\n(%)", "Chỉ số\nUV"]
                weather_table_data = [weather_headers]

                numeric_data_for_highlight = {'temperature': [], 'wind_speed': [
                ], 'wind_gust': [], 'rain': [], 'uv_index': [], 'humidity': [], 'pop': []}
                param_to_col_index = {'temperature': 2, 'humidity': 3, 'wind_speed': 4,
                                      'wind_gust': 5, 'rain': 7, 'pop': 8, 'uv_index': 9}

                max_entries_for_table = 7 * 24

                for row_idx, item in enumerate(weather_data[:max_entries_for_table]):
                    eng_desc = item.get('description', 'N/A')
                    eng_wind_dir = item.get('wind_direction', 'N/A')
                    viet_desc = WEATHER_DESC_VIET.get(eng_desc, None)
                    if viet_desc is None:
                        for code, desc_en in WMO_WEATHER_CODES_EN.items():
                            if desc_en == eng_desc:
                                viet_desc = WMO_WEATHER_CODES_VIET.get(
                                    code, eng_desc)
                                break
                        if viet_desc is None:
                            viet_desc = eng_desc

                    viet_wind_dir = WIND_DIR_VIET.get(eng_wind_dir, eng_wind_dir)

                    uvi = item.get('uv_index', 'N/A')
                    uv_index_formatted = f"{item.get('uv_index'):.1f}" if isinstance(
                        item.get('uv_index'), (int, float)) else 'N/A'
                    temp_val = item.get('temperature', 'N/A')
                    temp_formatted = f"{temp_val:.1f}" if isinstance(
                        temp_val, (int, float)) else 'N/A'
                    hum_val = item.get('humidity', 'N/A')
                    hum_formatted = f"{hum_val:.0f}" if isinstance(
                        hum_val, (int, float)) else 'N/A'
                    wind_val = item.get('wind_speed', 'N/A')
                    wind_formatted = f"{wind_val:.1f}" if isinstance(
                        wind_val, (int, float)) else 'N/A'
                    gust_val = item.get('wind_gust', 'N/A')
                    gust_formatted = f"{gust_val:.1f}" if isinstance(
                        gust_val, (int, float)) else 'N/A'
                    rain_val = item.get('rain', 'N/A')
                    rain_formatted = f"{rain_val:.1f}" if isinstance(
                        rain_val, (int, float)) else 'N/A'
                    pop_val = item.get('pop', 'N/A')
                    pop_formatted = f"{pop_val:.0f}" if isinstance(
                        pop_val, (int, float)) else 'N/A'
                    row = [
                        item['datetime'],
                        viet_desc,
                        temp_formatted,
                        hum_formatted,
                        wind_formatted,
                        gust_formatted,
                        viet_wind_dir,
                        rain_formatted,
                        pop_formatted,
                        uv_index_formatted
                    ]
                    weather_table_data.append(row)

                    table_row_index = row_idx + 1
                    for param, value in [('temperature', temp_val), ('humidity', hum_val), ('wind_speed', wind_val), ('wind_gust', gust_val), ('rain', rain_val), ('pop', pop_val), ('uv_index', uvi)]:
                        if isinstance(value, (int, float)) and not math.isnan(value):
                            numeric_data_for_highlight[param].append(
                                (value, table_row_index))

                weather_col_widths = [1.45*inch, 1.75*inch, 0.75*inch, 0.8*inch,
                                      0.95*inch, 0.95*inch, 0.72*inch, 0.93*inch, 0.72*inch, 0.75*inch]
                weather_table = Table(weather_table_data,
                                      repeatRows=1, colWidths=weather_col_widths)
                weather_style_cmds = [('BACKGROUND', (0, 0), (-1, 0), colors.darkblue), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke), ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                      ('FONTNAME', (0, 0), (-1, -1),
                                       VIETNAMESE_FONT_NAME),
                                      ('FONTNAME', (0, 0), (-1, 0),
                                       VIETNAMESE_FONT_NAME_BOLD),
                                      ('FONTSIZE', (0, 0), (-1, 0), 11), ('BOTTOMPADDING',
                                                                          (0, 0), (-1, 0), 8), ('TOPPADDING', (0, 0), (-1, 0), 6),
                                      ('FONTSIZE', (0, 1), (-1, -1), 10), ('TOPPADDING', (0, 1),
                                                                           (-1, -1), 5), ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                                      ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), ('ALIGN', (2, 1), (3, -1), 'RIGHT'), ('ALIGN', (4, 1), (5, -1), 'RIGHT'), ('ALIGN', (7, 1), (9, -1), 'RIGHT'), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightblue])]
                for param, data_points in numeric_data_for_highlight.items():
                    if data_points:
                        col_idx = param_to_col_index[param]
                        min_val, min_row_idx = min(data_points, key=lambda x: x[0])
                        max_val, max_row_idx = max(data_points, key=lambda x: x[0])
                        weather_style_cmds.append(
                            ('BACKGROUND', (col_idx, min_row_idx), (col_idx, min_row_idx), colors.cyan))
                        weather_style_cmds.append(
                            ('BACKGROUND', (col_idx, max_row_idx), (col_idx, max_row_idx), colors.pink))
                weather_table.setStyle(TableStyle(weather_style_cmds))
                elements.append(weather_table)
                elements.append(Spacer(1, 0.1*inch))
                note_text_viet = "Ghi chú: 1 knot = 1.85 km/h; Hướng gió = Hướng gió thổi tới; XS mưa = Xác suất có mưa (được ước tính theo giờ dựa trên sự hiện diện của mưa/tuyết)."
                elements.append(Paragraph(note_text_viet, small_note_style))
                elements.append(Spacer(1, 0.15*inch))
            else:
                elements.append(
                    Paragraph("Không có dữ liệu dự báo thời tiết", h2_style))
                elements.append(Spacer(1, 0.15*inch))

            if weather_data:
                elements.append(
                    Paragraph("Biểu Đồ Thông Số Thời Tiết", h2_style))

                temp_hum_chart = self.create_temp_humidity_chart(
                    weather_data,
                    xlabel_text='Ngày/Giờ',
                    temp_ylabel='Nhiệt Độ (°C)',
                    hum_ylabel='Độ Ẩm (%)',
                    title_text='Xu Hướng Nhiệt Độ và Độ Ẩm',
                    temp_label='Nhiệt Độ',
                    hum_label='Độ Ẩm'
                )
                if temp_hum_chart:
                    elements.append(temp_hum_chart)
                    elements.append(Spacer(1, 0.1*inch))

                wind_chart = self.create_wind_chart(
                    weather_data,
                    xlabel_text='Ngày/Giờ',
                    ylabel_text='Tốc độ (knots)',
                    title_text='Xu Hướng Tốc Độ Gió và Gió Giật',
                    speed_label='Tốc độ gió',
                    gust_label='Gió giật'
                )
                if wind_chart:
                    elements.append(wind_chart)
                    elements.append(Spacer(1, 0.1*inch))

                rain_pop_chart = self.create_rain_pop_chart(
                    weather_data,
                    xlabel_text='Ngày/Giờ',
                    rain_ylabel='Lượng mưa (mm/h)',
                    pop_ylabel='Xác Suất Mưa (%)',
                    title_text='Xu Hướng Lượng Mưa và Xác Suất Mưa',
                    rain_label='Lượng mưa',
                    pop_label='XS Mưa'
                )
                if rain_pop_chart:
                    elements.append(rain_pop_chart)
                    elements.append(Spacer(1, 0.1*inch))

                cloud_chart = self.create_chart(
                    weather_data, 'cloud_cover', 'Mây che phủ (%)', 'Xu Hướng Mây Che Phủ',
                    xlabel_text='Ngày/Giờ')
                if cloud_chart:
                    elements.append(cloud_chart)
                    elements.append(Spacer(1, 0.1*inch))

                uv_chart = self.create_chart(
                    weather_data,
                    'uv_index',
                    'Chỉ số UV',
                    'Xu Hướng Chỉ Số UV',
                    xlabel_text='Ngày/Giờ'
                )
                if uv_chart:
                    elements.append(uv_chart)
                    elements.append(Spacer(1, 0.1*inch))

                charts_added = sum(1 for chart in [
                                   temp_hum_chart, wind_chart, rain_pop_chart,
                                   cloud_chart, uv_chart] if chart)
                if charts_added == 0:
                    elements.append(
                        Paragraph("Không có dữ liệu để tạo biểu đồ.", normal_style))
                elements.append(Spacer(1, 0.1*inch))

            # --- NEW: Marine Forecast Section (for Open-Meteo only, specific locations) in Vietnamese ---
            if api_source == "OpenMeteo" and marine_data:
                elements.append(
                    Paragraph("Dự Báo Biển (7 Ngày Tới Theo Giờ)", h2_style))

                # --- BEGIN: Marine summary section (Vietnamese) ---
                wave_heights = [item.get('wave_height') for item in marine_data if isinstance(
                    item.get('wave_height'), (int, float))]
                wave_periods = [item.get('wave_period') for item in marine_data if isinstance(
                    item.get('wave_period'), (int, float))]
                swell_heights = [item.get('swell_wave_height') for item in marine_data if isinstance(
                    item.get('swell_wave_height'), (int, float))]
                swell_periods = [item.get('swell_wave_period') for item in marine_data if isinstance(
                    item.get('swell_wave_period'), (int, float))]
                wave_min = f"{min(wave_heights):.2f} m" if wave_heights else "N/A"
                wave_max = f"{max(wave_heights):.2f} m" if wave_heights else "N/A"
                wave_period_min = f"{min(wave_periods):.2f} s" if wave_periods else "N/A"
                wave_period_max = f"{max(wave_periods):.2f} s" if wave_periods else "N/A"
                swell_min = f"{min(swell_heights):.2f} m" if swell_heights else "N/A"
                swell_max = f"{max(swell_heights):.2f} m" if swell_heights else "N/A"
                swell_period_min = f"{min(swell_periods):.2f} s" if swell_periods else "N/A"
                swell_period_max = f"{max(swell_periods):.2f} s" if swell_periods else "N/A"
                marine_summary_vn = (
                    f'<font name="{VIETNAMESE_FONT_NAME_BOLD}">Tóm tắt:</font><br/> '
                    f'Chiều cao sóng: {wave_min} - {wave_max}<br/>'
                    f'Chiều cao sóng trường: {swell_min} - {swell_max}<br/>'
                    f'Chu kỳ sóng: {wave_period_min} - {wave_period_max}<br/>'
                    f'Chu kỳ sóng trường: {swell_period_min} - {swell_period_max}'
                )
                elements.append(Paragraph(marine_summary_vn, normal_style))
                elements.append(Spacer(1, 0.08*inch))
                # --- END: Marine summary section (Vietnamese) ---

                marine_headers_viet = [
                    "Ngày/Giờ", "Chiều Cao Sóng\n(m)", "Hướng\nSóng", "Chu Kỳ Sóng\n(giây)",
                    "Chiều Cao\nSóng Trường (m)", "Hướng\nSóng Trường", "Chu Kỳ\nSóng Trường (giây)"
                ]
                marine_col_widths_viet = [1.5*inch, 1.28*inch,
                                          1.1*inch, 1.1*inch, 1.4*inch, 1.2*inch, 1.6*inch]

                marine_table_data_viet = [marine_headers_viet]
                marine_numeric_data_for_highlight_viet = {
                    'wave_height': [], 'wave_period': [],
                    'swell_wave_height': [], 'swell_wave_period': []
                }
                marine_param_to_col_index_viet = {
                    'wave_height': 1, 'wave_period': 3,
                    'swell_wave_height': 4, 'swell_wave_period': 6
                }

                for row_idx, item in enumerate(marine_data):
                    row = [
                        item['datetime'],
                        f"{item.get('wave_height'):.1f}" if isinstance(
                            item.get('wave_height'), (int, float)) else 'N/A',
                        WIND_DIR_VIET.get(item.get('wave_direction'),
                                          item.get('wave_direction')),
                        f"{item.get('wave_period'):.1f}" if isinstance(
                            item.get('wave_period'), (int, float)) else 'N/A',
                        f"{item.get('swell_wave_height'):.1f}" if isinstance(
                            item.get('swell_wave_height'), (int, float)) else 'N/A',
                        WIND_DIR_VIET.get(item.get('swell_wave_direction'), item.get(
                            'swell_wave_direction')),
                        f"{item.get('swell_wave_period'):.1f}" if isinstance(
                            item.get('swell_wave_period'), (int, float)) else 'N/A'
                    ]
                    marine_table_data_viet.append(row)

                    table_row_index = row_idx + 1
                    for param in marine_numeric_data_for_highlight_viet.keys():
                        value = item.get(param)
                        if isinstance(value, (int, float)) and not math.isnan(value):
                            marine_numeric_data_for_highlight_viet[param].append(
                                (value, table_row_index))

                if len(marine_table_data_viet) > 1:
                    marine_table_viet = Table(
                        marine_table_data_viet, repeatRows=1, colWidths=marine_col_widths_viet)
                    marine_style_cmds_viet = [
                        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('FONTNAME', (0, 0), (-1, -1), VIETNAMESE_FONT_NAME),
                        ('FONTNAME', (0, 0), (-1, 0), VIETNAMESE_FONT_NAME_BOLD),
                        ('FONTSIZE', (0, 0), (-1, 0), 11),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('TOPPADDING', (0, 0), (-1, 0), 6),
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('TOPPADDING', (0, 1), (-1, -1), 5),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
                        ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
                        ('ALIGN', (6, 1), (6, -1), 'RIGHT'),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                         [colors.whitesmoke, colors.lightblue])
                    ]
                    for param, data_points in marine_numeric_data_for_highlight_viet.items():
                        if data_points:
                            col_idx = marine_param_to_col_index_viet[param]
                            min_val, min_row_idx = min(
                                data_points, key=lambda x: x[0])
                            max_val, max_row_idx = max(
                                data_points, key=lambda x: x[0])
                            marine_style_cmds_viet.append(
                                ('BACKGROUND', (col_idx, min_row_idx), (col_idx, min_row_idx), colors.cyan))
                            marine_style_cmds_viet.append(
                                ('BACKGROUND', (col_idx, max_row_idx), (col_idx, max_row_idx), colors.pink))
                    marine_table_viet.setStyle(TableStyle(marine_style_cmds_viet))
                    elements.append(marine_table_viet)
                    elements.append(Spacer(1, 0.1*inch))
                    elements.append(
                        Paragraph("Ghi chú: Hướng sóng = Hướng sóng tới.", small_note_style))
                    elements.append(Spacer(1, 0.15*inch))

                    elements.append(Paragraph("Biểu Đồ Thông Số Biển", h2_style))
                    height_img, period_img = self.create_combined_wave_chart(
                        marine_data,
                        xlabel_text='Ngày/Giờ',
                        height_ylabel='Chiều Cao (m)',
                        period_ylabel='Chu Kỳ (giây)',
                        height_title='Xu Hướng Chiều Cao Sóng & Sóng Trường',
                        period_title='Xu Hướng Chu Kỳ Sóng & Sóng Trường',
                        wave_height_label='Chiều Cao Sóng',
                        swell_height_label='Chiều Cao Sóng Trường',
                        wave_period_label='Chu Kỳ Sóng',
                        swell_period_label='Chu Kỳ Sóng Trường'
                    )
                    if height_img:
                        elements.append(height_img)
                        elements.append(Spacer(1, 0.1*inch))
                    if period_img:
                        elements.append(period_img)
                        elements.append(Spacer(1, 0.1*inch))
                else:
                    elements.append(Paragraph(
                        "Không có dữ liệu dự báo biển cho vị trí hoặc thời gian này.", normal_style))
                elements.append(Spacer(1, 0.1*inch))
            # --- END Marine Forecast Section in Vietnamese ---

            # --- Precipitation Map Section (Vietnamese) ---
            if precipitation_map:
                elements.append(Spacer(1, 0.2*inch))
                h2_style_vn = getSampleStyleSheet()['h2']
                h2_style_vn.fontName = VIETNAMESE_FONT_NAME_BOLD
                elements.append(Paragraph("Bản Đồ Lượng Mưa", h2_style_vn))
                elements.append(precipitation_map)

            elements.append(Spacer(1, 0.2*inch))
            elements.append(Paragraph("--- Kết thúc báo cáo ---",
                            footer_style))
            if api_source == "OWM":
                elements.append(
                    Paragraph("Dữ liệu thời tiết © OpenWeatherMap", footer_style))
            elif api_source == "OpenMeteo":
                elements.append(
                    Paragraph("Dữ liệu thời tiết, Dữ liệu biển © Open-Meteo.com", footer_style))  # Updated footer
            elements.append(Paragraph(
                "Tạo bởi Weather Reporter Tool | 2025 © TungTT", footer_style))

            try:
                doc.build(elements)
                print(f"PDF report generated (Vietnamese): {file_name}")
            except Exception as build_err:
                print(f"Error building Vietnamese PDF: {build_err}")
                print(traceback.format_exc())
                print(
                    self, "Lỗi PDF", f"Không thể tạo báo cáo PDF (Tiếng Việt):\n{build_err}")

