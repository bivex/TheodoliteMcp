import numpy as np
import math
from typing import List, Dict, Optional
from pydantic import BaseModel

class ObservationLS(BaseModel):
    from_pt: str
    to_pt: str
    target_pt: Optional[str] = None # For angles (from_pt is vertex)
    value: float
    std_dev: float
    type: str # "distance", "angle", "azimuth", "fixed_x", "fixed_y"

class LSAResult(BaseModel):
    adjusted_coordinates: Dict[str, Dict[str, float]]
    standard_deviations: Dict[str, Dict[str, float]]
    unit_weight_variance: float
    iterations: int

def adjust_network_2d(observations: List[ObservationLS], initial_coords: Dict[str, Dict[str, float]]) -> LSAResult:
    """
    Least Squares Adjustment for 2D networks.
    Linearizes non-linear observation equations and iterates.
    """
    pts_names = sorted(initial_coords.keys())
    # Identify which points are free vs fixed
    # For now, let's assume if it has a 'fixed_x' observation, it's fixed.
    fixed_pts = set()
    for obs in observations:
        if obs.type in ["fixed_x", "fixed_y"]:
            fixed_pts.add(obs.from_pt)
    
    free_pts = [p for p in pts_names if p not in fixed_pts]
    n_free = len(free_pts)
    if n_free == 0:
        return LSAResult(adjusted_coordinates=initial_coords, standard_deviations={}, unit_weight_variance=1.0, iterations=0)

    curr_coords = {name: coords.copy() for name, coords in initial_coords.items()}
    
    max_iters = 10
    for iter_idx in range(max_iters):
        # A matrix: Jacobians, L vector: (obs - calc)
        A = []
        L = []
        P = [] # Weight matrix diagonal

        for obs in observations:
            if obs.type == "distance":
                p1, p2 = curr_coords[obs.from_pt], curr_coords[obs.to_pt]
                dist_calc = math.hypot(p2['x'] - p1['x'], p2['y'] - p1['y'])
                L.append(obs.value - dist_calc)
                P.append(1.0 / (obs.std_dev**2))
                
                row = np.zeros(2 * n_free)
                # Partial derivatives: dD/dx2 = (x2-x1)/D, dD/dx1 = -(x2-x1)/D
                if obs.from_pt in free_pts:
                    idx = free_pts.index(obs.from_pt)
                    row[2*idx] = -(p2['x'] - p1['x']) / dist_calc
                    row[2*idx+1] = -(p2['y'] - p1['y']) / dist_calc
                if obs.to_pt in free_pts:
                    idx = free_pts.index(obs.to_pt)
                    row[2*idx] = (p2['x'] - p1['x']) / dist_calc
                    row[2*idx+1] = (p2['y'] - p1['y']) / dist_calc
                A.append(row)

            elif obs.type == "azimuth":
                p1, p2 = curr_coords[obs.from_pt], curr_coords[obs.to_pt]
                dx, dy = p2['x'] - p1['x'], p2['y'] - p1['y']
                dist2 = dx**2 + dy**2
                az_calc = math.degrees(math.atan2(dy, dx))
                L.append(obs.value - az_calc)
                P.append(1.0 / (obs.std_dev**2))
                
                row = np.zeros(2 * n_free)
                # dAz/dx = -dy / dist2, dAz/dy = dx / dist2 (in radians)
                rho = 180.0 / math.pi
                if obs.from_pt in free_pts:
                    idx = free_pts.index(obs.from_pt)
                    row[2*idx] = (dy / dist2) * rho
                    row[2*idx+1] = (-dx / dist2) * rho
                if obs.to_pt in free_pts:
                    idx = free_pts.index(obs.to_pt)
                    row[2*idx] = (-dy / dist2) * rho
                    row[2*idx+1] = (dx / dist2) * rho
                A.append(row)

            elif obs.type == "angle":
                # Angle at 'from_pt' between 'to_pt' and 'target_pt'
                if obs.target_pt is None or obs.target_pt not in curr_coords:
                    continue
                
                p_v = curr_coords[obs.from_pt] # Vertex
                p_1 = curr_coords[obs.to_pt]   # Backsight
                p_2 = curr_coords[obs.target_pt] # Foresight
                
                dx1, dy1 = p_1['x'] - p_v['x'], p_1['y'] - p_v['y']
                dx2, dy2 = p_2['x'] - p_v['x'], p_2['y'] - p_v['y']
                
                dist1_2 = dx1**2 + dy1**2
                dist2_2 = dx2**2 + dy2**2
                
                az1 = math.degrees(math.atan2(dy1, dx1))
                az2 = math.degrees(math.atan2(dy2, dx2))
                angle_calc = az2 - az1
                if angle_calc < 0: angle_calc += 360.0
                
                misc = obs.value - angle_calc
                if misc > 180: misc -= 360
                if misc < -180: misc += 360
                L.append(misc)
                P.append(1.0 / (obs.std_dev**2))
                
                row = np.zeros(2 * n_free)
                rho = 180.0 / math.pi
                
                # Derivatives for vertex (from_pt)
                if obs.from_pt in free_pts:
                    idx = free_pts.index(obs.from_pt)
                    # dAng/dxv = dAz2/dxv - dAz1/dxv = (dy2/dist2_2) - (dy1/dist1_2)
                    row[2*idx] = (dy2 / dist2_2 - dy1 / dist1_2) * rho
                    # dAng/dyv = dAz2/dyv - dAz1/dyv = (-dx2/dist2_2) - (-dx1/dist1_2)
                    row[2*idx+1] = (-dx2 / dist2_2 + dx1 / dist1_2) * rho
                
                # Derivatives for backsight (to_pt)
                if obs.to_pt in free_pts:
                    idx = free_pts.index(obs.to_pt)
                    # dAng/dx1 = -dAz1/dx1 = -(-dy1/dist1_2) = dy1/dist1_2
                    row[2*idx] = (dy1 / dist1_2) * rho
                    # dAng/dy1 = -dAz1/dy1 = -(dx1/dist1_2) = -dx1/dist1_2
                    row[2*idx+1] = (-dx1 / dist1_2) * rho
                
                # Derivatives for foresight (target_pt)
                if obs.target_pt in free_pts:
                    idx = free_pts.index(obs.target_pt)
                    # dAng/dx2 = dAz2/dx2 = -dy2/dist2_2
                    row[2*idx] = (-dy2 / dist2_2) * rho
                    # dAng/dy2 = dAz2/dy2 = dx2/dist2_2
                    row[2*idx+1] = (dx2 / dist2_2) * rho
                
                A.append(row)

            elif obs.type == "fixed_x":
                if obs.from_pt in free_pts:
                    idx = free_pts.index(obs.from_pt)
                    L.append(obs.value - curr_coords[obs.from_pt]['x'])
                    P.append(1.0 / (obs.std_dev**2 if obs.std_dev > 0 else 1e-12))
                    row = np.zeros(2 * n_free)
                    row[2*idx] = 1.0
                    A.append(row)

            elif obs.type == "fixed_y":
                if obs.from_pt in free_pts:
                    idx = free_pts.index(obs.from_pt)
                    L.append(obs.value - curr_coords[obs.from_pt]['y'])
                    P.append(1.0 / (obs.std_dev**2 if obs.std_dev > 0 else 1e-12))
                    row = np.zeros(2 * n_free)
                    row[2*idx+1] = 1.0
                    A.append(row)
        
        A = np.array(A)
        L = np.array(L)
        P = np.diag(P)
        
        # Normal equations: (A'PA)x = A'PL
        AtPA = A.T @ P @ A
        AtPL = A.T @ P @ L
        
        try:
            dx_vec = np.linalg.solve(AtPA, AtPL)
        except np.linalg.LinAlgError:
            # Singular matrix - likely not enough constraints
            break
            
        # Update coordinates
        max_correction = 0
        for i, name in enumerate(free_pts):
            curr_coords[name]['x'] += dx_vec[2*i]
            curr_coords[name]['y'] += dx_vec[2*i+1]
            max_correction = max(max_correction, abs(dx_vec[2*i]), abs(dx_vec[2*i+1]))
            
        if max_correction < 1e-5: # Convergence
            # Error analysis
            v = A @ dx_vec - L
            dof = len(L) - 2 * n_free
            sigma0_2 = (v.T @ P @ v) / dof if dof > 0 else 1.0
            
            try:
                Qxx = np.linalg.inv(AtPA)
                std_devs = {}
                for i, name in enumerate(free_pts):
                    std_devs[name] = {
                        'x': math.sqrt(abs(Qxx[2*i, 2*i] * sigma0_2)),
                        'y': math.sqrt(abs(Qxx[2*i+1, 2*i+1] * sigma0_2))
                    }
                return LSAResult(
                    adjusted_coordinates=curr_coords, 
                    standard_deviations=std_devs, 
                    unit_weight_variance=float(sigma0_2),
                    iterations=iter_idx + 1
                )
            except np.linalg.LinAlgError:
                return LSAResult(adjusted_coordinates=curr_coords, standard_deviations={}, unit_weight_variance=float(sigma0_2), iterations=iter_idx + 1)
            
    return LSAResult(adjusted_coordinates=curr_coords, standard_deviations={}, unit_weight_variance=0.0, iterations=max_iters)
