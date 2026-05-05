import os
from theodolite_mcp.domain.models import Point, Zone, PlotPlan
from theodolite_mcp.domain.rendering import render_plot_plan

def test_multilang():
    print("🌍 Testing Global Localization (German/Deutsch)...")
    boundary = [Point(name="1", x=0, y=0), Point(name="2", x=50, y=0), 
                Point(name="3", x=50, y=50), Point(name="4", x=0, y=50)]
    
    plan = PlotPlan(
        title="International Site Layout",
        project_number="INT-DE-2026",
        organization="Global Engineering GmbH",
        boundary_points=boundary,
        zones=[],
        language="de", # Test German
        paper_format="A4",
        orientation="landscape"
    )

    png_bytes = render_plot_plan(plan)
    with open("test_german_plan.png", "wb") as f:
        f.write(png_bytes)
    print("✅ German plan generated: test_german_plan.png")

if __name__ == "__main__":
    test_multilang()
