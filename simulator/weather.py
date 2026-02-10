"""Weather model generator for Monte Carlo simulation.

Generates synthetic hourly weather data (temperature, solar irradiance, cloud cover)
based on location-specific climate profiles for Polish/Central European locations.
"""

import numpy as np
from dataclasses import dataclass


# Climate profiles for Polish cities (monthly averages)
# Format: (avg_temp_c, temp_std, avg_solar_peak_w_m2, cloud_fraction, precip_days)
CLIMATE_PROFILES = {
    "Warszawa": {
        "lat": 52.23,
        "months": [
            (-2.5, 5.0, 80, 0.72, 16), (-1.5, 5.5, 140, 0.68, 14),
            (2.5, 4.5, 250, 0.60, 13), (8.5, 4.0, 380, 0.52, 12),
            (14.0, 3.5, 480, 0.48, 13), (17.5, 3.0, 520, 0.45, 13),
            (19.5, 3.0, 500, 0.44, 14), (19.0, 3.0, 430, 0.45, 12),
            (14.0, 3.5, 310, 0.50, 11), (8.5, 3.5, 180, 0.60, 12),
            (3.5, 4.0, 90, 0.70, 15), (-0.5, 4.5, 60, 0.75, 16),
        ],
    },
    "Wrocław": {
        "lat": 51.1,
        "months": [
            (-1.0, 5.0, 85, 0.70, 15), (0.0, 5.5, 150, 0.65, 13),
            (4.0, 4.5, 260, 0.58, 12), (9.5, 4.0, 390, 0.50, 11),
            (14.5, 3.5, 490, 0.46, 13), (18.0, 3.0, 530, 0.43, 13),
            (20.0, 3.0, 510, 0.42, 13), (19.5, 3.0, 440, 0.43, 11),
            (14.5, 3.5, 320, 0.48, 10), (9.0, 3.5, 190, 0.58, 11),
            (4.0, 4.0, 95, 0.68, 14), (0.5, 4.5, 65, 0.73, 15),
        ],
    },
    "Kraków": {
        "lat": 50.06,
        "months": [
            (-2.0, 5.5, 85, 0.72, 16), (-0.5, 5.5, 150, 0.67, 14),
            (3.5, 4.5, 260, 0.59, 13), (9.0, 4.0, 380, 0.52, 13),
            (14.0, 3.5, 480, 0.48, 14), (17.5, 3.0, 520, 0.45, 14),
            (19.5, 3.0, 500, 0.44, 14), (19.0, 3.0, 430, 0.44, 12),
            (14.0, 3.5, 310, 0.50, 11), (8.5, 3.5, 180, 0.60, 12),
            (3.5, 4.0, 90, 0.70, 15), (-0.5, 5.0, 60, 0.75, 16),
        ],
    },
    "Gdańsk": {
        "lat": 54.35,
        "months": [
            (-1.0, 4.5, 60, 0.75, 17), (-0.5, 4.5, 110, 0.72, 14),
            (2.0, 4.0, 220, 0.65, 13), (7.0, 3.5, 350, 0.55, 11),
            (12.0, 3.0, 460, 0.50, 12), (16.0, 2.5, 500, 0.48, 12),
            (18.0, 2.5, 480, 0.48, 13), (17.5, 2.5, 410, 0.48, 12),
            (13.5, 3.0, 280, 0.55, 12), (8.5, 3.5, 150, 0.65, 13),
            (3.5, 4.0, 70, 0.73, 16), (0.5, 4.5, 45, 0.78, 17),
        ],
    },
    "Poznań": {
        "lat": 52.41,
        "months": [
            (-1.5, 5.0, 80, 0.71, 15), (-0.5, 5.5, 140, 0.66, 13),
            (3.0, 4.5, 255, 0.59, 12), (9.0, 4.0, 385, 0.51, 11),
            (14.5, 3.5, 485, 0.47, 12), (17.5, 3.0, 525, 0.44, 13),
            (19.5, 3.0, 505, 0.43, 13), (19.0, 3.0, 435, 0.44, 11),
            (14.5, 3.5, 315, 0.49, 10), (9.0, 3.5, 185, 0.59, 12),
            (4.0, 4.0, 90, 0.69, 14), (0.0, 4.5, 60, 0.74, 15),
        ],
    },
    "Szczecin": {
        "lat": 53.43,
        "months": [
            (-0.5, 4.5, 70, 0.73, 16), (0.5, 5.0, 120, 0.69, 13),
            (3.5, 4.0, 240, 0.62, 12), (8.5, 3.5, 370, 0.53, 11),
            (13.5, 3.0, 470, 0.48, 12), (17.0, 2.5, 510, 0.46, 12),
            (19.0, 2.5, 490, 0.46, 13), (18.5, 2.5, 420, 0.46, 12),
            (14.0, 3.0, 290, 0.52, 11), (9.0, 3.5, 165, 0.62, 13),
            (4.0, 4.0, 80, 0.71, 15), (1.0, 4.5, 50, 0.76, 16),
        ],
    },
}


def _find_closest_profile(latitude: float, longitude: float) -> dict:
    """Find the closest climate profile to a given location."""
    best = None
    best_dist = float("inf")
    for name, profile in CLIMATE_PROFILES.items():
        dist = abs(profile["lat"] - latitude)
        if dist < best_dist:
            best_dist = dist
            best = profile
    return best


@dataclass
class HourlyWeather:
    """Weather data for 8760 hours of a year."""
    temperature_c: np.ndarray       # (8760,) outdoor temp
    ghi_w_m2: np.ndarray            # (8760,) global horizontal irradiance
    cloud_cover: np.ndarray         # (8760,) 0-1 cloud fraction
    wind_speed_ms: np.ndarray       # (8760,) wind speed


def generate_year_weather(
    latitude: float,
    longitude: float,
    rng: np.random.Generator,
    year_variability: float = 1.0,
) -> HourlyWeather:
    """Generate synthetic hourly weather for one year.

    Uses climate profiles with stochastic variation for Monte Carlo runs.
    year_variability controls how much this year deviates from average
    (sampled externally for inter-annual variation).
    """
    profile = _find_closest_profile(latitude, longitude)
    months = profile["months"]

    hours = 8760
    temp = np.zeros(hours)
    ghi = np.zeros(hours)
    cloud = np.zeros(hours)
    wind = np.zeros(hours)

    # Day-of-year to month mapping
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    hour_idx = 0
    for m_idx, (avg_t, std_t, peak_solar, cloud_frac, _) in enumerate(months):
        n_days = days_in_month[m_idx]
        n_hours = n_days * 24

        # Apply year-level anomaly
        temp_anomaly = rng.normal(0, 1.5) * year_variability
        solar_anomaly = rng.normal(1.0, 0.08 * year_variability)
        cloud_anomaly = rng.normal(0, 0.05) * year_variability

        for d in range(n_days):
            day_of_year = sum(days_in_month[:m_idx]) + d
            # Whether this is a cloudy day (multi-day weather patterns)
            is_cloudy_day = rng.random() < (cloud_frac + cloud_anomaly)
            day_cloud_base = 0.7 + rng.random() * 0.25 if is_cloudy_day else 0.1 + rng.random() * 0.25

            for h in range(24):
                idx = hour_idx + d * 24 + h

                # Temperature: diurnal cycle
                diurnal = -3.0 + 6.0 * np.sin(np.pi * (h - 6) / 12) if 6 <= h <= 18 else -3.0
                temp[idx] = avg_t + temp_anomaly + diurnal + rng.normal(0, std_t * 0.3)

                # Solar irradiance
                solar_elevation = _solar_elevation(latitude, day_of_year, h)
                if solar_elevation > 0:
                    clear_sky = peak_solar * np.sin(np.radians(solar_elevation))
                    cloud_factor = day_cloud_base + rng.normal(0, 0.05)
                    cloud_factor = np.clip(cloud_factor, 0.0, 1.0)
                    # Cloudy sky transmits ~20-30% of clear sky
                    ghi[idx] = clear_sky * solar_anomaly * (1.0 - 0.75 * cloud_factor)
                    ghi[idx] = max(0.0, ghi[idx])
                    cloud[idx] = cloud_factor
                else:
                    ghi[idx] = 0.0
                    cloud[idx] = day_cloud_base

                # Wind
                wind[idx] = max(0, rng.normal(3.5, 1.5))

        hour_idx += n_hours

    return HourlyWeather(
        temperature_c=temp,
        ghi_w_m2=ghi,
        cloud_cover=cloud,
        wind_speed_ms=wind,
    )


def _solar_elevation(latitude: float, day_of_year: int, hour: int) -> float:
    """Approximate solar elevation angle in degrees."""
    # Declination
    declination = 23.45 * np.sin(np.radians(360 / 365 * (day_of_year - 81)))
    # Hour angle (solar noon = 12)
    hour_angle = 15.0 * (hour - 12)
    # Elevation
    lat_r = np.radians(latitude)
    dec_r = np.radians(declination)
    ha_r = np.radians(hour_angle)

    sin_elev = (np.sin(lat_r) * np.sin(dec_r) +
                np.cos(lat_r) * np.cos(dec_r) * np.cos(ha_r))
    return np.degrees(np.arcsin(np.clip(sin_elev, -1, 1)))
