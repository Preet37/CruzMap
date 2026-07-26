"""Shared severity -> color/icon mapping used across the dashboard."""

SEVERITY_COLOR = {
    "low": "#3fb950",
    "medium": "#d29922",
    "high": "#db6d28",
    "critical": "#f85149",
}

SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}

CATEGORY_ICON = {
    "pothole": "\U0001F573️",
    "coastal_erosion": "\U0001F30A",
    "storm_drain_debris": "\U0001F6B0",
    "cracked_sidewalk": "\U0001F6B6",
    "fallen_tree": "\U0001F333",
    "other": "⚠️",
}


def color_for(severity: str) -> str:
    return SEVERITY_COLOR.get(severity, "#8b949e")


def icon_for(category: str) -> str:
    return CATEGORY_ICON.get(category, "⚠️")
