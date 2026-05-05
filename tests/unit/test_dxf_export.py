import os
import ezdxf
import pytest
from theodolite_mcp.domain.models import Point, Zone, PlotPlan
from theodolite_mcp.domain.dxf_export import export_plan_to_dxf

def test_export_to_dxf_file_creation(tmp_path):
    # Setup
    dxf_file = tmp_path / "test.dxf"
    boundary = [Point(name="P1", x=0, y=0), Point(name="P2", x=10, y=0), Point(name="P1", x=0, y=0)]
    plan = PlotPlan(title="Test Plan", boundary_points=boundary, zones=[])
    
    # Act
    path = export_plan_to_dxf(plan, str(dxf_file))
    
    # Assert
    assert os.path.exists(path)
    doc = ezdxf.readfile(path)
    assert doc.dxfversion == 'AC1024' # R2010

def test_dxf_layers_and_entities(tmp_path):
    # Setup
    dxf_file = tmp_path / "layers_test.dxf"
    boundary = [Point(name="1", x=0, y=0), Point(name="2", x=10, y=10)]
    zones = [
        Zone(name="House", points=[Point(name="H1", x=2, y=2), Point(name="H2", x=5, y=5)])
    ]
    plan = PlotPlan(title="Layer Test", boundary_points=boundary, zones=zones)
    
    # Act
    export_plan_to_dxf(plan, str(dxf_file))
    
    # Assert
    doc = ezdxf.readfile(str(dxf_file))
    layers = [layer.dxf.name for layer in doc.layers]
    
    assert "0_BOUNDARY" in layers
    assert "ZONE_BUILDINGS" in layers
    assert "0_POINTS" in layers
    
    msp = doc.modelspace()
    # Check for polyline in boundary layer
    boundary_entities = msp.query('LWPOLYLINE[layer=="0_BOUNDARY"]')
    assert len(boundary_entities) == 1
    
    # Check for polyline in building layer
    building_entities = msp.query('LWPOLYLINE[layer=="ZONE_BUILDINGS"]')
    assert len(building_entities) == 1
    
    # Check for points
    point_entities = msp.query('POINT[layer=="0_POINTS"]')
    assert len(point_entities) == 2

def test_dxf_text_labels(tmp_path):
    # Setup
    dxf_file = tmp_path / "text_test.dxf"
    boundary = [Point(name="TargetPoint", x=5.5, y=6.6)]
    plan = PlotPlan(title="Text Test", boundary_points=boundary, show_vertex_labels=True)
    
    # Act
    export_plan_to_dxf(plan, str(dxf_file))
    
    # Assert
    doc = ezdxf.readfile(str(dxf_file))
    msp = doc.modelspace()
    text_entities = msp.query('TEXT[layer=="0_TEXT"]')
    
    texts = [t.dxf.text for t in text_entities]
    assert "TargetPoint" in texts
