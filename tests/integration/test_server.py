import pytest
from theodolite_mcp.infrastructure.mcp_server import mcp

def test_mcp_tool_registration():
    # Check if the tools are registered in FastMCP
    tool_names = [tool.name for tool in mcp._tool_manager.list_tools()]
    assert "process_traverse" in tool_names
    assert "calculate_azimuth" in tool_names
    assert "convert_dms_to_decimal" in tool_names
    assert "convert_decimal_to_dms" in tool_names

@pytest.mark.anyio
async def test_process_traverse_tool():
    # Test the tool function directly
    # We can find the tool function from the manager
    process_tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "process_traverse")
    
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
    
    # result is the return value of process_traverse, which is a dict (model_dump)
    assert result["angular_misclosure"] == pytest.approx(0)
    assert result["points"][-1]["x"] == pytest.approx(0)
    assert result["points"][-1]["y"] == pytest.approx(0)

@pytest.mark.anyio
async def test_calculate_azimuth_tool():
    azimuth_tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "calculate_azimuth")
    
    # North
    result = await azimuth_tool.run({
        "x1": 0, "y1": 0, "x2": 10, "y2": 0
    })
    assert result == pytest.approx(0)
    
    # East
    result = await azimuth_tool.run({
        "x1": 0, "y1": 0, "x2": 0, "y2": 10
    })
    assert result == pytest.approx(90)
