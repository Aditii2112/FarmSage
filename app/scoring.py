from __future__ import annotations
from typing import Dict, Tuple, List
from app.models import Plan, Bucket, CostBucket, SoilImpact, GenerateRequest

_BUCKETS: List[Bucket] = ["Low", "Med", "High"]

def _clamp_bucket(idx: int) -> Bucket:
    return _BUCKETS[max(0, min(2, idx))]

def baseline_water_bucket(crop: str) -> Bucket:
    c = crop.lower()
    if c in ["rice", "alfalfa"]:
        return "High"
    if c in ["almond", "walnut", "grape", "tomato", "lettuce", "corn"]:
        return "Med"
    return "Med"

def irrigation_adjustment(irrigation: str) -> int:
    i = irrigation.lower()
    if i == "drip":
        return -1
    if i == "flood":
        return +1
    return 0

def score_plan(req: GenerateRequest, plan: Plan) -> Tuple[Bucket, CostBucket, SoilImpact, Bucket]:
    """
    Heuristic rubric so you can ship quickly.
    Uses keywords from practices/timeline to adjust relative buckets.
    """
    text = " ".join(plan.practices + sum(plan.timeline.values(), [])).lower()

    # Water
    base = _BUCKETS.index(baseline_water_bucket(req.crop))
    w = base + irrigation_adjustment(req.irrigation)

    if "deficit" in text or "regulated deficit" in text:
        w -= 1
    if "mulch" in text:
        w -= 1
    if "soil moisture sensor" in text or "sensor" in text:
        w -= 1
    if "cover crop" in text and "terminate" not in text:
        # cover crops can increase water use if mismanaged; keep small penalty
        w += 0

    water_use = _clamp_bucket(w)

    # Cost
    cost_score = 1  # start at $$
    if "sensor" in text or "automation" in text or "variable rate" in text:
        cost_score += 1
    if "compost" in text or "cover crop" in text:
        cost_score += 0
    if "new equipment" in text:
        cost_score += 1
    if "do nothing" in text:
        cost_score -= 1

    cost: CostBucket = ["$", "$$", "$$$"][max(0, min(2, cost_score))]

    # Soil health
    soil_score = 0
    if "cover crop" in text:
        soil_score += 1
    if "compost" in text:
        soil_score += 1
    if "reduced till" in text or "no-till" in text:
        soil_score += 1
    if "bare soil" in text or "heavy till" in text or "intensive till" in text:
        soil_score -= 1

    soil_health: SoilImpact
    if soil_score >= 2:
        soil_health = "++"
    elif soil_score == 1:
        soil_health = "+"
    elif soil_score == 0:
        soil_health = "0"
    else:
        soil_health = "-"

    # Risk
    # Water-saver deficit -> heat stress risk
    risk_score = 1  # Med
    if plan.key == "water_saver" and ("deficit" in text or "regulated deficit" in text):
        risk_score += 1
    if plan.key == "carbon_priority" and "cover crop" in text:
        risk_score += 0  # could add slight pest risk, but keep neutral
    if "ipm" in text or "scouting" in text:
        risk_score -= 0  # neutral
    if "heat" in " ".join(plan.risks).lower():
        risk_score += 0

    risk = _clamp_bucket(risk_score)

    return water_use, cost, soil_health, risk

def choose_recommendation(req: GenerateRequest, plans: List[Plan]) -> Dict:
    """
    Simple rule: respect explicit constraints first; else choose balanced.
    """
    constraints = set(req.constraints)

    # Prefer plan aligned with constraint
    if "water_limit" in constraints:
        winner = "water_saver"
        reason = "You selected a water limit, so the Water-Saver plan best matches your constraint."
    elif "maximize_carbon" in constraints:
        winner = "carbon_priority"
        reason = "You prioritized carbon/soil outcomes, so the Carbon-Priority plan fits best."
    elif "maximize_yield" in constraints:
        winner = "yield_priority"
        reason = "You prioritized yield, so the Yield-Priority plan fits best."
    else:
        # balanced: choose the plan with lowest risk + not $$$ if possible
        def rank(p: Plan) -> Tuple[int, int, int]:
            risk_rank = {"Low": 0, "Med": 1, "High": 2}[p.risk or "Med"]
            cost_rank = {"$": 0, "$$": 1, "$$$": 2}[p.cost or "$$"]
            water_rank = {"Low": 0, "Med": 1, "High": 2}[p.water_use or "Med"]
            return (risk_rank, cost_rank, water_rank)

        winner_plan = sorted(plans, key=rank)[0]
        winner = winner_plan.key
        reason = "No strict constraint selected, so I chose the most balanced option (lower risk and reasonable cost)."

    return {
        "winner": winner,
        "reason": reason,
        "next_steps": [
            "Review the checklist for your chosen plan.",
            "Adjust 1–2 practices based on your budget/labor reality.",
            "Run a small pilot block (e.g., 1–2 acres) before scaling if adopting new practices.",
        ],
        "disclaimer": "This is a planning assistant for hackathon/demo use; validate with local agronomy guidance before real-world decisions.",
    }
