import os
import math
from theodolite_mcp.domain.models import Point, Zone, PlotPlan
from theodolite_mcp.domain.rendering import render_plot_plan
from theodolite_mcp.domain.geodesy import WGS84, geodetic_to_ecef, gauss_kruger_forward, KRASOVSKY
from theodolite_mcp.domain.least_squares import ObservationLS, adjust_network_2d

def run_virtuoso_dam_project():
    print("🌊 Starting Virtuoso Dam Monitoring Project...")

    # --- PHASE 1: GEODETIC PROJECTION ---
    # We have two control points (GNSS measurements in Lat/Lon)
    # Location: Approximate outskirts of Kyiv (Central Meridian 30.0)
    cm = 30.0
    gnss_p1 = {"lat": 50.450000, "lon": 30.500000}
    gnss_p2 = {"lat": 50.450500, "lon": 30.500800}

    # Project to Local Gauss-Kruger (X, Y)
    x1, y1 = gauss_kruger_forward(gnss_p1["lat"], gnss_p1["lon"], 0.0, cm, ell=KRASOVSKY)
    x2, y2 = gauss_kruger_forward(gnss_p2["lat"], gnss_p2["lon"], 0.0, cm, ell=KRASOVSKY)

    print(f"📍 Control P1 (Local Grid): X={x1:.3f}, Y={y1:.3f}")
    print(f"📍 Control P2 (Local Grid): X={x2:.3f}, Y={y2:.3f}")

    # --- PHASE 2: LEAST SQUARES ADJUSTMENT ---
    # Monitoring network: 2 Control points (fixed), 3 Monitoring prisms on the dam
    # M1, M2, M3 are on the curved wall of the dam.
    
    # Rough initial guesses for monitoring points
    initial_coords = {
        "P1": {"x": x1, "y": y1},
        "P2": {"x": x2, "y": y2},
        "M1": {"x": x1 + 40, "y": y1 + 10},
        "M2": {"x": x1 + 60, "y": y1 + 30},
        "M3": {"x": x1 + 80, "y": y1 + 50}
    }

    # Field measurements (Distances and Azimuths with errors)
    # We add REDUNDANT measurements to use the LSA engine
    obs = [
        # Fixed points (Control)
        ObservationLS(from_pt="P1", to_pt="P1", value=x1, std_dev=0.001, type="fixed_x"),
        ObservationLS(from_pt="P1", to_pt="P1", value=y1, std_dev=0.001, type="fixed_y"),
        ObservationLS(from_pt="P2", to_pt="P2", value=x2, std_dev=0.001, type="fixed_x"),
        ObservationLS(from_pt="P2", to_pt="P2", value=y2, std_dev=0.001, type="fixed_y"),
        
        # Distance measurements from P1
        ObservationLS(from_pt="P1", to_pt="M1", value=42.512, std_dev=0.005, type="distance"),
        ObservationLS(from_pt="P1", to_pt="M2", value=65.234, std_dev=0.005, type="distance"),
        
        # Distance measurements from P2
        ObservationLS(from_pt="P2", to_pt="M2", value=35.120, std_dev=0.005, type="distance"),
        ObservationLS(from_pt="P2", to_pt="M3", value=58.450, std_dev=0.005, type="distance"),
        
        # Redundant cross-link between prisms (The "Virtuoso" part)
        ObservationLS(from_pt="M1", to_pt="M2", value=28.345, std_dev=0.003, type="distance"),
        ObservationLS(from_pt="M2", to_pt="M3", value=28.345, std_dev=0.003, type="distance"),
        
        # Azimuth orientation from Control P1
        ObservationLS(from_pt="P1", to_pt="P2", value=42.15, std_dev=0.0001, type="azimuth")
    ]

    lsa_res = adjust_network_2d(obs, initial_coords)
    adj = lsa_res.adjusted_coordinates
    print(f"✅ Network Adjusted in {lsa_res.iterations} iterations.")

    # --- PHASE 3: ISO RENDERING ---
    # Create final points for the plan
    final_points = [Point(name=k, x=v['x'], y=v['y']) for k, v in adj.items()]
    
    # Define Dam structure zone
    dam_structure = [
        Point(name="W1", x=adj["M1"]["x"]-5, y=adj["M1"]["y"]+10),
        Point(name="W2", x=adj["M2"]["x"]-5, y=adj["M2"]["y"]+10),
        Point(name="W3", x=adj["M3"]["x"]-5, y=adj["M3"]["y"]+10),
        Point(name="W4", x=adj["M3"]["x"]+5, y=adj["M3"]["y"]+15),
        Point(name="W5", x=adj["M1"]["x"]+5, y=adj["M1"]["y"]+15),
    ]

    zones = [
        Zone(name="Concrete Dam Wall", points=dam_structure, fill_color="#B0BEC5"),
        # Water reservoir
        Zone(name="Reservoir (Water)", 
             points=[Point(name="R1", x=adj["M1"]["x"]-50, y=adj["M1"]["y"]+20),
                     Point(name="R2", x=adj["M3"]["x"]+50, y=adj["M3"]["y"]+20),
                     Point(name="R3", x=adj["M3"]["x"]+50, y=adj["M3"]["y"]+80),
                     Point(name="R4", x=adj["M1"]["x"]-50, y=adj["M1"]["y"]+80)],
             fill_color="#E1F5FE")
    ]

    plan = PlotPlan(
        title="HIGH-PRECISION DAM MONITORING NETWORK",
        project_number="VIRT-DAM-2026",
        organization="Strategic Infrastructure Bureau",
        boundary_points=final_points, # Show adjusted network points
        zones=zones,
        language="en",
        standard="construction",
        paper_format="A3",
        orientation="landscape",
        show_vertex_labels=True,
        show_distances=True,
        show_azimuths=True,
        coordinate_labels=True,
        dpi=300
    )

    png_bytes = render_plot_plan(plan)
    output_path = os.path.join("output", "virtuoso_dam_monitoring.png")
    
    os.makedirs("output", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(png_bytes)

    print(f"🎨 Final ISO Plan generated: {output_path}")
    print("🏆 Project 'Virtuoso Dam' successfully completed.")

if __name__ == "__main__":
    run_virtuoso_dam_project()
