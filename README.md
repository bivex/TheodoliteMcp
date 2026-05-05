# 📐 Theodolite Survey MCP Server

A professional-grade MCP server for processing theodolite survey field books, traverse adjustments, and **ISO-compliant** technical drawing generation.

![Construction Site Plan](construction_site_plan.png)
*Example: ISO-compliant plot plan generated automatically from survey data.*

## 🌟 Core Features

- **Precision Surveying:** Automated angular and linear misclosure adjustment using the Compass Rule.
- **ISO Standard Rendering:** Generates professional technical drawings (PNG/PDF) following strict international standards:
    - **ISO 5457:** Standard paper formats (A0-A4) with precise 20mm/10mm margins.
    - **ISO 7200:** Non-proportional title blocks (stamps) with absolute dimensions.
    - **ISO 3098:** Technical lettering using the specialized `osifont`.
    - **ISO 5455:** Strict engineering scales (1:50, 1:100, 1:500, etc.).
    - **ISO 129-1:** Smart dimensioning with automatic leaders for tight spaces.
- **Geodesic Logic:** Area calculation (Gauss formula), Azimuth calculations, and DMS/Decimal conversions.
- **Validation:** Automatic precision checks against industrial standards (1:2000, 1:5000).

## 🚀 Quick Start

### 1. Installation
Ensure you have Python 3.10+ installed.

```bash
# Clone the repository
git clone https://github.com/your-repo/theodolite-mcp.git
cd theodolite_mcp

# Install dependencies
pip install .
```

### 2. Run Demos
Experience the full pipeline from raw measurements to a finished technical drawing:

```bash
# Generate a professional construction site plan
PYTHONPATH=src python3 demo_construction.py

# Run a full traverse adjustment task
PYTHONPATH=src python3 demo_task.py
```

## 🛠 Available Tools

| Tool | Description |
| :--- | :--- |
| `render_plot_plan` | Generates an ISO-compliant technical drawing from points and zones. |
| `process_traverse` | Calculates adjusted coordinates from survey observations. |
| `calculate_azimuth` | Calculates the bearing between two coordinate points. |
| `convert_dms_to_decimal`| Converts Degrees-Minutes-Seconds to Decimal Degrees. |

## 📐 Industrial Compliance

This server is designed for professionals. Unlike generic plotting libraries, our rendering engine ensures that every line weight, font height, and margin meets **ISO Technical Documentation** requirements, making outputs suitable for official site plans and engineering reports.

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details. Technical font `osifont` is licensed under GNU LGPL.
