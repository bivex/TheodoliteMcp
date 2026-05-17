import json
from theodolite_mcp.infrastructure.mcp_server import draw_pipeline_schematic

# --- ПРОЄКТ: ПРЕМІУМ-ВОДОПОСТАЧАННЯ ДЛЯ БУДИНКУ 40м2 ---
# Концепція: Надійність, ідеальний тиск (інвертор), чиста вода (кабінетний фільтр), колекторна розводка.

pipes = [
    # ГРУПА А: СВЕРДЛОВИНА З ІНВЕРТОРОМ
    {"start_pt": {"x": 0, "y": -15}, "end_pt": {"x": 0, "y": -5}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    {"start_pt": {"x": 0, "y": -5}, "end_pt": {"x": 0, "y": 0}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 5, "y": 0}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    
    # ГРУПА Б: ВВІД І СИСТЕМА ОЧИСТКИ (Водопідготовка)
    {"start_pt": {"x": 5, "y": 0}, "end_pt": {"x": 5, "y": 4}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    {"start_pt": {"x": 5, "y": 4}, "end_pt": {"x": 18, "y": 4}, "medium": "cold_water", "nominal_diameter": 32, "flow_direction": "forward"},
    
    # ГРУПА В: РОЗПОДІЛЬЧИЙ КОЛЕКТОР (Гребінка)
    {"start_pt": {"x": 18, "y": 4}, "end_pt": {"x": 22, "y": 4}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    # Колектор холодної води
    {"start_pt": {"x": 22, "y": 2}, "end_pt": {"x": 22, "y": 8}, "medium": "cold_water", "nominal_diameter": 32},
    # Відводи від колектора (ХВП)
    {"start_pt": {"x": 22, "y": 7}, "end_pt": {"x": 26, "y": 7}, "medium": "cold_water", "nominal_diameter": 16, "flow_direction": "forward"}, # На кухню
    {"start_pt": {"x": 22, "y": 5}, "end_pt": {"x": 26, "y": 5}, "medium": "cold_water", "nominal_diameter": 16, "flow_direction": "forward"}, # В санвузол
    {"start_pt": {"x": 22, "y": 3}, "end_pt": {"x": 26, "y": 3}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"}, # На бойлер
    
    # ГРУПА Г: РОЗУМНИЙ БОЙЛЕР
    {"start_pt": {"x": 26, "y": 3}, "end_pt": {"x": 30, "y": 3}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"},
    {"start_pt": {"x": 30, "y": 3.5}, "end_pt": {"x": 30, "y": 8}, "medium": "hot_water", "nominal_diameter": 20, "flow_direction": "forward"},
    
    # Колектор гарячої води
    {"start_pt": {"x": 30, "y": 8}, "end_pt": {"x": 34, "y": 8}, "medium": "hot_water", "nominal_diameter": 25, "flow_direction": "forward"},
    {"start_pt": {"x": 34, "y": 5}, "end_pt": {"x": 34, "y": 9}, "medium": "hot_water", "nominal_diameter": 25},
    # Відводи від колектора (ГВП)
    {"start_pt": {"x": 34, "y": 8}, "end_pt": {"x": 38, "y": 8}, "medium": "hot_water", "nominal_diameter": 16, "flow_direction": "forward"}, # На кухню
    {"start_pt": {"x": 34, "y": 6}, "end_pt": {"x": 38, "y": 6}, "medium": "hot_water", "nominal_diameter": 16, "flow_direction": "forward"}, # В санвузол
]

equipment = [
    # Преміум насос із частотним перетворювачем
    {"center_pt": {"x": 0, "y": -12}, "equipment_type": "centrifugal_pump", "label": "Grundfos SQE (Інвертор)", "tag": "P-1", "width": 2.0, "height": 2.0},
    
    # Міні-гідроакумулятор (для інвертора великий не потрібен)
    {"center_pt": {"x": 8, "y": 4}, "equipment_type": "expansion_vessel", "label": "Бак 8Л (Нержавійка)", "tag": "GA-1", "width": 1.5, "height": 1.5},
    
    # Станція водопідготовки
    {"center_pt": {"x": 12, "y": 4}, "equipment_type": "mesh_filter", "label": "Самопромивний Honeywell", "tag": "F-1", "width": 1.5, "height": 2.0},
    {"center_pt": {"x": 15, "y": 4}, "equipment_type": "storage_tank", "label": "Кабінетний пом'якшувач BWT", "tag": "WT-1", "width": 2.0, "height": 3.0},
    
    # Розумний бойлер
    {"center_pt": {"x": 30, "y": 5.5}, "equipment_type": "boiler", "label": "Drazice Steatite Cube Wi-Fi", "tag": "B-1", "width": 2.0, "height": 3.5},
]

valves = [
    {"center_pt": {"x": 0, "y": -3}, "valve_type": "check", "tag": "CV-1", "rotation": 90, "nominal_diameter": 60},
    {"center_pt": {"x": 2, "y": 0}, "valve_type": "ball", "tag": "V-1", "nominal_diameter": 60},
    
    # Редуктор тиску (захист системи)
    {"center_pt": {"x": 5, "y": 2}, "valve_type": "prv", "tag": "PRV-1", "rotation": 90, "nominal_diameter": 50},
    
    # Крани на колекторах (вбудовані)
    {"center_pt": {"x": 24, "y": 7}, "valve_type": "globe", "tag": "V-K-Cold", "nominal_diameter": 40},
    {"center_pt": {"x": 24, "y": 5}, "valve_type": "globe", "tag": "V-B-Cold", "nominal_diameter": 40},
    {"center_pt": {"x": 28, "y": 3}, "valve_type": "ball", "tag": "V-Boiler-In", "nominal_diameter": 40},
    
    {"center_pt": {"x": 36, "y": 8}, "valve_type": "globe", "tag": "V-K-Hot", "nominal_diameter": 40},
    {"center_pt": {"x": 36, "y": 6}, "valve_type": "globe", "tag": "V-B-Hot", "nominal_diameter": 40},
]

instruments = [
    # Електронний датчик тиску для інвертора
    {"center_pt": {"x": 9.5, "y": 6.5}, "measured_variable": "P", "suffix": "T", "tag_number": "01"}, # Pressure Transmitter
    {"center_pt": {"x": 12, "y": 6.5}, "measured_variable": "P", "suffix": "I", "tag_number": "01"}, # Манометр на фільтрі
]

try:
    draw_pipeline_schematic(
        title="ПРЕМІУМ ВОДОПОСТАЧАННЯ ДЛЯ БУДИНКУ 40 м²",
        project_number="UKR-PREMIUM-2026",
        organization="Top Engineering",
        pipes_json=pipes,
        equipment_json=equipment,
        valves_json=valves,
        instruments_json=instruments,
        language="uk",
        output_path="output/project_voda_premium.png"
    )
    print("Преміум-схему створено: output/project_voda_premium.png")
except Exception as e:
    print(f"Помилка: {e}")
