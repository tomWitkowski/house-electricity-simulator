"""Simulation engine for house energy system.

Runs 3 scenario types (cold/normal/warm year) with optional Monte Carlo repeats.
Tracks hourly: PV generation, battery SOC, grid import/export, heating/cooling.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

from .models import (
    Location, HouseParams, PVParams, BatteryParams, HeatPumpParams,
    RecuperatorParams, ACParams, FloorHeatingParams, AppliancesParams,
    TariffParams, SimulationParams,
)
from .weather import generate_year_weather


@dataclass
class YearResult:
    """Results for a single simulated year."""
    total_consumption_kwh: float = 0.0
    total_pv_generation_kwh: float = 0.0
    pv_self_consumed_kwh: float = 0.0
    pv_exported_kwh: float = 0.0
    grid_imported_kwh: float = 0.0
    battery_cycles: float = 0.0
    heating_kwh_thermal: float = 0.0
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
    # Hourly arrays for visualization (only stored for first year of first run)
    hourly_pv: Optional[np.ndarray] = None
    hourly_demand: Optional[np.ndarray] = None
    hourly_grid: Optional[np.ndarray] = None
    hourly_battery_soc: Optional[np.ndarray] = None
    hourly_heating: Optional[np.ndarray] = None
    scenario_name: str = ""


@dataclass
class SimulationResult:
    """Aggregate results across all runs."""
    year_results: list = field(default_factory=list)
    total_net_cost_mean: float = 0.0
    total_net_cost_std: float = 0.0
    total_net_cost_p5: float = 0.0
    total_net_cost_p95: float = 0.0
    annual_costs: Optional[pd.DataFrame] = None
    investment_cost: float = 0.0
    # Per-scenario summary for year 1
    scenario_year1: Optional[list] = None  # list of YearResult with hourly data


def _pv_output_on_surface(ghi, panel_tilt_deg, panel_azimuth_deg,
                          solar_elevation_deg, day_of_year, latitude):
    """Approximate irradiance on tilted surface from GHI."""
    if ghi <= 0 or solar_elevation_deg <= 0:
        return 0.0

    direct_fraction = min(0.85, max(0.2, solar_elevation_deg / 60.0))
    direct = ghi * direct_fraction
    diffuse = ghi * (1 - direct_fraction)

    tilt_r = np.radians(panel_tilt_deg)
    elev_r = np.radians(solar_elevation_deg)

    cos_incidence = (np.sin(elev_r) * np.cos(tilt_r) +
                     np.cos(elev_r) * np.sin(tilt_r))
    cos_incidence = max(0, cos_incidence)

    if np.sin(elev_r) > 0.01:
        direct_tilted = direct * cos_incidence / np.sin(elev_r)
    else:
        direct_tilted = 0.0

    diffuse_tilted = diffuse * (1 + np.cos(tilt_r)) / 2
    return max(0.0, direct_tilted + diffuse_tilted)


def _solar_elevation_approx(latitude, day_of_year, hour):
    """Quick solar elevation calculation."""
    declination = 23.45 * np.sin(np.radians(360 / 365 * (day_of_year - 81)))
    hour_angle = 15.0 * (hour - 12)
    lat_r = np.radians(latitude)
    dec_r = np.radians(declination)
    ha_r = np.radians(hour_angle)
    sin_elev = (np.sin(lat_r) * np.sin(dec_r) +
                np.cos(lat_r) * np.cos(dec_r) * np.cos(ha_r))
    return np.degrees(np.arcsin(np.clip(sin_elev, -1, 1)))


def _appliance_hourly_factor(hour):
    """Hourly usage profile for appliances (sums to 1.0 over 24h)."""
    profile = [
        0.020, 0.015, 0.015, 0.015, 0.015, 0.025,
        0.040, 0.060, 0.055, 0.040, 0.035, 0.040,
        0.050, 0.045, 0.035, 0.035, 0.045, 0.065,
        0.075, 0.070, 0.060, 0.050, 0.040, 0.030,
    ]
    return profile[hour]


def _hot_water_hourly_factor(hour):
    """Hourly hot water profile (sums to 1.0)."""
    profile = [
        0.01, 0.01, 0.01, 0.01, 0.01, 0.02,
        0.08, 0.12, 0.08, 0.04, 0.03, 0.03,
        0.03, 0.02, 0.02, 0.02, 0.03, 0.05,
        0.08, 0.10, 0.08, 0.06, 0.04, 0.02,
    ]
    return profile[hour]


def simulate_single_run(
    location, house, pv, battery, heat_pump, recuperator,
    ac, floor_heating, appliances, tariff, sim_params,
    rng, scenario_type="normal", store_hourly=False,
):
    """Run simulation for all years in one path.

    scenario_type: "cold", "normal", or "warm" - controls weather bias.
    """
    results = []
    for year_idx in range(sim_params.years):
        # Scenario bias
        if scenario_type == "cold":
            year_variability = rng.uniform(1.1, 1.4)
            temp_bias = -2.0
        elif scenario_type == "warm":
            year_variability = rng.uniform(0.6, 0.9)
            temp_bias = 2.0
        else:
            year_variability = rng.uniform(0.85, 1.15)
            temp_bias = 0.0

        weather = generate_year_weather(
            location.latitude, location.longitude, rng,
            year_variability=year_variability,
        )
        # Apply temperature bias for scenario
        if temp_bias != 0:
            weather.temperature_c = weather.temperature_c + temp_bias

        do_hourly = store_hourly and year_idx == 0
        yr = _simulate_year(
            year_idx, weather, location, house, pv, battery,
            heat_pump, recuperator, ac, floor_heating,
            appliances, tariff, rng, store_hourly=do_hourly,
        )
        yr.scenario_name = scenario_type
        results.append(yr)
    return results


def _simulate_year(
    year_idx, weather, location, house, pv, battery,
    heat_pump, recuperator, ac, floor_heating,
    appliances, tariff, rng, store_hourly=False,
):
    """Simulate one year hour by hour with corrected thermal model."""
    yr = YearResult()
    yr.fixed_costs_pln = tariff.fixed_monthly_cost * 12 * (
        (1 + tariff.annual_price_increase) ** year_idx
    )

    battery_soc_kwh = 0.0
    usable_bat = 0.0
    if battery.enabled:
        usable_bat = battery.usable_kwh * max(0, 1 - battery.degradation_per_year * year_idx)
        battery_soc_kwh = usable_bat * 0.5

    pv_degradation = (1 - pv.degradation_per_year) ** year_idx
    battery_discharged_total = 0.0

    # Hourly storage
    if store_hourly:
        yr.hourly_pv = np.zeros(8760)
        yr.hourly_demand = np.zeros(8760)
        yr.hourly_grid = np.zeros(8760)
        yr.hourly_battery_soc = np.zeros(8760)
        yr.hourly_heating = np.zeros(8760)

    # Precompute house thermal properties
    transmission_loss = house.transmission_loss_coefficient  # W/K
    infiltration_loss = house.infiltration_loss_coefficient  # W/K
    ventilation_loss = house.ventilation_loss_coefficient    # W/K

    # Recuperator only saves on mechanical ventilation portion
    if recuperator.enabled:
        vent_loss_after_recup = ventilation_loss * (1.0 - recuperator.efficiency)
    else:
        vent_loss_after_recup = ventilation_loss

    # Effective total loss coefficient
    effective_loss = transmission_loss + infiltration_loss + vent_loss_after_recup

    for h in range(8760):
        hour_of_day = h % 24
        day_of_year = h // 24
        temp_c = weather.temperature_c[h]
        ghi = weather.ghi_w_m2[h]

        # --- Appliance demand ---
        hourly_profile = _appliance_hourly_factor(hour_of_day)
        base_demand = appliances.base_daily_kwh * hourly_profile

        # --- Hot water ---
        hw_factor = _hot_water_hourly_factor(hour_of_day)
        if heat_pump.enabled:
            cop_hw = max(1.5, heat_pump.cop_at_temp(temp_c) * 0.85)  # DHW needs higher temps
            hw_electric = appliances.hot_water_daily_kwh * hw_factor / cop_hw
        else:
            hw_electric = appliances.hot_water_daily_kwh * hw_factor

        # --- Heating / cooling ---
        heating_electric = 0.0
        cooling_electric = 0.0
        floor_heat_electric = 0.0
        heating_thermal = 0.0

        delta_t_heat = house.target_temp_winter_c - temp_c
        delta_t_cool = temp_c - house.target_temp_summer_c

        if delta_t_heat > 0:
            # Thermal demand in kWh (for 1 hour)
            heating_thermal = effective_loss * delta_t_heat / 1000.0
            yr.heating_kwh_thermal += heating_thermal

            # Primary: heat pump
            if heat_pump.enabled and temp_c >= heat_pump.min_operating_temp_c:
                cop = heat_pump.cop_at_temp(temp_c)
                hp_max_thermal = heat_pump.rated_power_kw  # kW thermal output
                if heating_thermal <= hp_max_thermal:
                    heating_electric = heating_thermal / cop
                else:
                    # HP at max + backup
                    heating_electric = hp_max_thermal / cop
                    remaining = heating_thermal - hp_max_thermal

                    if ac.enabled and ac.heating_capacity_kw > 0:
                        ac_can = ac.num_units * ac.heating_capacity_kw
                        ac_thermal = min(remaining, ac_can)
                        heating_electric += ac_thermal / ac.heating_cop
                        remaining -= ac_thermal

                    if floor_heating.enabled and remaining > 0:
                        fh_can = floor_heating.total_power_kw
                        floor_heat_electric = min(remaining, fh_can)
                        heating_electric += floor_heat_electric
                        remaining -= floor_heat_electric
                        yr.floor_heating_kwh += floor_heat_electric

                    if remaining > 0:
                        heating_electric += remaining  # direct electric fallback
            elif ac.enabled and ac.heating_capacity_kw > 0:
                ac_can = ac.num_units * ac.heating_capacity_kw
                ac_thermal = min(heating_thermal, ac_can)
                heating_electric = ac_thermal / ac.heating_cop
                remaining = heating_thermal - ac_thermal
                if floor_heating.enabled and remaining > 0:
                    floor_heat_electric = min(remaining, floor_heating.total_power_kw)
                    heating_electric += floor_heat_electric
                    yr.floor_heating_kwh += floor_heat_electric
                    remaining -= floor_heat_electric
                if remaining > 0:
                    heating_electric += remaining
            elif floor_heating.enabled:
                floor_heat_electric = min(heating_thermal, floor_heating.total_power_kw)
                heating_electric = floor_heat_electric
                yr.floor_heating_kwh += floor_heat_electric
                remaining = heating_thermal - floor_heat_electric
                if remaining > 0:
                    heating_electric += remaining
            else:
                heating_electric = heating_thermal  # direct electric

            # Supplementary floor heating for comfort (bathrooms)
            if floor_heating.enabled and heat_pump.enabled and delta_t_heat > 5:
                supplement = floor_heating.total_power_kw * 0.1
                heating_electric += supplement
                yr.floor_heating_kwh += supplement

        elif delta_t_cool > 2:
            # Cooling needed
            # Cooling load is less than heating (solar gains help but also cause cooling need)
            cool_demand = effective_loss * (delta_t_cool - 2) * 0.5 / 1000.0
            if heat_pump.enabled and heat_pump.can_cool:
                cooling_electric = cool_demand / heat_pump.cooling_eer
            elif ac.enabled:
                cooling_electric = cool_demand / ac.cooling_eer

        # Recuperator fan power
        recup_power = recuperator.fan_power_w / 1000.0 if recuperator.enabled else 0.0

        total_demand = base_demand + hw_electric + heating_electric + cooling_electric + recup_power

        yr.total_consumption_kwh += total_demand
        yr.heating_kwh_electric += heating_electric
        yr.cooling_kwh_electric += cooling_electric
        yr.hot_water_kwh_electric += hw_electric
        yr.appliances_kwh += base_demand
        yr.recuperator_kwh += recup_power

        # --- PV generation ---
        pv_gen = 0.0
        if pv.enabled and ghi > 0:
            solar_elev = _solar_elevation_approx(location.latitude, day_of_year, hour_of_day)
            if solar_elev > 0:
                irr_tilted = _pv_output_on_surface(
                    ghi, pv.roof_tilt_deg, pv.roof_azimuth_deg,
                    solar_elev, day_of_year, location.latitude,
                )
                pv_gen += (pv.peak_power_kw * (irr_tilted / 1000.0) *
                          (1 - pv.system_losses) * pv_degradation)

                if pv.ground_mount_enabled and pv.ground_mount_kwp > 0:
                    irr_ground = _pv_output_on_surface(
                        ghi, pv.ground_tilt_deg, pv.ground_azimuth_deg,
                        solar_elev, day_of_year, location.latitude,
                    )
                    pv_gen += (pv.ground_mount_kwp * (irr_ground / 1000.0) *
                              (1 - pv.system_losses) * pv_degradation)

        yr.total_pv_generation_kwh += pv_gen

        # --- Energy balance ---
        net = total_demand - pv_gen
        grid_import = 0.0
        grid_export = 0.0

        if net > 0:
            # Need more power
            if battery.enabled and battery_soc_kwh > 0:
                discharge = min(net, battery.max_discharge_kw, battery_soc_kwh)
                battery_soc_kwh -= discharge
                battery_discharged_total += discharge
                net -= discharge

            if net > 0:
                grid_import = net
                yr.grid_imported_kwh += net
                price = tariff.price_at_hour(hour_of_day, year_idx)
                yr.grid_cost_pln += net * price

            yr.pv_self_consumed_kwh += pv_gen
        else:
            surplus = -net
            yr.pv_self_consumed_kwh += total_demand

            if battery.enabled:
                charge = min(surplus, battery.max_charge_kw,
                           max(0, usable_bat - battery_soc_kwh))
                battery_soc_kwh += charge * battery.round_trip_efficiency
                surplus -= charge

            if surplus > 0:
                grid_export = surplus
                yr.pv_exported_kwh += surplus
                yr.feed_in_income_pln += surplus * tariff.feed_in_at_year(year_idx)

        # Store hourly data (positive = grid import, negative = grid export)
        if store_hourly:
            yr.hourly_pv[h] = pv_gen
            yr.hourly_demand[h] = total_demand
            yr.hourly_grid[h] = grid_import - grid_export
            yr.hourly_battery_soc[h] = battery_soc_kwh if battery.enabled else 0
            yr.hourly_heating[h] = heating_electric

    yr.net_cost_pln = yr.grid_cost_pln + yr.fixed_costs_pln - yr.feed_in_income_pln
    if battery.enabled and usable_bat > 0:
        yr.battery_cycles = battery_discharged_total / usable_bat
    return yr


def run_monte_carlo(
    location, house, pv, battery, heat_pump, recuperator,
    ac, floor_heating, appliances, tariff, sim_params,
    progress_callback=None,
):
    """Run simulation with 3 scenarios (cold/normal/warm) x N repeats."""
    seed = sim_params.random_seed
    rng = np.random.default_rng(seed)

    scenarios = ["cold", "normal", "warm"]
    runs_per_scenario = max(1, sim_params.num_simulations // 3)

    all_runs = []
    scenario_year1 = []
    total_work = len(scenarios) * runs_per_scenario
    done = 0

    for scenario in scenarios:
        for i in range(runs_per_scenario):
            store = (i == 0)  # store hourly for first run of each scenario
            run_results = simulate_single_run(
                location, house, pv, battery, heat_pump, recuperator,
                ac, floor_heating, appliances, tariff, sim_params,
                rng, scenario_type=scenario, store_hourly=store,
            )
            all_runs.append(run_results)
            if store and len(run_results) > 0:
                scenario_year1.append(run_results[0])
            done += 1
            if progress_callback:
                progress_callback(done / total_work)

    # Aggregate
    result = SimulationResult()
    result.year_results = all_runs
    result.scenario_year1 = scenario_year1

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

    # Total costs
    total_costs = np.array([sum(yr.net_cost_pln for yr in run) for run in all_runs])
    result.total_net_cost_mean = float(np.mean(total_costs))
    result.total_net_cost_std = float(np.std(total_costs))
    result.total_net_cost_p5 = float(np.percentile(total_costs, 5))
    result.total_net_cost_p95 = float(np.percentile(total_costs, 95))

    annual_data = [[yr.net_cost_pln for yr in run] for run in all_runs]
    result.annual_costs = pd.DataFrame(
        annual_data,
        columns=[f"Year {i+1}" for i in range(sim_params.years)],
    )

    return result
