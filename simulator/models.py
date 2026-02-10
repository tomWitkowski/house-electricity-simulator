"""Data models for house electricity simulator."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Location:
    """Geographic location of the house."""
    latitude: float = 51.1  # Default: Warsaw area
    longitude: float = 17.0
    city_name: str = "Wrocław"
    altitude_m: float = 120.0


@dataclass
class HouseParams:
    """House physical parameters."""
    area_m2: float = 150.0
    floors: int = 2
    wall_insulation_cm: float = 20.0  # EPS/styrofoam thickness
    roof_insulation_cm: float = 30.0
    window_u_value: float = 0.9  # W/(m²·K), triple glazing default
    wall_u_value: float = 0.18  # W/(m²·K)
    roof_u_value: float = 0.12  # W/(m²·K)
    floor_u_value: float = 0.25  # W/(m²·K)
    window_area_ratio: float = 0.18  # windows as fraction of wall area
    ceiling_height_m: float = 2.7
    air_tightness_n50: float = 1.5  # air changes per hour at 50Pa
    thermal_mass: str = "medium"  # low, medium, high (brick/concrete)
    target_temp_winter_c: float = 21.0
    target_temp_summer_c: float = 24.0

    @property
    def volume_m3(self) -> float:
        return self.area_m2 * self.ceiling_height_m

    @property
    def envelope_loss_coefficient(self) -> float:
        """Total heat loss coefficient W/K through building envelope."""
        floor_area = self.area_m2 / self.floors
        roof_area = floor_area * 1.1  # slight pitch
        wall_height = self.ceiling_height_m * self.floors
        perimeter = 4 * (floor_area ** 0.5)  # approximate square
        wall_area = perimeter * wall_height
        window_area = wall_area * self.window_area_ratio
        opaque_wall_area = wall_area - window_area

        loss = (
            opaque_wall_area * self.wall_u_value
            + window_area * self.window_u_value
            + roof_area * self.roof_u_value
            + floor_area * self.floor_u_value
        )
        # Ventilation losses (infiltration only, recuperator handled separately)
        infiltration_rate = self.air_tightness_n50 / 20  # rough n50 to natural
        loss += 0.34 * infiltration_rate * self.volume_m3
        return loss


@dataclass
class PVParams:
    """Photovoltaic panel parameters."""
    enabled: bool = True
    peak_power_kw: float = 10.0  # kWp
    panel_efficiency: float = 0.21  # modern panels ~21%
    roof_tilt_deg: float = 35.0
    roof_azimuth_deg: float = 180.0  # 180=south
    system_losses: float = 0.14  # inverter, cables, degradation
    degradation_per_year: float = 0.005  # 0.5%/year
    cost_per_kwp: float = 4500.0  # PLN per kWp installed
    # Additional ground-mount array
    ground_mount_enabled: bool = False
    ground_mount_kwp: float = 0.0
    ground_tilt_deg: float = 30.0
    ground_azimuth_deg: float = 180.0

    @property
    def total_kwp(self) -> float:
        total = self.peak_power_kw if self.enabled else 0.0
        if self.ground_mount_enabled:
            total += self.ground_mount_kwp
        return total

    @property
    def total_cost(self) -> float:
        return self.total_kwp * self.cost_per_kwp


@dataclass
class BatteryParams:
    """Energy storage parameters."""
    enabled: bool = False
    capacity_kwh: float = 10.0
    max_charge_kw: float = 5.0
    max_discharge_kw: float = 5.0
    round_trip_efficiency: float = 0.92
    depth_of_discharge: float = 0.90
    degradation_per_year: float = 0.02  # 2%/year capacity loss
    cost_total: float = 25000.0  # PLN

    @property
    def usable_kwh(self) -> float:
        return self.capacity_kwh * self.depth_of_discharge


@dataclass
class HeatPumpParams:
    """Heat pump parameters (air-source by default)."""
    enabled: bool = True
    rated_power_kw: float = 8.0  # thermal output at rated conditions
    cop_at_7c: float = 4.0  # COP at 7°C outdoor / 35°C water
    cop_at_minus7c: float = 2.5  # COP at -7°C
    cop_at_minus15c: float = 1.8  # COP at -15°C
    min_operating_temp_c: float = -20.0
    can_cool: bool = True
    cooling_eer: float = 4.5
    cost_total: float = 35000.0  # PLN

    def cop_at_temp(self, outdoor_c: float) -> float:
        """Interpolate COP based on outdoor temperature."""
        if outdoor_c >= 7:
            return self.cop_at_7c
        elif outdoor_c >= -7:
            frac = (outdoor_c - (-7)) / (7 - (-7))
            return self.cop_at_minus7c + frac * (self.cop_at_7c - self.cop_at_minus7c)
        elif outdoor_c >= -15:
            frac = (outdoor_c - (-15)) / (-7 - (-15))
            return self.cop_at_minus15c + frac * (self.cop_at_minus7c - self.cop_at_minus15c)
        else:
            return max(1.0, self.cop_at_minus15c * 0.85)


@dataclass
class RecuperatorParams:
    """Heat recovery ventilation."""
    enabled: bool = True
    efficiency: float = 0.85  # heat recovery rate
    air_flow_m3h: float = 300.0  # m³/h
    fan_power_w: float = 80.0  # electrical consumption
    cost_total: float = 15000.0  # PLN


@dataclass
class ACParams:
    """Air conditioning (split units for heating/cooling)."""
    enabled: bool = False
    num_units: int = 2
    cooling_capacity_kw: float = 3.5  # per unit
    heating_capacity_kw: float = 4.0  # per unit
    cooling_eer: float = 5.0
    heating_cop: float = 4.2
    cost_per_unit: float = 4000.0  # PLN

    @property
    def total_cost(self) -> float:
        return self.num_units * self.cost_per_unit


@dataclass
class FloorHeatingParams:
    """Electric floor heating mats."""
    enabled: bool = False
    area_m2: float = 30.0  # heated area
    power_per_m2_w: float = 150.0
    cost_per_m2: float = 200.0  # PLN

    @property
    def total_power_kw(self) -> float:
        return self.area_m2 * self.power_per_m2_w / 1000.0

    @property
    def total_cost(self) -> float:
        return self.area_m2 * self.cost_per_m2


@dataclass
class Appliance:
    """Single household appliance."""
    name: str
    power_w: float
    daily_hours: float
    count: int = 1
    standby_w: float = 0.0

    @property
    def daily_kwh(self) -> float:
        active = self.power_w * self.daily_hours * self.count / 1000.0
        standby = self.standby_w * (24 - self.daily_hours) * self.count / 1000.0
        return active + standby


@dataclass
class AppliancesParams:
    """Household appliances configuration."""
    appliances: list = field(default_factory=lambda: [
        Appliance("Lodówka", 150, 24, 1, 0),
        Appliance("Zmywarka", 1800, 1.0, 1),
        Appliance("Pralka", 2000, 0.7, 1),
        Appliance("Kuchenka indukcyjna", 3500, 1.5, 1),
        Appliance("Czajnik elektryczny", 2200, 0.15, 1),
        Appliance("Piekarnik", 2500, 0.5, 1),
        Appliance("Laptop", 65, 8, 2, 5),
        Appliance("TV", 100, 4, 1, 1),
        Appliance("Oświetlenie LED", 200, 6, 1),
        Appliance("Router WiFi", 15, 24, 1),
        Appliance("Suszarka do włosów", 1500, 0.15, 1),
        Appliance("Odkurzacz", 800, 0.3, 1),
    ])
    hot_water_daily_kwh: float = 6.0  # if heated by heat pump

    @property
    def base_daily_kwh(self) -> float:
        return sum(a.daily_kwh for a in self.appliances)


@dataclass
class TariffParams:
    """Electricity tariff configuration."""
    price_per_kwh: float = 0.65  # PLN/kWh
    dual_tariff: bool = False
    day_price: float = 0.75  # PLN/kWh (peak 6:00-22:00)
    night_price: float = 0.45  # PLN/kWh (off-peak 22:00-6:00)
    feed_in_tariff: float = 0.40  # PLN/kWh for selling back
    fixed_monthly_cost: float = 30.0  # PLN (distribution, fees)
    annual_price_increase: float = 0.03  # 3% per year

    def price_at_hour(self, hour: int, year_offset: int = 0) -> float:
        escalation = (1 + self.annual_price_increase) ** year_offset
        if self.dual_tariff:
            if 6 <= hour < 22:
                return self.day_price * escalation
            return self.night_price * escalation
        return self.price_per_kwh * escalation

    def feed_in_at_year(self, year_offset: int = 0) -> float:
        escalation = (1 + self.annual_price_increase) ** year_offset
        return self.feed_in_tariff * escalation


@dataclass
class SimulationParams:
    """Monte Carlo simulation parameters."""
    years: int = 10
    num_simulations: int = 200
    random_seed: Optional[int] = None
