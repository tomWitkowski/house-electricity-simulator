"""Internationalization support for the house electricity simulator."""

TRANSLATIONS = {
    "en": {
        # App
        "app_title": "Home Energy Simulator",
        "app_subtitle": "Monte Carlo simulation of energy costs for various house configurations",
        "run_simulation": "Run Simulation",
        "simulation_running": "Running Monte Carlo simulation...",
        "simulation_progress": "Simulation: {pct:.0f}%",
        "click_to_run": "Click 'Run Simulation' to see results.",

        # Tabs
        "tab_map": "House & Map",
        "tab_results": "Simulation Results",
        "tab_weather": "Weather Model",
        "tab_details": "Technical Details",

        # Sidebar
        "configuration": "Configuration",
        "language": "Language",

        # Location
        "location": "Location",
        "city": "City",
        "other": "Other",
        "latitude": "Latitude",
        "longitude": "Longitude",
        "coordinates": "Coordinates: {lat}°N, {lon}°E",

        # House
        "house": "House",
        "area_m2": "Area (m²)",
        "floors": "Number of floors",
        "wall_insulation": "Wall insulation (cm EPS)",
        "window_u": "Window U-value (W/m²K)",
        "thermal_mass": "Thermal mass",
        "thermal_low": "Low (timber frame)",
        "thermal_medium": "Medium (hollow block)",
        "thermal_high": "High (concrete/brick)",
        "target_temp_winter": "Winter target temp (°C)",
        "target_temp_summer": "Summer target temp (°C)",

        # PV
        "pv_panels": "Solar Panels",
        "pv_enabled": "Photovoltaic panels",
        "pv_peak_power": "Peak power (kWp)",
        "pv_roof_tilt": "Roof tilt angle (°)",
        "pv_azimuth": "Roof azimuth (°)",
        "pv_azimuth_help": "180° = south, 90° = east, 270° = west",
        "pv_cost_per_kwp": "Cost per kWp ({currency})",
        "pv_ground": "Additional ground-mount panels",
        "pv_ground_power": "Ground-mount power (kWp)",

        # Battery
        "battery": "Energy Storage",
        "battery_enabled": "Energy storage",
        "battery_capacity": "Capacity (kWh)",
        "battery_cost": "Storage cost ({currency})",

        # Heat pump
        "heat_pump": "Heat Pump",
        "hp_enabled": "Heat pump",
        "hp_power": "Heating power (kW)",
        "hp_cop_7": "COP at 7°C",
        "hp_cop_m7": "COP at -7°C",
        "hp_cooling": "Cooling function",
        "hp_cost": "Heat pump cost ({currency})",

        # Recuperator
        "recuperator": "Heat Recovery Ventilation",
        "rec_enabled": "Heat recovery ventilation",
        "rec_efficiency": "Heat recovery efficiency",
        "rec_airflow": "Air flow (m³/h)",
        "rec_cost": "HRV cost ({currency})",

        # AC
        "ac": "Air Conditioning",
        "ac_enabled": "Air conditioning (split units)",
        "ac_units": "Number of units",
        "ac_cooling": "Cooling capacity/unit (kW)",
        "ac_cost_unit": "Cost per unit ({currency})",

        # Floor heating
        "floor_heating": "Floor Heating Mats",
        "fh_enabled": "Electric floor heating mats",
        "fh_area": "Heated area (m²)",
        "fh_power": "Power per m² (W/m²)",

        # Appliances
        "appliances": "Household Appliances",
        "appliances_hint": "Adjust appliance usage",
        "hours_per_day": "hours/day",
        "pieces": "pcs",
        "hot_water": "Hot water (kWh/day)",

        # Appliance names
        "appliance_fridge": "Fridge",
        "appliance_dishwasher": "Dishwasher",
        "appliance_washing_machine": "Washing machine",
        "appliance_induction_hob": "Induction hob",
        "appliance_kettle": "Electric kettle",
        "appliance_oven": "Oven",
        "appliance_laptop": "Laptop",
        "appliance_tv": "TV",
        "appliance_lighting": "LED lighting",
        "appliance_router": "WiFi router",
        "appliance_hair_dryer": "Hair dryer",
        "appliance_vacuum": "Vacuum cleaner",

        # Tariff
        "tariff": "Electricity Tariff",
        "dual_tariff": "Dual tariff (day/night)",
        "price_day": "Day price ({currency}/kWh)",
        "price_night": "Night price ({currency}/kWh)",
        "price_single": "Electricity price ({currency}/kWh)",
        "feed_in": "Feed-in tariff ({currency}/kWh)",
        "fixed_monthly": "Fixed monthly fee ({currency})",
        "annual_increase": "Annual price increase (%)",

        # Simulation params
        "sim_params": "Simulation Parameters",
        "sim_years": "Simulation period (years)",
        "sim_runs": "Monte Carlo simulations",
        "sim_seed": "Random seed (0 = random)",

        # Map tab
        "map_header": "House Location & Orientation",
        "map_hint": "Click on the map to set house location. Use the azimuth slider to rotate the roof orientation.",
        "map_set_by_click": "Set location by clicking the map",
        "current_location": "Current location",
        "roof_direction": "Roof orientation (azimuth)",

        # Overview in map tab
        "system_config": "System Configuration",
        "house_label": "House",
        "location_label": "Location",
        "area_label": "Area",
        "floors_label": "Floors",
        "insulation_label": "Insulation",
        "windows_label": "Windows U",
        "heat_loss_label": "Heat loss coefficient",
        "energy_systems": "Energy Systems",
        "investment_costs": "Investment Costs",
        "total": "Total",
        "base_consumption": "Base appliance consumption",
        "per_day": "/day",
        "per_year": "/year",
        "device": "Device",
        "power_w": "Power (W)",
        "daily_kwh": "kWh/day",

        # Results
        "cost_summary": "Cost Summary",
        "energy_cost_period": "Energy cost ({years} yrs)",
        "total_with_investment": "Total with investment",
        "monthly_average": "Monthly average",
        "spread_5_95": "Spread (5%-95%)",
        "cost_help": "Average net grid energy cost (after feed-in income)",
        "annual_costs": "Annual Costs",
        "year": "Year",
        "net_cost_year": "Net cost (PLN/year)",
        "range_5_95": "Range 5-95%",
        "range_25_75": "Range 25-75%",
        "mean": "Mean",

        "energy_balance": "Energy Balance (average, year 1)",
        "self_consumption": "Self-consumption",
        "grid_export": "Grid export",
        "pv_production": "PV production: {val:,.0f} kWh/yr",
        "heating": "Heating",
        "cooling": "Cooling",
        "hot_water_label": "Hot water",
        "appliances_label": "Appliances",
        "consumption_label": "Consumption: {val:,.0f} kWh/yr",

        "energy_autarky": "Energy autarky",
        "autarky_help": "Percentage of consumption covered by own production",
        "pv_self_consumption": "PV self-consumption",
        "self_consumption_help": "Percentage of PV production consumed on-site",
        "grid_import": "Grid import",

        "cost_distribution": "Total Cost Distribution (Monte Carlo)",
        "total_net_cost": "Total net cost ({years} yrs, {currency})",
        "simulation_count": "Number of simulations",

        "roi_analysis": "Return on Investment Analysis",
        "estimated_payback": "Estimated payback period",
        "payback_help": "Simplified - does not account for discounting",
        "years_unit": "years",
        "without_system": "Without system",
        "with_system": "With system (+ investment)",
        "cumulative_cost": "Cumulative cost ({currency})",

        # Weather
        "weather_header": "Sample Weather Model",
        "weather_hint": "One random year for selected location",
        "generate_weather": "Generate Weather",
        "temperature": "Temperature",
        "day_of_year": "Day of year",
        "solar_irradiance": "Solar Irradiance (GHI)",
        "kwh_m2_day": "kWh/m²/day",
        "monthly_summary": "Monthly Summary",
        "solar_monthly": "Irradiance (kWh/m²)",
        "avg_temp": "Avg temperature (°C)",
        "daily_range": "Daily min-max range",
        "daily_avg": "Daily average",

        # Details
        "technical_details": "Technical Simulation Details",
        "methodology": """
### Methodology

**Monte Carlo Simulation** generates multiple weather scenarios for the selected
location and calculates the energy balance hour by hour over the given period.

#### Weather Model
- Based on climate profiles for Polish cities
- Includes: temperature, solar irradiance (GHI), cloud cover, wind
- Each simulation generates a unique year with variation around the average
- Multi-day weather patterns are modeled (runs of cloudy/sunny days)

#### House Model
- Heat losses through envelope: walls, windows, roof, floor
- Ventilation losses (infiltration + mechanical ventilation)
- Solar gains through windows (simplified)
- Building thermal mass affects thermal inertia

#### Photovoltaics
- Tilted surface model (isotropic diffuse radiation model)
- Accounts for tilt angle and azimuth
- System losses (inverter, cables, soiling): ~14%
- Panel degradation: 0.5%/year

#### Hourly Energy Balance
1. Calculate demand: heating/cooling + DHW + appliances
2. Calculate PV production
3. PV surplus → battery → grid export
4. Deficit → battery → grid import
5. Costs according to tariff (optionally dual-zone)

#### Heat Pump
- COP interpolated based on outdoor temperature
- Reference points: COP at +7°C, -7°C, -15°C
- Below -20°C: backup electric heating

#### Model Limitations
- Simplified thermal building model (quasi-stationary)
- No shading between buildings modeled
- Static appliance usage profile (no seasonal variation)
- Energy prices increase linearly (no jumps)
""",

        # New keys
        "ventilation_rate": "Ventilation rate (m\u00b3/h)",
        "fh_cost_per_m2": "Cost per m\u00b2 ({currency})",
        "power_watts": "W",
        "export_settings": "Export settings",
        "import_settings": "Import settings",
        "settings_exported": "Settings exported! Copy the JSON below.",
        "settings_imported": "Settings imported successfully! Reload the page to apply.",
        "settings_import_error": "Invalid JSON format.",
        "upload_json": "Upload JSON file",
        "heating_thermal": "Heating (thermal)",
        "heating_electric": "Heating (electric)",
        "scenario_cold": "Cold year",
        "scenario_normal": "Normal year",
        "scenario_warm": "Warm year",
        "hourly_profiles": "Hourly Energy Profiles (Year 1)",
        "pv_vs_demand": "PV Generation vs Demand",
        "battery_soc": "Battery State of Charge",
        "monthly_energy": "Monthly Energy Balance",
        "pv_gen_monthly": "PV generation",
        "demand_monthly": "Demand",
        "grid_monthly": "Grid import",
        "hour_of_day": "Hour",
        "kwh": "kWh",
        "weekly_avg": "Weekly averages",
        "scenario_comparison": "Scenario Comparison (Year 1)",
        "total_consumption": "Total consumption",
        "pv_generation": "PV generation",
        "grid_import_label": "Grid import",
        "heating_thermal_label": "Heating demand (thermal)",
        "net_cost_label": "Net cost",

        # Months
        "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    },

    "pl": {
        "app_title": "Symulator Energii Domu",
        "app_subtitle": "Symulacja Monte Carlo kosztów energii dla różnych konfiguracji domu",
        "run_simulation": "Uruchom symulację",
        "simulation_running": "Trwa symulacja Monte Carlo...",
        "simulation_progress": "Symulacja: {pct:.0f}%",
        "click_to_run": "Kliknij 'Uruchom symulację' aby zobaczyć wyniki.",

        "tab_map": "Dom i mapa",
        "tab_results": "Wyniki symulacji",
        "tab_weather": "Model pogody",
        "tab_details": "Szczegóły techniczne",

        "configuration": "Konfiguracja",
        "language": "Język",

        "location": "Lokalizacja",
        "city": "Miasto",
        "other": "Inna",
        "latitude": "Szerokość geograficzna",
        "longitude": "Długość geograficzna",
        "coordinates": "Współrzędne: {lat}°N, {lon}°E",

        "house": "Dom",
        "area_m2": "Powierzchnia (m²)",
        "floors": "Liczba pięter",
        "wall_insulation": "Izolacja ścian (cm styropianu)",
        "window_u": "Współczynnik U okien (W/m²K)",
        "thermal_mass": "Masa termiczna",
        "thermal_low": "Niska (drewno)",
        "thermal_medium": "Średnia (pustak)",
        "thermal_high": "Wysoka (beton/cegła)",
        "target_temp_winter": "Temperatura zimą (°C)",
        "target_temp_summer": "Temperatura latem (°C)",

        "pv_panels": "Fotowoltaika",
        "pv_enabled": "Panele fotowoltaiczne",
        "pv_peak_power": "Moc szczytowa (kWp)",
        "pv_roof_tilt": "Kąt nachylenia dachu (°)",
        "pv_azimuth": "Azymut dachu (°)",
        "pv_azimuth_help": "180° = południe, 90° = wschód, 270° = zachód",
        "pv_cost_per_kwp": "Koszt za kWp ({currency})",
        "pv_ground": "Dodatkowe panele naziemne",
        "pv_ground_power": "Moc naziemna (kWp)",

        "battery": "Magazyn energii",
        "battery_enabled": "Magazyn energii",
        "battery_capacity": "Pojemność (kWh)",
        "battery_cost": "Koszt magazynu ({currency})",

        "heat_pump": "Pompa ciepła",
        "hp_enabled": "Pompa ciepła",
        "hp_power": "Moc grzewcza (kW)",
        "hp_cop_7": "COP przy 7°C",
        "hp_cop_m7": "COP przy -7°C",
        "hp_cooling": "Funkcja chłodzenia",
        "hp_cost": "Koszt pompy ({currency})",

        "recuperator": "Rekuperator",
        "rec_enabled": "Rekuperator",
        "rec_efficiency": "Sprawność odzysku ciepła",
        "rec_airflow": "Przepływ powietrza (m³/h)",
        "rec_cost": "Koszt rekuperatora ({currency})",

        "ac": "Klimatyzacja",
        "ac_enabled": "Klimatyzacja (split)",
        "ac_units": "Liczba jednostek",
        "ac_cooling": "Moc chłodzenia/jedn. (kW)",
        "ac_cost_unit": "Koszt za jednostkę ({currency})",

        "floor_heating": "Maty grzewcze",
        "fh_enabled": "Maty grzewcze podłogowe",
        "fh_area": "Powierzchnia ogrzewana (m²)",
        "fh_power": "Moc na m² (W/m²)",

        "appliances": "Urządzenia domowe",
        "appliances_hint": "Dostosuj zużycie urządzeń",
        "hours_per_day": "godz./dzień",
        "pieces": "szt.",
        "hot_water": "Ciepła woda (kWh/dzień)",

        "appliance_fridge": "Lodówka",
        "appliance_dishwasher": "Zmywarka",
        "appliance_washing_machine": "Pralka",
        "appliance_induction_hob": "Kuchenka indukcyjna",
        "appliance_kettle": "Czajnik elektryczny",
        "appliance_oven": "Piekarnik",
        "appliance_laptop": "Laptop",
        "appliance_tv": "TV",
        "appliance_lighting": "Oświetlenie LED",
        "appliance_router": "Router WiFi",
        "appliance_hair_dryer": "Suszarka do włosów",
        "appliance_vacuum": "Odkurzacz",

        "tariff": "Taryfa elektryczna",
        "dual_tariff": "Taryfa dwustrefowa (dzień/noc)",
        "price_day": "Cena dzień ({currency}/kWh)",
        "price_night": "Cena noc ({currency}/kWh)",
        "price_single": "Cena prądu ({currency}/kWh)",
        "feed_in": "Cena odkupu ({currency}/kWh)",
        "fixed_monthly": "Opłata stała miesięczna ({currency})",
        "annual_increase": "Roczny wzrost cen (%)",

        "sim_params": "Parametry symulacji",
        "sim_years": "Okres symulacji (lata)",
        "sim_runs": "Liczba symulacji Monte Carlo",
        "sim_seed": "Ziarno losowe (0 = losowe)",

        "map_header": "Lokalizacja i orientacja domu",
        "map_hint": "Kliknij na mapę aby ustawić lokalizację domu. Użyj suwaka azymutu aby obrócić orientację dachu.",
        "map_set_by_click": "Ustaw lokalizację klikając na mapę",
        "current_location": "Aktualna lokalizacja",
        "roof_direction": "Orientacja dachu (azymut)",

        "system_config": "Konfiguracja systemu",
        "house_label": "Dom",
        "location_label": "Lokalizacja",
        "area_label": "Powierzchnia",
        "floors_label": "Piętra",
        "insulation_label": "Izolacja",
        "windows_label": "Okna U",
        "heat_loss_label": "Współczynnik strat",
        "energy_systems": "Systemy energetyczne",
        "investment_costs": "Koszty inwestycji",
        "total": "Razem",
        "base_consumption": "Łączne zużycie bazowe",
        "per_day": "/dzień",
        "per_year": "/rok",
        "device": "Urządzenie",
        "power_w": "Moc (W)",
        "daily_kwh": "kWh/dzień",

        "cost_summary": "Podsumowanie kosztów",
        "energy_cost_period": "Koszt energii ({years} lat)",
        "total_with_investment": "Koszt łączny z inwestycją",
        "monthly_average": "Średnio miesięcznie",
        "spread_5_95": "Rozrzut (5%-95%)",
        "cost_help": "Średni koszt netto energii z sieci (po odliczeniu sprzedaży)",
        "annual_costs": "Koszty roczne",
        "year": "Rok",
        "net_cost_year": "Koszt netto (PLN/rok)",
        "range_5_95": "Zakres 5-95%",
        "range_25_75": "Zakres 25-75%",
        "mean": "Średnia",

        "energy_balance": "Bilans energetyczny (średnio, rok 1)",
        "self_consumption": "Autokonsumpcja",
        "grid_export": "Eksport do sieci",
        "pv_production": "Produkcja PV: {val:,.0f} kWh/rok",
        "heating": "Ogrzewanie",
        "cooling": "Chłodzenie",
        "hot_water_label": "Ciepła woda",
        "appliances_label": "Urządzenia",
        "consumption_label": "Zużycie: {val:,.0f} kWh/rok",

        "energy_autarky": "Autarkia energetyczna",
        "autarky_help": "Procent zużycia pokrytego z własnej produkcji",
        "pv_self_consumption": "Autokonsumpcja PV",
        "self_consumption_help": "Procent produkcji PV zużytej na miejscu",
        "grid_import": "Pobór z sieci",

        "cost_distribution": "Rozkład łącznych kosztów (Monte Carlo)",
        "total_net_cost": "Łączny koszt netto ({years} lat, {currency})",
        "simulation_count": "Liczba symulacji",

        "roi_analysis": "Analiza zwrotu inwestycji",
        "estimated_payback": "Szacowany okres zwrotu",
        "payback_help": "Uproszczony - nie uwzględnia dyskontowania",
        "years_unit": "lat",
        "without_system": "Bez systemu",
        "with_system": "Z systemem (+ inwestycja)",
        "cumulative_cost": "Skumulowany koszt ({currency})",

        "weather_header": "Przykładowy model pogody",
        "weather_hint": "Jeden losowy rok dla wybranej lokalizacji",
        "generate_weather": "Generuj pogodę",
        "temperature": "Temperatura",
        "day_of_year": "Dzień roku",
        "solar_irradiance": "Nasłonecznienie (GHI)",
        "kwh_m2_day": "kWh/m²/dzień",
        "monthly_summary": "Podsumowanie miesięczne",
        "solar_monthly": "Nasłonecznienie (kWh/m²)",
        "avg_temp": "Średnia temp. (°C)",
        "daily_range": "Zakres min-max",
        "daily_avg": "Średnia dzienna",

        "technical_details": "Szczegóły techniczne symulacji",
        "methodology": """
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
""",

        "ventilation_rate": "Przepływ wentylacji (m\u00b3/h)",
        "fh_cost_per_m2": "Koszt za m\u00b2 ({currency})",
        "power_watts": "W",
        "export_settings": "Eksportuj ustawienia",
        "import_settings": "Importuj ustawienia",
        "settings_exported": "Ustawienia wyeksportowane! Skopiuj JSON poniżej.",
        "settings_imported": "Ustawienia zaimportowane! Odśwież stronę aby zastosować.",
        "settings_import_error": "Nieprawidłowy format JSON.",
        "upload_json": "Wgraj plik JSON",
        "heating_thermal": "Ogrzewanie (cieplne)",
        "heating_electric": "Ogrzewanie (elektryczne)",
        "scenario_cold": "Zimny rok",
        "scenario_normal": "Normalny rok",
        "scenario_warm": "Ciepły rok",
        "hourly_profiles": "Profile godzinowe energii (rok 1)",
        "pv_vs_demand": "Produkcja PV vs zapotrzebowanie",
        "battery_soc": "Stan naładowania magazynu",
        "monthly_energy": "Miesięczny bilans energii",
        "pv_gen_monthly": "Produkcja PV",
        "demand_monthly": "Zapotrzebowanie",
        "grid_monthly": "Pobór z sieci",
        "hour_of_day": "Godzina",
        "kwh": "kWh",
        "weekly_avg": "Średnie tygodniowe",
        "scenario_comparison": "Porównanie scenariuszy (rok 1)",
        "total_consumption": "Łączne zużycie",
        "pv_generation": "Produkcja PV",
        "grid_import_label": "Pobór z sieci",
        "heating_thermal_label": "Zapotrzebowanie na ciepło",
        "net_cost_label": "Koszt netto",

        "months": ["Sty", "Lut", "Mar", "Kwi", "Maj", "Cze",
                    "Lip", "Sie", "Wrz", "Paź", "Lis", "Gru"],
    },
}

# Map Polish appliance names to translation keys
APPLIANCE_KEY_MAP = {
    "Lodówka": "appliance_fridge",
    "Zmywarka": "appliance_dishwasher",
    "Pralka": "appliance_washing_machine",
    "Kuchenka indukcyjna": "appliance_induction_hob",
    "Czajnik elektryczny": "appliance_kettle",
    "Piekarnik": "appliance_oven",
    "Laptop": "appliance_laptop",
    "TV": "appliance_tv",
    "Oświetlenie LED": "appliance_lighting",
    "Router WiFi": "appliance_router",
    "Suszarka do włosów": "appliance_hair_dryer",
    "Odkurzacz": "appliance_vacuum",
}


def t(key: str, lang: str = "en", **kwargs) -> str:
    """Get translated string."""
    text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return text
