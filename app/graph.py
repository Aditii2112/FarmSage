from __future__ import annotations

import os
from typing import Dict, Any, List, TypedDict

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

from app.models import GenerateRequest, Plan, ComparisonRow
from app.prompts import (
    WATER_SAVER_SYSTEM,
    YIELD_PRIORITY_SYSTEM,
    CARBON_PRIORITY_SYSTEM,
    USER_TEMPLATE,
)
from app.utils import safe_json_loads
from app.scoring import score_plan, choose_recommendation

load_dotenv()

def get_llm_strict():
    from langchain_openai import ChatOpenAI

    api_key = os.getenv("MORPH_API_KEY", "").strip()
    base_url = os.getenv("MORPH_BASE_URL", "https://api.morphllm.com/v1").strip()
    model = os.getenv("MORPH_MODEL", "morph-v3-fast").strip()

    if not api_key:
        raise RuntimeError("MORPH_API_KEY is not set. Add it to your .env and restart the server.")

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0.4,
    )



def stub_plan(strategy_key: str, req: GenerateRequest) -> Dict[str, Any]:
    crop = req.crop.lower()
    if strategy_key == "water_saver":
        return {
            "title": f"Water-Saver Plan for {req.crop.title()}",
            "summary": "Minimize irrigation demand using scheduling, mulching, and monitoring.\nMaintain acceptable yield with stress-aware adjustments.",
            "practices": [
                "Install or simulate soil moisture monitoring (sensor or manual tensiometer readings).",
                "Shift to early-morning irrigation; reduce evaporative losses.",
                "Mulch or maintain residue to reduce soil evaporation.",
                "Use regulated deficit irrigation only during tolerant growth stages.",
                "Fix leaks; pressure-check drip lines weekly.",
                "Improve uniformity: flush lines and check emitter clogging.",
                "Target fertigation to avoid excess vegetative growth.",
            ],
            "timeline": {
                "pre_season": ["Check irrigation uniformity (DU) and repair lines.", "Plan mulch/residue strategy."],
                "early_season": ["Establish moisture targets; irrigate to root-zone depth.", "Start weekly moisture checks."],
                "mid_season": ["Consider mild deficit only if crop stage allows.", "Irrigate in shorter, more frequent sets (drip)."],
                "late_season": ["Taper irrigation to reduce waste while protecting quality.", "Document water use and outcomes."],
            },
            "assumptions": [
                f"{req.crop.title()} grown in {req.location}.",
                f"Soil is {req.soil_type}; irrigation is {req.irrigation}.",
                "Relative estimates only (Low/Med/High buckets).",
            ],
            "risks": ["Heat stress if deficit irrigation is too aggressive.", "Uneven irrigation causing yield loss."],
            "mitigations": ["Avoid deficits during heat events.", "Use moisture checks + visual scouting to adjust quickly."],
        }

    if strategy_key == "yield_priority":
        return {
            "title": f"Yield-Priority Plan for {req.crop.title()}",
            "summary": "Maximize yield with tight nutrition, pest scouting, and consistent water.\nHigher inputs, stronger monitoring, fewer stress events.",
            "practices": [
                "Maintain consistent irrigation to avoid stress dips.",
                "Use split fertigation aligned to growth stages.",
                "Weekly scouting + IPM thresholds; act early.",
                "Optimize canopy management (pruning/training if relevant).",
                "Run a simple tissue/soil test cadence (even 1–2 times).",
                "Keep weed pressure low to reduce competition.",
                "Track operations and outcomes for rapid adjustments.",
            ],
            "timeline": {
                "pre_season": ["Plan fertility program and scouting cadence.", "Prep beds/rows for uniform establishment."],
                "early_season": ["Prioritize stand establishment; avoid early stress.", "Begin IPM scouting routine."],
                "mid_season": ["Peak fertigation + consistent water during critical stages.", "Rapid response to pests/disease."],
                "late_season": ["Maintain plant health to protect quality and harvest timing.", "Document yield drivers."],
            },
            "assumptions": [
                f"{req.crop.title()} grown in {req.location}.",
                "Inputs available for consistent fertility and monitoring.",
            ],
            "risks": ["Higher cost and labor demand.", "Potential over-irrigation if not monitored."],
            "mitigations": ["Use simple scheduling (ET-based or moisture checks).", "Prioritize top 2 yield drivers if labor-limited."],
        }

    return {
        "title": f"Carbon-Priority Plan for {req.crop.title()}",
        "summary": "Build soil carbon and resilience via cover crops, compost, and reduced disturbance.\nEmphasizes long-term soil health with moderate yield protection.",
        "practices": [
            "Add compost (rate tuned to budget) to increase organic matter.",
            "Introduce a seasonal cover crop (as appropriate) and terminate on time.",
            "Reduce tillage intensity where feasible.",
            "Maintain living roots/ground cover to reduce erosion.",
            "Use diverse rotations (or inter-row management) if possible.",
            "Implement nutrient management to reduce losses (right rate/time/place).",
            "Track soil indicators (OM%, infiltration) annually if possible.",
        ],
        "timeline": {
            "pre_season": ["Source compost/cover crop seed.", "Plan termination timing and equipment needs."],
            "early_season": ["Establish cover/ground cover strategy.", "Minimize soil disturbance passes."],
            "mid_season": ["Maintain residue/cover where feasible.", "Spot-treat issues instead of blanket actions if possible."],
            "late_season": ["Terminate cover crops to avoid unnecessary water competition.", "Record soil/field notes for next season."],
        },
        "assumptions": [
            f"{req.crop.title()} grown in {req.location}.",
            "Focus is soil health; yield may be slightly less optimized short-term.",
        ],
        "risks": ["Cover crop mismanagement can compete for water.", "More planning complexity."],
        "mitigations": ["Terminate cover crops early in dry years.", "Start on a small pilot acreage first."],
    }

# ---- LangGraph state ----
class GraphState(TypedDict, total=False):
    req: GenerateRequest
    farm_profile: Dict[str, Any]
    constraints: List[str]

    water_plan: Plan
    yield_plan: Plan
    carbon_plan: Plan

    plans: List[Plan]
    comparison: List[ComparisonRow]
    recommendation: Dict[str, Any]

def intake_node(state: GraphState) -> GraphState:
    req = state["req"]
    return {
        "farm_profile": {
            "crop": req.crop,
            "acres": req.acres,
            "soil_type": req.soil_type,
            "irrigation": req.irrigation,
            "location": req.location,
        },
        "constraints": req.constraints,
    }

def assumptions_node(state: GraphState) -> GraphState:
    # Placeholder hook: you could set crop baselines, local season windows, etc.
    return state

def make_strategy_node(strategy_key: str, system_prompt: str):
    def node(state: GraphState) -> GraphState:
        req = state["req"]
        user_prompt = USER_TEMPLATE.format(
            crop=req.crop,
            acres=req.acres,
            soil_type=req.soil_type,
            irrigation=req.irrigation,
            location=req.location,
            constraints=", ".join(req.constraints) if req.constraints else "none",
        )

        from langchain_core.messages import SystemMessage, HumanMessage

        try:
            llm = get_llm_strict()
            resp = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ])
            data = safe_json_loads(resp.content)
        except Exception as e:
            if req.allow_stub:
                data = stub_plan(strategy_key, req)
            else:
                raise RuntimeError(
                    f"LLM generation failed for {strategy_key}. "
                    f"Original error: {e}"
                )

        plan = Plan(
            key=strategy_key,  # type: ignore
            title=data["title"],
            summary=data["summary"],
            practices=data["practices"],
            timeline=data["timeline"],
            assumptions=data["assumptions"],
            risks=data["risks"],
            mitigations=data["mitigations"],
        )

        if strategy_key == "water_saver":
            return {"water_plan": plan}
        if strategy_key == "yield_priority":
            return {"yield_plan": plan}
        return {"carbon_plan": plan}

    return node


def scoring_node(state: GraphState) -> GraphState:
    req = state["req"]
    plans = [state["water_plan"], state["yield_plan"], state["carbon_plan"]]

    for p in plans:
        water_use, cost, soil_health, risk = score_plan(req, p)
        p.water_use = water_use
        p.cost = cost
        p.soil_health = soil_health
        p.risk = risk

    comparison = [
        ComparisonRow(
            plan_key=p.key,
            title=p.title,
            water_use=p.water_use,  # type: ignore
            cost=p.cost,            # type: ignore
            soil_health=p.soil_health,  # type: ignore
            risk=p.risk,            # type: ignore
        )
        for p in plans
    ]

    recommendation = choose_recommendation(req, plans)

    return {
        "plans": plans,
        "comparison": comparison,
        "recommendation": recommendation,
    }

def build_graph():
    g = StateGraph(GraphState)

    g.add_node("intake", intake_node)
    g.add_node("assumptions", assumptions_node)

    g.add_node("water_saver", make_strategy_node("water_saver", WATER_SAVER_SYSTEM))
    g.add_node("yield_priority", make_strategy_node("yield_priority", YIELD_PRIORITY_SYSTEM))
    g.add_node("carbon_priority", make_strategy_node("carbon_priority", CARBON_PRIORITY_SYSTEM))

    g.add_node("score_merge", scoring_node)

    g.set_entry_point("intake")
    g.add_edge("intake", "assumptions")

    # fan out (parallel branches)
    g.add_edge("assumptions", "water_saver")
    g.add_edge("assumptions", "yield_priority")
    g.add_edge("assumptions", "carbon_priority")

    # converge
    g.add_edge("water_saver", "score_merge")
    g.add_edge("yield_priority", "score_merge")
    g.add_edge("carbon_priority", "score_merge")

    g.add_edge("score_merge", END)

    return g.compile()
