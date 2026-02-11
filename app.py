"""House Electricity Simulator - Streamlit Application."""

import math
import json
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium

from simulator.models import (
    Location, HouseParams, PVParams, BatteryParams, HeatPumpParams,
    RecuperatorParams, ACParams, FloorHeatingParams, Appliance,
    AppliancesParams, TariffParams, SimulationParams,
    default_appliances, params_to_dict, params_from_dict,
)
from simulator.engine import run_monte_carlo
from simulator.weather import generate_year_weather
from simulator.i18n import t, APPLIANCE_KEY_MAP

st.set_page_config(page_title="Home Energy Simulator", page_icon="\U0001F3E0",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
.block-container {padding-top: 1rem; padding-bottom: 1rem;}
div[data-testid="stMetric"] {background-color: #f0f2f6; border-radius: 8px; padding: 12px;}
</style>""", unsafe_allow_html=True)

CURRENCY = "PLN"
CITY_COORDS = {
    "Wroclaw": (51.1, 17.0), "Warszawa": (52.23, 21.0),
    "Krakow": (50.06, 19.94), "Gdansk": (54.35, 18.65),
    "Poznan": (52.41, 16.93), "Szczecin": (53.43, 14.55),
}

# ══════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════

with st.sidebar:
    lang = st.selectbox("Language / Jezyk", ["en", "pl"],
                        format_func=lambda x: {"en": "English", "pl": "Polski"}[x])
    st.header(t("configuration", lang))

    # ── Import / Export ──
    with st.expander(t("import_settings", lang) + " / " + t("export_settings", lang)):
        uploaded = st.file_uploader(t("upload_json", lang), type=["json"], key="import_json")
        if uploaded is not None:
            try:
                data = json.loads(uploaded.read().decode("utf-8"))
                st.session_state["imported_settings"] = data
                st.success(t("settings_imported", lang))
            except Exception:
                st.error(t("settings_import_error", lang))
        if st.button(t("export_settings", lang), key="btn_export"):
            st.session_state["do_export"] = True

    # ── Location ──
    with st.expander(t("location", lang), expanded=True):
        city_options = list(CITY_COORDS.keys()) + [t("other", lang)]
        city = st.selectbox(t("city", lang), city_options, index=0)
        if city == t("other", lang):
            lat = st.number_input(t("latitude", lang), 49.0, 55.0,
                                  st.session_state.get("map_lat", 51.1), 0.1)
            lon = st.number_input(t("longitude", lang), 14.0, 24.0,
                                  st.session_state.get("map_lon", 17.0), 0.1)
        else:
            lat, lon = CITY_COORDS[city]
            if "map_lat" in st.session_state and st.session_state.get("map_city_override"):
                lat = st.session_state["map_lat"]
                lon = st.session_state["map_lon"]
            st.caption(t("coordinates", lang, lat=lat, lon=lon))
        location = Location(latitude=lat, longitude=lon, city_name=city)

    # ── House ──
    with st.expander(t("house", lang), expanded=True):
        h_area = st.slider(t("area_m2", lang), 60, 400, 150, 10)
        h_floors = st.selectbox(t("floors", lang), [1, 2, 3], index=1)
        h_insulation = st.select_slider(t("wall_insulation", lang),
                                        options=[10, 15, 20, 25, 30], value=20)
        h_window_u = st.slider(t("window_u", lang), 0.5, 1.5, 0.9, 0.1)
        thermal_labels = {"low": t("thermal_low", lang), "medium": t("thermal_medium", lang),
                          "high": t("thermal_high", lang)}
        h_thermal = st.selectbox(t("thermal_mass", lang), ["low", "medium", "high"],
                                 format_func=lambda x: thermal_labels[x], index=1)
        h_vent = st.slider(t("ventilation_rate", lang), 100, 500, 200, 25)
        h_target_winter = st.slider(t("target_temp_winter", lang), 18.0, 24.0, 21.0, 0.5)
        h_target_summer = st.slider(t("target_temp_summer", lang), 22.0, 28.0, 24.0, 0.5)
        house = HouseParams(area_m2=h_area, floors=h_floors, wall_insulation_cm=h_insulation,
                            window_u_value=h_window_u, thermal_mass=h_thermal,
                            ventilation_rate_m3h=h_vent,
                            target_temp_winter_c=h_target_winter, target_temp_summer_c=h_target_summer)

    # ── PV ──
    with st.expander(t("pv_panels", lang), expanded=True):
        pv_enabled = st.checkbox(t("pv_enabled", lang), value=True)
        if pv_enabled:
            pv_kwp = st.slider(t("pv_peak_power", lang), 2.0, 30.0, 10.0, 0.5)
            pv_tilt = st.slider(t("pv_roof_tilt", lang), 0, 60, 35, 5)
            pv_azimuth = st.slider(t("pv_azimuth", lang), 90, 270, 180, 10,
                                   help=t("pv_azimuth_help", lang))
            pv_cost = st.number_input(t("pv_cost_per_kwp", lang, currency=CURRENCY),
                                      2000, 8000, 4500, 100)
            pv_ground = st.checkbox(t("pv_ground", lang))
            pv_ground_kwp = st.slider(t("pv_ground_power", lang), 1.0, 20.0, 5.0, 0.5) if pv_ground else 0.0
        else:
            pv_kwp, pv_tilt, pv_azimuth, pv_cost = 0, 35, 180, 4500
            pv_ground, pv_ground_kwp = False, 0.0
        pv_params = PVParams(enabled=pv_enabled, peak_power_kw=pv_kwp, roof_tilt_deg=pv_tilt,
                             roof_azimuth_deg=pv_azimuth, cost_per_kwp=pv_cost,
                             ground_mount_enabled=pv_ground, ground_mount_kwp=pv_ground_kwp)

    # ── Battery ──
    with st.expander(t("battery", lang)):
        bat_enabled = st.checkbox(t("battery_enabled", lang), value=False)
        if bat_enabled:
            bat_kwh = st.slider(t("battery_capacity", lang), 2.0, 30.0, 10.0, 1.0)
            bat_cost = st.number_input(t("battery_cost", lang, currency=CURRENCY),
                                       5000, 80000, 25000, 1000)
        else:
            bat_kwh, bat_cost = 10.0, 25000
        battery = BatteryParams(enabled=bat_enabled, capacity_kwh=bat_kwh, cost_total=bat_cost)

    # ── Heat Pump ──
    with st.expander(t("heat_pump", lang), expanded=True):
        hp_enabled = st.checkbox(t("hp_enabled", lang), value=True)
        if hp_enabled:
            hp_power = st.slider(t("hp_power", lang), 4.0, 16.0, 8.0, 1.0)
            hp_cop7 = st.slider(t("hp_cop_7", lang), 2.5, 6.0, 4.0, 0.1)
            hp_cop_m7 = st.slider(t("hp_cop_m7", lang), 1.5, 4.0, 2.5, 0.1)
            hp_cool = st.checkbox(t("hp_cooling", lang), value=True)
            hp_cost = st.number_input(t("hp_cost", lang, currency=CURRENCY), 15000, 70000, 35000, 1000)
        else:
            hp_power, hp_cop7, hp_cop_m7, hp_cool, hp_cost = 8.0, 4.0, 2.5, True, 35000
        heat_pump = HeatPumpParams(enabled=hp_enabled, rated_power_kw=hp_power,
                                   cop_at_7c=hp_cop7, cop_at_minus7c=hp_cop_m7,
                                   can_cool=hp_cool, cost_total=hp_cost)

    # ── Recuperator ──
    with st.expander(t("recuperator", lang)):
        rec_enabled = st.checkbox(t("rec_enabled", lang), value=True)
        if rec_enabled:
            rec_eff = st.slider(t("rec_efficiency", lang), 0.5, 0.95, 0.85, 0.05)
            rec_cost = st.number_input(t("rec_cost", lang, currency=CURRENCY), 5000, 30000, 15000, 1000)
        else:
            rec_eff, rec_cost = 0.85, 15000
        recuperator = RecuperatorParams(enabled=rec_enabled, efficiency=rec_eff, cost_total=rec_cost)

    # ── AC ──
    with st.expander(t("ac", lang)):
        ac_enabled = st.checkbox(t("ac_enabled", lang), value=False)
        if ac_enabled:
            ac_units = st.slider(t("ac_units", lang), 1, 5, 2)
            ac_cool_cap = st.slider(t("ac_cooling", lang), 2.0, 7.0, 3.5, 0.5)
            ac_cost_unit = st.number_input(t("ac_cost_unit", lang, currency=CURRENCY), 2000, 10000, 4000, 500)
        else:
            ac_units, ac_cool_cap, ac_cost_unit = 2, 3.5, 4000
        ac_params = ACParams(enabled=ac_enabled, num_units=ac_units,
                             cooling_capacity_kw=ac_cool_cap, cost_per_unit=ac_cost_unit)

    # ── Floor Heating ──
    with st.expander(t("floor_heating", lang)):
        fh_enabled = st.checkbox(t("fh_enabled", lang), value=False)
        if fh_enabled:
            fh_area = st.slider(t("fh_area", lang), 5, 100, 30, 5)
            fh_power = st.slider(t("fh_power", lang), 100, 200, 150, 10)
            fh_cost_m2 = st.number_input(t("fh_cost_per_m2", lang, currency=CURRENCY), 50, 500, 200, 25)
        else:
            fh_area, fh_power, fh_cost_m2 = 30, 150, 200
        floor_heating = FloorHeatingParams(enabled=fh_enabled, area_m2=fh_area,
                                           power_per_m2_w=fh_power, cost_per_m2=fh_cost_m2)

    # ── Appliances (with power editing) ──
    with st.expander(t("appliances", lang)):
        st.caption(t("appliances_hint", lang))
        defaults = default_appliances()
        custom_appliances = []
        for app in defaults:
            tr_key = APPLIANCE_KEY_MAP.get(app.name, app.name)
            display_name = t(tr_key, lang)
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1:
                hours = st.number_input(f"{display_name} - {t('hours_per_day', lang)}",
                                        0.0, 24.0, float(app.daily_hours), 0.1,
                                        key=f"app_h_{app.name}")
            with c2:
                power = st.number_input(f"{t('power_watts', lang)}",
                                        1, 10000, int(app.power_w), 10,
                                        key=f"app_w_{app.name}")
            with c3:
                count = st.number_input(t("pieces", lang), 0, 10, app.count, 1,
                                        key=f"app_c_{app.name}")
            custom_appliances.append(Appliance(name=display_name, power_w=power,
                                               daily_hours=hours, count=count, standby_w=app.standby_w))
        hw_kwh = st.slider(t("hot_water", lang), 2.0, 15.0, 5.0, 0.5)
        appliances = AppliancesParams(appliances=custom_appliances, hot_water_daily_kwh=hw_kwh)

    # ── Tariff ──
    with st.expander(t("tariff", lang), expanded=True):
        dual = st.checkbox(t("dual_tariff", lang), value=False)
        if dual:
            t_day = st.number_input(t("price_day", lang, currency=CURRENCY), 0.30, 2.00, 0.75, 0.05)
            t_night = st.number_input(t("price_night", lang, currency=CURRENCY), 0.20, 1.50, 0.45, 0.05)
            t_single = (t_day + t_night) / 2
        else:
            t_single = st.number_input(t("price_single", lang, currency=CURRENCY), 0.30, 2.00, 0.65, 0.05)
            t_day = t_night = t_single
        t_feed = st.number_input(t("feed_in", lang, currency=CURRENCY), 0.0, 1.50, 0.40, 0.05)
        t_fixed = st.number_input(t("fixed_monthly", lang, currency=CURRENCY), 0.0, 200.0, 30.0, 5.0)
        t_increase = st.slider(t("annual_increase", lang), 0, 15, 3) / 100.0
        tariff = TariffParams(price_per_kwh=t_single, dual_tariff=dual, day_price=t_day,
                              night_price=t_night, feed_in_tariff=t_feed,
                              fixed_monthly_cost=t_fixed, annual_price_increase=t_increase)

    # ── Simulation ──
    with st.expander(t("sim_params", lang)):
        sim_years = st.slider(t("sim_years", lang), 1, 30, 10)
        sim_n = st.slider(t("sim_runs", lang), 3, 300, 9, 3,
                          help="3 scenarios (cold/normal/warm) x N repeats")
        sim_seed = st.number_input(t("sim_seed", lang), 0, 99999, 0)
        sim_params = SimulationParams(years=sim_years, num_simulations=sim_n,
                                      random_seed=sim_seed if sim_seed > 0 else None)

# Investment total
total_inv = 0.0
if pv_params.enabled: total_inv += pv_params.total_cost
if battery.enabled: total_inv += battery.cost_total
if heat_pump.enabled: total_inv += heat_pump.cost_total
if recuperator.enabled: total_inv += recuperator.cost_total
if ac_params.enabled: total_inv += ac_params.total_cost
if floor_heating.enabled: total_inv += floor_heating.total_cost

# Handle export
if st.session_state.get("do_export"):
    export_data = params_to_dict(location, house, pv_params, battery, heat_pump,
                                 recuperator, ac_params, floor_heating, appliances, tariff, sim_params)
    st.session_state["do_export"] = False
    st.sidebar.download_button("Download JSON", json.dumps(export_data, indent=2, ensure_ascii=False),
                               "energy_sim_settings.json", "application/json")

# ── Title ──
st.title(t("app_title", lang))
st.caption(t("app_subtitle", lang))

tab_map, tab_results, tab_energy, tab_weather, tab_details = st.tabs([
    t("tab_map", lang), t("tab_results", lang),
    t("hourly_profiles", lang), t("tab_weather", lang), t("tab_details", lang),
])

# ══════════════════════════════════════════════════════════════════════════
# TAB 1: Map
# ══════════════════════════════════════════════════════════════════════════

def _house_polygon(lat, lon, azimuth_deg, size_m=40):
    w, d, peak = size_m / 2, size_m / 2, size_m * 0.35
    pts = [(-w, -d), (w, -d), (w, d), (0, d + peak), (-w, d)]
    a = math.radians(azimuth_deg - 180)
    ca, sa = math.cos(a), math.sin(a)
    mlat, mlon = 111320.0, 111320.0 * math.cos(math.radians(lat))
    coords = [[lat + (x * sa + y * ca) / mlat, lon + (x * ca - y * sa) / mlon] for x, y in pts]
    coords.append(coords[0])
    return coords

def _pv_polygon(lat, lon, azimuth_deg, size_m=40):
    w, d, peak = size_m / 2 * 0.8, size_m / 2, size_m * 0.35
    pts = [(-w * 0.9, d * 0.3), (w * 0.9, d * 0.3), (0, d + peak * 0.85)]
    a = math.radians(azimuth_deg - 180)
    ca, sa = math.cos(a), math.sin(a)
    mlat, mlon = 111320.0, 111320.0 * math.cos(math.radians(lat))
    coords = [[lat + (x * sa + y * ca) / mlat, lon + (x * ca - y * sa) / mlon] for x, y in pts]
    coords.append(coords[0])
    return coords

with tab_map:
    st.subheader(t("map_header", lang))
    st.caption(t("map_hint", lang))
    map_col, info_col = st.columns([3, 2])

    with map_col:
        m = folium.Map(location=[lat, lon], zoom_start=17, tiles="OpenStreetMap")
        azimuth = pv_azimuth if pv_enabled else 180
        folium.Polygon(locations=_house_polygon(lat, lon, azimuth), color="#5C6BC0",
                       fill=True, fill_color="#7986CB", fill_opacity=0.6, weight=2,
                       tooltip=f"{t('house', lang)}: {house.area_m2}m\u00b2").add_to(m)
        if pv_enabled:
            folium.Polygon(locations=_pv_polygon(lat, lon, azimuth), color="#F57F17",
                           fill=True, fill_color="#FFD54F", fill_opacity=0.7, weight=2,
                           tooltip=f"PV: {pv_params.total_kwp:.1f} kWp").add_to(m)
        # Direction arrow
        mlat, mlon = 111320.0, 111320.0 * math.cos(math.radians(lat))
        ae_lat = lat + 60 * math.cos(math.radians(180 - azimuth)) / mlat
        ae_lon = lon + 60 * math.sin(math.radians(azimuth - 180)) / mlon
        dir_labels = {0: "N", 45: "NE", 90: "E", 135: "SE", 180: "S", 225: "SW", 270: "W", 315: "NW"}
        dir_label = dir_labels[min(dir_labels, key=lambda d: abs(d - azimuth))]
        folium.PolyLine([[lat, lon], [ae_lat, ae_lon]], color="#E53935", weight=3, dash_array="8",
                        tooltip=f"{t('roof_direction', lang)}: {azimuth}\u00b0 ({dir_label})").add_to(m)
        folium.Marker([ae_lat, ae_lon], icon=folium.DivIcon(
            html=f'<div style="font-size:14px;font-weight:bold;color:#E53935">{dir_label}</div>',
            icon_size=(30, 20), icon_anchor=(15, 10))).add_to(m)
        map_data = st_folium(m, width=None, height=500, returned_objects=["last_clicked"])
        if map_data and map_data.get("last_clicked"):
            c = map_data["last_clicked"]
            nl, no = round(c["lat"], 4), round(c["lng"], 4)
            if abs(nl - lat) > 0.0001 or abs(no - lon) > 0.0001:
                st.session_state["map_lat"] = nl
                st.session_state["map_lon"] = no
                st.session_state["map_city_override"] = True
                st.rerun()
        st.caption(f"{t('current_location', lang)}: {lat:.4f}\u00b0N, {lon:.4f}\u00b0E")

    with info_col:
        st.markdown(f"**{t('house_label', lang)}**")
        st.write(f"- {t('area_label', lang)}: {house.area_m2} m\u00b2 | {t('floors_label', lang)}: {house.floors}")
        st.write(f"- {t('insulation_label', lang)}: {house.wall_insulation_cm} cm | {t('windows_label', lang)}: {house.window_u_value}")
        st.write(f"- {t('heat_loss_label', lang)}: {house.envelope_loss_coefficient:.0f} W/K "
                 f"(trans: {house.transmission_loss_coefficient:.0f}, vent: {house.ventilation_loss_coefficient:.0f}, "
                 f"infil: {house.infiltration_loss_coefficient:.0f})")

        st.markdown(f"**{t('energy_systems', lang)}**")
        if pv_params.enabled: st.write(f"- PV: {pv_params.total_kwp:.1f} kWp ({azimuth}\u00b0)")
        if battery.enabled: st.write(f"- {t('battery', lang)}: {battery.capacity_kwh} kWh")
        if heat_pump.enabled: st.write(f"- {t('heat_pump', lang)}: {heat_pump.rated_power_kw} kW")
        if recuperator.enabled: st.write(f"- {t('recuperator', lang)}: {recuperator.efficiency*100:.0f}%")
        if ac_params.enabled: st.write(f"- {t('ac', lang)}: {ac_params.num_units}x {ac_params.cooling_capacity_kw} kW")
        if floor_heating.enabled: st.write(f"- {t('floor_heating', lang)}: {floor_heating.area_m2} m\u00b2")

        st.markdown(f"**{t('investment_costs', lang)}**")
        for name, cost in [(t("pv_panels", lang), pv_params.total_cost)] * pv_params.enabled + \
                          [(t("battery", lang), battery.cost_total)] * battery.enabled + \
                          [(t("heat_pump", lang), heat_pump.cost_total)] * heat_pump.enabled + \
                          [(t("recuperator", lang), recuperator.cost_total)] * recuperator.enabled + \
                          [(t("ac", lang), ac_params.total_cost)] * ac_params.enabled + \
                          [(t("floor_heating", lang), floor_heating.total_cost)] * floor_heating.enabled:
            st.write(f"- {name}: {cost:,.0f} {CURRENCY}")
        st.markdown(f"**{t('total', lang)}: {total_inv:,.0f} {CURRENCY}**")
        st.divider()
        st.write(f"**{t('base_consumption', lang)}:** {appliances.base_daily_kwh:.1f} kWh{t('per_day', lang)} "
                 f"({appliances.base_daily_kwh * 365:.0f} kWh{t('per_year', lang)})")

# ══════════════════════════════════════════════════════════════════════════
# TAB 2: Simulation Results
# ══════════════════════════════════════════════════════════════════════════

with tab_results:
    if st.button(t("run_simulation", lang), type="primary", use_container_width=True):
        progress_bar = st.progress(0.0, text=t("simulation_running", lang))
        def update_progress(frac):
            progress_bar.progress(frac, text=t("simulation_progress", lang, pct=frac * 100))
        result = run_monte_carlo(location, house, pv_params, battery, heat_pump,
                                 recuperator, ac_params, floor_heating, appliances,
                                 tariff, sim_params, progress_callback=update_progress)
        progress_bar.empty()
        st.session_state["result"] = result
        st.session_state["sim_params_r"] = sim_params
        st.session_state["investment_r"] = total_inv

    if "result" in st.session_state:
        result = st.session_state["result"]
        sim_p = st.session_state["sim_params_r"]
        investment = st.session_state["investment_r"]

        # ── Scenario comparison table ──
        if result.scenario_year1:
            st.subheader(t("scenario_comparison", lang))
            sc_data = []
            for yr in result.scenario_year1:
                sc_name = {"cold": t("scenario_cold", lang), "normal": t("scenario_normal", lang),
                           "warm": t("scenario_warm", lang)}.get(yr.scenario_name, yr.scenario_name)
                sc_data.append({
                    "": sc_name,
                    t("total_consumption", lang): f"{yr.total_consumption_kwh:,.0f} kWh",
                    t("heating_thermal", lang): f"{yr.heating_kwh_thermal:,.0f} kWh",
                    t("heating_electric", lang): f"{yr.heating_kwh_electric:,.0f} kWh",
                    t("pv_generation", lang): f"{yr.total_pv_generation_kwh:,.0f} kWh",
                    t("grid_import_label", lang): f"{yr.grid_imported_kwh:,.0f} kWh",
                    t("net_cost_label", lang): f"{yr.net_cost_pln:,.0f} {CURRENCY}",
                })
            st.dataframe(pd.DataFrame(sc_data), use_container_width=True, hide_index=True)

        st.subheader(t("cost_summary", lang))
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric(t("energy_cost_period", lang, years=sim_p.years),
                      f"{result.total_net_cost_mean:,.0f} {CURRENCY}",
                      help=t("cost_help", lang))
        with c2:
            st.metric(t("total_with_investment", lang),
                      f"{result.total_net_cost_mean + investment:,.0f} {CURRENCY}")
        with c3:
            st.metric(t("monthly_average", lang),
                      f"{result.total_net_cost_mean / sim_p.years / 12:,.0f} {CURRENCY}")
        with c4:
            st.metric(t("spread_5_95", lang),
                      f"{result.total_net_cost_p5:,.0f} - {result.total_net_cost_p95:,.0f}")

        st.divider()

        # Annual costs chart
        st.subheader(t("annual_costs", lang))
        annual_df = result.annual_costs
        years = list(range(1, sim_p.years + 1))
        means = annual_df.mean()
        p5, p25, p75, p95 = (annual_df.quantile(q) for q in [0.05, 0.25, 0.75, 0.95])
        fig_a = go.Figure()
        fig_a.add_trace(go.Scatter(x=years, y=p95.values, mode="lines", line=dict(width=0), showlegend=False))
        fig_a.add_trace(go.Scatter(x=years, y=p5.values, mode="lines", line=dict(width=0),
                                   fill="tonexty", fillcolor="rgba(255,107,53,0.15)", name=t("range_5_95", lang)))
        fig_a.add_trace(go.Scatter(x=years, y=p75.values, mode="lines", line=dict(width=0), showlegend=False))
        fig_a.add_trace(go.Scatter(x=years, y=p25.values, mode="lines", line=dict(width=0),
                                   fill="tonexty", fillcolor="rgba(255,107,53,0.3)", name=t("range_25_75", lang)))
        fig_a.add_trace(go.Scatter(x=years, y=means.values, mode="lines+markers",
                                   line=dict(color="#FF6B35", width=3), name=t("mean", lang)))
        fig_a.update_layout(xaxis_title=t("year", lang), yaxis_title=t("net_cost_year", lang),
                            template="plotly_white", height=400)
        st.plotly_chart(fig_a, use_container_width=True)

        # Energy balance
        st.subheader(t("energy_balance", lang))
        fy = [run[0] for run in result.year_results]
        avg = lambda attr: np.mean([getattr(y, attr) for y in fy])
        avg_gen = avg("total_pv_generation_kwh")
        avg_cons = avg("total_consumption_kwh")
        avg_self = avg("pv_self_consumed_kwh")
        avg_export = avg("pv_exported_kwh")
        avg_grid = avg("grid_imported_kwh")
        avg_heat = avg("heating_kwh_electric")
        avg_cool = avg("cooling_kwh_electric")
        avg_hw = avg("hot_water_kwh_electric")
        avg_appl = avg("appliances_kwh")

        c1, c2 = st.columns(2)
        with c1:
            fig = go.Figure(data=[go.Pie(labels=[t("self_consumption", lang), t("grid_export", lang)],
                                         values=[avg_self, avg_export],
                                         marker_colors=["#FF6B35", "#FFC107"], hole=0.4)])
            fig.update_layout(title=t("pv_production", lang, val=avg_gen), height=350)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = go.Figure(data=[go.Pie(
                labels=[t("heating", lang), t("cooling", lang), t("hot_water_label", lang), t("appliances_label", lang)],
                values=[avg_heat, avg_cool, avg_hw, avg_appl],
                marker_colors=["#E53935", "#42A5F5", "#FF9800", "#66BB6A"], hole=0.4)])
            fig.update_layout(title=t("consumption_label", lang, val=avg_cons), height=350)
            st.plotly_chart(fig, use_container_width=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            autarky = (1 - avg_grid / avg_cons) * 100 if avg_cons > 0 else 0
            st.metric(t("energy_autarky", lang), f"{autarky:.0f}%", help=t("autarky_help", lang))
        with c2:
            sc_rate = (avg_self / avg_gen) * 100 if avg_gen > 0 else 0
            st.metric(t("pv_self_consumption", lang), f"{sc_rate:.0f}%", help=t("self_consumption_help", lang))
        with c3:
            st.metric(t("grid_import", lang), f"{avg_grid:,.0f} kWh/yr")

        # Histogram
        st.subheader(t("cost_distribution", lang))
        tc = [sum(yr.net_cost_pln for yr in run) for run in result.year_results]
        fig_h = go.Figure(data=[go.Histogram(x=tc, nbinsx=30, marker_color="#FF6B35", opacity=0.8)])
        fig_h.add_vline(x=np.mean(tc), line_dash="dash", line_color="red", annotation_text=t("mean", lang))
        fig_h.update_layout(xaxis_title=t("total_net_cost", lang, years=sim_p.years, currency=CURRENCY),
                            yaxis_title=t("simulation_count", lang), template="plotly_white", height=350)
        st.plotly_chart(fig_h, use_container_width=True)

        # ROI
        if investment > 0:
            st.subheader(t("roi_analysis", lang))
            no_sys = avg_cons * tariff.price_per_kwh
            with_sys = result.total_net_cost_mean / sim_p.years
            savings = no_sys - with_sys
            if savings > 0:
                st.metric(t("estimated_payback", lang), f"{investment / savings:.1f} {t('years_unit', lang)}",
                         help=t("payback_help", lang))
            fig_r = go.Figure()
            cum_no = np.cumsum([no_sys * (1 + tariff.annual_price_increase) ** (y-1) for y in years])
            cum_with = investment + np.cumsum(means.values)
            fig_r.add_trace(go.Scatter(x=years, y=cum_no, name=t("without_system", lang),
                                       line=dict(color="gray", dash="dash")))
            fig_r.add_trace(go.Scatter(x=years, y=cum_with, name=t("with_system", lang),
                                       line=dict(color="#FF6B35")))
            fig_r.update_layout(xaxis_title=t("year", lang),
                                yaxis_title=t("cumulative_cost", lang, currency=CURRENCY),
                                template="plotly_white", height=400)
            st.plotly_chart(fig_r, use_container_width=True)
    else:
        st.info(t("click_to_run", lang))

# ══════════════════════════════════════════════════════════════════════════
# TAB 3: Hourly Energy Profiles
# ══════════════════════════════════════════════════════════════════════════

with tab_energy:
    if "result" in st.session_state and st.session_state["result"].scenario_year1:
        scenario_data = st.session_state["result"].scenario_year1
        scenario_names = {
            "cold": t("scenario_cold", lang),
            "normal": t("scenario_normal", lang),
            "warm": t("scenario_warm", lang),
        }
        # Pick scenario to show
        options = [yr.scenario_name for yr in scenario_data if yr.hourly_pv is not None]
        if options:
            chosen = st.selectbox("Scenario", options,
                                  format_func=lambda x: scenario_names.get(x, x))
            yr = [y for y in scenario_data if y.scenario_name == chosen and y.hourly_pv is not None][0]

            # Weekly averages for cleaner plots
            weeks = 52
            def weekly(arr):
                return np.array([arr[w*168:(w+1)*168].mean() for w in range(weeks)])

            w_pv = weekly(yr.hourly_pv)
            w_demand = weekly(yr.hourly_demand)
            w_grid = weekly(yr.hourly_grid)
            w_heat = weekly(yr.hourly_heating)
            week_nums = list(range(1, weeks + 1))

            # PV vs Demand
            st.subheader(t("pv_vs_demand", lang) + f" ({t('weekly_avg', lang)})")
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=week_nums, y=w_demand, name=t("demand_monthly", lang),
                                     fill="tozeroy", fillcolor="rgba(229,57,53,0.2)",
                                     line=dict(color="#E53935")))
            fig.add_trace(go.Scatter(x=week_nums, y=w_pv, name=t("pv_gen_monthly", lang),
                                     fill="tozeroy", fillcolor="rgba(255,193,7,0.3)",
                                     line=dict(color="#FFC107")))
            fig.add_trace(go.Scatter(x=week_nums, y=w_heat, name=t("heating", lang),
                                     line=dict(color="#FF6B35", dash="dot")))
            fig.update_layout(xaxis_title=f"Week", yaxis_title=t("kwh", lang),
                              template="plotly_white", height=400)
            st.plotly_chart(fig, use_container_width=True)

            # Battery SOC
            if battery.enabled and yr.hourly_battery_soc is not None:
                st.subheader(t("battery_soc", lang))
                w_soc = weekly(yr.hourly_battery_soc)
                fig_b = go.Figure()
                fig_b.add_trace(go.Scatter(x=week_nums, y=w_soc,
                                           fill="tozeroy", fillcolor="rgba(92,107,192,0.3)",
                                           line=dict(color="#5C6BC0"), name="SOC"))
                fig_b.update_layout(xaxis_title="Week", yaxis_title="kWh",
                                    template="plotly_white", height=300)
                st.plotly_chart(fig_b, use_container_width=True)

            # Monthly energy balance
            st.subheader(t("monthly_energy", lang))
            days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            months_labels = t("months", lang)
            m_pv, m_demand, m_grid = [], [], []
            start = 0
            for d in days_in_month:
                end = start + d * 24
                m_pv.append(yr.hourly_pv[start:end].sum())
                m_demand.append(yr.hourly_demand[start:end].sum())
                m_grid.append(max(0, yr.hourly_grid[start:end].sum()))
                start = end

            fig_m = go.Figure()
            fig_m.add_trace(go.Bar(x=months_labels, y=m_demand, name=t("demand_monthly", lang),
                                   marker_color="#E53935"))
            fig_m.add_trace(go.Bar(x=months_labels, y=m_pv, name=t("pv_gen_monthly", lang),
                                   marker_color="#FFC107"))
            fig_m.add_trace(go.Bar(x=months_labels, y=m_grid, name=t("grid_monthly", lang),
                                   marker_color="#78909C"))
            fig_m.update_layout(barmode="group", template="plotly_white", height=400,
                                yaxis_title=t("kwh", lang))
            st.plotly_chart(fig_m, use_container_width=True)
        else:
            st.info(t("click_to_run", lang))
    else:
        st.info(t("click_to_run", lang))

# ══════════════════════════════════════════════════════════════════════════
# TAB 4: Weather
# ══════════════════════════════════════════════════════════════════════════

with tab_weather:
    st.subheader(t("weather_header", lang))
    st.caption(t("weather_hint", lang))
    if st.button(t("generate_weather", lang), key="gen_weather"):
        rng = np.random.default_rng(42)
        weather = generate_year_weather(location.latitude, location.longitude, rng)
        dt = weather.temperature_c.reshape(365, 24)
        daily_avg, daily_max, daily_min = dt.mean(1), dt.max(1), dt.min(1)
        fig_t = go.Figure()
        fig_t.add_trace(go.Scatter(x=list(range(365)), y=daily_max, mode="lines",
                                   line=dict(width=0), showlegend=False))
        fig_t.add_trace(go.Scatter(x=list(range(365)), y=daily_min, mode="lines",
                                   line=dict(width=0), fill="tonexty", fillcolor="rgba(255,107,53,0.2)",
                                   name=t("daily_range", lang)))
        fig_t.add_trace(go.Scatter(x=list(range(365)), y=daily_avg, mode="lines",
                                   line=dict(color="#FF6B35"), name=t("daily_avg", lang)))
        fig_t.update_layout(title=t("temperature", lang), xaxis_title=t("day_of_year", lang),
                            yaxis_title="\u00b0C", template="plotly_white", height=300)
        st.plotly_chart(fig_t, use_container_width=True)

        daily_ghi = weather.ghi_w_m2.reshape(365, 24).sum(1) / 1000
        fig_s = go.Figure(data=[go.Bar(x=list(range(365)), y=daily_ghi, marker_color="#FFC107")])
        fig_s.update_layout(title=t("solar_irradiance", lang), xaxis_title=t("day_of_year", lang),
                            yaxis_title=t("kwh_m2_day", lang), template="plotly_white", height=300)
        st.plotly_chart(fig_s, use_container_width=True)

        ml = t("months", lang)
        dim = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        mt, ms = [], []
        s = 0
        for d in dim:
            e = s + d * 24
            mt.append(weather.temperature_c[s:e].mean())
            ms.append(weather.ghi_w_m2[s:e].sum() / 1000)
            s = e
        fig_mm = make_subplots(specs=[[{"secondary_y": True}]])
        fig_mm.add_trace(go.Bar(x=ml, y=ms, name=t("solar_monthly", lang), marker_color="#FFC107"), secondary_y=False)
        fig_mm.add_trace(go.Scatter(x=ml, y=mt, name=t("avg_temp", lang),
                                    line=dict(color="#E53935", width=3)), secondary_y=True)
        fig_mm.update_layout(title=t("monthly_summary", lang), template="plotly_white", height=350)
        fig_mm.update_yaxes(title_text="kWh/m\u00b2", secondary_y=False)
        fig_mm.update_yaxes(title_text="\u00b0C", secondary_y=True)
        st.plotly_chart(fig_mm, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════
# TAB 5: Technical Details
# ══════════════════════════════════════════════════════════════════════════

with tab_details:
    st.subheader(t("technical_details", lang))
    st.markdown(t("methodology", lang))
