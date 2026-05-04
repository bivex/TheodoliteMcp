import json
from theodolite_mcp.domain.models import PlotPlan, Point, Zone
from theodolite_mcp.domain.rendering import render_plot_plan
import matplotlib.pyplot as plt

def test_rendering():
    boundary = [
        {"name": "1", "x": 0, "y": 0},
        {"name": "2", "x": 100, "y": 0},
        {"name": "3", "x": 100, "y": 100},
        {"name": "4", "x": 0, "y": 100},
    ]
    boundary_points = [Point(**p) for p in boundary]
    
    plan = PlotPlan(
        title="Test ISO 129-1 & 129-4 Plan",
        boundary_points=boundary_points,
        zones=[],
        standard="shipbuilding", # Test arrowheads
        show_azimuths=True,
        show_scale_bar=True
    )
    
    png_bytes = render_plot_plan(plan)
    with open("test_plan_iso.png", "wb") as f:
        f.write(png_bytes)
    print("Plan rendered to test_plan_iso.png")
    
    plan.standard = "construction" # Test ticks
    png_bytes = render_plot_plan(plan)
    with open("test_plan_iso_ticks.png", "wb") as f:
        f.write(png_bytes)
    print("Plan rendered to test_plan_iso_ticks.png")
    
    # Test leaders directly via internal function for demo
    from theodolite_mcp.domain.rendering import _draw_leader
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 50); ax.set_ylim(0, 50)
    _draw_leader(ax, 10, 10, "Point A (Boundary)", offset_x=10, offset_y=10, terminator="arrow", m_per_pt=0.05)
    _draw_leader(ax, 30, 30, "Zone 1 (Area)", offset_x=-10, offset_y=5, terminator="dot", m_per_pt=0.05)
    fig.savefig("test_iso_leaders.png")
    print("Leader test rendered to test_iso_leaders.png")

if __name__ == "__main__":
    test_rendering()
