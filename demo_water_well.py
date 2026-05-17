import json
from theodolite_mcp.infrastructure.mcp_server import draw_pipeline_schematic

# Более реалистичная схема: Скважина (вертикально) -> Поворот -> Горизонтально -> В дом

pipes = [
    # Вертикальный участок из скважины
    {"start_pt": {"x": 0, "y": -2}, "end_pt": {"x": 0, "y": 0}, "medium": "cold_water", "nominal_diameter": 32},
    # Горизонтальный участок к гидроаккумулятору
    {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 4, "y": 0}, "medium": "cold_water", "nominal_diameter": 32},
    # От гидроаккумулятора к фильтру (чуть вверх)
    {"start_pt": {"x": 4, "y": 0}, "end_pt": {"x": 4, "y": 1}, "medium": "cold_water", "nominal_diameter": 25},
    {"start_pt": {"x": 4, "y": 1}, "end_pt": {"x": 8, "y": 1}, "medium": "cold_water", "nominal_diameter": 25},
    # Ввод в дом
    {"start_pt": {"x": 8, "y": 1}, "end_pt": {"x": 10, "y": 1}, "medium": "cold_water", "nominal_diameter": 25},
]

equipment = [
    # Насос скважинный (внизу)
    {"center_pt": {"x": 0, "y": -1.5}, "equipment_type": "centrifugal_pump", "label": "Скважинный насос", "tag": "P-1"},
    # Гидроаккумулятор (на повороте)
    {"center_pt": {"x": 4, "y": 0}, "equipment_type": "expansion_vessel", "label": "Гидроаккумулятор", "tag": "T-1", "width": 0.8, "height": 1.2},
    # Фильтр (на верхней полке)
    {"center_pt": {"x": 6, "y": 1}, "equipment_type": "mesh_filter", "label": "Фильтр очистки", "tag": "F-1"},
]

valves = [
    # Обратный клапан на выходе из скважины
    {"center_pt": {"x": 0, "y": -0.5}, "valve_type": "check", "tag": "V-1", "rotation": 90},
    # Запорный кран перед домом
    {"center_pt": {"x": 9, "y": 1}, "valve_type": "ball", "tag": "V-2"},
]

instruments = [
    # Манометр на гидроаккумуляторе
    {"center_pt": {"x": 4, "y": 0.5}, "measured_variable": "P", "suffix": "I", "tag_number": "01"}
]

try:
    # Увеличим масштаб (меньшее число = крупнее элементы на листе)
    result = draw_pipeline_schematic(
        title="Водопостачання: Схема підключення",
        pipes_json=pipes,
        equipment_json=equipment,
        valves_json=valves,
        instruments_json=instruments,
        language="ru",
        scale=25, # 1:25 будет крупнее чем 1:50
        output_path="output/water_well_improved.png"
    )
    print("Схема успешно создана: output/water_well_improved.png")
except Exception as e:
    print(f"Ошибка: {e}")
