"""Data models for house electricity simulator."""

from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class Location:
    """Geographic location of the house."""
    latitude: float = 51.1  # Default: Wroclaw area
    longitude: float = 17.0
    city_name: str = "Wroclaw"
    altitude_m: float = 120.0


@dataclass
class HouseParams:
    """House physical parameters."""
    area_m2: float = 150.0
    floors: int = 2
    wall_insulation_cm: float = 20.0  # EPS/styrofoam thickness
    roof_insulation_cm: float = 30.0
    window_u_value: float = 0.9  # W/(m2K), triple glazing default
    wall_u_value: float = 0.18  # W/(m2K)
    roof_u_value: float = 0.12  # W/(m2K)
    floor_u_value: float = 0.25  # W/(m2K)
    window_area_ratio: float = 0.18  # windows as fraction of wall area
    ceiling_height_m: float = 2.7
    air_tightness_n50: float = 1.5  # air changes per hour at 50Pa
    thermal_mass: str = "medium"  # low, medium, high (brick/concrete)
    target_temp_winter_c: float = 21.0
    target_temp_summer_c: float = 24.0
    ventilation_rate_m3h: float = 200.0  # mechanical ventilation rate

    @property
    def volume_m3(self) -> float:
        return self.area_m2 * self.ceiling_height_m

    @property
    def floor_area(self) -> float:
        return self.area_m2 / self.floors

    @property
    def transmission_loss_coefficient(self) -> float:
        """Heat loss coefficient W/K through walls, windows, roof, floor only."""
        floor_a = self.floor_area
        roof_area = floor_a * 1.1  # slight pitch
        wall_height = self.ceiling_height_m * self.floors
        perimeter = 4 * (floor_a ** 0.5)
        wall_area = perimeter * wall_height
        window_area = wall_area * self.window_area_ratio
        opaque_wall_area = wall_area - window_area

        return (
            opaque_wall_area * self.wall_u_value
            + window_area * self.window_u_value
            + roof_area * self.roof_u_value
            + floor_a * self.floor_u_value
        )

    @property
    def infiltration_loss_coefficient(self) -> float:
        """Heat loss W/K from air infiltration (uncontrolled leakage)."""
        infiltration_ach = self.air_tightness_n50 / 20.0
        return 0.34 * infiltration_ach * self.volume_m3

    @property
    def ventilation_loss_coefficient(self) -> float:
        """Heat loss W/K from mechanical ventilation (before recuperator)."""
        return 0.34 * self.ventilation_rate_m3h

    @property
    def total_loss_coefficient(self) -> float:
        """Total heat loss coefficient W/K (transmission + infiltration + ventilation)."""
        return (self.transmission_loss_coefficient
                + self.infiltration_loss_coefficient
                + self.ventilation_loss_coefficient)

    @property
    def envelope_loss_coefficient(self) -> float:
        """Backward-compatible alias."""
        return self.total_loss_coefficient


@dataclass
class PVParams:
    """Photovoltaic panel parameters."""
    enabled: bool = True
    peak_power_kw: float = 10.0
    panel_efficiency: float = 0.21
    roof_tilt_deg: float = 35.0
    roof_azimuth_deg: float = 180.0  # 180=south
    system_losses: float = 0.14
    degradation_per_year: float = 0.005
    cost_per_kwp: float = 4500.0
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
    degradation_per_year: float = 0.02
    cost_total: float = 25000.0

    @property
    def usable_kwh(self) -> float:
        return self.capacity_kwh * self.depth_of_discharge


@dataclass
class HeatPumpParams:
    """Heat pump parameters (air-source by default)."""
    enabled: bool = True
    rated_power_kw: float = 8.0
    cop_at_7c: float = 4.0
    cop_at_minus7c: float = 2.5
    cop_at_minus15c: float = 1.8
    min_operating_temp_c: float = -20.0
    can_cool: bool = True
    cooling_eer: float = 4.5
    cost_total: float = 35000.0

    def cop_at_temp(self, outdoor_c: float) -> float:
        if outdoor_c >= 7:
            return self.cop_at_7c
        elif outdoor_c >= -7:
            frac = (outdoor_c - (-7)) / 14.0
            return self.cop_at_minus7c + frac * (self.cop_at_7c - self.cop_at_minus7c)
        elif outdoor_c >= -15:
            frac = (outdoor_c - (-15)) / 8.0
            return self.cop_at_minus15c + frac * (self.cop_at_minus7c - self.cop_at_minus15c)
        else:
            return max(1.0, self.cop_at_minus15c * 0.85)


@dataclass
class RecuperatorParams:
    """Heat recovery ventilation."""
    enabled: bool = True
    efficiency: float = 0.85
    fan_power_w: float = 80.0
    cost_total: float = 15000.0


@dataclass
class ACParams:
    """Air conditioning (split units for heating/cooling)."""
    enabled: bool = False
    num_units: int = 2
    cooling_capacity_kw: float = 3.5
    heating_capacity_kw: float = 4.0
    cooling_eer: float = 5.0
    heating_cop: float = 4.2
    cost_per_unit: float = 4000.0

    @property
    def total_cost(self) -> float:
        return self.num_units * self.cost_per_unit


@dataclass
class FloorHeatingParams:
    """Electric floor heating mats."""
    enabled: bool = False
    area_m2: float = 30.0
    power_per_m2_w: float = 150.0
    cost_per_m2: float = 200.0

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


def default_appliances() -> list:
    return [
        Appliance("Lodówka", 80, 24, 1, 0),       # modern A+++ ~80W avg
        Appliance("Zmywarka", 1800, 1.0, 1),
        Appliance("Pralka", 2000, 0.7, 1),
        Appliance("Kuchenka indukcyjna", 2000, 1.5, 1),  # avg power during cooking
        Appliance("Czajnik elektryczny", 2200, 0.1, 1),
        Appliance("Piekarnik", 2000, 0.4, 1),
        Appliance("Laptop", 50, 8, 2, 3),
        Appliance("TV", 80, 4, 1, 1),
        Appliance("Oświetlenie LED", 150, 5, 1),
        Appliance("Router WiFi", 12, 24, 1),
        Appliance("Suszarka do włosów", 1500, 0.1, 1),
        Appliance("Odkurzacz", 700, 0.2, 1),
    ]


@dataclass
class AppliancesParams:
    """Household appliances configuration."""
    appliances: list = field(default_factory=default_appliances)
    hot_water_daily_kwh: float = 5.0  # DHW thermal energy

    @property
    def base_daily_kwh(self) -> float:
        return sum(a.daily_kwh for a in self.appliances)


@dataclass
class TariffParams:
    """Electricity tariff configuration."""
    price_per_kwh: float = 0.65
    dual_tariff: bool = False
    day_price: float = 0.75
    night_price: float = 0.45
    feed_in_tariff: float = 0.40
    fixed_monthly_cost: float = 30.0
    annual_price_increase: float = 0.03

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
    """Simulation parameters."""
    years: int = 10
    num_simulations: int = 3  # 1 per scenario (cold/normal/warm)
    random_seed: Optional[int] = None


def params_to_dict(location, house, pv, battery, heat_pump, recuperator,
                   ac, floor_heating, appliances, tariff, sim_params) -> dict:
    """Serialize all parameters to a JSON-safe dict."""
    def dc_to_dict(obj):
        d = {}
        for f in obj.__dataclass_fields__:
            val = getattr(obj, f)
            if isinstance(val, list):
                val = [dc_to_dict(v) if hasattr(v, '__dataclass_fields__') else v for v in val]
            d[f] = val
        return d

    return {
        "location": dc_to_dict(location),
        "house": dc_to_dict(house),
        "pv": dc_to_dict(pv),
        "battery": dc_to_dict(battery),
        "heat_pump": dc_to_dict(heat_pump),
        "recuperator": dc_to_dict(recuperator),
        "ac": dc_to_dict(ac),
        "floor_heating": dc_to_dict(floor_heating),
        "appliances": dc_to_dict(appliances),
        "tariff": dc_to_dict(tariff),
        "sim_params": dc_to_dict(sim_params),
    }


def params_from_dict(data: dict):
    """Deserialize parameters from a dict."""
    def make_appliance(d):
        return Appliance(**d)

    loc = Location(**data["location"])
    house = HouseParams(**data["house"])
    pv = PVParams(**data["pv"])
    bat = BatteryParams(**data["battery"])
    hp = HeatPumpParams(**data["heat_pump"])
    rec = RecuperatorParams(**data["recuperator"])
    ac_p = ACParams(**data["ac"])
    fh = FloorHeatingParams(**data["floor_heating"])

    app_data = data["appliances"]
    app_list = [make_appliance(a) for a in app_data["appliances"]]
    app = AppliancesParams(appliances=app_list, hot_water_daily_kwh=app_data["hot_water_daily_kwh"])

    tariff = TariffParams(**data["tariff"])
    sim = SimulationParams(**data["sim_params"])

    return loc, house, pv, bat, hp, rec, ac_p, fh, app, tariff, sim
