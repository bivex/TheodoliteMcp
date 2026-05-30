import os
import ezdxf
import pytest
from theodolite_mcp.domain.models import Point, Zone, PlotPlan
from theodolite_mcp.domain.models.profile import ProfilePlan, ProfilePoint
from theodolite_mcp.domain.models.schematic import (
    PipelineSchematic, PipeSegment, ValveSymbol, EquipmentSymbol,
    PipeMedium, ValveType, EquipmentType
)
from theodolite_mcp.domain.dxf_export import (
    export_plan_to_dxf,
    export_profile_to_dxf,
    export_schematic_to_dxf
)
from theodolite_mcp.domain.dxf_validation import validate_dxf_file

class TestDXFExportExtended:
    
    def test_export_plot_plan_full(self, tmp_path):
        dxf_path = str(tmp_path / "plot_plan.dxf")
        plan = PlotPlan(
            title="Complex Plot Plan",
            boundary_points=[
                Point(x=0, y=0), Point(x=100, y=0),
                Point(x=100, y=100), Point(x=0, y=100), Point(x=0, y=0)
            ],
            zones=[
                Zone(name="Building A", points=[
                    Point(x=10, y=10), Point(x=30, y=10), Point(x=30, y=30), Point(x=10, y=30), Point(x=10, y=10)
                ], fill_color="#FF0000")
            ]
        )
        
        export_plan_to_dxf(plan, dxf_path)
        assert os.path.exists(dxf_path)
        
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
        
        # Verify layers
        layers = {layer.dxf.name for layer in doc.layers}
        assert "0_BOUNDARY" in layers
        assert "ZONE_BUILDINGS" in layers
        
        # Verify geometry
        polylines = msp.query('LWPOLYLINE')
        assert len(polylines) >= 2
        
        # Run validation
        report = validate_dxf_file(dxf_path)
        assert report.is_valid
        # Check validation issues by checking errors and warnings properties
        assert len(report.errors) == 0

    def test_export_profile_dxf(self, tmp_path):
        dxf_path = str(tmp_path / "profile.dxf")
        plan = ProfilePlan(
            title="Road Profile",
            points=[
                ProfilePoint(station=0, ground_z=100.0, design_z=101.0),
                ProfilePoint(station=100, ground_z=105.0, design_z=106.0),
            ],
            horiz_scale=1000,
            vert_scale=100
        )
        
        export_profile_to_dxf(plan, dxf_path)
        assert os.path.exists(dxf_path)
        
        doc = ezdxf.readfile(dxf_path)
        layers = {layer.dxf.name for layer in doc.layers}
        assert "V-PROF-GROUND" in layers
        assert "V-PROF-DESIGN" in layers
        
        report = validate_dxf_file(dxf_path)
        assert report.is_valid

    def test_export_schematic_dxf(self, tmp_path):
        dxf_path = str(tmp_path / "schematic.dxf")
        plan = PipelineSchematic(
            title="Boiler Room",
            pipes=[
                PipeSegment(start_pt=Point(x=0, y=0), end_pt=Point(x=10, y=0), 
                            medium=PipeMedium.HEATING_SUPPLY, nominal_diameter=50)
            ],
            valves=[
                ValveSymbol(center_pt=Point(x=5, y=0), valve_type=ValveType.GATE, tag="V1")
            ],
            equipment=[
                EquipmentSymbol(center_pt=Point(x=0, y=0), equipment_type=EquipmentType.BOILER, tag="B1")
            ]
        )
        
        export_schematic_to_dxf(plan, dxf_path)
        assert os.path.exists(dxf_path)
        
        doc = ezdxf.readfile(dxf_path)
        layers = {layer.dxf.name for layer in doc.layers}
        
        # Schematic uses layers based on medium and symbol type
        assert "PIPE_HEATING_SUPPLY" in layers
        assert "SYMBOLS_EQUIPMENT" in layers or "SYMBOLS_VALVES" in layers
        
        report = validate_dxf_file(dxf_path)
        assert report.is_valid

    def test_dxf_validation_on_corrupt_file(self, tmp_path):
        # Create a non-DXF file
        corrupt_path = tmp_path / "corrupt.dxf"
        with open(corrupt_path, "w") as f:
            f.write("This is not a DXF file")
            
        report = validate_dxf_file(str(corrupt_path))
        assert not report.is_valid
        assert any("Cannot read DXF file" in issue.message for issue in report.issues)
