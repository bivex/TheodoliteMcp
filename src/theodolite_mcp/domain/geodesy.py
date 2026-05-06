import math
import numpy as np
from typing import Tuple, NamedTuple


class Ellipsoid(NamedTuple):
    a: float  # Semi-major axis
    f_inv: float  # Inverse flattening

    @property
    def b(self) -> float:
        return self.a * (1 - 1 / self.f_inv)

    @property
    def e2(self) -> float:
        """First eccentricity squared."""
        return (self.a**2 - self.b**2) / self.a**2

    @property
    def ep2(self) -> float:
        """Second eccentricity squared."""
        return (self.a**2 - self.b**2) / self.b**2


# Standard Ellipsoids
WGS84 = Ellipsoid(6378137.0, 298.257223563)
KRASOVSKY = Ellipsoid(6378245.0, 298.3)


def helmert_transform(
    x: float,
    y: float,
    z: float,
    dx: float,
    dy: float,
    dz: float,
    rx_sec: float,
    ry_sec: float,
    rz_sec: float,
    s_ppm: float,
) -> Tuple[float, float, float]:
    """
    7-parameter Helmert Transformation.
    rx, ry, rz are in arc-seconds. s is in PPM.
    """
    # Convert arc-seconds to radians
    rx = math.radians(rx_sec / 3600.0)
    ry = math.radians(ry_sec / 3600.0)
    rz = math.radians(rz_sec / 3600.0)

    # Scale factor
    m = 1.0 + (s_ppm / 1e6)

    # Rotation matrix (small angle approximation)
    # R = [ 1  rz -ry
    #      -rz  1  rx
    #       ry -rx  1 ]

    vec = np.array([x, y, z])
    rot = np.array([[1.0, rz, -ry], [-rz, 1.0, rx], [ry, -rx, 1.0]])

    trans = np.array([dx, dy, dz])

    res = trans + m * np.dot(rot, vec)
    return tuple(res)


def geodetic_to_ecef(
    lat: float, lon: float, h: float, ell: Ellipsoid = WGS84
) -> Tuple[float, float, float]:
    """Lat/Lon (decimal degrees) to ECEF XYZ."""
    phi = math.radians(lat)
    lam = math.radians(lon)

    n = ell.a / math.sqrt(1 - ell.e2 * math.sin(phi) ** 2)

    x = (n + h) * math.cos(phi) * math.cos(lam)
    y = (n + h) * math.cos(phi) * math.sin(lam)
    z = (n * (1 - ell.e2) + h) * math.sin(phi)

    return x, y, z


def ecef_to_geodetic(
    x: float, y: float, z: float, ell: Ellipsoid = WGS84
) -> Tuple[float, float, float]:
    """ECEF XYZ to Lat/Lon/H (decimal degrees)."""
    lam = math.atan2(y, x)

    p = math.hypot(x, y)
    phi = math.atan2(z, p * (1 - ell.e2))

    # Iterate for better precision
    h = 0.0  # Initialize h
    for _ in range(5):
        n = ell.a / math.sqrt(1 - ell.e2 * math.sin(phi) ** 2)
        
        cos_phi = math.cos(phi)
        if abs(cos_phi) < 1e-10:  # Check for near-polar case
            h = abs(z) + n * ell.e2 - n # Approximation for poles
            # In this case, phi is already very close to +/- PI/2, so the next phi calculation
            # using atan2 is robust.
        else:
            h = p / cos_phi - n
        phi = math.atan2(z, p * (1 - ell.e2 * (n / (n + h))))

    return math.degrees(phi), math.degrees(lam), h


def gauss_kruger_forward(
    lat: float, lon: float, lon0: float, ell: Ellipsoid = KRASOVSKY
) -> Tuple[float, float]:
    """
    Simplified Gauss-Krüger Forward Projection.
    Calculates Easting (Y) and Northing (X).
    """
    phi = math.radians(lat)
    lam = math.radians(lon - lon0)

    a = ell.a
    e2 = ell.e2

    # Meridian arc length calculation (simplified)
    # This is a complex series, using a simplified version for demonstration
    # In a full virtuoso implementation, we use precise coefficients.

    n = a / math.sqrt(1 - e2 * math.sin(phi) ** 2)
    t = math.tan(phi) ** 2
    c = ell.ep2 * math.cos(phi) ** 2
    al = lam * math.cos(phi)

    # M - Meridian arc from equator to phi
    m = a * (
        (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256) * phi
        - (3 * e2 / 8 + 3 * e2**2 / 32 + 45 * e2**3 / 1024) * math.sin(2 * phi)
        + (15 * e2**2 / 256 + 45 * e2**3 / 1024) * math.sin(4 * phi)
        - (35 * e2**3 / 3072) * math.sin(6 * phi)
    )

    # X (Northing)
    x = m + n * math.tan(phi) * (al**2 / 2 + (5 - t + 9 * c + 4 * c**2) * al**4 / 24)

    # Y (Easting)
    y = n * (
        al
        + (1 - t + c) * al**3 / 6
        + (5 - 18 * t + t**2 + 72 * c - 58 * ell.ep2) * al**5 / 120
    )

    # False Easting (Standard for many countries is zone_no * 1e6 + 500000)
    y = y + 500000  # Add standard false easting
    return x, y


def utm_forward(
    lat: float, lon: float, ell: Ellipsoid = WGS84
) -> Tuple[float, float, int, str]:
    """
    UTM Forward Projection (NATO Military Grid Standard).
    Returns: (northing, easting, zone_number, zone_letter)
    """
    # Determine UTM zone
    zone_num = int((lon + 180) / 6) + 1
    if zone_num > 60:
        zone_num = 60

    # Zone central meridian
    lon0 = (zone_num - 1) * 6 - 180 + 3

    # Scale factor for UTM
    k0 = 0.9996

    phi = math.radians(lat)
    lam = math.radians(lon - lon0)

    a = ell.a
    e2 = ell.e2
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))

    n = (a - ell.b) / (a + ell.b)
    n2 = n**2
    n3 = n**3
    n4 = n**4
    n5 = n**5
    n6 = n**6

    # Meridian arc
    A = a * (1 - n + (5 / 4) * (n2 - n3) + (81 / 64) * (n4 - n5))
    B = (3 * a * n / 2) * (1 - n + (7 / 8) * (n2 - n3) + (55 / 64) * (n4 - n5))
    C = (15 * a * n2 / 16) * (1 - n + (3 / 4) * (n2 - n3))
    D = (35 * a * n3 / 48) * (1 - n + (11 / 16) * (n2 - n3))
    E = (315 * a * n4 / 512) * (1 - n)

    S = (
        A * phi
        - B * math.sin(2 * phi)
        + C * math.sin(4 * phi)
        - D * math.sin(6 * phi)
        + E * math.sin(8 * phi)
    )

    # Radius of curvature in prime vertical
    nu = a / math.sqrt(1 - e2 * math.sin(phi) ** 2)
    # Radius of curvature in meridian
    rho = a * (1 - e2) / ((1 - e2 * math.sin(phi) ** 2) ** 1.5)

    eta2 = nu / rho - 1

    t = math.tan(phi) ** 2
    t2 = t**2
    t4 = t**4

    l = lam
    l2 = l**2
    l3 = l**3
    l4 = l**4
    l5 = l**5
    l6 = l**6

    # Easting
    x = (
        k0
        * nu
        * (
            l * math.cos(phi)
            + (l3 / 6) * (1 - t + eta2)
            + (l5 / 120) * (5 - 18 * t + t2 + 72 * eta2 - 58 * ell.ep2)
        )
    )

    # Northing
    y = k0 * (
        S
        + nu
        * math.tan(phi)
        * (
            l2 / 2
            + (l4 / 24) * (5 - t + 9 * eta2 + 4 * eta2**2)
            + (l6 / 720) * (61 - 58 * t + t2 + 600 * eta2 - 330 * ell.ep2)
        )
    )

    # Apply false easting/northing
    x = x + 500000
    if y < 0:
        y += 10000000

    # Zone letter (latitude band)
    zone_letters = "CDEFGHJKLMNPQRSTUVWXX"
    lat_idx = int((lat + 80) / 8)
    if lat_idx < 0:
        lat_idx = 0
    if lat_idx >= len(zone_letters):
        lat_idx = len(zone_letters) - 1
    zone_letter = zone_letters[lat_idx]

    return y, x, zone_num, zone_letter


def utm_inverse(
    northing: float,
    easting: float,
    zone_num: int,
    zone_letter: str,
    ell: Ellipsoid = WGS84,
) -> Tuple[float, float]:
    """
    UTM Inverse Projection (NATO Military Grid Standard).
    Converts UTM coordinates back to lat/lon.
    """
    k0 = 0.9996

    # Remove false easting
    x = easting - 500000

    # False northing for southern hemisphere: letters C through M (excluding I,O)
    if zone_letter in "CDEFGHJKLM":
        y = northing - 10000000
    else:
        y = northing

    # Central meridian
    lon0 = (zone_num - 1) * 6 - 180 + 3

    # Meridian arc from northing
    M = y / k0

    a = ell.a
    e2 = ell.e2
    b = ell.b

    n = (a - b) / (a + b)
    n2 = n**2
    n3 = n**3
    n4 = n**4
    n5 = n**5

    A = a * (1 - n + (5 / 4) * (n2 - n3) + (81 / 64) * (n4 - n5))
    B = (3 * a * n / 2) * (1 - n + (7 / 8) * (n2 - n3) + (55 / 64) * (n4 - n5))
    C = (15 * a * n2 / 16) * (1 - n + (3 / 4) * (n2 - n3))
    D = (35 * a * n3 / 48) * (1 - n + (11 / 16) * (n2 - n3))
    E = (315 * a * n4 / 512) * (1 - n)

    mu = M / A
    phi = mu
    for _ in range(10):
        phi_old = phi
        phi = (
            mu
            + (B / A) * math.sin(2 * phi)
            + (C / A) * math.sin(4 * phi)
            + (D / A) * math.sin(6 * phi)
            + (E / A) * math.sin(8 * phi)
        )
        if abs(phi - phi_old) < 1e-12:
            break

    sin_phi = math.sin(phi)
    cos_phi = math.cos(phi)
    tan_phi = math.tan(phi)

    nu = a / math.sqrt(1 - e2 * sin_phi**2)
    eta2 = (nu / (a * (1 - e2) / ((1 - e2 * sin_phi**2) ** 1.5))) - 1
    t = tan_phi**2

    # Compute λ from easting
    alpha = x / (k0 * nu * cos_phi)

    term1 = (1 - t + eta2) * alpha**3 / 6
    term2 = (5 - 18 * t + t**2 + 72 * eta2 - 58 * ell.ep2) * alpha**5 / 120

    lam = alpha - term1 - term2

    lon = lon0 + math.degrees(lam)
    lat = math.degrees(phi)

    return lat, lon


def mgrs_to_latlon(mgrs: str, ell: Ellipsoid = WGS84) -> Tuple[float, float]:
    """
    Convert MGRS (Military Grid Reference System) to lat/lon.
    MGRS format: DDLTT EEEENNNN (e.g., '33T 12345 67890')
    """
    mgrs = mgrs.replace(" ", "").upper()

    # Parse: zone number (1-2 digits), zone letter, 100km grid square, easting, northing
    import re

    match = re.match(r"(\d{1,2})([A-Z])([A-Z]{2})(\d+)(\d+)$", mgrs)
    if not match:
        raise ValueError(f"Invalid MGRS format: {mgrs}")

    zone_num = int(match.group(1))
    zone_letter = match.group(2)
    grid_sq = match.group(3)
    easting_digits = match.group(4)
    northing_digits = match.group(5)

    # 100km grid square letters
    col_letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    row_letters = "ABCDEFGHJKLMNPQRSTUV"

    col_idx = col_letters.index(grid_sq[0])
    row_idx = row_letters.index(grid_sq[1])

    # Calculate 100km grid origins
    easting_100k = col_idx * 100000 + 100000  # False easting starts at 100km
    northing_100k = row_idx * 100000

    # Adjust for zone letter (latitude bands)
    zone_letters = "CDEFGHJKLMNPQRSTUVWXX"
    lat_band_idx = zone_letters.index(zone_letter)
    lat_band_min = -80 + lat_band_idx * 8
    northing_100k += int(lat_band_min / 8) * 800000  # Approximate

    # Combine 100km grid with given digits
    easting = easting_100k + int(easting_digits) * (10 ** (5 - len(easting_digits)))
    northing = northing_100k + int(northing_digits) * (10 ** (5 - len(northing_digits)))

    # Convert to lat/lon using UTM inverse
    return utm_inverse(northing, easting, zone_num, zone_letter, ell)


def calculate_grid_convergence(
    lat: float, lon: float, central_meridian: float, ell: Ellipsoid = WGS84
) -> float:
    """
    Calculate grid convergence (meridian convergence) in decimal degrees.
    Positive = grid north is east of true north.
    Critical for converting between grid azimuth and true azimuth.
    """
    phi = math.radians(lat)
    lam = math.radians(lon - central_meridian)
    e2 = ell.e2

    # Grid convergence formula for transverse Mercator
    nu = ell.a / math.sqrt(1 - e2 * math.sin(phi) ** 2)
    t = math.tan(phi) ** 2
    eta2 = (nu / (ell.a * (1 - e2) / ((1 - e2 * math.sin(phi) ** 2) ** 1.5))) - 1

    # Convergence
    gamma = lam * math.sin(phi) + (lam**3 * math.sin(phi) * math.cos(phi) ** 2 / 3) * (
        1 + 3 * eta2 + 2 * eta2**2
    )

    return math.degrees(gamma)


def calculate_point_scale_factor(
    lat: float, lon: float, central_meridian: float, ell: Ellipsoid = WGS84
) -> float:
    """
    Calculate point scale factor (k) for UTM/Transverse Mercator projection.
    k = scale factor at point (1.0000 at standard meridian for UTM with k0=0.9996)
    """
    phi = math.radians(lat)
    lam = math.radians(lon - central_meridian)
    e2 = ell.e2

    nu = ell.a / math.sqrt(1 - e2 * math.sin(phi) ** 2)
    rho = ell.a * (1 - e2) / ((1 - e2 * math.sin(phi) ** 2) ** 1.5)
    eta2 = nu / rho - 1
    t = math.tan(phi) ** 2

    # Scale factor
    k = 0.9996 * (nu / ell.a) * (1 + (lam**2 / 2) * math.cos(phi) ** 2 * (1 + eta2 + t))

    return k


def geoid_height_approx(lat: float, lon: float, model: str = "EGM96") -> float:
    """
    Approximate geoid height (N) in meters.
    N = height of geoid above ellipsoid.
    Positive N means geoid is above ellipsoid.
    Uses simplified 2-term model for demonstration.
    For production use: EGM2008, full grid interpolation.
    """
    phi = math.radians(lat)
    lam = math.radians(lon)

    if model == "EGM96":
        # Simplified: 2 dominant spherical harmonics
        # Real EGM96 has 130,676 coefficients
        n = 13.4 * math.sin(phi) - 53.9 * math.cos(phi) * math.sin(lam)
        return round(n, 2)
    elif model == "EGM2008":
        # Slightly more accurate simplification
        n = 15.1 * math.sin(phi) - 48.7 * math.cos(phi) * math.sin(lam + 1.5)
        return round(n, 2)

    return 0.0


def sk42_to_wgs84(
    northing: float, easting: float, zone: int
) -> Tuple[float, float, float]:
    """
    Convert Soviet SK-42 (SK-42) coordinates to WGS84.
    SK-42 uses Krassovsky ellipsoid with specific Gauss-Kruger zones.
    Returns: (lat, lon, h)
    """
    # First convert SK-42 grid to Krassovsky geodetic
    lat_kr, lon_kr = gauss_kruger_inverse(northing, easting, zone * 6 - 183, KRASOVSKY)

    # Then transform to WGS84 using Helmert
    x, y, z = geodetic_to_ecef(lat_kr, lon_kr, 0.0, KRASOVSKY)

    # SK-42 to WGS84 parameters (approximate)
    dx, dy, dz = 24.82, -123.79, -94.23
    rx, ry, rz = 0.2054, 0.5417, 0.7218
    s = 0.614

    x_wgs, y_wgs, z_wgs = helmert_transform(x, y, z, dx, dy, dz, rx, ry, rz, s)
    lat_wgs, lon_wgs, h_wgs = ecef_to_geodetic(x_wgs, y_wgs, z_wgs, WGS84)

    return lat_wgs, lon_wgs, h_wgs


def gauss_kruger_inverse(
    x: float, y: float, lon0: float, ell: Ellipsoid = KRASOVSKY
) -> Tuple[float, float]:
    """
    Gauss-Kruger Inverse Projection (from grid to geodetic).
    x = Northing, y = Easting (with false easting removed).
    Returns: (lat, lon) in decimal degrees.
    """
    a = ell.a
    e2 = ell.e2
    b = ell.b

    # Remove false easting if present (typically 500000 + zone*1e6)
    if y > 1000000:
        y = y % 1000000
    y = y - 500000

    # Meridian arc to footprint latitude
    n = (a - b) / (a + b)
    n2 = n**2
    n3 = n**3
    n4 = n**4
    n5 = n**5

    A = a * (1 - n + (5 / 4) * (n2 - n3) + (81 / 64) * (n4 - n5))
    B = (3 * a * n / 2) * (1 - n + (7 / 8) * (n2 - n3) + (55 / 64) * (n4 - n5))
    C = (15 * a * n2 / 16) * (1 - n + (3 / 4) * (n2 - n3))
    D = (35 * a * n3 / 48) * (1 - n + (11 / 16) * (n2 - n3))
    E = (315 * a * n4 / 512) * (1 - n)

    # Footprint latitude
    mu = x / A
    phi = mu
    for _ in range(10):
        phi_old = phi
        phi = (
            mu
            + (B / A) * math.sin(2 * phi)
            + (C / A) * math.sin(4 * phi)
            + (D / A) * math.sin(6 * phi)
            + (E / A) * math.sin(8 * phi)
        )
        if abs(phi - phi_old) < 1e-12:
            break

    # Latitude
    nu = a / math.sqrt(1 - e2 * math.sin(phi) ** 2)
    rho = a * (1 - e2) / ((1 - e2 * math.sin(phi) ** 2) ** 1.5)
    t = math.tan(phi) ** 2
    eta2 = nu / rho - 1

    lat = (
        phi
        - (t * y**2 / (2 * rho * nu))
        + (t * y**4 / (24 * rho * nu**3))
        * (5 + 3 * t + eta2 - 4 * eta2**2 - 9 * t * eta2)
    )
    lat = math.degrees(lat)

    # Longitude
    lon = lon0 + math.degrees(
        (y / (nu * math.cos(phi)))
        - (y**3 / (6 * nu**3 * math.cos(phi))) * (1 + 2 * t + eta2)
    )

    return lat, lon
