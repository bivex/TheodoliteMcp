# 📐 Theodolite Survey MCP Server (Virtuoso Edition)

A professional-grade MCP server for engineering, surveying, and architectural automation. From raw field measurements to high-precision CAD interoperability and ISO-compliant technical drawings.

![Construction Site Plan](docs/gallery/construction_site_plan.png)
*Example: ISO-compliant plot plan with standardized material hatching and reference grids.*

---

## 🌟 Core Capabilities

- **Precision Surveying:** Automated Bowditch (Compass Rule) and **Least Squares Adjustment (LSA)** for surveying networks.
- **Infrastructure Engineering:** Longitudinal profiles for pipelines and roads with vertical exaggeration and auto-calculated slope tables ("podvals").
- **Architectural Design:** Professional floor plans with thick walls, material hatching (ISO 128-50), and dynamic furniture/sanitary blocks.
- **Construction Management:** As-built survey reports with deviation vectors (plan/fact) and earthwork volume cartograms.
- **Scientific Geodesy:** Support for ellipsoids (WGS84, Krasovsky), Gauss-Krüger/UTM projections, and 7-parameter Helmert transformations.
- **Global Compliance:** Full support for **23 languages** and strict adherence to **ISO 5457, 7200, 3098, 129-1, and 128-50**.

---

## 📂 Project Structure

- `src/theodolite_mcp/` - Core application logic (LSA engine, Geodetic math, Rendering).
- `examples/` - Demonstration scripts for all major use cases.
- `docs/gallery/` - Visual examples of generated ISO-compliant plans.
- `tests/` - Robust unit test suite covering edge cases and pixel-perfect rendering.
- `output/` - Default directory for generated PNG and DXF files.

---

## 🛠 Available MCP Tools

### 🖋 Professional Rendering (PNG)
- **`draw_plot_plan`**: Generates ISO-compliant cadastral, topographic, and site plans.
- **`draw_longitudinal_profile`**: Generates engineering profiles with auto-calculated slope/depth tables.
- **`draw_interior_plan`**: Generates architectural floor plans with walls, openings, and furniture.
- **`draw_construction_as_built_report`**: Generates deviation schemes and earthwork volume plans.

### 📂 CAD Interoperability (DXF)
- **`export_to_dxf`**: Exports any PlotPlan to a multi-layered AutoCAD-compatible file.
- **`export_profile_to_dxf`**: Exports engineering profiles to DXF with correct vertical exaggeration.

### 📐 Surveying & Mathematics (LSA)
- **`adjust_network_least_squares`**: Scientific network adjustment using the Gauss-Markov model.
- **`adjust_traverse_network`**: Standard Bowditch adjustment for theodolite traverses.
- **`compute_parcel_area`**: Precise area calculation using the Gauss polygon formula.

### 🧭 Geodesy & Conversions
- **`transform_coordinate_system`**: 7-parameter Helmert transformation (WGS84 ↔ Local).
- **`project_coordinates_gauss_kruger`**: Projects geodetic coordinates to flat X, Y grid.
- **`compute_inverse_geodetic_problem`**: Calculates distance/azimuth between points.
- **`dms_to_decimal_degrees`** / **`decimal_degrees_to_dms`**: Angle format conversions.

---

## 🚀 Quick Start

Ensure you have Python 3.10+ installed.

```bash
# Install the server
pip install .

# Run a professional showcase
PYTHONPATH=src python3 examples/virtuoso_dam_project.py  # High-precision monitoring
PYTHONPATH=src python3 examples/demo_interior_full.py     # Architectural layout
PYTHONPATH=src python3 examples/demo_profile.py           # Pipeline profile
```

## 📐 Industrial Compliance

This server is built for engineers, not just developers. Every line weight, font height (osifont), and margin meets **ISO Technical Documentation** requirements, making outputs suitable for official blueprints and legal engineering reports.

## 📄 License
MIT License. Technical font `osifont` is licensed under GNU LGPL.
