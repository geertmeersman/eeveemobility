"""Constants used by EeveeMobility."""
import json
from pathlib import Path
from typing import Final

from homeassistant.const import Platform

PLATFORMS: Final = [Platform.SENSOR, Platform.DEVICE_TRACKER]

ATTRIBUTION: Final = "Data provided by Eevee Mobility"

CUSTOM_HEADERS = {
    "User-Agent": "Home Assistant Eevee Mobility Integration",
}

DEFAULT_SCAN_INTERVAL = 15
SCAN_INTERVAL_MIN = 15
SCAN_INTERVAL_MAX = 1440
WEBSITE = "https://eeveemobility.com/"

EVENTS_LIMIT = 50
EVENTS_EXCLUDE_KEYS = ["polyline", "graphs"]

manifestfile = Path(__file__).parent / "manifest.json"
with open(manifestfile) as json_file:
    manifest_data = json.load(json_file)

DOMAIN = manifest_data.get("domain")
NAME = manifest_data.get("name")
VERSION = manifest_data.get("version")
ISSUEURL = manifest_data.get("issue_tracker")
STARTUP = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom component
If you have any issues with this you need to open an issue here:
{ISSUEURL}
-------------------------------------------------------------------
"""
