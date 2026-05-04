import json
from theodolite_mcp.domain.models import PlotPlan, Point, Zone
from theodolite_mcp.domain.rendering import render_plot_plan

def create_ship_demo():
    # Hull profile (simplified side view)
    hull = [
        {"name": "0", "x": 0, "y": 10},   # Stern Top
        {"name": "5", "x": 0, "y": 0},    # Stern Bottom
        {"name": "10", "x": 80, "y": 0},  # Bottom Mid
        {"name": "15", "x": 100, "y": 15},# Bow Top
        {"name": "20", "x": 50, "y": 15}, # Main Deck
        {"name": "25", "x": 0, "y": 10},  # Back to Stern
    ]
    boundary_points = [Point(**p) for p in hull]
    
    # Internal structures
    zones = [
        # A water-tight bulkhead (should use Railway line)
        Zone(
            name="Water-tight Bulkhead (FR40)",
            points=[Point(name="B1", x=40, y=0), Point(name="B2", x=40, y=12)],
            fill_color="#E3F2FD"
        ),
        # An engine room zone
        Zone(
            name="Engine Room",
            points=[Point(name="E1", x=10, y=0.5), Point(name="E2", x=35, y=0.5), 
                    Point(name="E3", x=35, y=5), Point(name="E4", x=10, y=5)],
            fill_color="#FCE4EC"
        ),
        # A deck level
        Zone(
            name="Lower Deck",
            points=[Point(name="D1", x=5, y=6), Point(name="D2", x=90, y=6)],
            fill_color=None # Just lines
        )
    ]
    
    plan = PlotPlan(
        title="Project: T-2026 'Seafarer' - General Arrangement",
        boundary_points=boundary_points,
        zones=zones,
        standard="shipbuilding",
        language="en",
        show_azimuths=False,
        show_scale_bar=True,
        width_inches=12,
        height_inches=8
    )
    
    png_bytes = render_plot_plan(plan)
    with open("shipbuilding_demo_plan.png", "wb") as f:
        f.write(png_bytes)
    print("🚢 Shipbuilding demo plan generated: shipbuilding_demo_plan.png")

if __name__ == "__main__":
    create_ship_demo()
