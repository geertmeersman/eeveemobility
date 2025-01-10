"""Models used by EeveeMobility."""

from __future__ import annotations

from typing import TypedDict


class EeveeMobilityConfigEntryData(TypedDict):
    """Config entry for the EeveeMobility integration."""

    email: str | None
    password: str | None
