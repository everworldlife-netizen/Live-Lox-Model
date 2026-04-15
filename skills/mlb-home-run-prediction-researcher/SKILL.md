---
name: mlb-home-run-prediction-researcher
description: Use this skill when the user asks for MLB home run predictions, shortlist picks, or matchup-based HR probability analysis using Statcast, BDL GOAT tier API context, pitcher vulnerability, park effects, weather, lineup context, and bullpen state.
---

# MLB Home Run Prediction Researcher

Use this skill to produce context-rich, evidence-based MLB home run probability projections.

## Trigger Conditions
Use this skill when the user asks for any of the following:
- “Best HR picks today/tonight” or “home run ladder”
- Batter-level HR probability for specific games
- Matchup-based HR analysis (batter vs starter/bullpen)
- Statcast-driven HR projection with weather and park effects

## Required Workflow

1. **Collect game context first**
   - Confirm slate date and timezone explicitly.
   - Identify probable starters, venue, and expected roof status.
   - Pull projected/confirmed lineup spots (especially batting 2–5).
   - Pull MLB BDL GOAT tier API context for current slate entities (team/player identifiers, schedule alignment, and any provided projection metadata).

2. **Build batter power profile (primary weight)**
   - Barrel%, hard-hit%, avg/max/P90 EV, sweet-spot launch angle share
   - HR/FB vs xHR/FB, ISO trend, fly-ball trend, xSLG/xwOBA
   - Recency weighting: 40% last 14 days, 30% last 30, 20% season, 10% career
   - Regress unstable small samples toward baseline (Bayesian shrinkage)

3. **Model pitcher vulnerability (critical context)**
   - HR/9, HR/FB allowed, EV/barrel allowed
   - Pitch mix and pitch-type HR susceptibility
   - Handedness splits and zone-location risk
   - Velo/spin trend changes across recent starts
   - Times-through-order adjustment (1.00 / 1.05 / 1.15)

4. **Apply environment multipliers**
   - Park factor (1y/3y/5y blend)
   - Dimensions/altitude/roof state
   - Weather: temperature, wind vector, pressure, humidity
   - Air-density adjustment from temp + humidity + pressure + altitude

5. **Add situational and bullpen effects**
   - Fatigue/travel/rest and day-night split context
   - Injury return dampening if recently off IL
   - Bullpen usage last 3 days and likely reliever HR susceptibility

6. **Generate prediction outputs**
   For each batter:
   - Base HR probability (per PA)
   - Game HR probability (~4 PA; adapt if lineup slot changes expected PA)
   - Confidence tier: **ELITE / STRONG / LEAN / FADE**
   - One key driver
   - Risk factors that could invalidate edge

7. **Cross-source reconciliation before final answer**
   - Reconcile Baseball Savant/FanGraphs values with MLB BDL GOAT tier API outputs.
   - If source discrepancies are material, prefer Statcast-grounded contact-quality metrics and document the discrepancy.
   - Surface any stale or missing BDL fields as an explicit confidence downgrade.

## Data Source Priority
1. Baseball Savant (Statcast) — contact quality ground truth
2. FanGraphs — advanced metrics and split context
3. MLB BDL GOAT tier API — slate-level IDs, projection context, and integration bridge
4. MLB/Rotowire lineups + status feeds — role and batting-order confirmation
5. Weather providers (e.g., weather.gov) — game-time conditions

## Multipliers and Guardrails
- Park multiplier: **0.70–1.40**
- Weather multiplier: **0.85–1.20**
- Pitcher vulnerability multiplier: **0.60–1.50**
- Fatigue/rest multiplier: **0.90–1.10**

## Edge-Case Checklist
Before finalizing picks, verify:
- Opener/bulk pitcher risk
- Doubleheader context
- Recent stuff change (velo/spin/new pitch)
- Umpire zone tendency if available
- Elevation outlier venue

## Anti-Patterns (Do Not Use)
- “Due for a HR” reasoning
- Overweighting career stats vs recency
- Ignoring park + weather compounding effects
- Treating small BvP samples as signal (<15 PA)

## Response Format
Use a concise table for ranked picks, then short notes:

| Rank | Batter | Opp Pitcher | Base HR/PA | Game HR Prob | Tier | Key Driver | Main Risk |
|---|---|---|---:|---:|---|---|---|

Then include:
- Brief assumptions list (lineups/weather/roof status timestamps)
- A “what could change before first pitch” section
- If data is incomplete, clearly label the uncertainty and downgrade confidence
