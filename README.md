# Theodolite Survey MCP Server

An MCP server for processing theodolite survey field books (traverse adjustment and coordinate calculation).

## Features
- Traverse adjustment (Angular and Linear misclosure)
- Compass Rule adjustment
- Coordinate calculation
- Azimuth calculation
- DMS to Decimal degree conversion

## Installation
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
