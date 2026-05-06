import os
from pathlib import Path
from typing import List, Dict, Optional
from theodolite_mcp.domain.models import TraverseData, TraverseResult, PlotPlan, ProfilePlan, InteriorPlan
from ..domain.logic import calculate_traverse
from ..domain.rendering import render_plot_plan, render_profile_plan, render_interior_plan
from ..domain.dxf_export import export_plan_to_dxf, export_profile_to_dxf
from ..domain.least_squares import ObservationLS, adjust_network_2d, LSAResult
from ..domain.geodesy import (
    WGS84, KRASOVSKY, helmert_transform, 
    geodetic_to_ecef, ecef_to_geodetic, gauss_kruger_forward
)

class SurveyService:
    def _save_if_needed(self, data: bytes, path: Optional[str]) -> bytes:
        if path:
            output_path = Path(path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(data)
        return data

    def process_theodolite_traverse(self, data: TraverseData) -> TraverseResult:
        return calculate_traverse(data)

    def render_plot(self, plan: PlotPlan, output_path: Optional[str] = None) -> bytes:
        return self._save_if_needed(render_plot_plan(plan), output_path)

    def render_profile(self, plan: ProfilePlan, output_path: Optional[str] = None) -> bytes:
        return self._save_if_needed(render_profile_plan(plan), output_path)

    def render_interior(self, plan: InteriorPlan, output_path: Optional[str] = None) -> bytes:
        return self._save_if_needed(render_interior_plan(plan), output_path)

    def export_dxf(self, plan: PlotPlan, output_path: str) -> str:
        return export_plan_to_dxf(plan, output_path)

    def export_profile_dxf(self, plan: ProfilePlan, output_path: str) -> str:
        return export_profile_to_dxf(plan, output_path)

    def adjust_network_least_squares(self, observations: List[ObservationLS], 
                                     initial_coords: Dict[str, Dict[str, float]]) -> LSAResult:
        return adjust_network_2d(observations, initial_coords)

    def transform_wgs84_to_local(self, lat: float, lon: float, h: float, 
                                 params: Dict[str, float], 
                                 target_ellipsoid=KRASOVSKY) -> Dict[str, float]:
        """
        Full pipeline: WGS84 Geodetic -> ECEF -> Helmert -> Local ECEF -> Local Geodetic.
        """
        # 1. WGS84 Geodetic to ECEF
        x, y, z = geodetic_to_ecef(lat, lon, h, ell=WGS84)
        
        # 2. Helmert Transform
        xt, yt, zt = helmert_transform(x, y, z, **params)
        
        # 3. Local ECEF to Geodetic
        lat_l, lon_l, h_l = ecef_to_geodetic(xt, yt, zt, ell=target_ellipsoid)
        
        return {"lat": lat_l, "lon": lon_l, "h": h_l}

    def project_to_grid(self, lat: float, lon: float, lon0: float, 
                        ellipsoid=KRASOVSKY) -> Dict[str, float]:
        """Gauss-Krüger projection to X, Y (Northing/Easting)."""
        x, y = gauss_kruger_forward(lat, lon, lon0, ell=ellipsoid)
        return {"x": x, "y": y}
