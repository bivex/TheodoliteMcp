import json
from theodolite_mcp.infrastructure.mcp_server import draw_pipeline_schematic

# --- ПРОЄКТ: "ДЕШЕВО ТА СЕРДИТО" (Економ-варіант водопостачання) ---
# Мінімум автоматики, вібраційний насос типу "Малюк", проста фільтрація.

pipes = [
    # Від свердловини до будинку (ПНД 25мм - дешевше)
    {"start_pt": {"x": 0, "y": -10}, "end_pt": {"x": 0, "y": -2}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    {"start_pt": {"x": 0, "y": -2}, "end_pt": {"x": 8, "y": -2}, "medium": "cold_water", "nominal_diameter": 25, "flow_direction": "forward"},
    
    # Ввід і автоматика (ПП 20мм)
    {"start_pt": {"x": 8, "y": -2}, "end_pt": {"x": 8, "y": 2}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"},
    {"start_pt": {"x": 8, "y": 2}, "end_pt": {"x": 14, "y": 2}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"},
    
    # На кухню
    {"start_pt": {"x": 14, "y": 2}, "end_pt": {"x": 20, "y": 2}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"},
    {"start_pt": {"x": 20, "y": 2.5}, "end_pt": {"x": 20, "y": 6}, "medium": "hot_water", "nominal_diameter": 20, "flow_direction": "forward"},
    {"start_pt": {"x": 20, "y": 6}, "end_pt": {"x": 24, "y": 6}, "medium": "hot_water", "nominal_diameter": 20, "flow_direction": "forward"},
    # Холодна до мийки
    {"start_pt": {"x": 20, "y": 2}, "end_pt": {"x": 24, "y": 2}, "medium": "cold_water", "nominal_diameter": 20, "flow_direction": "forward"},
]

equipment = [
    # Насос - вібраційний (дешевий)
    {"center_pt": {"x": 0, "y": -8}, "equipment_type": "centrifugal_pump", "label": "Насос 'Малюк'", "tag": "P-1", "width": 1.0, "height": 1.0},
    
    # Гідроакумулятор (маленький і дешевий)
    {"center_pt": {"x": 8, "y": 2}, "equipment_type": "expansion_vessel", "label": "Бак 24Л", "tag": "GA-1", "width": 1.5, "height": 2.0},
    
    # Очистка (лише один дешевий фільтр-колба)
    {"center_pt": {"x": 12, "y": 2}, "equipment_type": "mesh_filter", "label": "Фільтр 10\"", "tag": "F-1", "width": 0.8, "height": 1.2},
    
    # Малий бойлер під мийку
    {"center_pt": {"x": 20, "y": 4}, "equipment_type": "boiler", "label": "Бойлер 15Л", "tag": "B-1", "width": 1.2, "height": 1.5},
]

valves = [
    {"center_pt": {"x": 0, "y": -1.5}, "valve_type": "check", "tag": "CV-1", "rotation": 90, "nominal_diameter": 32},
    {"center_pt": {"x": 5, "y": -2}, "valve_type": "ball", "tag": "V-1", "nominal_diameter": 32}, # Головний кран
    
    # Обв'язка бойлера (один кран для економії)
    {"center_pt": {"x": 18, "y": 2}, "valve_type": "ball", "tag": "V-2", "nominal_diameter": 25},
]

instruments = [
    # Найдешевше механічне реле
    {"center_pt": {"x": 10.0, "y": 2.6}, "measured_variable": "P", "suffix": "C", "tag_number": "01"},
]

try:
    draw_pipeline_schematic(
        title="ЕКОНОМ-ВОДОПОСТАЧАННЯ (Бюджетний варіант)",
        project_number="UKR-CHEAP-01",
        organization="DIY Village",
        pipes_json=pipes,
        equipment_json=equipment,
        valves_json=valves,
        instruments_json=instruments,
        language="uk",
        output_path="output/project_voda_cheap.png"
    )
    print("Економ-схему створено: output/project_voda_cheap.png")
except Exception as e:
    print(f"Помилка: {e}")
