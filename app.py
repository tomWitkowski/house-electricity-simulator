"""House Electricity Simulator - Streamlit Application.

Monte Carlo simulation of home energy costs with PV, battery, heat pump, etc.
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from simulator.models import (
    Location, HouseParams, PVParams, BatteryParams, HeatPumpParams,
    RecuperatorParams, ACParams, FloorHeatingParams, Appliance,
    AppliancesParams, TariffParams, SimulationParams,
)
from simulator.engine import run_monte_carlo

st.set_page_config(
    page_title="Symulator Energii Domu",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    .stTabs [data-baseweb="tab-list"] {gap: 8px;}
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 8px 8px 0 0;
    }
    div[data-testid="stMetric"] {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 12px;
    }
    .investment-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("Symulator Energii Domu")
st.caption("Symulacja Monte Carlo kosztów energii dla różnych konfiguracji domu")


# ── Sidebar: Configuration panels ───────────────────────────────────────────

with st.sidebar:
    st.header("Konfiguracja")

    # ── Location ──
    with st.expander("Lokalizacja", expanded=True):
        city_options = [
            "Wrocław", "Warszawa", "Kraków", "Gdańsk", "Poznań", "Szczecin", "Inna"
        ]
        city = st.selectbox("Miasto", city_options, index=0)

        if city == "Inna":
            lat = st.number_input("Szerokość geograficzna", 49.0, 55.0, 51.1, 0.1)
            lon = st.number_input("Długość geograficzna", 14.0, 24.0, 17.0, 0.1)
        else:
            city_coords = {
                "Wrocław": (51.1, 17.0), "Warszawa": (52.23, 21.0),
                "Kraków": (50.06, 19.94), "Gdańsk": (54.35, 18.65),
                "Poznań": (52.41, 16.93), "Szczecin": (53.43, 14.55),
            }
            lat, lon = city_coords[city]
            st.caption(f"Współrzędne: {lat}°N, {lon}°E")

        location = Location(latitude=lat, longitude=lon, city_name=city)

    # ── House ──
    with st.expander("Dom", expanded=True):
        h_area = st.slider("Powierzchnia (m²)", 60, 400, 150, 10)
        h_floors = st.selectbox("Liczba pięter", [1, 2, 3], index=1)
        h_insulation = st.select_slider(
            "Izolacja ścian (cm styropianu)",
            options=[10, 15, 20, 25, 30], value=20,
        )
        h_window_u = st.slider("Współczynnik U okien (W/m²K)", 0.5, 1.5, 0.9, 0.1)
        h_thermal = st.selectbox(
            "Masa termiczna", ["low", "medium", "high"],
            format_func=lambda x: {"low": "Niska (drewno)", "medium": "Średnia (pustak)", "high": "Wysoka (beton/cegła)"}[x],
            index=1,
        )
        h_target_winter = st.slider("Temperatura zimą (°C)", 18.0, 24.0, 21.0, 0.5)
        h_target_summer = st.slider("Temperatura latem (°C)", 22.0, 28.0, 24.0, 0.5)

        house = HouseParams(
            area_m2=h_area, floors=h_floors,
            wall_insulation_cm=h_insulation,
            window_u_value=h_window_u,
            thermal_mass=h_thermal,
            target_temp_winter_c=h_target_winter,
            target_temp_summer_c=h_target_summer,
        )

    # ── PV ──
    with st.expander("Fotowoltaika", expanded=True):
        pv_enabled = st.checkbox("Panele fotowoltaiczne", value=True)
        if pv_enabled:
            pv_kwp = st.slider("Moc szczytowa (kWp)", 2.0, 30.0, 10.0, 0.5)
            pv_tilt = st.slider("Kąt nachylenia dachu (°)", 0, 60, 35, 5)
            pv_azimuth = st.slider(
                "Azymut dachu (°)", 90, 270, 180, 10,
                help="180° = południe, 90° = wschód, 270° = zachód",
            )
            pv_cost = st.number_input("Koszt za kWp (PLN)", 2000, 8000, 4500, 100)
            pv_ground = st.checkbox("Dodatkowe panele naziemne")
            pv_ground_kwp = 0.0
            if pv_ground:
                pv_ground_kwp = st.slider("Moc naziemna (kWp)", 1.0, 20.0, 5.0, 0.5)
        else:
            pv_kwp = 0
            pv_tilt = 35
            pv_azimuth = 180
            pv_cost = 4500
            pv_ground = False
            pv_ground_kwp = 0.0

        pv_params = PVParams(
            enabled=pv_enabled, peak_power_kw=pv_kwp,
            roof_tilt_deg=pv_tilt, roof_azimuth_deg=pv_azimuth,
            cost_per_kwp=pv_cost,
            ground_mount_enabled=pv_ground, ground_mount_kwp=pv_ground_kwp,
        )

    # ── Battery ──
    with st.expander("Magazyn energii"):
        bat_enabled = st.checkbox("Magazyn energii", value=False)
        if bat_enabled:
            bat_kwh = st.slider("Pojemność (kWh)", 2.0, 30.0, 10.0, 1.0)
            bat_cost = st.number_input("Koszt magazynu (PLN)", 5000, 80000, 25000, 1000)
        else:
            bat_kwh = 10.0
            bat_cost = 25000

        battery = BatteryParams(
            enabled=bat_enabled, capacity_kwh=bat_kwh, cost_total=bat_cost,
        )

    # ── Heat Pump ──
    with st.expander("Pompa ciepła", expanded=True):
        hp_enabled = st.checkbox("Pompa ciepła", value=True)
        if hp_enabled:
            hp_power = st.slider("Moc grzewcza (kW)", 4.0, 16.0, 8.0, 1.0)
            hp_cop7 = st.slider("COP przy 7°C", 2.5, 6.0, 4.0, 0.1)
            hp_cop_m7 = st.slider("COP przy -7°C", 1.5, 4.0, 2.5, 0.1)
            hp_cool = st.checkbox("Funkcja chłodzenia", value=True)
            hp_cost = st.number_input("Koszt pompy (PLN)", 15000, 70000, 35000, 1000)
        else:
            hp_power = 8.0
            hp_cop7 = 4.0
            hp_cop_m7 = 2.5
            hp_cool = True
            hp_cost = 35000

        heat_pump = HeatPumpParams(
            enabled=hp_enabled, rated_power_kw=hp_power,
            cop_at_7c=hp_cop7, cop_at_minus7c=hp_cop_m7,
            can_cool=hp_cool, cost_total=hp_cost,
        )

    # ── Recuperator ──
    with st.expander("Rekuperator"):
        rec_enabled = st.checkbox("Rekuperator", value=True)
        if rec_enabled:
            rec_eff = st.slider("Sprawność odzysku ciepła", 0.5, 0.95, 0.85, 0.05)
            rec_flow = st.slider("Przepływ powietrza (m³/h)", 100, 600, 300, 50)
            rec_cost = st.number_input("Koszt rekuperatora (PLN)", 5000, 30000, 15000, 1000)
        else:
            rec_eff = 0.85
            rec_flow = 300
            rec_cost = 15000

        recuperator = RecuperatorParams(
            enabled=rec_enabled, efficiency=rec_eff,
            air_flow_m3h=rec_flow, cost_total=rec_cost,
        )

    # ── AC ──
    with st.expander("Klimatyzacja"):
        ac_enabled = st.checkbox("Klimatyzacja (split)", value=False)
        if ac_enabled:
            ac_units = st.slider("Liczba jednostek", 1, 5, 2)
            ac_cool_cap = st.slider("Moc chłodzenia/jedn. (kW)", 2.0, 7.0, 3.5, 0.5)
            ac_cost_unit = st.number_input("Koszt za jednostkę (PLN)", 2000, 10000, 4000, 500)
        else:
            ac_units = 2
            ac_cool_cap = 3.5
            ac_cost_unit = 4000

        ac_params = ACParams(
            enabled=ac_enabled, num_units=ac_units,
            cooling_capacity_kw=ac_cool_cap, cost_per_unit=ac_cost_unit,
        )

    # ── Floor Heating ──
    with st.expander("Maty grzewcze"):
        fh_enabled = st.checkbox("Maty grzewcze podłogowe", value=False)
        if fh_enabled:
            fh_area = st.slider("Powierzchnia ogrzewana (m²)", 5, 100, 30, 5)
            fh_power = st.slider("Moc na m² (W/m²)", 100, 200, 150, 10)
        else:
            fh_area = 30
            fh_power = 150

        floor_heating = FloorHeatingParams(
            enabled=fh_enabled, area_m2=fh_area, power_per_m2_w=fh_power,
        )

    # ── Appliances ──
    with st.expander("Urządzenia domowe"):
        st.caption("Dostosuj zużycie urządzeń")
        default_app = AppliancesParams()
        custom_appliances = []
        for app in default_app.appliances:
            col1, col2 = st.columns([3, 1])
            with col1:
                hours = st.number_input(
                    f"{app.name} - godziny/dzień",
                    0.0, 24.0, float(app.daily_hours), 0.1,
                    key=f"app_h_{app.name}",
                )
            with col2:
                count = st.number_input(
                    "szt.",
                    0, 10, app.count, 1,
                    key=f"app_c_{app.name}",
                )
            custom_appliances.append(Appliance(
                name=app.name, power_w=app.power_w,
                daily_hours=hours, count=count, standby_w=app.standby_w,
            ))
        hw_kwh = st.slider("Ciepła woda (kWh/dzień)", 2.0, 15.0, 6.0, 0.5)

        appliances = AppliancesParams(appliances=custom_appliances, hot_water_daily_kwh=hw_kwh)

    # ── Tariff ──
    with st.expander("Taryfa elektryczna", expanded=True):
        dual = st.checkbox("Taryfa dwustrefowa (dzień/noc)", value=False)
        if dual:
            t_day = st.number_input("Cena dzień (PLN/kWh)", 0.30, 2.00, 0.75, 0.05)
            t_night = st.number_input("Cena noc (PLN/kWh)", 0.20, 1.50, 0.45, 0.05)
            t_single = (t_day + t_night) / 2
        else:
            t_single = st.number_input("Cena prądu (PLN/kWh)", 0.30, 2.00, 0.65, 0.05)
            t_day = t_single
            t_night = t_single

        t_feed = st.number_input("Cena odkupu (PLN/kWh)", 0.0, 1.50, 0.40, 0.05)
        t_fixed = st.number_input("Opłata stała miesięczna (PLN)", 0.0, 200.0, 30.0, 5.0)
        t_increase = st.slider("Roczny wzrost cen (%)", 0, 15, 3) / 100.0

        tariff = TariffParams(
            price_per_kwh=t_single, dual_tariff=dual,
            day_price=t_day, night_price=t_night,
            feed_in_tariff=t_feed, fixed_monthly_cost=t_fixed,
            annual_price_increase=t_increase,
        )

    # ── Simulation ──
    with st.expander("Parametry symulacji"):
        sim_years = st.slider("Okres symulacji (lata)", 1, 30, 10)
        sim_n = st.slider("Liczba symulacji Monte Carlo", 10, 1000, 200, 10)
        sim_seed = st.number_input("Ziarno losowe (0 = losowe)", 0, 99999, 0)

        sim_params = SimulationParams(
            years=sim_years, num_simulations=sim_n,
            random_seed=sim_seed if sim_seed > 0 else None,
        )


# ── Main area ───────────────────────────────────────────────────────────────

tab_overview, tab_results, tab_weather, tab_details = st.tabs([
    "Przegląd konfiguracji", "Wyniki symulacji",
    "Model pogody", "Szczegóły techniczne",
])

with tab_overview:
    st.subheader("Konfiguracja systemu")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Dom**")
        st.write(f"- Lokalizacja: {location.city_name}")
        st.write(f"- Powierzchnia: {house.area_m2} m²")
        st.write(f"- Piętra: {house.floors}")
        st.write(f"- Izolacja: {house.wall_insulation_cm} cm")
        st.write(f"- Okna U={house.window_u_value} W/m²K")
        st.write(f"- Współczynnik strat: {house.envelope_loss_coefficient:.0f} W/K")

    with col2:
        st.markdown("**Systemy energetyczne**")
        if pv_params.enabled:
            st.write(f"- PV: {pv_params.total_kwp:.1f} kWp")
        if battery.enabled:
            st.write(f"- Magazyn: {battery.capacity_kwh} kWh")
        if heat_pump.enabled:
            st.write(f"- Pompa ciepła: {heat_pump.rated_power_kw} kW")
        if recuperator.enabled:
            st.write(f"- Rekuperator: {recuperator.efficiency*100:.0f}%")
        if ac_params.enabled:
            st.write(f"- Klimatyzacja: {ac_params.num_units}x {ac_params.cooling_capacity_kw} kW")
        if floor_heating.enabled:
            st.write(f"- Maty grzewcze: {floor_heating.area_m2} m²")

    with col3:
        st.markdown("**Koszty inwestycji**")
        total_inv = 0
        items = []
        if pv_params.enabled:
            items.append(("Fotowoltaika", pv_params.total_cost))
        if battery.enabled:
            items.append(("Magazyn energii", battery.cost_total))
        if heat_pump.enabled:
            items.append(("Pompa ciepła", heat_pump.cost_total))
        if recuperator.enabled:
            items.append(("Rekuperator", recuperator.cost_total))
        if ac_params.enabled:
            items.append(("Klimatyzacja", ac_params.total_cost))
        if floor_heating.enabled:
            items.append(("Maty grzewcze", floor_heating.total_cost))

        for name, cost in items:
            st.write(f"- {name}: {cost:,.0f} PLN")
            total_inv += cost
        st.markdown(f"**Razem: {total_inv:,.0f} PLN**")

    st.divider()

    st.subheader("Zużycie bazowe urządzeń")
    app_data = []
    for a in appliances.appliances:
        app_data.append({
            "Urządzenie": a.name,
            "Moc (W)": a.power_w,
            "Godziny/dzień": a.daily_hours,
            "Sztuk": a.count,
            "kWh/dzień": round(a.daily_kwh, 2),
        })
    df_app = pd.DataFrame(app_data)
    st.dataframe(df_app, use_container_width=True, hide_index=True)
    st.write(f"**Łączne zużycie bazowe: {appliances.base_daily_kwh:.1f} kWh/dzień "
             f"({appliances.base_daily_kwh * 365:.0f} kWh/rok)**")


# ── Run simulation ──────────────────────────────────────────────────────────

with tab_results:
    if st.button("Uruchom symulację", type="primary", use_container_width=True):
        progress_bar = st.progress(0.0, text="Trwa symulacja Monte Carlo...")

        def update_progress(frac):
            progress_bar.progress(frac, text=f"Symulacja: {frac*100:.0f}%")

        result = run_monte_carlo(
            location, house, pv_params, battery, heat_pump,
            recuperator, ac_params, floor_heating, appliances,
            tariff, sim_params,
            progress_callback=update_progress,
        )
        progress_bar.empty()

        st.session_state["result"] = result
        st.session_state["sim_params"] = sim_params
        st.session_state["investment"] = total_inv

    if "result" in st.session_state:
        result = st.session_state["result"]
        sim_p = st.session_state["sim_params"]
        investment = st.session_state["investment"]

        st.subheader("Podsumowanie kosztów")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                f"Koszt energii ({sim_p.years} lat)",
                f"{result.total_net_cost_mean:,.0f} PLN",
                help="Średni koszt netto energii z sieci (po odliczeniu sprzedaży)",
            )
        with col2:
            total_with_inv = result.total_net_cost_mean + investment
            st.metric(
                "Koszt łączny z inwestycją",
                f"{total_with_inv:,.0f} PLN",
            )
        with col3:
            annual_avg = result.total_net_cost_mean / sim_p.years
            monthly_avg = annual_avg / 12
            st.metric("Średnio miesięcznie", f"{monthly_avg:,.0f} PLN")
        with col4:
            st.metric(
                "Rozrzut (5%-95%)",
                f"{result.total_net_cost_p5:,.0f} - {result.total_net_cost_p95:,.0f} PLN",
            )

        st.divider()

        # ── Annual costs chart ──
        st.subheader("Koszty roczne")
        annual_df = result.annual_costs
        years = list(range(1, sim_p.years + 1))

        means = annual_df.mean()
        p5 = annual_df.quantile(0.05)
        p25 = annual_df.quantile(0.25)
        p75 = annual_df.quantile(0.75)
        p95 = annual_df.quantile(0.95)

        fig_annual = go.Figure()
        fig_annual.add_trace(go.Scatter(
            x=years, y=p95.values, mode="lines", line=dict(width=0),
            showlegend=False, name="P95",
        ))
        fig_annual.add_trace(go.Scatter(
            x=years, y=p5.values, mode="lines", line=dict(width=0),
            fill="tonexty", fillcolor="rgba(255,107,53,0.15)",
            showlegend=True, name="Zakres 5-95%",
        ))
        fig_annual.add_trace(go.Scatter(
            x=years, y=p75.values, mode="lines", line=dict(width=0),
            showlegend=False,
        ))
        fig_annual.add_trace(go.Scatter(
            x=years, y=p25.values, mode="lines", line=dict(width=0),
            fill="tonexty", fillcolor="rgba(255,107,53,0.3)",
            showlegend=True, name="Zakres 25-75%",
        ))
        fig_annual.add_trace(go.Scatter(
            x=years, y=means.values, mode="lines+markers",
            line=dict(color="#FF6B35", width=3),
            name="Średnia",
        ))
        fig_annual.update_layout(
            xaxis_title="Rok", yaxis_title="Koszt netto (PLN/rok)",
            template="plotly_white", height=400,
        )
        st.plotly_chart(fig_annual, use_container_width=True)

        # ── Energy balance (first year average) ──
        st.subheader("Bilans energetyczny (średnio, rok 1)")

        first_year_data = [run[0] for run in result.year_results]
        avg_gen = np.mean([y.total_pv_generation_kwh for y in first_year_data])
        avg_cons = np.mean([y.total_consumption_kwh for y in first_year_data])
        avg_self = np.mean([y.pv_self_consumed_kwh for y in first_year_data])
        avg_export = np.mean([y.pv_exported_kwh for y in first_year_data])
        avg_grid = np.mean([y.grid_imported_kwh for y in first_year_data])
        avg_heat = np.mean([y.heating_kwh_electric for y in first_year_data])
        avg_cool = np.mean([y.cooling_kwh_electric for y in first_year_data])
        avg_hw = np.mean([y.hot_water_kwh_electric for y in first_year_data])
        avg_appl = np.mean([y.appliances_kwh for y in first_year_data])

        col1, col2 = st.columns(2)

        with col1:
            fig_gen = go.Figure(data=[go.Pie(
                labels=["Autokonsumpcja", "Eksport do sieci"],
                values=[avg_self, avg_export],
                marker_colors=["#FF6B35", "#FFC107"],
                hole=0.4,
            )])
            fig_gen.update_layout(
                title=f"Produkcja PV: {avg_gen:,.0f} kWh/rok",
                height=350,
            )
            st.plotly_chart(fig_gen, use_container_width=True)

        with col2:
            fig_cons = go.Figure(data=[go.Pie(
                labels=["Ogrzewanie", "Chłodzenie", "Ciepła woda", "Urządzenia"],
                values=[avg_heat, avg_cool, avg_hw, avg_appl],
                marker_colors=["#E53935", "#42A5F5", "#FF9800", "#66BB6A"],
                hole=0.4,
            )])
            fig_cons.update_layout(
                title=f"Zużycie: {avg_cons:,.0f} kWh/rok",
                height=350,
            )
            st.plotly_chart(fig_cons, use_container_width=True)

        # Key metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            autarky = (1 - avg_grid / avg_cons) * 100 if avg_cons > 0 else 0
            st.metric("Autarkia energetyczna", f"{autarky:.0f}%",
                      help="Procent zużycia pokrytego z własnej produkcji")
        with col2:
            self_cons_rate = (avg_self / avg_gen) * 100 if avg_gen > 0 else 0
            st.metric("Autokonsumpcja PV", f"{self_cons_rate:.0f}%",
                      help="Procent produkcji PV zużytej na miejscu")
        with col3:
            st.metric("Pobór z sieci", f"{avg_grid:,.0f} kWh/rok")

        # ── Distribution histogram ──
        st.subheader("Rozkład łącznych kosztów (Monte Carlo)")
        total_costs = [sum(yr.net_cost_pln for yr in run) for run in result.year_results]
        fig_hist = go.Figure(data=[go.Histogram(
            x=total_costs, nbinsx=40,
            marker_color="#FF6B35", opacity=0.8,
        )])
        fig_hist.add_vline(x=np.mean(total_costs), line_dash="dash",
                          line_color="red", annotation_text="Średnia")
        fig_hist.update_layout(
            xaxis_title=f"Łączny koszt netto ({sim_p.years} lat, PLN)",
            yaxis_title="Liczba symulacji",
            template="plotly_white", height=350,
        )
        st.plotly_chart(fig_hist, use_container_width=True)

        # ── ROI analysis ──
        if investment > 0:
            st.subheader("Analiza zwrotu inwestycji")

            # Compare with no-systems scenario (rough)
            no_pv_annual = avg_cons * tariff.price_per_kwh
            with_systems_annual = result.total_net_cost_mean / sim_p.years
            annual_savings = no_pv_annual - with_systems_annual

            if annual_savings > 0:
                payback = investment / annual_savings
                st.metric("Szacowany okres zwrotu", f"{payback:.1f} lat",
                         help="Uproszczony - nie uwzględnia dyskontowania")

            # Cumulative cost comparison
            fig_roi = go.Figure()
            cum_no_sys = []
            cum_with_sys = [investment]
            for y in range(1, sim_p.years + 1):
                esc = (1 + tariff.annual_price_increase) ** (y - 1)
                cum_no_sys.append(no_pv_annual * esc)
                cum_with_sys.append(cum_with_sys[-1] + means.values[y-1])

            cum_no_sys = np.cumsum(cum_no_sys)
            cum_with_sys = np.array(cum_with_sys[1:])

            fig_roi.add_trace(go.Scatter(
                x=list(range(1, sim_p.years + 1)), y=cum_no_sys,
                name="Bez systemu", line=dict(color="gray", dash="dash"),
            ))
            fig_roi.add_trace(go.Scatter(
                x=list(range(1, sim_p.years + 1)), y=cum_with_sys,
                name="Z systemem (+ inwestycja)", line=dict(color="#FF6B35"),
            ))
            fig_roi.update_layout(
                xaxis_title="Rok", yaxis_title="Skumulowany koszt (PLN)",
                template="plotly_white", height=400,
            )
            st.plotly_chart(fig_roi, use_container_width=True)

    else:
        st.info("Kliknij 'Uruchom symulację' aby zobaczyć wyniki.")


# ── Weather tab ─────────────────────────────────────────────────────────────

with tab_weather:
    st.subheader("Przykładowy model pogody")
    st.caption("Jeden losowy rok dla wybranej lokalizacji")

    if st.button("Generuj pogodę", key="gen_weather"):
        rng = np.random.default_rng(42)
        weather = __import__("simulator.weather", fromlist=["generate_year_weather"]).generate_year_weather(
            location.latitude, location.longitude, rng,
        )

        hours = np.arange(8760)
        days = hours / 24

        # Temperature
        fig_temp = go.Figure()
        # Daily averages for cleaner display
        daily_temp = weather.temperature_c.reshape(365, 24).mean(axis=1)
        daily_temp_max = weather.temperature_c.reshape(365, 24).max(axis=1)
        daily_temp_min = weather.temperature_c.reshape(365, 24).min(axis=1)

        fig_temp.add_trace(go.Scatter(
            x=list(range(365)), y=daily_temp_max,
            mode="lines", line=dict(width=0), showlegend=False,
        ))
        fig_temp.add_trace(go.Scatter(
            x=list(range(365)), y=daily_temp_min,
            mode="lines", line=dict(width=0),
            fill="tonexty", fillcolor="rgba(255,107,53,0.2)",
            name="Zakres min-max",
        ))
        fig_temp.add_trace(go.Scatter(
            x=list(range(365)), y=daily_temp,
            mode="lines", line=dict(color="#FF6B35"),
            name="Średnia dzienna",
        ))
        fig_temp.update_layout(
            title="Temperatura", xaxis_title="Dzień roku",
            yaxis_title="°C", template="plotly_white", height=300,
        )
        st.plotly_chart(fig_temp, use_container_width=True)

        # Solar irradiance
        daily_ghi = weather.ghi_w_m2.reshape(365, 24).sum(axis=1) / 1000  # kWh/m²/day
        fig_solar = go.Figure()
        fig_solar.add_trace(go.Bar(
            x=list(range(365)), y=daily_ghi,
            marker_color="#FFC107", name="GHI",
        ))
        fig_solar.update_layout(
            title="Nasłonecznienie (GHI)",
            xaxis_title="Dzień roku",
            yaxis_title="kWh/m²/dzień",
            template="plotly_white", height=300,
        )
        st.plotly_chart(fig_solar, use_container_width=True)

        # Monthly summary
        months_pl = ["Sty", "Lut", "Mar", "Kwi", "Maj", "Cze",
                     "Lip", "Sie", "Wrz", "Paź", "Lis", "Gru"]
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        monthly_temp = []
        monthly_solar = []
        start = 0
        for d in days_in_month:
            end = start + d * 24
            monthly_temp.append(weather.temperature_c[start:end].mean())
            monthly_solar.append(weather.ghi_w_m2[start:end].sum() / 1000)
            start = end

        fig_monthly = make_subplots(specs=[[{"secondary_y": True}]])
        fig_monthly.add_trace(go.Bar(
            x=months_pl, y=monthly_solar, name="Nasłonecznienie (kWh/m²)",
            marker_color="#FFC107",
        ), secondary_y=False)
        fig_monthly.add_trace(go.Scatter(
            x=months_pl, y=monthly_temp, name="Średnia temp. (°C)",
            line=dict(color="#E53935", width=3),
        ), secondary_y=True)
        fig_monthly.update_layout(
            title="Podsumowanie miesięczne", template="plotly_white", height=350,
        )
        fig_monthly.update_yaxes(title_text="kWh/m²", secondary_y=False)
        fig_monthly.update_yaxes(title_text="°C", secondary_y=True)
        st.plotly_chart(fig_monthly, use_container_width=True)


# ── Technical details tab ───────────────────────────────────────────────────

with tab_details:
    st.subheader("Szczegóły techniczne symulacji")

    st.markdown("""
    ### Metodologia

    **Symulacja Monte Carlo** generuje wiele scenariuszy pogodowych dla wybranej
    lokalizacji i oblicza bilans energetyczny godzina po godzinie przez zadany okres.

    #### Model pogody
    - Bazuje na profilach klimatycznych dla polskich miast
    - Uwzględnia: temperaturę, nasłonecznienie (GHI), zachmurzenie, wiatr
    - Każda symulacja generuje unikalny rok z wariacją względem średniej
    - Modelowane są wielodniowe wzorce pogodowe (ciągi pochmurnych/słonecznych dni)

    #### Model domu
    - Straty ciepła przez przegrody: ściany, okna, dach, podłoga
    - Straty wentylacyjne (infiltracja + wentylacja mechaniczna)
    - Zyski solarne przez okna (uproszczone)
    - Masa termiczna budynku wpływa na bezwładność cieplną

    #### Fotowoltaika
    - Model nachylonej powierzchni (izotropowy model promieniowania rozproszonego)
    - Uwzględnia kąt nachylenia i azymut
    - Straty systemowe (inwerter, kable, zabrudzenie): ~14%
    - Degradacja paneli: 0.5%/rok

    #### Bilans energetyczny (godzinowy)
    1. Oblicz zapotrzebowanie: ogrzewanie/chłodzenie + CWU + urządzenia
    2. Oblicz produkcję PV
    3. Nadwyżka PV → magazyn → eksport do sieci
    4. Deficyt → magazyn → import z sieci
    5. Koszty według taryfy (opcjonalnie dwustrefowej)

    #### Pompa ciepła
    - COP interpolowany na podstawie temperatury zewnętrznej
    - Punkty: COP przy +7°C, -7°C, -15°C
    - Poniżej -20°C: rezerwowe ogrzewanie elektryczne

    #### Ograniczenia modelu
    - Uproszczony model termiczny budynku (quasi-stacjonarny)
    - Brak modelowania zacienienia między budynkami
    - Profil zużycia urządzeń statyczny (nie zmienia się sezonowo)
    - Ceny energii rosną liniowo (brak skoków)
    """)
