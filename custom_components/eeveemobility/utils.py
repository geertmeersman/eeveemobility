"""EeveeMobility utils."""
from __future__ import annotations

def sensor_name(string: str) -> str:
    """Format sensor name."""
    string = string.strip().replace("_", " ").title()
    return string
