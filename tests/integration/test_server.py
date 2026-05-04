import pytest
from theodolite_mcp.infrastructure.mcp_server import mcp

def test_mcp_tool_registration():
    # Check if the tools are registered in FastMCP
    tool_names = [tool.name for tool in mcp._tool_manager.list_tools()]
    assert "adjust_traverse_network" in tool_names
    assert "compute_forward_azimuth" in tool_names
    assert "dms_to_decimal_degrees" in tool_names
    assert "decimal_degrees_to_dms" in tool_names

@pytest.mark.anyio
async def test_adjust_traverse_network_tool():
    # Test the tool function directly
    process_tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "adjust_traverse_network")
    
    # Square 100x100
    observations = [
        {"point_name": "P2", "horizontal_angle": 90.0, "distance": 100.0},
        {"point_name": "P3", "horizontal_angle": 90.0, "distance": 100.0},
        {"point_name": "P4", "horizontal_angle": 90.0, "distance": 100.0},
        {"point_name": "P1_back", "horizontal_angle": 90.0, "distance": 100.0},
    ]
    
    result = await process_tool.run({
        "start_x": 0.0,
        "start_y": 0.0,
        "start_name": "P1",
        "start_azimuth": 0.0,
        "observations_json": observations,
        "is_closed": True
    })
    
    assert result["angular_misclosure"] == pytest.approx(0)
    assert result["points"][-1]["x"] == pytest.approx(0)

@pytest.mark.anyio
async def test_compute_forward_azimuth_tool():
    azimuth_tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "compute_forward_azimuth")
    
    # North
    result = await azimuth_tool.run({
        "x1": 0, "y1": 0, "x2": 10, "y2": 0
    })
    assert result == pytest.approx(0)
