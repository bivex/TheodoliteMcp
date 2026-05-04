import math
from typing import List
from .models import TraverseData, TraverseResult, Point, Observation

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

    return TraverseResult(
        points=points,
        angular_misclosure=angular_misclosure,
        linear_misclosure=linear_misclosure,
        relative_precision=relative_precision,
        total_length=total_dist
    )
