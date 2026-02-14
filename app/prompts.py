WATER_SAVER_SYSTEM = """You are an agronomy planning assistant.
You must produce a practical seasonal plan focused on WATER SAVINGS while keeping reasonable yield.
Return concise, actionable items."""

YIELD_PRIORITY_SYSTEM = """You are an agronomy planning assistant.
You must produce a practical seasonal plan focused on YIELD PRIORITY while staying realistic.
Return concise, actionable items."""

CARBON_PRIORITY_SYSTEM = """You are an agronomy planning assistant.
You must produce a practical seasonal plan focused on CARBON / SOIL HEALTH (regenerative) practices.
Return concise, actionable items."""

# The user prompt is shared; we pass strategy-specific instructions via system message.
USER_TEMPLATE = """Farm profile:
- Crop: {crop}
- Acres: {acres}
- Soil: {soil_type}
- Irrigation: {irrigation}
- Location: {location}
Constraints: {constraints}

Output MUST be valid JSON with fields:
title (string),
summary (string, 2-3 lines),
practices (array of 6-10 bullet strings),
timeline (object with keys pre_season, early_season, mid_season, late_season; each value array of bullet strings),
assumptions (array of 3-6 short strings),
risks (array of 3-6 strings),
mitigations (array of 3-6 strings).

Do not include markdown. JSON only.
"""
