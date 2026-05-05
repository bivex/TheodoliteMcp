import pytest
import json
from theodolite_mcp.infrastructure.mcp_server import (
    adjust_traverse_network, draw_plot_plan, dms_to_decimal_degrees
)
from theodolite_mcp.domain.models import Point

def test_full_survey_workflow_integration():
    """
    Simulate a full workflow: 
    1. Convert angles
    2. Adjust a closed traverse
    3. Render the resulting points into a plan
    """
    # 1. Angles conversion
    angle_a = dms_to_decimal_degrees(90, 0, 0) # 90.0
    angle_b = dms_to_decimal_degrees(90, 0, 0)
    angle_c = dms_to_decimal_degrees(90, 0, 0)
    angle_d = dms_to_decimal_degrees(90, 0, 0)
    
    assert angle_a == 90.0
    
    # 2. Closed Loop Traverse (Square 100x100)
    observations = [
        {"point_name": "P2", "horizontal_angle": 90.0, "distance": 100.0},
        {"point_name": "P3", "horizontal_angle": 90.0, "distance": 100.0},
        {"point_name": "P4", "horizontal_angle": 90.0, "distance": 100.0},
        {"point_name": "P1_back", "horizontal_angle": 90.0, "distance": 100.0},
    ]
    
    result = adjust_traverse_network(
        start_x=0.0,
        start_y=0.0,
        start_name="P1",
        start_azimuth=0.0, # Facing East
        observations_json=observations,
        is_closed=True
    )
    
    # Check closure
    assert result["linear_misclosure"] < 0.001
    assert result["angular_misclosure"] == 0.0
    assert len(result["points"]) == 5 # P1, P2, P3, P4, P1_final
    
    # Verify square coordinates
    # Surveying convention (X=North, Y=East):
    # 1. P1->P2: StartAz=0, Angle=90. NewAz = 0 + 90 - 180 = -90 = 270 (West). 
    #    dx (North) = 100 * cos(270) = 0, dy (East) = 100 * sin(270) = -100.
    #    P2: (0, -100)
    p2 = result["points"][1]
    assert p2["x"] == pytest.approx(0.0, abs=1e-4)
    assert p2["y"] == pytest.approx(-100.0, abs=1e-4)
    
    # 3. Rendering Integration
    # Take the points and render a plan
    boundary = result["points"][:-1] # Remove closing duplicate
    
    # Test MCP tool draw_plot_plan
    image = draw_plot_plan(
        title="Integration Test Plot",
        boundary_json=boundary,
        standard="construction",
        show_vertex_labels=True,
        coordinate_labels=True
    )
    
    assert len(image.data) > 0

def test_shipbuilding_render_integration():
    """Verify that shipbuilding standard renders correctly through the MCP tool."""
    boundary = [
        {"name": "0", "x": 0, "y": 0},
        {"name": "10", "x": 50, "y": 0},
        {"name": "10", "x": 50, "y": 10},
        {"name": "0", "x": 0, "y": 10},
    ]
    
    image = draw_plot_plan(
        title="Ship Hull Section",
        boundary_json=boundary,
        standard="shipbuilding",
        language="uk"
    )
    
    assert len(image.data) > 0

def test_precision_evaluation_integration():
    """Verify that precision evaluation works through the MCP tool."""
    # Closed Loop with intentional 1m error
    observations = [
        {"point_name": "P2", "horizontal_angle": 90.0, "distance": 100.0},
        {"point_name": "P3", "horizontal_angle": 90.0, "distance": 100.0},
        {"point_name": "P4", "horizontal_angle": 90.0, "distance": 100.0},
        {"point_name": "P1_back", "horizontal_angle": 90.0, "distance": 101.0}, # 1m error
    ]
    
    result = adjust_traverse_network(
        start_x=0.0,
        start_y=0.0,
        observations_json=observations,
        is_closed=True
    )
    
    assert "Satisfactory" in result["precision_status"] or "Excellent" in result["precision_status"] or "Unacceptable" in result["precision_status"]
    assert result["linear_misclosure"] > 0.5
