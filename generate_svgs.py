import os
from theodolite_mcp.domain.models import (
    Point, Wall, Opening, Room, InteriorPlan, FurnitureItem,
    PlotPlan, Zone, AsBuiltPoint,
)
from theodolite_mcp.domain.models.profile import ProfilePlan, ProfilePoint
from theodolite_mcp.domain.models.schematic import (
    PipelineSchematic, PipeSegment, ValveSymbol, EquipmentSymbol,
    PipeMedium, ValveType, EquipmentType, InstrumentSymbol,
)
from theodolite_mcp.domain.rendering import (
    render_plot_plan, render_profile_plan, render_interior_plan,
)
from theodolite_mcp.domain.schematic_rendering import render_pipeline_schematic

def main():
    os.makedirs("output", exist_ok=True)

    print("Generating Plot Plan SVG...")
    plot_plan = PlotPlan(
        title="Zoned Plot Plan",
        boundary_points=[
            Point(x=0, y=0), Point(x=100, y=0),
            Point(x=100, y=100), Point(x=0, y=100),
        ],
        zones=[
            Zone(name="Building", points=[
                Point(x=20, y=20), Point(x=80, y=20),
                Point(x=80, y=80), Point(x=20, y=80),
            ], fill_color="#FFDDDD"),
        ],
    )
    svg_plot = render_plot_plan(plot_plan, output_format="svg")
    with open("output/plot_plan.svg", "wb") as f:
        f.write(svg_plot)
    
    print("Generating Profile Plan SVG...")
    profile_plan = ProfilePlan(
        title="Longitudinal Profile",
        points=[
            ProfilePoint(station=0, ground_z=100.0, design_z=101.0),
            ProfilePoint(station=50, ground_z=102.5, design_z=101.5),
            ProfilePoint(station=100, ground_z=98.0, design_z=102.0),
        ],
    )
    svg_profile = render_profile_plan(profile_plan, output_format="svg")
    with open("output/profile_plan.svg", "wb") as f:
        f.write(svg_profile)

    print("Generating Interior Plan SVG...")
    interior_plan = InteriorPlan(
        title="Apartment Interior",
        walls=[
            Wall(start_pt=Point(x=0, y=0), end_pt=Point(x=6, y=0), thickness=0.3,
                 openings=[Opening(type="door", start_distance=2.0, width=0.9)]),
            Wall(start_pt=Point(x=6, y=0), end_pt=Point(x=6, y=5), thickness=0.3),
            Wall(start_pt=Point(x=6, y=5), end_pt=Point(x=0, y=5), thickness=0.3,
                 openings=[Opening(type="window", start_distance=2.0, width=2.0)]),
            Wall(start_pt=Point(x=0, y=5), end_pt=Point(x=0, y=0), thickness=0.3),
        ],
        rooms=[Room(name="Living Room", number="1", points=[
            Point(x=0.5, y=0.5), Point(x=5.5, y=4.5)
        ])],
        furniture=[
            FurnitureItem(type="bed", center_pt=Point(x=1.5, y=3.5), width=1.6, length=2.0),
            FurnitureItem(type="wc", center_pt=Point(x=5, y=1), width=0.5, length=0.7),
        ],
    )
    svg_interior = render_interior_plan(interior_plan, output_format="svg")
    with open("output/interior_plan.svg", "wb") as f:
        f.write(svg_interior)

    print("Generating Pipeline Schematic SVG...")
    schematic_plan = PipelineSchematic(
        title="Heating System Schematic",
        pipes=[
            PipeSegment(start_pt=Point(x=3, y=9.5), end_pt=Point(x=8, y=9.5),
                        medium=PipeMedium.HEATING_SUPPLY, nominal_diameter=32),
            PipeSegment(start_pt=Point(x=3, y=4.5), end_pt=Point(x=8, y=4.5),
                        medium=PipeMedium.HEATING_RETURN, nominal_diameter=32),
        ],
        equipment=[
            EquipmentSymbol(center_pt=Point(x=2, y=7), equipment_type=EquipmentType.BOILER,
                            tag="B1", label="Coal Boiler", width=2.0, height=3.0),
            EquipmentSymbol(center_pt=Point(x=6, y=4.5),
                            equipment_type=EquipmentType.CIRCULATION_PUMP,
                            tag="PU1", label="Pump", width=0.8, height=0.8),
        ],
        valves=[
            ValveSymbol(center_pt=Point(x=4, y=9.5), valve_type=ValveType.BALL, tag="V1"),
        ]
    )
    svg_schematic = render_pipeline_schematic(schematic_plan, output_format="svg")
    with open("output/pipeline_schematic.svg", "wb") as f:
        f.write(svg_schematic)

    print("SVG generation complete. Check the 'output/' directory.")

if __name__ == "__main__":
    main()
