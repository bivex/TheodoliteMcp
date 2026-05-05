# 📐 Theodolite Survey MCP Server

A professional-grade MCP server for processing theodolite survey field books, traverse adjustments, and **ISO-compliant** technical drawing generation.

![Construction Site Plan](docs/gallery/construction_site_plan.png)
*Example: ISO-compliant plot plan generated automatically from survey data.*

---

## 🌟 Core Features

- **Precision Surveying:** Automated angular and linear misclosure adjustment using the Compass Rule (Bowditch).
- **ISO Standard Rendering:** Generates professional technical drawings (PNG/PDF) following strict international standards:
    - **ISO 5457:** Standard paper formats (A0-A4) with precise 20mm/10mm margins and reference grids.
    - **ISO 7200:** Absolute-dimension title blocks (stamps) for professional identification.
    - **ISO 3098:** Technical lettering using the specialized `osifont` for engineering clarity.
    - **ISO 5455:** Strict engineering scales (1:50, 1:100, 1:500, etc.).
    - **ISO 129-1:** Smart dimensioning with automatic leader placement for tight spaces.
    - **ISO 128-50:** Standardized material hatching (Concrete, Brick, Metal, Soil, etc.).
- **Global Reach:** Full support for **23 languages**, covering most of Europe and major global markets.
- **Geodesic Logic:** Area calculation (Gauss formula), Azimuth calculations, and DMS/Decimal conversions.

---

## 📂 Project Structure

- `src/theodolite_mcp/` - Core application logic and MCP server infrastructure.
- `examples/` - Demonstration scripts for various use cases (Construction, Cadastral, Shipbuilding, etc.).
- `docs/gallery/` - Examples of generated ISO-compliant plans.
- `tests/` - Unit and integration tests to ensure computation and rendering accuracy.

---

## 🚀 Quick Start

### 1. Installation
Ensure you have Python 3.10+ installed.

```bash
# Clone the repository
git clone https://github.com/your-repo/theodolite-mcp.git
cd theodolite-mcp

# Install dependencies
pip install .
```

### 2. Experience the Demos
Run our showcase examples to see the rendering engine in action:

```bash
# Generate a professional construction site plan (A3)
PYTHONPATH=src python3 examples/demo_construction.py

# Generate the "Dream City" material showcase (A2)
PYTHONPATH=src python3 examples/demo_dream_city.py

# Run a full traverse adjustment task
PYTHONPATH=src python3 examples/demo_task.py
```
*Results will be saved in the root or specified output directory.*

---

## 🛠 Available Tools

### 🖋 Rendering & Visualization
- **`draw_plot_plan`**: Generates an ISO-compliant technical drawing. Supports standard formats (A0-A4), 23 languages, and professional styles.

### 📐 Survey Computation
- **`adjust_traverse_network`**: Performs Bowditch adjustment, handles misclosures, and generates Markdown reports.
- **`reduce_stadia_readings`**: Tacheometric reduction from stadia hair readings.
- **`compute_parcel_area`**: Precise area calculation using the Gauss polygon formula.

### 🧭 Geodesic Utilities & Conversions
- **`compute_inverse_geodetic_problem`**: Distance/Azimuth between two points.
- **`compute_forward_azimuth`** / **`compute_back_azimuth`**: Bearing calculations.
- **`dms_to_decimal_degrees`** / **`decimal_degrees_to_dms`**: Precise coordinate conversions.

---

## 📐 Industrial Compliance

This server is designed for engineering professionals. Unlike generic plotting libraries, our rendering engine ensures that every line weight, font height, and margin meets **ISO Technical Documentation** requirements, making outputs suitable for official site plans, blueprints, and engineering reports.

## 📄 License
This project is licensed under the MIT License. Technical font `osifont` is licensed under GNU LGPL.
