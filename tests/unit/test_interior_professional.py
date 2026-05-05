import pytest
import matplotlib.pyplot as plt
from theodolite_mcp.domain.models import Point, Wall, Opening, Room, InteriorPlan, FurnitureItem
from theodolite_mcp.domain.rendering import render_interior_plan

def test_interior_plan_renders_all_entities():
    """Verify that walls, furniture, and rooms are all processed."""
    w1 = Wall(start_pt=Point(x=0, y=0), end_pt=Point(x=5, y=0), thickness=0.3)
    w2 = Wall(start_pt=Point(x=5, y=0), end_pt=Point(x=5, y=5), thickness=0.3,
              openings=[Opening(type="door", start_distance=1.0, width=0.8)])
    
    furniture = [FurnitureItem(type="bed", center_pt=Point(x=2, y=2), width=1.6, length=2.0)]
    
    rooms = [
        Room(name="Master Bed", number="101", points=[Point(x=0.5, y=0.5), Point(x=4.5, y=4.5)])
    ]
    
    plan = InteriorPlan(
        title="Test Professional Plan",
        walls=[w1, w2],
        furniture=furniture,
        rooms=rooms
    )
    
    png_bytes = render_interior_plan(plan)
    assert len(png_bytes) > 0
    assert png_bytes.startswith(b'\x89PNG')

def test_interior_label_presence():
    """Verify room labels and legends exist using the full rendering pipeline."""
    from theodolite_mcp.domain.rendering import render_interior_plan
    
    rooms = [Room(name="Office", number="A-1", points=[Point(x=0, y=0), Point(x=10, y=0), Point(x=10, y=10), Point(x=0, y=10)])]
    plan = InteriorPlan(title="Test Plan", walls=[], rooms=rooms, furniture=[], language="en")
    
    # Act
    # Re-import because we need to inspect the Figure created INSIDE render_interior_plan
    # But since render_interior_plan returns bytes, we'll patch Figure.savefig to inspect it
    import io
    from matplotlib.figure import Figure
    
    captured_fig = None
    original_savefig = Figure.savefig
    
    def mock_savefig(self, *args, **kwargs):
        nonlocal captured_fig
        captured_fig = self
        return original_savefig(self, *args, **kwargs)
        
    import matplotlib.figure
    matplotlib.figure.Figure.savefig = mock_savefig
    
    try:
        render_interior_plan(plan)
    finally:
        matplotlib.figure.Figure.savefig = original_savefig

    # Assertions on the captured figure
    all_texts = [t.get_text() for t in captured_fig.findobj(plt.Text)]
    
    # Check for room label (number and area)
    # The area for 10x10 is 100.00
    assert any("A-1" in txt for txt in all_texts), f"Room number not found in: {all_texts}"
    assert any("100.00" in txt for txt in all_texts), f"Area not found in: {all_texts}"
    
    # Check for legend title (EN: 'ZONE EXPLICATION')
    assert any("ZONE EXPLICATION" in txt.upper() for txt in all_texts), f"Legend title not found in: {all_texts}"

def test_wall_thickness_geometry():
    """Verify that walls with thickness don't cause singular transformations."""
    # This was a bug when scale was 0
    w = Wall(start_pt=Point(x=0, y=0), end_pt=Point(x=10, y=10), thickness=0.3)
    plan = InteriorPlan(walls=[w], scale=0)
    
    # Should not raise UserWarning/RuntimeError about singular transformation
    png_bytes = render_interior_plan(plan)
    assert len(png_bytes) > 0
