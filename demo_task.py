import json
from theodolite_mcp.infrastructure.mcp_server import mcp, convert_dms_to_decimal, process_traverse, calculate_azimuth
import asyncio

async def run_demo():
    print("🏗 Site Planning Demonstration Task")
    print("=" * 40)
    
    # 1. Convert DMS measurements to decimal
    # Observations:
    # AB: 95°20'30"
    # BC: 87°10'20"
    # CD: 92°15'10"
    # DA: 85°14'00"
    
    angles_dms = [
        (95, 20, 30),
        (87, 10, 20),
        (92, 15, 10),
        (85, 14, 0)
    ]
    
    decimal_angles = [convert_dms_to_decimal(*dms) for dms in angles_dms]
    
    observations = [
        {"point_name": "B", "horizontal_angle": decimal_angles[0], "distance": 100.00},
        {"point_name": "C", "horizontal_angle": decimal_angles[1], "distance": 120.00},
        {"point_name": "D", "horizontal_angle": decimal_angles[2], "distance": 90.00},
        {"point_name": "A_back", "horizontal_angle": decimal_angles[3], "distance": 110.00},
    ]
    
    print(f"1. Converted {len(decimal_angles)} observations to decimal.")
    
    # 2. Process Traverse
    result = process_traverse(
        start_x=1000.0,
        start_y=1000.0,
        start_name="A",
        start_azimuth=45.0, # 45°00'00"
        observations_json=observations,
        is_closed=True
    )
    
    print("\n2. Traverse Adjustment Results:")
    print(f"   - Angular Misclosure: {result['angular_misclosure']:.4f}°")
    print(f"   - Linear Misclosure: {result['linear_misclosure']:.4f} m")
    print(f"   - Relative Precision: 1:{int(1/result['relative_precision']) if result['relative_precision'] > 0 else 0}")
    print(f"   - Status: {result['precision_status']}")
    print(f"   - Total Length: {result['total_length']:.2f} m")
    print(f"   - Calculated Area: {result['area']:.2f} m²")
    
    print("\n3. Adjusted Coordinates:")
    for pt in result['points']:
        print(f"   Point {pt['name']}: X={pt['x']:.3f}, Y={pt['y']:.3f}")
        
    # 4. Building Axis Orientation
    # Calculate azimuth between A and C for building alignment
    pA = result['points'][0]
    pC = result['points'][2]
    az_AC = calculate_azimuth(pA['x'], pA['y'], pC['x'], pC['y'])
    
    print(f"\n4. Building Axis Orientation:")
    print(f"   - Azimuth A -> C: {az_AC:.4f}°")
    
    print("\n" + "=" * 40)
    print("✅ Demo Task Completed Successfully")

if __name__ == "__main__":
    asyncio.run(run_demo())
