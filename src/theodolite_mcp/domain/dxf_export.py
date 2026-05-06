import ezdxf
from theodolite_mcp.domain.models import PlotPlan, Point, Zone, ProfilePlan
import os

def export_plan_to_dxf(plan: PlotPlan, output_path: str):
    """
    Exports a PlotPlan to a DXF file with standardized layers.
    """
    doc = ezdxf.new('R2010') # Use DXF R2010 version
    msp = doc.modelspace()

    # 1. Setup Layers
    doc.layers.add(name="0_BOUNDARY", color=7) # White/Black
    doc.layers.add(name="0_POINTS", color=1)   # Red
    doc.layers.add(name="0_TEXT", color=7)
    doc.layers.add(name="ZONE_BUILDINGS", color=4) # Blue
    doc.layers.add(name="ZONE_WATER", color=5)     # Cyan
    doc.layers.add(name="ZONE_GREEN", color=3)     # Green
    doc.layers.add(name="ZONE_OTHER", color=8)     # Dark Gray

    # 2. Draw Boundary
    if plan.boundary_points:
        points = [(p.x, p.y) for p in plan.boundary_points]
        # Ensure it's closed for polyline if first and last match
        msp.add_lwpolyline(points, close=True, dxfattribs={'layer': '0_BOUNDARY'})

    # 3. Draw Points as Blocks/Points
    for p in plan.boundary_points:
        msp.add_point((p.x, p.y), dxfattribs={'layer': '0_POINTS'})
        if plan.show_vertex_labels:
            label = p.name
            if plan.coordinate_labels:
                label += f" (X:{p.x:.2f}, Y:{p.y:.2f})"
            msp.add_text(label, dxfattribs={'layer': '0_TEXT', 'height': 0.5}).set_placement((p.x + 0.5, p.y + 0.5))

    # 4. Draw Zones
    for zone in plan.zones:
        name_l = zone.name.lower()
        layer = "ZONE_OTHER"
        if any(k in name_l for k in ['дом', 'house', 'building', 'здание']): layer = "ZONE_BUILDINGS"
        elif any(k in name_l for k in ['вода', 'water', 'lake', 'stream']): layer = "ZONE_WATER"
        elif any(k in name_l for k in ['сад', 'trees', 'park', 'grass']): layer = "ZONE_GREEN"
        
        if zone.points:
            z_points = [(pt.x, pt.y) for pt in zone.points]
            msp.add_lwpolyline(z_points, close=True, dxfattribs={'layer': layer})
            
            # Label zone center
            cx = sum(pt.x for pt in zone.points) / len(zone.points)
            cy = sum(pt.y for pt in zone.points) / len(zone.points)
            msp.add_text(zone.name, dxfattribs={'layer': '0_TEXT', 'height': 0.7}).set_placement((cx, cy))

    # 5. Save
    doc.saveas(output_path)
    return output_path

def export_profile_to_dxf(plan: ProfilePlan, output_path: str):
    """
    Exports a Longitudinal Profile to a DXF file.
    Includes the 'podval' table and profile lines.
    """
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # 1. Layers
    doc.layers.add(name="V-PROF-GROUND", color=7)
    doc.layers.add(name="V-PROF-DESIGN", color=1) # Red
    doc.layers.add(name="V-PROF-TABLE", color=7)
    doc.layers.add(name="V-PROF-TEXT", color=7)
    doc.layers.add(name="V-PROF-ORDINATES", color=8) # Gray
    
    # Scales
    h_scale = plan.horiz_scale
    v_scale = plan.vert_scale
    exaggeration = h_scale / v_scale
    
    # 2. Draw Lines
    points = plan.points
    ground_pts = [(p.station, p.ground_z * exaggeration) for p in points]
    msp.add_lwpolyline(ground_pts, dxfattribs={'layer': 'V-PROF-GROUND'})
    
    design_pts = [(p.station, p.design_z * exaggeration) for p in points if p.design_z is not None]
    if design_pts:
        msp.add_lwpolyline(design_pts, dxfattribs={'layer': 'V-PROF-DESIGN'})
        
    # 3. Draw Ordinates and Table (Simplified logic for CAD)
    y_table_top = (min(p.ground_z for p in points) - 10) * exaggeration
    
    for p in points:
        # Ordinate line
        msp.add_line((p.station, p.ground_z * exaggeration), (p.station, y_table_top), 
                     dxfattribs={'layer': 'V-PROF-ORDINATES'})
        
        # Table labels (Vertical)
        msp.add_text(f"{p.ground_z:.2f}", dxfattribs={'layer': 'V-PROF-TEXT', 'height': 0.5, 'rotation': 90}).set_placement((p.station + 0.2, y_table_top - 5))
        if p.design_z is not None:
             msp.add_text(f"{p.design_z:.2f}", dxfattribs={'layer': 'V-PROF-TEXT', 'height': 0.5, 'rotation': 90, 'color': 1}).set_placement((p.station + 0.8, y_table_top - 5))
             
    # Table borders
    table_bottom = y_table_top - 15
    msp.add_line((points[0].station, y_table_top), (points[-1].station, y_table_top), dxfattribs={'layer': 'V-PROF-TABLE'})
    msp.add_line((points[0].station, table_bottom), (points[-1].station, table_bottom), dxfattribs={'layer': 'V-PROF-TABLE'})
    
    doc.saveas(output_path)
    return output_path
