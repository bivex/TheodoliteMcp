import pytest
import os
from theodolite_mcp.infrastructure.mcp_server import draw_pipeline_schematic
from theodolite_mcp.domain.models.schematic import PipelineSchematic

def test_extreme_text_collision_density():
    """
    Тест на экстремальную плотность текста.
    Создаем ситуацию, где много оборудования и труб в одной точке.
    """
    output_path = "output/test_collision_density.png"
    
    # Очень плотное размещение элементов в одной зоне
    pipes = [
        {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 2, "y": 0}, "medium": "cold_water", "nominal_diameter": 32},
        {"start_pt": {"x": 0, "y": 0.2}, "end_pt": {"x": 2, "y": 0.2}, "medium": "hot_water", "nominal_diameter": 32},
        {"start_pt": {"x": 0.5, "y": -1}, "end_pt": {"x": 0.5, "y": 1}, "medium": "gas", "nominal_diameter": 25},
    ]
    
    equipment = [
        {"center_pt": {"x": 0.5, "y": 0}, "equipment_type": "centrifugal_pump", "label": "PUMP-ALPHA-12345", "tag": "P1-STATION-A"},
        {"center_pt": {"x": 1.0, "y": 0}, "equipment_type": "expansion_vessel", "label": "TANK-BETA-999", "tag": "T1-ZONE-B"},
    ]
    
    valves = [
        {"center_pt": {"x": 0.2, "y": 0}, "valve_type": "check", "tag": "CHECK-VALVE-01"},
        {"center_pt": {"x": 1.8, "y": 0}, "valve_type": "ball", "tag": "BALL-VALVE-GLOBAL"},
    ]
    
    try:
        draw_pipeline_schematic(
            title="DIAGNOSTIC: TEXT COLLISION TEST",
            pipes_json=pipes,
            equipment_json=equipment,
            valves_json=valves,
            scale=10, # Крупный масштаб для проверки деталей
            output_path=output_path
        )
        assert os.path.exists(output_path)
        print(f"\n[OK] Diagnostic collision map created at {output_path}")
    except Exception as e:
        pytest.fail(f"Rendering failed: {e}")

def test_long_labels_overlap():
    """
    Тест на длинные подписи, которые гарантированно должны пересекаться без трекера.
    """
    output_path = "output/test_long_labels.png"
    
    pipes = [
        {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 10, "y": 0}, "medium": "cold_water", "nominal_diameter": 50},
    ]
    
    # Оборудование очень близко друг к другу с длинными названиями
    equipment = [
        {"center_pt": {"x": 4, "y": 0}, "equipment_type": "boiler", "label": "VERY-LONG-BOILER-LABEL-THAT-MIGHT-OVERLAP", "tag": "B1"},
        {"center_pt": {"x": 6, "y": 0}, "equipment_type": "boiler", "label": "ANOTHER-EXTREMELY-LONG-LABEL-FOR-TESTING", "tag": "B2"},
    ]
    
    try:
        draw_pipeline_schematic(
            title="DIAGNOSTIC: LONG LABELS",
            pipes_json=pipes,
            equipment_json=equipment,
            scale=20,
            output_path=output_path
        )
        assert os.path.exists(output_path)
        print(f"[OK] Long label diagnostic created at {output_path}")
    except Exception as e:
        pytest.fail(f"Rendering failed: {e}")

if __name__ == "__main__":
    # Запускаем вручную если нужно сгенерировать картинки
    test_extreme_text_collision_density()
    test_long_labels_overlap()
