import json
from theodolite_mcp.infrastructure.mcp_server import draw_pipeline_schematic

# Тест всех типов оборудования и арматуры
pipes = [
    {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 20, "y": 0}, "medium": "cold_water", "nominal_diameter": 25},
]

equipment = [
    {"center_pt": {"x": 2, "y": 1}, "equipment_type": "centrifugal_pump", "label": "Насос"},
    {"center_pt": {"x": 4, "y": 1}, "equipment_type": "boiler", "label": "Бойлер"},
    {"center_pt": {"x": 6, "y": 1}, "equipment_type": "expansion_vessel", "label": "Бак"},
    {"center_pt": {"x": 8, "y": 1}, "equipment_type": "storage_tank", "label": "Резервуар"},
    {"center_pt": {"x": 10, "y": 1}, "equipment_type": "mesh_filter", "label": "Фильтр"},
    {"center_pt": {"x": 12, "y": 1}, "equipment_type": "pressure_gauge", "label": "Манометр"},
    {"center_pt": {"x": 14, "y": 1}, "equipment_type": "thermometer", "label": "Термометр"},
]

valves = [
    {"center_pt": {"x": 1, "y": 0}, "valve_type": "gate", "tag": "Gate"},
    {"center_pt": {"x": 3, "y": 0}, "valve_type": "ball", "tag": "Ball"},
    {"center_pt": {"x": 5, "y": 0}, "valve_type": "check", "tag": "Check"},
    {"center_pt": {"x": 7, "y": 0}, "valve_type": "butterfly", "tag": "Butterfly"},
    {"center_pt": {"x": 9, "y": 0}, "valve_type": "globe", "tag": "Globe"},
    {"center_pt": {"x": 11, "y": 0}, "valve_type": "3way_mixing", "tag": "3-Way"},
    {"center_pt": {"x": 13, "y": 0}, "valve_type": "prv", "tag": "PRV"},
    {"center_pt": {"x": 15, "y": 0}, "valve_type": "safety", "tag": "Safety"},
]

try:
    draw_pipeline_schematic(
        title="TEST: ALL ICONS",
        pipes_json=pipes,
        equipment_json=equipment,
        valves_json=valves,
        output_path="output/test_all_icons.png"
    )
    print("Test file created: output/test_all_icons.png")
except Exception as e:
    print(f"Error: {e}")
