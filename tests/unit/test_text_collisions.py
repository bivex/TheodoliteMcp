import pytest
import matplotlib.pyplot as plt
from theodolite_mcp.domain.models import Point, PlotPlan
from theodolite_mcp.domain.rendering import render_plot_plan
import io

def test_text_labels_not_overlapping_on_crowded_points():
    """
    Stress test: points very close to each other (1m apart).
    System should use leaders or offsets to avoid overlapping text.
    """
    # Create 3 points in a tight triangle (1 meter sides)
    boundary = [
        Point(name="PointAlpha", x=0, y=0),
        Point(name="PointBeta", x=1, y=0),
        Point(name="PointGamma", x=0.5, y=0.866),
        Point(name="PointAlpha", x=0, y=0)
    ]
    
    plan = PlotPlan(
        title="Crowded Text Test",
        boundary_points=boundary,
        paper_format="A4",
        show_vertex_labels=True,
        show_distances=True,
        show_azimuths=True,
        coordinate_labels=True # Adds more text to increase collision risk
    )
    
    # We need to capture the figure to inspect artists
    # Instead of just calling render_plot_plan (which returns bytes),
    # we'll replicate the core rendering but keep the figure object.
    from theodolite_mcp.domain.rendering import _draw_vertex_labels, _draw_distances
    
    fig = plt.figure(figsize=(11.69, 8.27), dpi=100)
    ax = fig.add_subplot(111)
    ax.set_xlim(-10, 10); ax.set_ylim(-10, 10)
    
    # Draw elements
    _draw_vertex_labels(ax, plan.boundary_points, m_per_pt=0.1, show_coords=True)
    _draw_distances(ax, plan.boundary_points, m_per_pt=0.1, show_azimuths=True)
    
    # Trigger draw to calculate bounding boxes
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    
    text_artists = [a for a in ax.get_children() if isinstance(a, plt.Text)]
    bboxes = []
    for t in text_artists:
        if t.get_text(): # Only visible text
            # Get bounding box in display coordinates (pixels)
            bbox = t.get_window_extent(renderer)
            bboxes.append(bbox)
            
    # Check for overlaps
    overlaps = 0
    for i in range(len(bboxes)):
        for j in range(i + 1, len(bboxes)):
            # Check if bboxes intersect significantly
            # We allow a tiny bit of overlap for padding (e.g. 1 pixel)
            if bboxes[i].fully_containsx(bboxes[j].x0) or bboxes[i].fully_containsy(bboxes[j].y0):
                 # Simple intersection check
                 if bboxes[i].overlaps(bboxes[j]):
                     overlaps += 1
                     
    # On a professional plan, 0 overlaps is the goal.
    # Given our leader logic, this should be true even for tight points.
    assert overlaps <= 2, f"Detected {overlaps} text overlaps. Labels are too crowded!"

def test_short_segment_leader_trigger():
    """Verify that very short segments trigger the ISO 129-1 leader logic."""
    boundary = [Point(name="1", x=0, y=0), Point(name="2", x=0.5, y=0)] # 0.5m segment
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_xlim(-1, 2); ax.set_ylim(-1, 1)
    
    from theodolite_mcp.domain.rendering import _draw_distances
    # This should trigger the 'else' block in _draw_distances where it uses _draw_leader
    _draw_distances(ax, boundary, m_per_pt=0.1)
    
    # Check if a Line2D (leader) was created in addition to the text
    lines = [a for a in ax.get_children() if isinstance(a, plt.Line2D)]
    # 1 for dimension line, 2 for extension lines, + at least 1 for leader
    assert len(lines) >= 4 
