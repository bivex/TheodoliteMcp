import json
from theodolite_mcp.infrastructure.mcp_server import draw_pipeline_schematic

# --- ПРОЄКТ: ЕКОНОМ-ВОДОПОСТАЧАННЯ (УКРАЇНА) ---
# Бюджет: ~7 137 грн
# Свердловина (Малюк) -> ПНД 25 -> П'ятірник з автоматикою -> Фільтр колба 10" -> Бойлер 10Л під мийку

pipes = [
    # ГРУПА А: СВЕРДЛОВИНА (x: 0-4)
    # Вібраційний насос піднімає воду ПНД трубою 25мм
    {"start_pt": {"x": 0, "y": -12}, "end_pt": {"x": 0, "y": -6}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    {"start_pt": {"x": 0, "y": -6}, "end_pt": {"x": 0, "y": 0}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 6, "y": 0}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    
    # ГРУПА Б: ВВІД У БУДИНОК (x: 6-12)
    # Перехід на ППР 20мм після крана
    {"start_pt": {"x": 6, "y": 0}, "end_pt": {"x": 12, "y": 0}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"},
    {"start_pt": {"x": 12, "y": 0}, "end_pt": {"x": 12, "y": 4}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"},
    {"start_pt": {"x": 12, "y": 4}, "end_pt": {"x": 18, "y": 4}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"},
    
    # ГРУПА В: ОЧИСТКА (x: 18-26)
    # Один магістральний фільтр Ecosoft 10"
    {"start_pt": {"x": 18, "y": 4}, "end_pt": {"x": 26, "y": 4}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"},
    
    # ГРУПА Г: РОЗВОДКА ПІД МИЙКОЮ (x: 26-36)
    {"start_pt": {"x": 26, "y": 4}, "end_pt": {"x": 30, "y": 4}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"},
    # Підключення до холодного крана змішувача
    {"start_pt": {"x": 30, "y": 4}, "end_pt": {"x": 34, "y": 4}, "medium": "cold_water", "nominal_diameter": 15, "flow_direction": "forward"},
    # Підключення до бойлера під мийкою (опуск вниз)
    {"start_pt": {"x": 30, "y": 4}, "end_pt": {"x": 30, "y": 1}, "medium": "cold_water", "nominal_diameter": 15, "flow_direction": "forward"},
    
    # Вихід гарячої води з бойлера вгору до змішувача
    {"start_pt": {"x": 34, "y": 1}, "end_pt": {"x": 34, "y": 8}, "medium": "hot_water", "nominal_diameter": 15, "flow_direction": "forward"},
]

equipment = [
    # Насос вібраційний (менший за розміром)
    {"center_pt": {"x": 0, "y": -9}, "equipment_type": "centrifugal_pump", "label": "Expert Pump VMP 70", "tag": "P-1", "width": 1.2, "height": 1.2},
    
    # Гідроакумулятор 24л (Горизонтальний)
    {"center_pt": {"x": 12, "y": 4}, "equipment_type": "expansion_vessel", "label": "Бак 24л (Горизонт.)", "tag": "GA-1", "width": 2.5, "height": 1.5, "rotation": 90},
    
    # Очистка (одна колба)
    {"center_pt": {"x": 22, "y": 4}, "equipment_type": "mesh_filter", "label": "Ecosoft 10\" (PP-10)", "tag": "F-1", "width": 1.5, "height": 2.2},
    
    # Бойлер під мийку 10л (квадратний/малий)
    {"center_pt": {"x": 32, "y": 1}, "equipment_type": "boiler", "label": "RENS 10л (Під мийку)", "tag": "B-1", "width": 1.8, "height": 1.8},
]

valves = [
    # Зворотний клапан латунний
    {"center_pt": {"x": 0, "y": -3}, "valve_type": "check", "tag": "CV-1", "rotation": 90, "nominal_diameter": 60},
    # Головний кран на вводі
    {"center_pt": {"x": 4, "y": 0}, "valve_type": "ball", "tag": "V-1", "nominal_diameter": 60},
    
    # Вентиль перед фільтром для заміни картриджа
    {"center_pt": {"x": 18, "y": 4}, "valve_type": "ball", "tag": "V-2", "nominal_diameter": 40},
    
    # Кран на бойлер
    {"center_pt": {"x": 30, "y": 2.5}, "valve_type": "ball", "tag": "V-3", "rotation": 90, "nominal_diameter": 30},
]

instruments = [
    # Автоматика на п'ятірнику біля ГА
    {"center_pt": {"x": 10.5, "y": 4}, "measured_variable": "P", "suffix": "I", "tag_number": "01"}, # Манометр 0-6 бар
    {"center_pt": {"x": 13.5, "y": 4}, "measured_variable": "P", "suffix": "C", "tag_number": "01"}, # Реле WETRON
]

try:
    draw_pipeline_schematic(
        title="ПРОЄКТ: ЕКОНОМ-ВОДОПОСТАЧАННЯ (Бюджет ~7.1к грн)",
        project_number="UKR-DIY-7K",
        organization="DIY Village",
        pipes_json=pipes,
        equipment_json=equipment,
        valves_json=valves,
        instruments_json=instruments,
        language="uk",
        output_path="output/project_voda_cheap_bom.png"
    )
    print("Економ-креслення за списком BOM створено: output/project_voda_cheap_bom.png")
except Exception as e:
    print(f"Помилка: {e}")
