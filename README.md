# Theodolite Survey MCP Server

An MCP server for processing theodolite survey field books (traverse adjustment and coordinate calculation).

## Features
- **Traverse Adjustment:** Angular and Linear misclosure adjustment (Compass Rule).
- **Coordinate Calculation:** X (North), Y (East) generation.
- **Area Calculation:** Automatic area calculation for closed traverses using the Gauss formula.
- **Precision Validation:** Automated status report based on industrial standards (1:2000, 1:5000).
- **Surveying Utilities:** Azimuth calculation, DMS/Decimal conversions.

## Demonstration Task
The repository includes `demo_task.py`, which showcases a real-world scenario: **Planning a construction site.**

It performs the following steps:
1. Converts field DMS measurements to decimal degrees.
2. Processes a closed traverse around a site.
3. Calculates adjusted coordinates, total area, and misclosure.
4. Evaluates whether the precision meets professional standards.
5. Determines the azimuth for building axis orientation.

Run the demo:
```bash
PYTHONPATH=src ./venv/bin/python3 demo_task.py
```
```bash
pip install -e .
```

## Running the server
```bash
python -m theodolite_mcp.infrastructure.mcp_server
```

## Tools
- `process_traverse`: Calculates coordinates from survey observations.
- `calculate_azimuth`: Calculates bearing between two points.
- `convert_dms_to_decimal`: Degrees, Minutes, Seconds -> Decimal.
- `convert_decimal_to_dms`: Decimal -> Degrees, Minutes, Seconds.
