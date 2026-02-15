# 🌱 Farm Sage

AI-Powered Climate-Smart Crop Planning

Farm Sage is a multi-agent AI system that helps farmers generate climate-smart crop strategies in seconds.
It simulates tradeoffs between water efficiency, yield maximization, and soil carbon health, then ranks strategies using a composite KPI score tailored to real-world constraints.

Built using LangGraph multi-agent orchestration + Morph LLM, Farm Sage transforms complex agricultural decision-making into a clear, data-driven recommendation dashboard.

Demo: https://drive.google.com/file/d/1j7UVs-Q60YhjKRXQYOyR2RzFGxnN1kUd/view?usp=sharing

![Workflow Graph](https://github.com/Aditii2112/FarmSage/blob/main/assets/Dasshboard.png?raw=true)

# Why Farm Sage?

Farmers today face impossible tradeoffs:

✔Water scarcity

✔Rising input costs

✔Climate volatility

✔Soil degradation

Yet most planning tools are static, single-objective, or spreadsheet-based.

Farm Sage changes that.

It runs three intelligent strategy agents in parallel — Water Saver, Yield Priority, and Carbon Priority — and merges them into a ranked, constraint-aware recommendation using a transparent composite scoring system.

Instead of guesswork, farmers get:

✔ Structured seasonal plans

✔ Risk analysis

✔ Soil impact insights

✔ A ranked best-fit strategy

# System Architecture

Farm Sage is powered by a LangGraph multi-agent workflow:


![Workflow Graph](https://github.com/Aditii2112/FarmSage/blob/main/assets/workflow_graph.png?raw=true)




# Flow Explanation

Intake Node – Captures farm profile & constraints

Assumptions Node – Establishes contextual baselines

✔Parallel Strategy Agents

✔Water Saver

✔Yield Priority

✔Carbon Priority

Score & Merge Node

Computes water, cost, soil, risk metrics

Applies constraint-weighted composite KPI

Selects final recommendation

This architecture enables parallel AI reasoning + structured merging, rather than single-response generation.

# Composite KPI Scoring

Each plan is scored using:

Score = f(Water, Cost, Soil Health, Risk)
        + Constraint Weighting


Lower water use, lower cost, lower risk, and stronger soil health increase the score.
User-selected constraints dynamically adjust weights to personalize recommendations.

This makes the system:

Transparent

Adjustable

Scientifically defensible

Demo-ready for judges

# Tech Stack
Backend: Python , FastAPI, LangGraph , LangChain, Morph LLM API, Pydantic models

# Frontend

Vanilla JS, Glassmorphism dashboard UI, Composite KPI visualization, Interactive scenario builder

# Architecture

Parallel AI agents

Structured JSON enforcement

Deterministic scoring layer

Agent orchestration via state graph


# How To Run
1️⃣ Install Dependencies
pip install -r requirements.txt

2️⃣ Add Environment Variables

Create .env:

MORPH_API_KEY=your_key_here
MORPH_BASE_URL=https://api.morphllm.com/v1
MORPH_MODEL=morph-v3-fast

3️⃣ Run Server
uvicorn app.main:app --reload


Visit:

[http://localhost:8000](http://127.0.0.1:8000/)


# Vision

Farm Sage is designed as a foundation for:

Climate-adaptive farm planning

ESG-aligned soil regeneration modeling

Decision-support tools for agricultural cooperatives

Scalable AI advisory systems
