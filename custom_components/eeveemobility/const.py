"""Constants used by EeveeMobility."""
from datetime import timedelta
import json
from pathlib import Path
from typing import Final

from homeassistant.const import Platform

PLATFORMS: Final = [Platform.SENSOR]

ATTRIBUTION: Final = "Data provided by Eevee Mobility"

COORDINATOR_UPDATE_INTERVAL = timedelta(minutes=15)
WEBSITE = "https://eeveemobility.com/"

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
