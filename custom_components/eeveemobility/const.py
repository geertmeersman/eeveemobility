"""Constants used by EeveeMobility."""

import json
from pathlib import Path
from typing import Final

from homeassistant.const import Platform

BASE_URL = "https://api.eeveeapp.com"
API_URL = f"{BASE_URL}/v2"
TOKEN_URL = f"{BASE_URL}/auth/token"
CLIENT_ID = 1
CLIENT_SECRET = "McXRSWON3XyaeXPVL3VrPNV4JEtMlcyXWkpRetCQ"
HEADERS = {}

PLATFORMS: Final = [Platform.SENSOR, Platform.DEVICE_TRACKER]

ATTRIBUTION: Final = "Data provided by Eevee Mobility"

manifestfile = Path(__file__).parent / "manifest.json"
with open(manifestfile) as json_file:
    manifest_data = json.load(json_file)

DOMAIN = manifest_data.get("domain")
NAME = manifest_data.get("name")
VERSION = manifest_data.get("version")
ISSUEURL = manifest_data.get("issue_tracker")

CUSTOM_HEADERS = {
    "User-Agent": f"Home Assistant Eevee Mobility Integration {VERSION}",
}

DEFAULT_SCAN_INTERVAL = 15
SCAN_INTERVAL_MIN = 15
SCAN_INTERVAL_MAX = 1440
WEBSITE = "https://eeveemobility.com/"

EVENTS_LIMIT = 50
EVENTS_EXCLUDE_KEYS = ["polyline", "graphs"]

STARTUP = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom component
If you have any issues with this you need to open an issue here:
{ISSUEURL}
-------------------------------------------------------------------
"""
