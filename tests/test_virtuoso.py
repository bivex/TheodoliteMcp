import os
from theodolite_mcp.domain.least_squares import ObservationLS, adjust_network_2d
from theodolite_mcp.domain.geodesy import WGS84, geodetic_to_ecef

def test_virtuoso_capabilities():
    print("🚀 Testing Virtuoso Features...")

    # 1. Test Least Squares (Simple distance network)
    # Target: Triangle with known fixed base
    # P1 (0,0) Fixed, P2 (10,0) Fixed. P3 approx (5, 8)
    initial = {
        "P1": {"x": 0.0, "y": 0.0},
        "P2": {"x": 10.0, "y": 0.0},
        "P3": {"x": 5.0, "y": 7.5} # Rough guess
    }
    
    obs = [
        ObservationLS(from_pt="P1", to_pt="P1", value=0, std_dev=0.001, type="fixed_x"),
        ObservationLS(from_pt="P1", to_pt="P1", value=0, std_dev=0.001, type="fixed_y"),
        ObservationLS(from_pt="P2", to_pt="P2", value=10, std_dev=0.001, type="fixed_x"),
        ObservationLS(from_pt="P2", to_pt="P2", value=0, std_dev=0.001, type="fixed_y"),
        # Distances to free point P3
        ObservationLS(from_pt="P1", to_pt="P3", value=9.434, std_dev=0.01, type="distance"),
        ObservationLS(from_pt="P2", to_pt="P3", value=9.434, std_dev=0.01, type="distance"),
    ]
    
    res = adjust_network_2d(obs, initial)
    print(f"✅ LSA Adjusted P3: {res.adjusted_coordinates['P3']}")
    print(f"✅ LSA Sigma: {res.unit_weight_variance:.4f}")

    # 2. Test Geodesy (WGS84 to ECEF)
    # Kyiv approximate
    lat, lon, h = 50.45, 30.52, 180.0
    x, y, z = geodetic_to_ecef(lat, lon, h, WGS84)
    print(f"✅ Geodetic to ECEF: {x:.2f}, {y:.2f}, {z:.2f}")

if __name__ == "__main__":
    test_virtuoso_capabilities()
