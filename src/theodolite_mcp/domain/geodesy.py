import math
import numpy as np
from typing import Tuple, NamedTuple

class Ellipsoid(NamedTuple):
    a: float  # Semi-major axis
    f_inv: float  # Inverse flattening

    @property
    def b(self) -> float:
        return self.a * (1 - 1/self.f_inv)

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

def helmert_transform(x: float, y: float, z: float, 
                      dx: float, dy: float, dz: float, 
                      rx_sec: float, ry_sec: float, rz_sec: float, 
                      s_ppm: float) -> Tuple[float, float, float]:
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
    rot = np.array([
        [1.0, rz, -ry],
        [-rz, 1.0, rx],
        [ry, -rx, 1.0]
    ])
    
    trans = np.array([dx, dy, dz])
    
    res = trans + m * np.dot(rot, vec)
    return tuple(res)

def geodetic_to_ecef(lat: float, lon: float, h: float, ell: Ellipsoid = WGS84) -> Tuple[float, float, float]:
    """Lat/Lon (decimal degrees) to ECEF XYZ."""
    phi = math.radians(lat)
    lam = math.radians(lon)
    
    n = ell.a / math.sqrt(1 - ell.e2 * math.sin(phi)**2)
    
    x = (n + h) * math.cos(phi) * math.cos(lam)
    y = (n + h) * math.cos(phi) * math.sin(lam)
    z = (n * (1 - ell.e2) + h) * math.sin(phi)
    
    return x, y, z

def ecef_to_geodetic(x: float, y: float, z: float, ell: Ellipsoid = WGS84) -> Tuple[float, float, float]:
    """ECEF XYZ to Lat/Lon/H (decimal degrees)."""
    lam = math.atan2(y, x)
    
    p = math.hypot(x, y)
    phi = math.atan2(z, p * (1 - ell.e2))
    
    # Iterate for better precision
    for _ in range(5):
        n = ell.a / math.sqrt(1 - ell.e2 * math.sin(phi)**2)
        h = p / math.cos(phi) - n
        phi = math.atan2(z, p * (1 - ell.e2 * (n / (n + h))))
        
    return math.degrees(phi), math.degrees(lam), h

def gauss_kruger_forward(lat: float, lon: float, lat0: float, lon0: float, 
                         ell: Ellipsoid = KRASOVSKY) -> Tuple[float, float]:
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
    
    n = a / math.sqrt(1 - e2 * math.sin(phi)**2)
    t = math.tan(phi)**2
    c = ell.ep2 * math.cos(phi)**2
    al = lam * math.cos(phi)
    
    # M - Meridian arc from equator to phi
    m = a * ((1 - e2/4 - 3*e2**2/64 - 5*e2**3/256) * phi -
             (3*e2/8 + 3*e2**2/32 + 45*e2**3/1024) * math.sin(2*phi) +
             (15*e2**2/256 + 45*e2**3/1024) * math.sin(4*phi) -
             (35*e2**3/3072) * math.sin(6*phi))
    
    # X (Northing)
    x = m + n * math.tan(phi) * (al**2/2 + (5 - t + 9*c + 4*c**2) * al**4/24)
    
    # Y (Easting)
    y = n * (al + (1 - t + c) * al**3/6 + (5 - 18*t + t**2 + 72*c - 58*ell.ep2) * al**5/120)
    
    # False Easting (Standard for many countries is zone_no * 1e6 + 500000)
    return x, y
