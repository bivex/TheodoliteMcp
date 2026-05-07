#!/usr/bin/env python3
"""
Command-line tool to validate DXF files produced by theodolite-mcp.
Usage: python validate_dxf.py <path_to_dxf> [--no-geometry]
"""

import sys
import argparse
from pathlib import Path

# Add src to path for direct execution
sys.path.insert(0, str(Path(__file__).parent))

from theodolite_mcp.domain.dxf_validation import validate_dxf_file


def main():
    parser = argparse.ArgumentParser(
        description="Validate DXF files for cadastral/surveying plans"
    )
    parser.add_argument("dxf_path", type=str, help="Path to DXF file to validate")
    parser.add_argument(
        "--no-geometry",
        action="store_true",
        help="Skip expensive geometry checks (self-intersection, overlaps)",
    )
    args = parser.parse_args()

    dxf_path = Path(args.dxf_path)
    if not dxf_path.exists():
        print(f"ERROR: File not found: {dxf_path}")
        sys.exit(1)

    print(f"Validating: {dxf_path}")
    print("-" * 60)

    report = validate_dxf_file(str(dxf_path), check_geometry=not args.no_geometry)

    # Print summary
    print(report.summary())
    print()

    # Print layers
    if report.layers_found:
        print(f"Layers ({len(report.layers_found)}):")
        for layer in sorted(report.layers_found):
            print(f"  - {layer}")
        print()

    # Print entity counts
    print("Entity counts:")
    print(f"  Total:     {report.total_entities}")
    print(f"  Polylines: {report.polyline_entities}")
    print(f"  Lines:     {report.line_entities}")
    print(f"  Texts:     {report.text_entities}")
    print()

    # Print issues grouped by severity
    if report.errors:
        print(f"ERRORS ({len(report.errors)}):")
        for issue in report.errors:
            loc = (
                f" at ({issue.location[0]:.2f}, {issue.location[1]:.2f})"
                if issue.location
                else ""
            )
            print(f"  [{issue.entity_type}] {issue.message}{loc}")
        print()

    if report.warnings:
        print(f"WARNINGS ({len(report.warnings)}):")
        for issue in report.warnings:
            loc = (
                f" at ({issue.location[0]:.2f}, {issue.location[1]:.2f})"
                if issue.location
                else ""
            )
            print(
                f"  [{issue.entity_type}/{issue.layer or 'no-layer'}] {issue.message}{loc}"
            )
        print()

    if not report.issues:
        print("No issues found. DXF looks clean.")

    sys.exit(0 if report.is_valid else 2)


if __name__ == "__main__":
    main()
