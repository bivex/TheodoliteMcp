import math
from typing import List
from theodolite_mcp.domain.models import (
    TraverseData,
    TraverseResult,
    Point,
    Observation,
    StadiaMeasurement,
    StadiaResult,
    EDMParameters,
)


def normalize_angle(angle: float) -> float:
    """Normalize angle to [0, 360) degrees."""
    result = angle % 360.0
    # Floating-point modulo can return exactly 360.0 for angles very close to 0
    # (e.g., from tiny negative values). Normalize that to 0.0.
    if result == 360.0:
        result = 0.0
    return result


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
    dx = p2.x - p1.x  # North difference
    dy = p2.y - p1.y  # East difference
    if abs(dx) < 1e-10 and abs(dy) < 1e-10:
        raise ValueError("Points are identical; azimuth is undefined.")
    # In surveying, X is often North and Azimuth is clockwise from North.
    # So we use atan2(East, North) -> atan2(dy, dx)
    azimuth = math.degrees(math.atan2(dy, dx))
    return normalize_angle(azimuth)


def calculate_area(points: List[Point]) -> float:
    """Calculates area using the Shoelace formula (Gauss area formula)."""
    if len(points) < 3:
        return 0.0
    area = 0.0
    n = len(points)
    for i in range(n):
        j = (i + 1) % n
        area += points[i].x * points[j].y
        area -= points[j].x * points[i].y
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
    ks_c = m.constant_k * s + m.constant_c
    hd = ks_c * (math.cos(v_rad) ** 2)
    vd = 0.5 * ks_c * math.sin(2 * v_rad)
    elevation_diff = vd + m.instrument_height - m.target_height
    return StadiaResult(
        horizontal_distance=round(hd, 3),
        vertical_distance=round(vd, 3),
        elevation_diff=round(elevation_diff, 3),
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
        res["slope_distance"] = round(math.sqrt(dist**2 + (p2.z - p1.z) ** 2), 3)
        res["grade_percent"] = round((p2.z - p1.z) / dist * 100, 2) if dist > 0 else 0
    return res


def generate_markdown_report(result: TraverseResult) -> str:
    """Generates a professional survey report in Markdown."""
    lines = [
        "# Geodetic Survey Analysis Report",
        f"**Status:** {result.precision_status}",
        "",
        "## Network Summary",
        f"- **Total Length:** {result.total_length:.3f} m",
        f"- **Angular Misclosure:** {result.angular_misclosure:.4f}°",
        f"- **Linear Misclosure:** {result.linear_misclosure:.4f} m",
        f"- **Relative Precision:** 1:{int(1 / result.relative_precision) if result.relative_precision > 0 else 0}",
    ]
    if result.area:
        lines.append(f"- **Calculated Parcel Area:** {result.area:.2f} m²")
    lines.extend(
        [
            "",
            "## Adjusted Coordinate List",
            "| Point | X (North) | Y (East) | Z (Elev) |",
            "| :--- | :--- | :--- | :--- |",
        ]
    )
    for pt in result.points:
        z_str = f"{pt.z:.3f}" if pt.z is not None else "-"
        lines.append(f"| {pt.name} | {pt.x:.3f} | {pt.y:.3f} | {z_str} |")
    return "\n".join(lines)


def calculate_ppm_correction(p: EDMParameters) -> float:
    ppm = p.frequency_const - (0.29525 * p.pressure_hpa) / (
        1 + p.temperature_c / 273.15
    )
    return ppm


def apply_combined_factor(
    distance: float, elevation: float, grid_factor: float
) -> float:
    R = 6371000.0
    sea_level_factor = R / (R + elevation)
    combined_factor = sea_level_factor * grid_factor
    return distance * combined_factor


def _calculate_angular_misclosure(
    data: TraverseData, n_traverse: int, angles: List[float]
) -> float:
    if data.is_closed:
        actual_sum = sum(angles)
        theoretical_int = (n_traverse - 2) * 180
        theoretical_ext = (n_traverse + 2) * 180
        mis_int = actual_sum - theoretical_int
        mis_ext = actual_sum - theoretical_ext
        return mis_int if abs(mis_int) < abs(mis_ext) else mis_ext

    if data.closing_azimuth is not None:
        calc_closing = normalize_angle(
            data.start_azimuth + sum(angles) - n_traverse * 180
        )
        mis = calc_closing - data.closing_azimuth
        if mis > 180:
            mis -= 360
        if mis < -180:
            mis += 360
        return mis

    return 0.0


def _calculate_azimuths(start_az: float, adj_angles: List[float]) -> List[float]:
    azimuths = []
    current_az = start_az
    for angle in adj_angles:
        current_az = normalize_angle(current_az + angle - 180)
        azimuths.append(current_az)
    return azimuths


def calculate_traverse(data: TraverseData) -> TraverseResult:
    traverse_obs = [o for o in data.observations if not o.is_sideshot]
    n_traverse = len(traverse_obs)
    if n_traverse < 1:
        raise ValueError("At least one main traverse observation is required.")

    # Apply distance corrections (Combined Scale Factor)
    for obs in traverse_obs:
        obs.distance = apply_combined_factor(
            obs.distance, data.average_elevation, data.grid_scale_factor
        )

    total_dist = sum(obs.distance for obs in traverse_obs)

    # 1. Angular adjustment
    angles = [obs.horizontal_angle for obs in traverse_obs]
    angular_misclosure = _calculate_angular_misclosure(data, n_traverse, angles)

    correction = -angular_misclosure / n_traverse
    adj_angles = [a + correction for a in angles]

    # 2. Calculate Azimuths for main traverse
    azimuths = _calculate_azimuths(data.start_azimuth, adj_angles)

    # 3. Calculate Increments for main traverse
    # Surveying convention: North = 0 deg (X axis), East = 90 deg (Y axis)
    # dx (North) = dist * cos(az), dy (East) = dist * sin(az)
    dxs = [
        obs.distance * math.cos(math.radians(az))
        for obs, az in zip(traverse_obs, azimuths)
    ]
    dys = [
        obs.distance * math.sin(math.radians(az))
        for obs, az in zip(traverse_obs, azimuths)
    ]

    # 4. Linear Misclosure
    sum_dx, sum_dy = sum(dxs), sum(dys)
    mis_x, mis_y = 0.0, 0.0
    if data.is_closed:
        mis_x, mis_y = sum_dx, sum_dy
    elif data.end_point and data.end_point.x is not None:
        mis_x = sum_dx - (data.end_point.x - data.start_point.x)
        mis_y = sum_dy - (data.end_point.y - data.start_point.y)

    linear_misclosure = math.sqrt(mis_x**2 + mis_y**2)
    relative_precision = linear_misclosure / total_dist if total_dist > 0 else 0.0

    # 5. Compass Rule Adjustment
    if total_dist > 0:
        for i in range(n_traverse):
            dxs[i] -= (mis_x * traverse_obs[i].distance) / total_dist
            dys[i] -= (mis_y * traverse_obs[i].distance) / total_dist

    # 6. Final Coordinates (Main Traverse)
    points = [data.start_point]
    cx, cy = data.start_point.x, data.start_point.y
    for i in range(n_traverse):
        cx += dxs[i]
        cy += dys[i]
        points.append(Point(name=traverse_obs[i].point_name, x=cx, y=cy))

    # 8. Final Area & Status
    area = calculate_area(points[:-1] if data.is_closed else points)
    status = evaluate_precision(relative_precision)

    return TraverseResult(
        points=points,
        angular_misclosure=angular_misclosure,
        linear_misclosure=linear_misclosure,
        relative_precision=relative_precision,
        total_length=total_dist,
        area=area,
        precision_status=status,
    )
