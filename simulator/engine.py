"""Monte Carlo simulation engine for house energy system."""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

from .models import (
    Location, HouseParams, PVParams, BatteryParams, HeatPumpParams,
    RecuperatorParams, ACParams, FloorHeatingParams, AppliancesParams,
    TariffParams, SimulationParams,
)
from .weather import generate_year_weather, HourlyWeather


@dataclass
class YearResult:
    """Results for a single simulated year."""
    total_consumption_kwh: float = 0.0
    total_pv_generation_kwh: float = 0.0
    pv_self_consumed_kwh: float = 0.0
    pv_exported_kwh: float = 0.0
    grid_imported_kwh: float = 0.0
    battery_cycles: float = 0.0
    heating_kwh_electric: float = 0.0
    cooling_kwh_electric: float = 0.0
    hot_water_kwh_electric: float = 0.0
    appliances_kwh: float = 0.0
    recuperator_kwh: float = 0.0
    floor_heating_kwh: float = 0.0
    grid_cost_pln: float = 0.0
    feed_in_income_pln: float = 0.0
    fixed_costs_pln: float = 0.0
    net_cost_pln: float = 0.0


@dataclass
class SimulationResult:
    """Aggregate results across all Monte Carlo runs."""
    year_results: list = field(default_factory=list)  # list of lists of YearResult
    # Aggregated stats
    total_net_cost_mean: float = 0.0
    total_net_cost_std: float = 0.0
    total_net_cost_p5: float = 0.0
    total_net_cost_p95: float = 0.0
    annual_costs: Optional[pd.DataFrame] = None  # year x simulation
    investment_cost: float = 0.0
    monthly_profiles: Optional[pd.DataFrame] = None


def _pv_output_on_surface(
    ghi: float, panel_tilt_deg: float, panel_azimuth_deg: float,
    solar_elevation_deg: float, day_of_year: int, latitude: float,
) -> float:
    """Approximate irradiance on a tilted surface from GHI.

    Uses a simplified isotropic model.
    """
    if ghi <= 0 or solar_elevation_deg <= 0:
        return 0.0

    # Rough decomposition: on clear conditions, direct is ~80% of GHI
    # On cloudy, diffuse dominates. Use elevation as proxy.
    direct_fraction = min(0.85, max(0.2, solar_elevation_deg / 60.0))
    direct = ghi * direct_fraction
    diffuse = ghi * (1 - direct_fraction)

    # Solar azimuth approximation (simplified - south at noon)
    declination = 23.45 * np.sin(np.radians(360 / 365 * (day_of_year - 81)))

    # Incidence angle on tilted surface (simplified)
    tilt_r = np.radians(panel_tilt_deg)
    elev_r = np.radians(solar_elevation_deg)

    # For a south-facing panel, tilt benefit
    cos_incidence = (np.sin(elev_r) * np.cos(tilt_r) +
                     np.cos(elev_r) * np.sin(tilt_r))
    cos_incidence = max(0, cos_incidence)

    # Direct on tilted
    if np.sin(elev_r) > 0.01:
        direct_tilted = direct * cos_incidence / np.sin(elev_r)
    else:
        direct_tilted = 0.0

    # Diffuse (isotropic model)
    diffuse_tilted = diffuse * (1 + np.cos(tilt_r)) / 2

    return max(0.0, direct_tilted + diffuse_tilted)


def simulate_single_run(
    location: Location,
    house: HouseParams,
    pv: PVParams,
    battery: BatteryParams,
    heat_pump: HeatPumpParams,
    recuperator: RecuperatorParams,
    ac: ACParams,
    floor_heating: FloorHeatingParams,
    appliances: AppliancesParams,
    tariff: TariffParams,
    sim_params: SimulationParams,
    rng: np.random.Generator,
) -> list:
    """Run simulation for all years in one Monte Carlo path."""
    results = []

    for year_idx in range(sim_params.years):
        year_variability = rng.normal(1.0, 0.15)
        weather = generate_year_weather(
            location.latitude, location.longitude, rng,
            year_variability=abs(year_variability),
        )

        yr = _simulate_year(
            year_idx, weather, location, house, pv, battery,
            heat_pump, recuperator, ac, floor_heating,
            appliances, tariff, rng,
        )
        results.append(yr)

    return results


def _simulate_year(
    year_idx: int,
    weather: HourlyWeather,
    location: Location,
    house: HouseParams,
    pv: PVParams,
    battery: BatteryParams,
    heat_pump: HeatPumpParams,
    recuperator: RecuperatorParams,
    ac: ACParams,
    floor_heating: FloorHeatingParams,
    appliances: AppliancesParams,
    tariff: TariffParams,
    rng: np.random.Generator,
) -> YearResult:
    """Simulate one year hour by hour."""
    yr = YearResult()
    yr.fixed_costs_pln = tariff.fixed_monthly_cost * 12 * (
        (1 + tariff.annual_price_increase) ** year_idx
    )

    battery_soc_kwh = 0.0
    if battery.enabled:
        usable = battery.usable_kwh * (1 - battery.degradation_per_year * year_idx)
        battery_soc_kwh = usable * 0.5  # start half charged

    pv_degradation = (1 - pv.degradation_per_year) ** year_idx

    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    for h in range(8760):
        hour_of_day = h % 24
        day_of_year = h // 24
        month = 0
        day_count = 0
        for m, d in enumerate(days_in_month):
            if day_count + d > day_of_year:
                month = m
                break
            day_count += d

        temp_c = weather.temperature_c[h]
        ghi = weather.ghi_w_m2[h]

        # --- Demand calculation ---
        # Base appliances (spread with daily pattern)
        hourly_profile = _appliance_hourly_factor(hour_of_day)
        base_demand = appliances.base_daily_kwh * hourly_profile / 1.0  # kWh this hour

        # Hot water (morning + evening peaks)
        hw_factor = _hot_water_hourly_factor(hour_of_day)
        hw_electric = 0.0
        if heat_pump.enabled:
            hw_electric = appliances.hot_water_daily_kwh * hw_factor / heat_pump.cop_at_temp(temp_c)
        else:
            hw_electric = appliances.hot_water_daily_kwh * hw_factor  # direct electric

        # Heating demand
        heating_electric = 0.0
        cooling_electric = 0.0
        floor_heat_electric = 0.0

        heat_loss_coeff = house.envelope_loss_coefficient
        # Recuperator reduces ventilation losses
        if recuperator.enabled:
            vent_flow = recuperator.air_flow_m3h
            vent_loss_saved = 0.34 * (vent_flow / 3600) * recuperator.efficiency
            # This is approximate - recuperator saves on ventilation heat loss
            yr.recuperator_kwh += recuperator.fan_power_w / 1000.0

        delta_t = house.target_temp_winter_c - temp_c

        if delta_t > 0:  # Heating needed
            # Total heat demand this hour (kW * 1h = kWh)
            heat_demand_kwh = heat_loss_coeff * delta_t / 1000.0

            # Recuperator savings
            if recuperator.enabled:
                recup_saving = (0.34 * recuperator.air_flow_m3h *
                               recuperator.efficiency * delta_t / 1000.0)
                heat_demand_kwh = max(0, heat_demand_kwh - recup_saving)

            if heat_pump.enabled and temp_c >= heat_pump.min_operating_temp_c:
                cop = heat_pump.cop_at_temp(temp_c)
                hp_electric = heat_demand_kwh / cop
                heating_electric += hp_electric
            elif ac.enabled and ac.heating_capacity_kw > 0:
                ac_electric = heat_demand_kwh / ac.heating_cop
                heating_electric += ac_electric
            elif floor_heating.enabled:
                floor_heat_electric = min(
                    heat_demand_kwh,
                    floor_heating.total_power_kw
                )
                heating_electric += floor_heat_electric
                yr.floor_heating_kwh += floor_heat_electric
            else:
                # Direct electric as fallback
                heating_electric += heat_demand_kwh

            # Floor heating as supplementary
            if floor_heating.enabled and heat_pump.enabled:
                # Use floor heating for bathroom comfort (small fraction)
                supplementary = floor_heating.total_power_kw * 0.15
                if delta_t > 10:  # cold day
                    supplementary *= 1.5
                floor_heat_electric = supplementary
                heating_electric += floor_heat_electric
                yr.floor_heating_kwh += floor_heat_electric

        elif temp_c > house.target_temp_summer_c + 2:  # Cooling needed
            cooling_delta = temp_c - house.target_temp_summer_c
            cool_demand_kwh = heat_loss_coeff * cooling_delta * 0.4 / 1000.0

            if heat_pump.enabled and heat_pump.can_cool:
                cooling_electric = cool_demand_kwh / heat_pump.cooling_eer
            elif ac.enabled:
                cooling_electric = cool_demand_kwh / ac.cooling_eer
            # else: no cooling available

        total_demand = (base_demand + hw_electric + heating_electric +
                       cooling_electric +
                       (recuperator.fan_power_w / 1000.0 if recuperator.enabled else 0))

        yr.total_consumption_kwh += total_demand
        yr.heating_kwh_electric += heating_electric
        yr.cooling_kwh_electric += cooling_electric
        yr.hot_water_kwh_electric += hw_electric
        yr.appliances_kwh += base_demand

        # --- PV generation ---
        pv_gen = 0.0
        if pv.enabled and ghi > 0:
            solar_elev = _solar_elevation_approx(location.latitude, day_of_year, hour_of_day)
            if solar_elev > 0:
                # Roof array
                irr_tilted = _pv_output_on_surface(
                    ghi, pv.roof_tilt_deg, pv.roof_azimuth_deg,
                    solar_elev, day_of_year, location.latitude,
                )
                pv_gen += (pv.peak_power_kw * (irr_tilted / 1000.0) *
                          (1 - pv.system_losses) * pv_degradation)

                # Ground mount
                if pv.ground_mount_enabled and pv.ground_mount_kwp > 0:
                    irr_ground = _pv_output_on_surface(
                        ghi, pv.ground_tilt_deg, pv.ground_azimuth_deg,
                        solar_elev, day_of_year, location.latitude,
                    )
                    pv_gen += (pv.ground_mount_kwp * (irr_ground / 1000.0) *
                              (1 - pv.system_losses) * pv_degradation)

        yr.total_pv_generation_kwh += pv_gen

        # --- Energy balance ---
        net = total_demand - pv_gen  # positive = need from grid/battery

        if net > 0:
            # Need power: try battery first, then grid
            from_battery = 0.0
            if battery.enabled and battery_soc_kwh > 0:
                usable_now = battery.usable_kwh * (1 - battery.degradation_per_year * year_idx)
                discharge = min(net, battery.max_discharge_kw, battery_soc_kwh)
                battery_soc_kwh -= discharge
                from_battery = discharge
                net -= discharge

            if net > 0:
                yr.grid_imported_kwh += net
                price = tariff.price_at_hour(hour_of_day, year_idx)
                yr.grid_cost_pln += net * price

            yr.pv_self_consumed_kwh += pv_gen  # all PV was used
        else:
            # Surplus PV
            surplus = -net
            yr.pv_self_consumed_kwh += total_demand  # demand was fully covered

            # Charge battery
            to_battery = 0.0
            if battery.enabled:
                usable_now = battery.usable_kwh * (1 - battery.degradation_per_year * year_idx)
                charge = min(surplus, battery.max_charge_kw,
                           usable_now - battery_soc_kwh)
                charge = max(0, charge)
                battery_soc_kwh += charge * battery.round_trip_efficiency
                to_battery = charge
                surplus -= charge

            # Export remainder
            if surplus > 0:
                yr.pv_exported_kwh += surplus
                yr.feed_in_income_pln += surplus * tariff.feed_in_at_year(year_idx)

    yr.net_cost_pln = yr.grid_cost_pln + yr.fixed_costs_pln - yr.feed_in_income_pln
    return yr


def run_monte_carlo(
    location: Location,
    house: HouseParams,
    pv: PVParams,
    battery: BatteryParams,
    heat_pump: HeatPumpParams,
    recuperator: RecuperatorParams,
    ac: ACParams,
    floor_heating: FloorHeatingParams,
    appliances: AppliancesParams,
    tariff: TariffParams,
    sim_params: SimulationParams,
    progress_callback=None,
) -> SimulationResult:
    """Run full Monte Carlo simulation."""
    seed = sim_params.random_seed
    rng = np.random.default_rng(seed)

    all_runs = []
    for i in range(sim_params.num_simulations):
        run_results = simulate_single_run(
            location, house, pv, battery, heat_pump, recuperator,
            ac, floor_heating, appliances, tariff, sim_params, rng,
        )
        all_runs.append(run_results)
        if progress_callback:
            progress_callback((i + 1) / sim_params.num_simulations)

    # Aggregate
    result = SimulationResult()
    result.year_results = all_runs

    # Investment cost
    result.investment_cost = 0.0
    if pv.enabled:
        result.investment_cost += pv.total_cost
    if battery.enabled:
        result.investment_cost += battery.cost_total
    if heat_pump.enabled:
        result.investment_cost += heat_pump.cost_total
    if recuperator.enabled:
        result.investment_cost += recuperator.cost_total
    if ac.enabled:
        result.investment_cost += ac.total_cost
    if floor_heating.enabled:
        result.investment_cost += floor_heating.total_cost

    # Total net costs across simulations
    total_costs = []
    annual_data = []
    for run in all_runs:
        run_total = sum(yr.net_cost_pln for yr in run)
        total_costs.append(run_total)
        annual_data.append([yr.net_cost_pln for yr in run])

    total_costs = np.array(total_costs)
    result.total_net_cost_mean = float(np.mean(total_costs))
    result.total_net_cost_std = float(np.std(total_costs))
    result.total_net_cost_p5 = float(np.percentile(total_costs, 5))
    result.total_net_cost_p95 = float(np.percentile(total_costs, 95))

    result.annual_costs = pd.DataFrame(
        annual_data,
        columns=[f"Rok {i+1}" for i in range(sim_params.years)],
    )

    return result


def _appliance_hourly_factor(hour: int) -> float:
    """Hourly usage profile for appliances (sums to ~1.0 over 24h)."""
    profile = [
        0.02, 0.02, 0.02, 0.02, 0.02, 0.03,  # 0-5
        0.04, 0.06, 0.06, 0.04, 0.04, 0.05,  # 6-11
        0.06, 0.05, 0.04, 0.04, 0.05, 0.07,  # 12-17
        0.08, 0.07, 0.06, 0.05, 0.04, 0.03,  # 18-23
    ]
    return profile[hour]


def _hot_water_hourly_factor(hour: int) -> float:
    """Hourly hot water usage profile (sums to ~1.0 over 24h)."""
    profile = [
        0.01, 0.01, 0.01, 0.01, 0.01, 0.02,
        0.08, 0.12, 0.08, 0.04, 0.03, 0.03,
        0.03, 0.02, 0.02, 0.02, 0.03, 0.05,
        0.08, 0.10, 0.08, 0.06, 0.04, 0.02,
    ]
    return profile[hour]


def _solar_elevation_approx(latitude: float, day_of_year: int, hour: int) -> float:
    """Quick solar elevation calculation."""
    declination = 23.45 * np.sin(np.radians(360 / 365 * (day_of_year - 81)))
    hour_angle = 15.0 * (hour - 12)
    lat_r = np.radians(latitude)
    dec_r = np.radians(declination)
    ha_r = np.radians(hour_angle)
    sin_elev = (np.sin(lat_r) * np.sin(dec_r) +
                np.cos(lat_r) * np.cos(dec_r) * np.cos(ha_r))
    return np.degrees(np.arcsin(np.clip(sin_elev, -1, 1)))
