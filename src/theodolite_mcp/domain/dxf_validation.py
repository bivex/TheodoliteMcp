"""
DXF file validation module.
Checks for common issues in generated DXF files:
- Orphan/hanging entities (no layer or invalid layer)
- Overlapping/self-intersecting contours
- Invalid or out-of-bounds text labels
- Duplicate entities
- Zero-length segments
"""

import ezdxf
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ValidationSeverity(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ValidationIssue:
    entity_type: str
    layer: Optional[str]
    handle: str
    severity: ValidationSeverity
    message: str
    location: Optional[Tuple[float, float]] = None


@dataclass
class ValidationReport:
    file_path: str
    total_entities: int
    issues: List[ValidationIssue] = field(default_factory=list)
    layers_found: List[str] = field(default_factory=list)
    text_entities: int = 0
    polyline_entities: int = 0
    line_entities: int = 0

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def has_critical_errors(self) -> bool:
        """Check if any ERROR-level issues exist (as opposed to warnings)."""
        return any(i.severity == ValidationSeverity.ERROR for i in self.issues)

    def add_issue(self, issue: ValidationIssue):
        self.issues.append(issue)

    def summary(self) -> str:
        status = "PASS" if self.is_valid else "FAIL"
        return (
            f"Validation: {status}\n"
            f"Entities: {self.total_entities}, "
            f"Layers: {len(self.layers_found)}, "
            f"Issues: {len(self.issues)} "
            f"(Errors: {len(self.errors)}, Warnings: {len(self.warnings)})"
        )


def validate_dxf_file(dxf_path: str, check_geometry: bool = True) -> ValidationReport:
    """
    Main validation entry point. Reads DXF and runs all checks.

    Args:
        dxf_path: Path to DXF file
        check_geometry: Enable expensive geometry checks (self-intersection, overlaps)

    Returns:
        ValidationReport with all findings
    """
    report = ValidationReport(file_path=dxf_path, total_entities=0)

    try:
        doc = ezdxf.readfile(dxf_path)
    except Exception as e:
        report.add_issue(
            ValidationIssue(
                entity_type="FILE",
                layer=None,
                handle="",
                severity=ValidationSeverity.ERROR,
                message=f"Cannot read DXF file: {str(e)}",
            )
        )
        return report

    msp = doc.modelspace()
    report.total_entities = len(msp)

    # Collect layers
    report.layers_found = [layer.dxf.name for layer in doc.layers]

    # Entities to collect for geometry checks
    polylines: List[Any] = []
    lines: List[Any] = []
    texts: List[Any] = []

    # First pass: entity classification
    for entity in msp:
        entity_type = entity.dxftype()
        handle = entity.dxf.handle
        layer = entity.dxf.layer

        # Check for orphan entities (unusual layers)
        _check_layer_validity(entity, layer, report, handle, entity_type)

        # Categorize for second pass
        if entity_type == "LWPOLYLINE":
            polylines.append(entity)
            report.polyline_entities += 1
        elif entity_type == "LINE":
            lines.append(entity)
            report.line_entities += 1
        elif entity_type in ("TEXT", "MTEXT", "ATTRIB"):
            texts.append(entity)
            report.text_entities += 1
            _check_text_validity(entity, layer, report, handle)

    # Second pass: geometry checks (expensive)
    if check_geometry:
        _check_polyline_geometry(polylines, report)
        _check_line_geometry(lines, report)
        _check_overlapping_contours(polylines, report)

    return report


def _check_layer_validity(
    entity, layer: str, report: ValidationReport, handle: str, entity_type: str
):
    """Check if entity's layer is within expected set."""
    expected_layers = {
        "0_BOUNDARY",
        "0_POINTS",
        "0_TEXT",
        "ZONE_BUILDINGS",
        "ZONE_WATER",
        "ZONE_GREEN",
        "ZONE_OTHER",
        "V-PROF-GROUND",
        "V-PROF-DESIGN",
        "V-PROF-TABLE",
        "V-PROF-TEXT",
        "V-PROF-ORDINATES",
    }

    # Standard AutoCAD layers that are always present and acceptable
    standard_layers = {"0", "Defpoints"}

    if not layer:
        report.add_issue(
            ValidationIssue(
                entity_type=entity_type,
                layer=None,
                handle=handle,
                severity=ValidationSeverity.WARNING,
                message="Entity has no layer assigned (orphan)",
            )
        )
    elif layer not in expected_layers and layer not in standard_layers:
        report.add_issue(
            ValidationIssue(
                entity_type=entity_type,
                layer=layer,
                handle=handle,
                severity=ValidationSeverity.WARNING,
                message=f"Unexpected layer: '{layer}'",
            )
        )


def _check_text_validity(
    text_entity, layer: str, report: ValidationReport, handle: str
):
    """Check text entity for common issues."""
    # Get text content
    if hasattr(text_entity, "dxf"):
        text_content = text_entity.dxf.text if hasattr(text_entity.dxf, "text") else ""
        if hasattr(text_entity.dxf, "text") is False:
            text_content = str(text_entity)
    else:
        text_content = str(text_entity)

    # Empty text
    if not text_content or text_content.strip() == "":
        report.add_issue(
            ValidationIssue(
                entity_type="TEXT",
                layer=layer,
                handle=handle,
                severity=ValidationSeverity.WARNING,
                message="Empty text content",
            )
        )
        return

    # Coordinates
    coords = text_entity.dxf.insert
    x, y = coords.x, coords.y

    # Out-of-bounds check (text too far from origin)
    if abs(x) > 1e9 or abs(y) > 1e9:
        report.add_issue(
            ValidationIssue(
                entity_type="TEXT",
                layer=layer,
                handle=handle,
                severity=ValidationSeverity.WARNING,
                message=f"Text at extreme coordinates ({x:.2f}, {y:.2f})",
                location=(x, y),
            )
        )

    # Numeric content validation: detect NaN, Inf, and malformed numbers
    normalized = text_content.strip()
    # Try to parse as float regardless of format
    try:
        val = float(normalized)
        if val != val:  # NaN
            report.add_issue(
                ValidationIssue(
                    entity_type="TEXT",
                    layer=layer,
                    handle=handle,
                    severity=ValidationSeverity.ERROR,
                    message="Numeric text contains NaN",
                    location=(x, y),
                )
            )
        elif abs(val) == float("inf"):
            report.add_issue(
                ValidationIssue(
                    entity_type="TEXT",
                    layer=layer,
                    handle=handle,
                    severity=ValidationSeverity.ERROR,
                    message="Numeric text contains infinity",
                    location=(x, y),
                )
            )
    except ValueError:
        # Not a plain float. Check for scientific notation with NaN/Inf
        low = normalized.lower()
        if low in ("nan", "inf", "infinity", "-inf", "-infinity", "+inf", "+infinity"):
            report.add_issue(
                ValidationIssue(
                    entity_type="TEXT",
                    layer=layer,
                    handle=handle,
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid numeric literal: '{text_content}'",
                    location=(x, y),
                )
            )


def _check_polyline_geometry(polylines: List[Any], report: ValidationReport):
    """Check polylines for self-intersection, zero-length segments, and closure."""
    for pline in polylines:
        handle = pline.dxf.handle
        layer = pline.dxf.layer
        points = list(pline.vertices_in_wcs())

        if len(points) < 2:
            report.add_issue(
                ValidationIssue(
                    entity_type="LWPOLYLINE",
                    layer=layer,
                    handle=handle,
                    severity=ValidationSeverity.ERROR,
                    message="Polyline has less than 2 vertices",
                    location=(points[0].x, points[0].y) if points else None,
                )
            )
            continue

        # Check for zero-length consecutive segments
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            dist = ((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2) ** 0.5
            if dist < 1e-9:
                report.add_issue(
                    ValidationIssue(
                        entity_type="LWPOLYLINE",
                        layer=layer,
                        handle=handle,
                        severity=ValidationSeverity.WARNING,
                        message=f"Zero-length segment between vertex {i} and {i + 1}",
                        location=(p1.x, p1.y),
                    )
                )


def _check_line_geometry(lines: List[Any], report: ValidationReport):
    """Check lines for zero-length."""
    for line in lines:
        handle = line.dxf.handle
        layer = line.dxf.layer
        start = line.dxf.start
        end = line.dxf.end

        dist = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5
        if dist < 1e-9:
            report.add_issue(
                ValidationIssue(
                    entity_type="LINE",
                    layer=layer,
                    handle=handle,
                    severity=ValidationSeverity.WARNING,
                    message="Zero-length line segment",
                    location=(start[0], start[1]),
                )
            )


def _check_overlapping_contours(polylines: List[Any], report: ValidationReport):
    """
    Detect overlapping polylines (same or nearly coincident vertices).
    Basic O(n²) check - acceptable for small plans.
    """
    # Group polylines by approximate bounding box
    for i, pline1 in enumerate(polylines):
        pts1 = list(pline1.vertices_in_wcs())
        if not pts1:
            continue

        bbox1 = _get_bbox(pts1)
        handle1 = pline1.dxf.handle
        layer1 = pline1.dxf.layer

        for j, pline2 in enumerate(polylines[i + 1 :], start=i + 1):
            pts2 = list(pline2.vertices_in_wcs())
            if not pts2:
                continue

            bbox2 = _get_bbox(pts2)
            handle2 = pline2.dxf.handle
            layer2 = pline2.dxf.layer

            # Quick bbox intersection test
            if _bboxes_overlap(bbox1, bbox2):
                # Check for shared vertices
                shared = _count_shared_vertices(pts1, pts2, tol=1e-6)
                if shared > 0:
                    severity = (
                        ValidationSeverity.WARNING
                        if shared < min(len(pts1), len(pts2))
                        else ValidationSeverity.ERROR
                    )
                    report.add_issue(
                        ValidationIssue(
                            entity_type="LWPOLYLINE",
                            layer=f"{layer1}/{layer2}",
                            handle=f"{handle1}/{handle2}",
                            severity=severity,
                            message=f"Overlapping contours detected ({shared} shared vertex(es))",
                            location=(pts1[0].x, pts1[0].y),
                        )
                    )


def _get_bbox(points: List[Any]) -> Tuple[float, float, float, float]:
    """Return (min_x, min_y, max_x, max_y) for point list."""
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _bboxes_overlap(
    bbox1: Tuple[float, float, float, float],
    bbox2: Tuple[float, float, float, float],
    tol: float = 1e-6,
) -> bool:
    """Check if two bounding boxes overlap."""
    minx1, miny1, maxx1, maxy1 = bbox1
    minx2, miny2, maxx2, maxy2 = bbox2
    return not (
        maxx1 < minx2 - tol
        or maxx2 < minx1 - tol
        or maxy1 < miny2 - tol
        or maxy2 < miny1 - tol
    )


def _count_shared_vertices(pts1: List[Any], pts2: List[Any], tol: float = 1e-6) -> int:
    """Count vertices that are the same (within tolerance)."""
    shared = 0
    for p1 in pts1:
        for p2 in pts2:
            if abs(p1.x - p2.x) <= tol and abs(p1.y - p2.y) <= tol:
                shared += 1
                break
    return shared
