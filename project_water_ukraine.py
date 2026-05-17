import json
from theodolite_mcp.infrastructure.mcp_server import draw_pipeline_schematic

# Проект: Водопостачання (Україна)
# Свердловина 32м -> Водолій БЦПЭ -> SantehPlast 24L -> Atlantic 50L

# 1. ТРУБОПРОВОДИ (Координати в метрах)
pipes = [
    # Вертикальний підйом зі свердловини (32м вниз, показуємо частину)
    {"start_pt": {"x": 0, "y": -5}, "end_pt": {"x": 0, "y": 0}, "medium": "cold_water", "nominal_diameter": 32},
    # Магістраль до будинку (14 метрів)
    {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 14, "y": 0}, "medium": "cold_water", "nominal_diameter": 32},
    # Вхід у будинок та підйом до автоматики
    {"start_pt": {"x": 14, "y": 0}, "end_pt": {"x": 14, "y": 1.5}, "medium": "cold_water", "nominal_diameter": 25},
    # Лінія через фільтри до бойлера
    {"start_pt": {"x": 14, "y": 1.5}, "end_pt": {"x": 20, "y": 1.5}, "medium": "cold_water", "nominal_diameter": 20},
    # Гаряча вода від бойлера до споживача
    {"start_pt": {"x": 20, "y": 2.5}, "end_pt": {"x": 25, "y": 2.5}, "medium": "hot_water", "nominal_diameter": 20},
]

# 2. ОБЛАДНАННЯ
equipment = [
    # Скважинний насос
    {"center_pt": {"x": 0, "y": -4}, "equipment_type": "centrifugal_pump", "label": "Водолій БЦПЭ 0,5-40У", "tag": "P-1"},
    
    # Гідроакумулятор
    {"center_pt": {"x": 14, "y": 1.5}, "equipment_type": "expansion_vessel", "label": "SantehPlast HT-24L", "tag": "GA-1", "width": 0.6, "height": 0.9},
    
    # Фільтрація
    {"center_pt": {"x": 16.5, "y": 1.5}, "equipment_type": "mesh_filter", "label": "Груба очистка", "tag": "F-1"},
    {"center_pt": {"x": 18.5, "y": 1.5}, "equipment_type": "storage_tank", "label": "Тонка очистка", "tag": "F-2", "width": 0.5, "height": 0.8},
    
    # Бойлер
    {"center_pt": {"x": 20, "y": 2.0}, "equipment_type": "boiler", "label": "Atlantic VM 50 S3", "tag": "B-1", "width": 0.8, "height": 1.2},
]

# 3. АРМАТУРА (Крани та клапани)
valves = [
    # Зворотний клапан (важливо для Водолія)
    {"center_pt": {"x": 0, "y": -2}, "valve_type": "check", "tag": "CV-1", "rotation": 90},
    
    # Головний кран на вході
    {"center_pt": {"x": 13, "y": 0.5}, "valve_type": "ball", "tag": "V-1", "rotation": 90},
    
    # Обв'язка бойлера
    {"center_pt": {"x": 19.5, "y": 1.5}, "valve_type": "ball", "tag": "V-2"}, # Вхід ХВП
    {"center_pt": {"x": 20.5, "y": 2.5}, "valve_type": "ball", "tag": "V-3"}, # Вихід ГВП
]

# 4. ПРИЛАДИ (Автоматика)
instruments = [
    # Реле тиску та манометр біля ГА
    {"center_pt": {"x": 14.5, "y": 2.2}, "measured_variable": "P", "suffix": "I", "tag_number": "01"},
    {"center_pt": {"x": 15.5, "y": 2.2}, "measured_variable": "P", "suffix": "C", "tag_number": "01"}, # Pressure Controller
]

try:
    result = draw_pipeline_schematic(
        title="Проєкт водопостачання: Свердловина - Будинок - Бойлер",
        project_number="WATER-2026-02",
        organization="Solo Developer Project",
        pipes_json=pipes,
        equipment_json=equipment,
        valves_json=valves,
        instruments_json=instruments,
        language="ru",
        scale=50, 
        output_path="output/project_voda_ukraine.png"
    )
    print("Чертеж проекта успешно создан: output/project_voda_ukraine.png")
except Exception as e:
    print(f"Ошибка при создании чертежа: {e}")
