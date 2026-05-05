import os
import json
from theodolite_mcp.infrastructure.mcp_server import (
    mcp, dms_to_decimal_degrees, adjust_traverse_network, compute_forward_azimuth
)
import asyncio

async def run_demo():
    print("🏗 Survey Computation Engine - Site Planning Demo")
    print("=" * 45)
    
    # 1. Convert DMS measurements to decimal
    angles_dms = [(95, 20, 30), (87, 10, 20), (92, 15, 10), (85, 14, 0)]
    decimal_angles = [dms_to_decimal_degrees(*dms) for dms in angles_dms]
    
    observations = [
        {"point_name": "B", "horizontal_angle": decimal_angles[0], "distance": 100.00},
        {"point_name": "C", "horizontal_angle": decimal_angles[1], "distance": 120.00},
        {"point_name": "D", "horizontal_angle": decimal_angles[2], "distance": 90.00},
        {"point_name": "A_back", "horizontal_angle": decimal_angles[3], "distance": 110.00},
    ]
    
    # 2. Adjust Traverse Network
    result = adjust_traverse_network(
        start_x=1000.0,
        start_y=1000.0,
        start_name="A",
        start_azimuth=45.0,
        observations_json=observations,
        is_closed=True
    )
    
    print("\n[Analysis Report]")
    print(result["report_md"])
    
    # 3. Compute Building Orientation
    pA = result['points'][0]
    pC = result['points'][2]
    az_AC = compute_forward_azimuth(pA['x'], pA['y'], pC['x'], pC['y'])
    
    print(f"\n[Layout Data]")
    print(f"- Construction Axis Azimuth (A->C): {az_AC:.4f}°")
    
    print("\n" + "=" * 45)
    print("✅ Professional Engineering Task Completed")

if __name__ == "__main__":
    asyncio.run(run_demo())
