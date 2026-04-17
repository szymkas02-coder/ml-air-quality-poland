import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

def read_openmeteo(lon,lat):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": "2016-01-01",
        "end_date": "2020-01-01",
        "daily": ["temperature_2m_min", "wind_speed_10m_max", "wind_direction_10m_dominant", "cloud_cover_mean", "surface_pressure_mean", "dew_point_2m_mean", "relative_humidity_2m_min", "wind_speed_10m_mean"],
        "hourly": "boundary_layer_height",
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation: {response.Elevation()} m asl")
    print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_boundary_layer_height = hourly.Variables(0).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}

    hourly_data["boundary_layer_height"] = hourly_boundary_layer_height

    hourly_dataframe = pd.DataFrame(data = hourly_data)
    print("\nHourly data\n", hourly_dataframe)

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_temperature_2m_min = daily.Variables(0).ValuesAsNumpy()
    daily_wind_speed_10m_max = daily.Variables(1).ValuesAsNumpy()
    daily_wind_direction_10m_dominant = daily.Variables(2).ValuesAsNumpy()
    daily_cloud_cover_mean = daily.Variables(3).ValuesAsNumpy()
    daily_surface_pressure_mean = daily.Variables(4).ValuesAsNumpy()
    daily_dew_point_2m_mean = daily.Variables(5).ValuesAsNumpy()
    daily_relative_humidity_2m_min = daily.Variables(6).ValuesAsNumpy()
    daily_wind_speed_10m_mean = daily.Variables(7).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
        end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = daily.Interval()),
        inclusive = "left"
    )}

    daily_data["temperature_2m_min"] = daily_temperature_2m_min
    daily_data["wind_speed_10m_max"] = daily_wind_speed_10m_max
    daily_data["wind_direction_10m_dominant"] = daily_wind_direction_10m_dominant
    daily_data["cloud_cover_mean"] = daily_cloud_cover_mean
    daily_data["surface_pressure_mean"] = daily_surface_pressure_mean
    daily_data["dew_point_2m_mean"] = daily_dew_point_2m_mean
    daily_data["relative_humidity_2m_min"] = daily_relative_humidity_2m_min
    daily_data["wind_speed_10m_mean"] = daily_wind_speed_10m_mean

    daily_dataframe = pd.DataFrame(data = daily_data)
    print("\nDaily data\n", daily_dataframe)

    hourly_dataframe["date"] = pd.to_datetime(hourly_dataframe['date'])
    hourly_dataframe = hourly_dataframe.set_index('date')
    hourly_dataframe = hourly_dataframe.resample('D').mean()

    daily_dataframe['date'] = pd.to_datetime(daily_dataframe['date'])
    daily_dataframe = daily_dataframe.set_index('date')
    daily_dataframe = daily_dataframe.join(hourly_dataframe)
    elevation = response.Elevation()

    return daily_dataframe, elevation