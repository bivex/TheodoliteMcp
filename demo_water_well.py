import json
from theodolite_mcp.infrastructure.mcp_server import draw_pipeline_schematic

# Расширенная схема: Скважина -> Насос -> Очистка -> Ввод в дом -> Гребенка -> Потребители

pipes = [
    # Участок Скважина - Кессон (вертикальный)
    {"start_pt": {"x": 0, "y": -2}, "end_pt": {"x": 0, "y": 0}, "medium": "cold_water", "nominal_diameter": 32},
    # Участок Кессон - Дом (горизонтальный в земле)
    {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 4, "y": 0}, "medium": "cold_water", "nominal_diameter": 32},
    # Подъем в доме к гидроаккумулятору
    {"start_pt": {"x": 4, "y": 0}, "end_pt": {"x": 4, "y": 1}, "medium": "cold_water", "nominal_diameter": 32},
    # Горизонтальный участок в котельной (через фильтр)
    {"start_pt": {"x": 4, "y": 1}, "end_pt": {"x": 10, "y": 1}, "medium": "cold_water", "nominal_diameter": 25},
    
    # ПОСЛЕ КРАНА V-2: Распределение в доме (Гребенка)
    # Основная ветка гребенки
    {"start_pt": {"x": 10, "y": 1}, "end_pt": {"x": 10, "y": 3}, "medium": "cold_water", "nominal_diameter": 32},
    # Ветка на кухню
    {"start_pt": {"x": 10, "y": 2}, "end_pt": {"x": 12, "y": 2}, "medium": "cold_water", "nominal_diameter": 20},
    # Ветка в санузел
    {"start_pt": {"x": 10, "y": 3}, "end_pt": {"x": 12, "y": 3}, "medium": "cold_water", "nominal_diameter": 20},
]

equipment = [
    # Оборудование в скважине/кессоне
    {"center_pt": {"x": 0, "y": -1.5}, "equipment_type": "centrifugal_pump", "label": "Насос", "tag": "P-1"},
    
    # Оборудование в доме
    {"center_pt": {"x": 4, "y": 1}, "equipment_type": "expansion_vessel", "label": "Бак 50л", "tag": "T-1", "width": 0.8, "height": 1.2},
    {"center_pt": {"x": 6, "y": 1}, "equipment_type": "mesh_filter", "label": "Грубая очистка", "tag": "F-1"},
    {"center_pt": {"x": 8, "y": 1}, "equipment_type": "storage_tank", "label": "Тонкая очистка", "tag": "F-2", "width": 0.6, "height": 1.0},
    
    # Потребители
    {"center_pt": {"x": 12, "y": 2}, "equipment_type": "boiler", "label": "Кухня", "tag": "KITCHEN", "width": 0.4, "height": 0.4},
    {"center_pt": {"x": 12, "y": 3}, "equipment_type": "boiler", "label": "Санузел", "tag": "BATH", "width": 0.4, "height": 0.4},
]

valves = [
    {"center_pt": {"x": 0, "y": -0.5}, "valve_type": "check", "tag": "V-1", "rotation": 90}, # Обратный клапан
    {"center_pt": {"x": 9.5, "y": 1}, "valve_type": "ball", "tag": "V-2"}, # Главный кран в доме
    
    # Краны на гребенке
    {"center_pt": {"x": 11, "y": 2}, "valve_type": "ball", "tag": "V-3"},
    {"center_pt": {"x": 11, "y": 3}, "valve_type": "ball", "tag": "V-4"},
]

instruments = [
    {"center_pt": {"x": 4, "y": 1.8}, "measured_variable": "P", "suffix": "I", "tag_number": "01"} # Манометр
]

try:
    result = draw_pipeline_schematic(
        title="Водопостачання: Повна схема (від свердловини до будинку)",
        pipes_json=pipes,
        equipment_json=equipment,
        valves_json=valves,
        instruments_json=instruments,
        language="ru",
        scale=30, 
        output_path="output/water_well_complete.png"
    )
    print("Полная схема создана: output/water_well_complete.png")
except Exception as e:
    print(f"Ошибка: {e}")
