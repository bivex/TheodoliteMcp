import pytest
import base64
from theodolite_mcp.infrastructure.mcp_server import mcp

@pytest.mark.anyio
async def test_draw_pipeline_schematic_tool():
    tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "draw_pipeline_schematic")
    
    pipes = [
        {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 10, "y": 0}, "medium": "heating_supply"}
    ]
    valves = [
        {"center_pt": {"x": 5, "y": 0}, "valve_type": "gate", "tag": "V1"}
    ]
    
    result = await tool.run({
        "title": "Integration Test Schematic",
        "pipes_json": pipes,
        "valves_json": valves
    })
    
    # FastMCP Image result has 'data' (bytes) and '_format'
    assert result._format == "png"
    assert len(result.data) > 0
    assert result.data.startswith(b'\x89PNG')

@pytest.mark.anyio
async def test_draw_pipeline_schematic_svg_tool():
    tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "draw_pipeline_schematic_svg")
    
    pipes = [
        {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 5, "y": 0}}
    ]
    
    result = await tool.run({
        "title": "SVG Integration Test",
        "pipes_json": pipes
    })
    
    assert isinstance(result, str)
    assert "<svg" in result
    assert "</svg>" in result

@pytest.mark.anyio
async def test_export_schematic_to_dxf_tool():
    tool = next(t for t in mcp._tool_manager.list_tools() if t.name == "mcp_export_schematic_to_dxf")
    
    pipes = [
        {"start_pt": {"x": 0, "y": 0}, "end_pt": {"x": 10, "y": 0}, "medium": "gas"}
    ]
    
    filename = "test_schematic_export.dxf"
    result = await tool.run({
        "filename": filename,
        "pipes_json": pipes
    })
    
    assert "test_schematic_export.dxf" in result
    import os
    assert os.path.exists(result)
    # Cleanup
    if os.path.exists(result):
        os.remove(result)
