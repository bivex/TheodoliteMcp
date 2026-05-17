import json
from theodolite_mcp.infrastructure.mcp_server import draw_pipeline_schematic

# --- ПРОЄКТ: ЕКСПЕРТНЕ ВОДОПОСТАЧАННЯ (УКРАЇНА) ---
# Свердловина 32м -> Фільтрація -> Бойлер
# Принцип: Просторове групування вузлів, великі іконки, читабельний текст

# 1. ТРУБОПРОВОДИ (Стиснуті по осі X, щоб все ідеально влізло на А3)
pipes = [
    # ГРУПА А: СВЕРДЛОВИНА ТА КЕСОН (x: 0-1)
    {"start_pt": {"x": 0, "y": -4}, "end_pt": {"x": 0, "y": 0}, "medium": "cold_water", "nominal_diameter": 32},
    {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 2, "y": 0}, "medium": "cold_water", "nominal_diameter": 32},
    
    # ГРУПА Б: ВВІД У БУДИНОК ТА ГІДРОАКУМУЛЯТОР (x: 2-3)
    {"start_pt": {"x": 2, "y": 0}, "end_pt": {"x": 2, "y": 1.5}, "medium": "cold_water", "nominal_diameter": 32},
    {"start_pt": {"x": 2, "y": 1.5}, "end_pt": {"x": 4, "y": 1.5}, "medium": "cold_water", "nominal_diameter": 25},
    
    # ГРУПА В: КАСКАД ОЧИСТКИ (x: 4-7)
    {"start_pt": {"x": 4, "y": 1.5}, "end_pt": {"x": 7, "y": 1.5}, "medium": "cold_water", "nominal_diameter": 25},
    {"start_pt": {"x": 7, "y": 1.5}, "end_pt": {"x": 7, "y": 3}, "medium": "cold_water", "nominal_diameter": 20},
    
    # ГРУПА Г: ПРИГОТУВАННЯ ГАРЯЧОЇ ВОДИ (x: 7-10)
    {"start_pt": {"x": 7, "y": 3}, "end_pt": {"x": 8, "y": 3}, "medium": "cold_water", "nominal_diameter": 20},
    {"start_pt": {"x": 8, "y": 3.5}, "end_pt": {"x": 8, "y": 4.5}, "medium": "hot_water", "nominal_diameter": 20},
    {"start_pt": {"x": 8, "y": 4.5}, "end_pt": {"x": 10, "y": 4.5}, "medium": "hot_water", "nominal_diameter": 20},
]

# 2. ОБЛАДНАННЯ (Великі розміри для кращої видимості)
equipment = [
    # Свердловина
    {"center_pt": {"x": 0, "y": -3.5}, "equipment_type": "centrifugal_pump", "label": "Водолій БЦПЕ 0.5-40У", "tag": "P-1"},
    
    # Автоматика
    {"center_pt": {"x": 2, "y": 1.5}, "equipment_type": "expansion_vessel", "label": "SantehPlast HT-24L", "tag": "GA-1", "width": 1.2, "height": 1.8},
    
    # Очистка
    {"center_pt": {"x": 4.5, "y": 1.5}, "equipment_type": "mesh_filter", "label": "Груба очистка", "tag": "F-1", "width": 0.8, "height": 0.8},
    {"center_pt": {"x": 6.0, "y": 1.5}, "equipment_type": "storage_tank", "label": "Тонка очистка", "tag": "F-2", "width": 0.8, "height": 1.2},
    
    # Бойлер (Atlantic)
    {"center_pt": {"x": 8, "y": 3.25}, "equipment_type": "boiler", "label": "Atlantic VM 50 S3", "tag": "B-1", "width": 1.2, "height": 1.8},
]

# 3. АРМАТУРА
valves = [
    {"center_pt": {"x": 0, "y": -1.5}, "valve_type": "check", "tag": "CV-1", "rotation": 90, "nominal_diameter": 40},
    {"center_pt": {"x": 1, "y": 0}, "valve_type": "ball", "tag": "V-1", "nominal_diameter": 40}, # Головний кран на ввід
    
    # Обв'язка бойлера
    {"center_pt": {"x": 7.5, "y": 3}, "valve_type": "ball", "tag": "V-2", "nominal_diameter": 30}, # Вхід ХВП
    {"center_pt": {"x": 8, "y": 4}, "valve_type": "ball", "tag": "V-3", "nominal_diameter": 30, "rotation": 90}, # Вихід ГВП
]

# 4. КИПІА (Контрольні точки)
instruments = [
    {"center_pt": {"x": 2.5, "y": 2.5}, "measured_variable": "P", "suffix": "I", "tag_number": "01"}, # Манометр
    {"center_pt": {"x": 3.2, "y": 2.5}, "measured_variable": "P", "suffix": "C", "tag_number": "01"}, # Реле тиску
]

try:
    draw_pipeline_schematic(
        title="ПРОЄКТ ВОДОПОСТАЧАННЯ (ЕКСПЕРТНИЙ РІВЕНЬ)",
        project_number="UKR-WATER-2026",
        organization="Solo Developer Project",
        pipes_json=pipes,
        equipment_json=equipment,
        valves_json=valves,
        instruments_json=instruments,
        language="uk", # Використовуємо українську
        scale=30, # Більший масштаб
        output_path="output/project_voda_expert.png"
    )
    print("Експертне креслення створено: output/project_voda_expert.png")
except Exception as e:
    print(f"Помилка: {e}")
