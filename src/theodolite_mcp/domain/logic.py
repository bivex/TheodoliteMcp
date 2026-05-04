import math
from typing import List
from .models import TraverseData, TraverseResult, Point, Observation, StadiaMeasurement, StadiaResult

def normalize_angle(angle: float) -> float:
    return angle % 360

def dms_to_decimal(degrees: int, minutes: int, seconds: float) -> float:
    sign = 1 if degrees >= 0 else -1
    return degrees + sign * (minutes / 60 + seconds / 3600)

def decimal_to_dms(decimal: float):
    sign = 1 if decimal >= 0 else -1
    abs_decimal = abs(decimal)
    degrees = int(abs_decimal)
    minutes = int((abs_decimal - degrees) * 60)
    seconds = (abs_decimal - degrees - minutes / 60) * 3600
    return sign * degrees, minutes, seconds

def calculate_azimuth_from_points(p1: Point, p2: Point) -> float:
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    if abs(dx) < 1e-10 and abs(dy) < 1e-10:
        raise ValueError("Points are identical; azimuth is undefined.")
    # atan2(y, x) gives angle from X-axis towards Y-axis.
    # In surveying, X is often North and Azimuth is clockwise from North.
    # So we use atan2(dy, dx) where dx is North difference and dy is East difference.
    azimuth = math.degrees(math.atan2(dy, dx))
    return normalize_angle(azimuth)

def calculate_area(points: List[Point]) -> float:
    """Calculates area using the Shoelace formula (Gauss area formula)."""
    if len(points) < 3:
        return 0.0
    
    # Area = 0.5 * |sum(Xi * Yi+1 - Xi+1 * Yi)|
    area = 0.0
    n = len(points)
    for i in range(n):
        j = (i + 1) % n
        area += (points[i].x * points[j].y)
        area -= (points[j].x * points[i].y)
    return abs(area) / 2.0

def evaluate_precision(relative_error: float) -> str:
    if relative_error <= 0:
        return "Perfect (Theoretical)"
    inv_error = 1.0 / relative_error
    if inv_error >= 5000:
        return f"Excellent (1:{int(inv_error)})"
    elif inv_error >= 2000:
        return f"Satisfactory (1:{int(inv_error)})"
    else:
        return f"Unacceptable (1:{int(inv_error)}) - Re-measurement recommended"

def calculate_stadia(m: StadiaMeasurement) -> StadiaResult:
    """Performs tacheometric (stadia) reduction."""
    s = abs(m.top_hair - m.bottom_hair)
    v_rad = math.radians(m.vertical_angle)
    
    # Horizontal Distance = (K*S + C) * cos^2(V)
    ks_c = m.constant_k * s + m.constant_c
    hd = ks_c * (math.cos(v_rad) ** 2)
    
    # Vertical Distance = 0.5 * (K*S + C) * sin(2V)
    vd = 0.5 * ks_c * math.sin(2 * v_rad)
    
    # Elevation Difference = VD + HI - HT
    elevation_diff = vd + m.instrument_height - m.target_height
    
    return StadiaResult(
        horizontal_distance=round(hd, 3),
        vertical_distance=round(vd, 3),
        elevation_diff=round(elevation_diff, 3)
    )

def calculate_inverse(p1: Point, p2: Point) -> dict:
    """Calculates azimuth and horizontal distance between two points."""
    dx = p2.x - p1.x
    dy = p2.y - p1.y
    dist = math.sqrt(dx**2 + dy**2)
    az = calculate_azimuth_from_points(p1, p2)
    
    res = {"azimuth": round(az, 4), "distance": round(dist, 3)}
    if p1.z is not None and p2.z is not None:
        res["dz"] = round(p2.z - p1.z, 3)
        res["slope_distance"] = round(math.sqrt(dist**2 + (p2.z - p1.z)**2), 3)
        res["grade_percent"] = round((p2.z - p1.z) / dist * 100, 2) if dist > 0 else 0
    return res

def generate_markdown_report(result: TraverseResult) -> str:
    """Generates a professional survey report in Markdown."""
    lines = [
        "# Theodolite Survey Processing Report",
        f"**Status:** {result.precision_status}",
        "",
        "## Summary",
        f"- **Total Length:** {result.total_length:.3f} m",
        f"- **Angular Misclosure:** {result.angular_misclosure:.4f}°",
        f"- **Linear Misclosure:** {result.linear_misclosure:.4f} m",
        f"- **Relative Precision:** 1:{int(1/result.relative_precision) if result.relative_precision > 0 else 0}",
    ]
    
    if result.area:
        lines.append(f"- **Calculated Area:** {result.area:.2f} m²")
        
    lines.extend([
        "",
        "## Adjusted Coordinates",
        "| Point | X (North) | Y (East) | Z (Elev) |",
        "| :--- | :--- | :--- | :--- |"
    ])
    
    for pt in result.points:
        z_str = f"{pt.z:.3f}" if pt.z is not None else "-"
        lines.append(f"| {pt.name} | {pt.x:.3f} | {pt.y:.3f} | {z_str} |")
        
    return "\n".join(lines)

def calculate_traverse(data: TraverseData) -> TraverseResult:
    n = len(data.observations)
    if n < 1:
        raise ValueError("At least one observation is required.")

    for obs in data.observations:
        if obs.distance < 0:
            raise ValueError(f"Distance to {obs.point_name} cannot be negative.")

    total_dist = sum(obs.distance for obs in data.observations)
    
    # 1. Angular adjustment (if closed)
    # For a closed loop, the sum of internal angles is (n-2)*180
    # Actually, in a traverse, we measure n angles if we close back to start.
    # Let's assume the user provides the "closing" angle as well if it's closed.
    
    # For simplicity, if is_closed is True, we assume observations are angles at stations 1..n
    # and the last observation closes back to station 1.
    
    angles = [obs.horizontal_angle for obs in data.observations]
    
    angular_misclosure = 0.0
    if data.is_closed:
        theoretical_sum = (n - 2) * 180 # Interior angles
        # If they are exterior angles, it's (n+2)*180
        # For a traverse, it's often more complex.
        # Let's assume interior for now.
        actual_sum = sum(angles)
        angular_misclosure = actual_sum - theoretical_sum
        
        # Adjust angles
        correction = -angular_misclosure / n
        angles = [a + correction for a in angles]

    # 2. Calculate Azimuths
    azimuths = []
    current_azimuth = data.start_azimuth
    for angle in angles:
        # Alpha_next = Alpha_prev + Beta - 180
        current_azimuth = normalize_angle(current_azimuth + angle - 180)
        azimuths.append(current_azimuth)

    # 3. Calculate Increments
    dxs = []
    dys = []
    for i, obs in enumerate(data.observations):
        dx = obs.distance * math.cos(math.radians(azimuths[i]))
        dy = obs.distance * math.sin(math.radians(azimuths[i]))
        dxs.append(dx)
        dys.append(dy)

    # 4. Linear Misclosure
    sum_dx = sum(dxs)
    sum_dy = sum(dys)
    
    linear_misclosure_x = 0.0
    linear_misclosure_y = 0.0
    
    if data.is_closed:
        linear_misclosure_x = sum_dx
        linear_misclosure_y = sum_dy
    elif data.end_point and data.end_point.x is not None and data.end_point.y is not None:
        linear_misclosure_x = sum_dx - (data.end_point.x - data.start_point.x)
        linear_misclosure_y = sum_dy - (data.end_point.y - data.start_point.y)

    linear_misclosure = math.sqrt(linear_misclosure_x**2 + linear_misclosure_y**2)
    relative_precision = linear_misclosure / total_dist if total_dist > 0 else 0.0

    # 5. Adjust Increments (Compass Rule)
    if total_dist > 0:
        for i in range(n):
            dxs[i] -= (linear_misclosure_x * data.observations[i].distance) / total_dist
            dys[i] -= (linear_misclosure_y * data.observations[i].distance) / total_dist

    # 6. Final Coordinates
    points = [data.start_point]
    curr_x = data.start_point.x
    curr_y = data.start_point.y
    for i in range(n):
        curr_x += dxs[i]
        curr_y += dys[i]
        points.append(Point(name=data.observations[i].point_name, x=curr_x, y=curr_y))

    # 7. Area Calculation (if closed)
    area = None
    if data.is_closed:
        # For area, we exclude the duplicated closing point if it exists
        unique_points = points[:-1] if len(points) > 1 else points
        area = calculate_area(unique_points)

    # 8. Precision Evaluation
    status = evaluate_precision(relative_precision)

    return TraverseResult(
        points=points,
        angular_misclosure=angular_misclosure,
        linear_misclosure=linear_misclosure,
        relative_precision=relative_precision,
        total_length=total_dist,
        area=area,
        precision_status=status
    )
