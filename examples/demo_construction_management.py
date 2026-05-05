import os
from theodolite_mcp.domain.models import Point, Zone, PlotPlan, AsBuiltPoint, VolumeGrid, GridCell
from theodolite_mcp.domain.rendering import render_plot_plan

def create_construction_management_demo():
    print("🚧 Generating Construction Management Demos (As-Built & Cartogram)...")

    # --- PART 1: AS-BUILT SURVEY (Column Layout) ---
    # Imagine we are checking 4 concrete columns
    as_built_data = [
        # Column 1: Shifted 12mm Left, 5mm Up
        AsBuiltPoint(name="Col-1", design_x=10.0, design_y=10.0, actual_x=9.988, actual_y=10.005, design_z=100.0, actual_z=100.002),
        # Column 2: Shifted 18mm Right, 10mm Down
        AsBuiltPoint(name="Col-2", design_x=20.0, design_y=10.0, actual_x=20.018, actual_y=9.990, design_z=100.0, actual_z=99.995),
        # Column 3: Perfect XY, but 15mm too low
        AsBuiltPoint(name="Col-3", design_x=20.0, design_y=20.0, actual_x=20.0, actual_y=20.0, design_z=100.0, actual_z=99.985),
        # Column 4: Large deviation (out of tolerance)
        AsBuiltPoint(name="Col-4", design_x=10.0, design_y=20.0, actual_x=10.045, actual_y=19.965, design_z=100.0, actual_z=100.012),
    ]

    # --- PART 2: EARTHWORK CARTOGRAM (Excavation) ---
    # Small 2x2 grid for demonstration
    cells = [
        GridCell(center_x=30.0, center_y=10.0, size_m=5.0, design_z=98.5, actual_z=100.2, volume=42.5), # Fill
        GridCell(center_x=35.0, center_y=10.0, size_m=5.0, design_z=98.5, actual_z=100.5, volume=50.0), # Fill
        GridCell(center_x=30.0, center_y=15.0, size_m=5.0, design_z=98.5, actual_z=97.8, volume=-17.5), # Cut
        GridCell(center_x=35.0, center_y=15.0, size_m=5.0, design_z=98.5, actual_z=98.0, volume=-12.5), # Cut
    ]
    volume_grid = VolumeGrid(
        title="Foundation Pit Excavation",
        cells=cells,
        total_cut=30.0,
        total_fill=92.5,
        net_volume=62.5
    )

    # 3. Create PlotPlan
    plan = PlotPlan(
        title="CONSTRUCTION AS-BUILT & VOLUME REPORT",
        project_number="BUILD-2026-X",
        organization="Advanced Construction Ltd",
        boundary_points=[Point(name="B1", x=5, y=5), Point(name="B2", x=45, y=5), 
                         Point(name="B3", x=45, y=25), Point(name="B4", x=5, y=25)],
        as_built_points=as_built_data,
        volume_grid=volume_grid,
        language="en",
        paper_format="A3",
        orientation="landscape",
        dpi=300
    )

    # 4. Render and Save
    png_bytes = render_plot_plan(plan)
    output_path = os.path.join("output", "construction_management_report.png")
    
    os.makedirs("output", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(png_bytes)

    print(f"✅ Management report generated: {output_path}")

if __name__ == "__main__":
    create_construction_management_demo()
