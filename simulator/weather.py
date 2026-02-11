"""Weather model generator for Monte Carlo simulation.

Generates synthetic hourly weather data (temperature, solar irradiance, cloud cover)
based on location-specific climate profiles. Supports any European location via
inverse-distance weighted interpolation between reference city profiles.
"""

import numpy as np
from dataclasses import dataclass


# Climate profiles for European reference cities (monthly averages)
# Format: (avg_temp_c, temp_std, avg_solar_peak_w_m2, cloud_fraction, precip_days)
CLIMATE_PROFILES = {
    "Warszawa": {
        "lat": 52.23, "lon": 21.0,
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
        "lat": 51.1, "lon": 17.0,
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
        "lat": 50.06, "lon": 19.94,
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
        "lat": 54.35, "lon": 18.65,
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
        "lat": 52.41, "lon": 16.93,
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
        "lat": 53.43, "lon": 14.55,
        "months": [
            (-0.5, 4.5, 70, 0.73, 16), (0.5, 5.0, 120, 0.69, 13),
            (3.5, 4.0, 240, 0.62, 12), (8.5, 3.5, 370, 0.53, 11),
            (13.5, 3.0, 470, 0.48, 12), (17.0, 2.5, 510, 0.46, 12),
            (19.0, 2.5, 490, 0.46, 13), (18.5, 2.5, 420, 0.46, 12),
            (14.0, 3.0, 290, 0.52, 11), (9.0, 3.5, 165, 0.62, 13),
            (4.0, 4.0, 80, 0.71, 15), (1.0, 4.5, 50, 0.76, 16),
        ],
    },
    # ── Scandinavia ──
    "Stockholm": {
        "lat": 59.33, "lon": 18.07,
        "months": [
            (-3.0, 5.0, 30, 0.78, 16), (-3.0, 5.5, 70, 0.74, 13),
            (0.5, 4.5, 190, 0.65, 12), (5.5, 3.5, 330, 0.55, 10),
            (11.5, 3.0, 460, 0.48, 10), (16.0, 2.5, 510, 0.44, 11),
            (18.5, 2.5, 490, 0.46, 12), (17.0, 2.5, 400, 0.48, 11),
            (12.0, 3.0, 250, 0.55, 12), (7.0, 3.5, 120, 0.66, 13),
            (2.5, 4.0, 45, 0.76, 15), (-1.0, 4.5, 20, 0.80, 16),
        ],
    },
    "Oslo": {
        "lat": 59.91, "lon": 10.75,
        "months": [
            (-4.0, 5.5, 25, 0.76, 15), (-3.5, 5.5, 65, 0.72, 12),
            (-0.5, 5.0, 185, 0.64, 12), (5.0, 3.5, 320, 0.54, 10),
            (11.0, 3.0, 450, 0.48, 10), (15.5, 2.5, 500, 0.45, 11),
            (17.5, 2.5, 480, 0.47, 13), (16.0, 2.5, 380, 0.49, 12),
            (11.5, 3.0, 240, 0.56, 12), (6.0, 3.5, 110, 0.67, 14),
            (1.0, 4.5, 35, 0.75, 15), (-2.5, 5.0, 15, 0.79, 16),
        ],
    },
    "Helsinki": {
        "lat": 60.17, "lon": 24.94,
        "months": [
            (-5.5, 5.5, 20, 0.80, 16), (-5.5, 6.0, 55, 0.76, 13),
            (-1.5, 5.0, 175, 0.68, 12), (4.0, 3.5, 310, 0.58, 10),
            (10.5, 3.0, 440, 0.50, 10), (15.0, 2.5, 490, 0.46, 11),
            (17.5, 2.5, 470, 0.48, 12), (16.0, 2.5, 370, 0.50, 12),
            (11.0, 3.0, 230, 0.58, 13), (5.5, 3.5, 100, 0.70, 14),
            (1.0, 4.5, 30, 0.78, 16), (-3.5, 5.0, 12, 0.82, 17),
        ],
    },
    # ── Western Europe ──
    "Berlin": {
        "lat": 52.52, "lon": 13.41,
        "months": [
            (0.0, 4.5, 70, 0.72, 15), (1.0, 5.0, 130, 0.67, 13),
            (4.5, 4.0, 250, 0.60, 12), (9.5, 3.5, 380, 0.52, 11),
            (14.5, 3.0, 480, 0.47, 12), (17.5, 2.5, 520, 0.44, 12),
            (20.0, 2.5, 500, 0.44, 13), (19.5, 2.5, 430, 0.44, 11),
            (15.0, 3.0, 310, 0.50, 10), (9.5, 3.5, 175, 0.60, 12),
            (4.5, 4.0, 80, 0.70, 14), (1.0, 4.5, 50, 0.75, 15),
        ],
    },
    "London": {
        "lat": 51.51, "lon": -0.13,
        "months": [
            (4.5, 3.5, 55, 0.78, 17), (4.5, 3.5, 100, 0.74, 14),
            (6.5, 3.0, 200, 0.66, 14), (9.0, 3.0, 320, 0.58, 13),
            (12.5, 2.5, 420, 0.52, 12), (16.0, 2.5, 460, 0.50, 11),
            (18.0, 2.0, 450, 0.50, 12), (17.5, 2.0, 390, 0.52, 12),
            (14.5, 2.5, 270, 0.56, 12), (11.0, 3.0, 150, 0.65, 14),
            (7.0, 3.5, 70, 0.75, 15), (5.0, 3.5, 40, 0.80, 16),
        ],
    },
    "Paris": {
        "lat": 48.86, "lon": 2.35,
        "months": [
            (3.5, 3.5, 65, 0.75, 16), (4.0, 4.0, 120, 0.70, 13),
            (7.0, 3.5, 240, 0.62, 13), (10.5, 3.0, 360, 0.54, 12),
            (14.5, 3.0, 460, 0.48, 12), (18.0, 2.5, 510, 0.44, 11),
            (20.0, 2.5, 520, 0.42, 10), (19.5, 2.5, 450, 0.43, 10),
            (16.0, 3.0, 320, 0.48, 10), (11.5, 3.0, 180, 0.58, 12),
            (7.0, 3.5, 80, 0.70, 14), (4.0, 3.5, 50, 0.76, 15),
        ],
    },
    # ── Southern Europe ──
    "Madrid": {
        "lat": 40.42, "lon": -3.70,
        "months": [
            (6.0, 3.5, 180, 0.45, 8), (7.5, 3.5, 240, 0.42, 8),
            (10.5, 3.0, 360, 0.38, 7), (13.0, 3.0, 470, 0.35, 8),
            (17.0, 2.5, 560, 0.30, 7), (22.5, 2.5, 640, 0.20, 4),
            (26.0, 2.0, 660, 0.15, 2), (25.5, 2.0, 600, 0.18, 3),
            (21.0, 2.5, 460, 0.28, 5), (15.0, 3.0, 300, 0.38, 8),
            (9.5, 3.5, 190, 0.45, 9), (6.5, 3.5, 150, 0.48, 9),
        ],
    },
    "Rome": {
        "lat": 41.90, "lon": 12.50,
        "months": [
            (7.0, 3.0, 160, 0.52, 10), (8.0, 3.0, 210, 0.48, 9),
            (10.5, 3.0, 320, 0.42, 9), (13.5, 2.5, 420, 0.38, 8),
            (18.0, 2.5, 530, 0.30, 6), (22.0, 2.0, 600, 0.22, 4),
            (25.0, 2.0, 630, 0.15, 2), (25.0, 2.0, 570, 0.18, 3),
            (21.5, 2.5, 430, 0.28, 6), (16.5, 3.0, 280, 0.40, 8),
            (11.5, 3.0, 170, 0.52, 10), (8.0, 3.0, 130, 0.55, 11),
        ],
    },
    "Vienna": {
        "lat": 48.21, "lon": 16.37,
        "months": [
            (-0.5, 5.0, 75, 0.72, 15), (1.0, 5.0, 135, 0.67, 13),
            (5.5, 4.0, 260, 0.58, 12), (10.5, 3.5, 380, 0.50, 11),
            (15.5, 3.0, 490, 0.45, 12), (18.5, 2.5, 540, 0.42, 12),
            (21.0, 2.5, 530, 0.40, 12), (20.5, 2.5, 450, 0.42, 11),
            (15.5, 3.0, 320, 0.48, 10), (10.0, 3.5, 185, 0.58, 11),
            (4.5, 4.0, 80, 0.70, 14), (0.5, 4.5, 55, 0.75, 15),
        ],
    },
    "Munich": {
        "lat": 48.14, "lon": 11.58,
        "months": [
            (-1.0, 5.0, 80, 0.72, 15), (0.5, 5.0, 140, 0.67, 13),
            (4.5, 4.0, 260, 0.58, 13), (9.0, 3.5, 380, 0.52, 12),
            (14.0, 3.0, 480, 0.46, 13), (17.5, 2.5, 530, 0.43, 13),
            (19.5, 2.5, 520, 0.42, 13), (19.0, 2.5, 440, 0.43, 12),
            (14.5, 3.0, 320, 0.48, 10), (9.0, 3.5, 185, 0.58, 12),
            (4.0, 4.0, 85, 0.70, 14), (0.0, 4.5, 55, 0.75, 15),
        ],
    },
    # ── Eastern/Northern ──
    "Tromsø": {
        "lat": 69.65, "lon": 18.96,
        "months": [
            (-4.0, 5.0, 0, 0.82, 16), (-3.5, 5.0, 10, 0.80, 14),
            (-2.0, 4.5, 100, 0.72, 14), (1.5, 3.5, 220, 0.62, 12),
            (6.0, 3.0, 350, 0.55, 11), (10.5, 2.5, 400, 0.52, 12),
            (13.0, 2.0, 380, 0.54, 14), (11.5, 2.5, 280, 0.56, 14),
            (7.5, 3.0, 150, 0.62, 14), (3.0, 3.5, 50, 0.72, 15),
            (-1.0, 4.5, 5, 0.80, 16), (-3.0, 5.0, 0, 0.84, 17),
        ],
    },
    "Moscow": {
        "lat": 55.75, "lon": 37.62,
        "months": [
            (-8.0, 6.0, 50, 0.78, 16), (-6.5, 6.0, 95, 0.74, 13),
            (-1.0, 5.0, 215, 0.64, 12), (7.0, 4.0, 340, 0.54, 11),
            (13.5, 3.5, 460, 0.48, 12), (17.0, 3.0, 500, 0.46, 12),
            (19.5, 3.0, 480, 0.48, 13), (17.5, 3.0, 390, 0.50, 12),
            (12.0, 3.5, 260, 0.56, 12), (5.5, 4.0, 130, 0.66, 14),
            (-1.0, 5.0, 55, 0.76, 16), (-5.5, 5.5, 30, 0.80, 17),
        ],
    },
    "Athens": {
        "lat": 37.98, "lon": 23.73,
        "months": [
            (9.5, 2.5, 200, 0.48, 10), (10.0, 2.5, 260, 0.44, 8),
            (12.5, 2.5, 380, 0.38, 8), (16.0, 2.0, 490, 0.30, 6),
            (21.0, 2.0, 590, 0.22, 4), (25.5, 1.5, 660, 0.12, 2),
            (28.5, 1.5, 680, 0.08, 1), (28.0, 1.5, 620, 0.10, 1),
            (24.0, 2.0, 480, 0.18, 3), (19.0, 2.5, 320, 0.32, 7),
            (14.0, 3.0, 210, 0.44, 9), (10.5, 2.5, 170, 0.50, 11),
        ],
    },
}


def _find_climate_profile(latitude: float, longitude: float) -> list:
    """Interpolate climate profile from nearest reference cities.

    Uses inverse-distance-weighted average of the 3 nearest profiles.
    Distance is computed in lat/lon space (with lon weighted by cos(lat)
    to approximate real distances).
    """
    cos_lat = np.cos(np.radians(latitude))
    distances = {}
    for name, profile in CLIMATE_PROFILES.items():
        dlat = profile["lat"] - latitude
        dlon = (profile["lon"] - longitude) * cos_lat
        distances[name] = np.sqrt(dlat**2 + dlon**2)

    # Pick 3 nearest
    nearest = sorted(distances, key=distances.get)[:3]
    dists = np.array([max(distances[n], 0.1) for n in nearest])  # avoid div by zero
    weights = 1.0 / dists
    weights /= weights.sum()

    # Weighted average of monthly parameters
    result = []
    for m in range(12):
        avg_t, std_t, peak_solar, cloud_frac, precip = 0.0, 0.0, 0.0, 0.0, 0.0
        for i, name in enumerate(nearest):
            mt = CLIMATE_PROFILES[name]["months"][m]
            avg_t += mt[0] * weights[i]
            std_t += mt[1] * weights[i]
            peak_solar += mt[2] * weights[i]
            cloud_frac += mt[3] * weights[i]
            precip += mt[4] * weights[i]
        result.append((avg_t, std_t, peak_solar, cloud_frac, precip))

    return result


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

    Uses interpolated climate profiles with stochastic variation.
    Works for any European location (lat ~35-70, lon ~-10 to 40).
    """
    months_profile = _find_climate_profile(latitude, longitude)

    hours = 8760
    temp = np.zeros(hours)
    ghi = np.zeros(hours)
    cloud = np.zeros(hours)
    wind = np.zeros(hours)

    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    hour_idx = 0
    for m_idx, (avg_t, std_t, peak_solar, cloud_frac, _) in enumerate(months_profile):
        n_days = days_in_month[m_idx]
        n_hours = n_days * 24

        # Apply year-level anomaly
        temp_anomaly = rng.normal(0, 1.5) * year_variability
        solar_anomaly = rng.normal(1.0, 0.08 * year_variability)
        cloud_anomaly = rng.normal(0, 0.05) * year_variability

        for d in range(n_days):
            day_of_year = sum(days_in_month[:m_idx]) + d
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
    declination = 23.45 * np.sin(np.radians(360 / 365 * (day_of_year - 81)))
    hour_angle = 15.0 * (hour - 12)
    lat_r = np.radians(latitude)
    dec_r = np.radians(declination)
    ha_r = np.radians(hour_angle)

    sin_elev = (np.sin(lat_r) * np.sin(dec_r) +
                np.cos(lat_r) * np.cos(dec_r) * np.cos(ha_r))
    return np.degrees(np.arcsin(np.clip(sin_elev, -1, 1)))
