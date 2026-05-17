import json
from theodolite_mcp.infrastructure.mcp_server import draw_pipeline_schematic

# --- ПРОЕКТ: ЕКСПЕРТНЕ ВОДОПОСТАЧАННЯ (УКРАЇНА) ---
# Свердловина 32м -> Фільтрація -> Бойлер
# Принцип: Просторове групування вузлів для 100% читаємості

# 1. ТРУБОПРОВОДИ (Збільшені відстані між вузлами для уникнення злипання тексту)
pipes = [
    # ГРУПА А: СВЕРДЛОВИНА ТА КЕСОН (x: 0-5)
    {"start_pt": {"x": 0, "y": -5}, "end_pt": {"x": 0, "y": 0}, "medium": "cold_water", "nominal_diameter": 32},
    {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 5, "y": 0}, "medium": "cold_water", "nominal_diameter": 32},
    
    # ГРУПА Б: ВВІД У БУДИНОК ТА ГІДРОАКУМУЛЯТОР (x: 10-15)
    {"start_pt": {"x": 5, "y": 0}, "end_pt": {"x": 10, "y": 0}, "medium": "cold_water", "nominal_diameter": 32},
    {"start_pt": {"x": 10, "y": 0}, "end_pt": {"x": 10, "y": 2}, "medium": "cold_water", "nominal_diameter": 32},
    {"start_pt": {"x": 10, "y": 2}, "end_pt": {"x": 15, "y": 2}, "medium": "cold_water", "nominal_diameter": 25},
    
    # ГРУПА В: КАСКАД ОЧИСТКИ (x: 18-24)
    {"start_pt": {"x": 15, "y": 2}, "end_pt": {"x": 25, "y": 2}, "medium": "cold_water", "nominal_diameter": 25},
    
    # ГРУПА Г: ПРИГОТУВАННЯ ГАРЯЧОЇ ВОДИ (x: 28-35)
    {"start_pt": {"x": 25, "y": 2}, "end_pt": {"x": 30, "y": 2}, "medium": "cold_water", "nominal_diameter": 20},
    {"start_pt": {"x": 30, "y": 2.5}, "end_pt": {"x": 30, "y": 4}, "medium": "hot_water", "nominal_diameter": 20},
    {"start_pt": {"x": 30, "y": 4}, "end_pt": {"x": 35, "y": 4}, "medium": "hot_water", "nominal_diameter": 20},
]

# 2. ОБЛАДНАННЯ (Кожен вузол має вільний радіус 2-3 метри)
equipment = [
    # Свердловина
    {"center_pt": {"x": 0, "y": -4}, "equipment_type": "centrifugal_pump", "label": "Водолій БЦПЭ 0.5-40У", "tag": "P-1"},
    
    # Автоматика (В розриві лінії)
    {"center_pt": {"x": 10, "y": 2}, "equipment_type": "expansion_vessel", "label": "SantehPlast HT-24L", "tag": "GA-1", "width": 1.0, "height": 1.5},
    
    # Очистка (Рознесено на 4 метри один від одного)
    {"center_pt": {"x": 19, "y": 2}, "equipment_type": "mesh_filter", "label": "Груба очистка", "tag": "F-1"},
    {"center_pt": {"x": 23, "y": 2}, "equipment_type": "storage_tank", "label": "Тонка очистка", "tag": "F-2", "width": 0.8, "height": 1.2},
    
    # Бойлер (Atlantic)
    {"center_pt": {"x": 30, "y": 3.2}, "equipment_type": "boiler", "label": "Atlantic VM 50 S3", "tag": "B-1", "width": 1.0, "height": 1.4},
]

# 3. АРМАТУРА (Чітко на стиках)
valves = [
    {"center_pt": {"x": 0, "y": -1.5}, "valve_type": "check", "tag": "CV-1", "rotation": 90},
    {"center_pt": {"x": 8, "y": 0}, "valve_type": "ball", "tag": "V-1"}, # Головний кран на ввід
    
    # Обв'язка бойлера
    {"center_pt": {"x": 28, "y": 2}, "valve_type": "ball", "tag": "V-2"}, # Вхід ХВП
    {"center_pt": {"x": 32, "y": 4}, "valve_type": "ball", "tag": "V-3"}, # Вихід ГВП
]

# 4. КИПІА (Контрольні точки)
instruments = [
    {"center_pt": {"x": 11, "y": 3}, "measured_variable": "P", "suffix": "I", "tag_number": "01"}, # Манометр
    {"center_pt": {"x": 13, "y": 3}, "measured_variable": "P", "suffix": "C", "tag_number": "01"}, # Реле тиску
]

try:
    draw_pipeline_schematic(
        title="ПРОЄКТ ВОДОПОСТАЧАННЯ (ЕКСПЕРТНИЙ РІВЕНЬ)",
        project_number="UKR-WATER-2026-EXPERT",
        organization="Santyh Master Pro",
        pipes_json=pipes,
        equipment_json=equipment,
        valves_json=valves,
        instruments_json=instruments,
        language="ru",
        scale=60, # Трохи зменшуємо масштаб, щоб на А3 влізли всі рознесені вузли
        output_path="output/project_voda_expert.png"
    )
    print("Експертний чертеж створено: output/project_voda_expert.png")
except Exception as e:
    print(f"Помилка: {e}")
