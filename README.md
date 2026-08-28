# FPL-AI

Experimental Fantasy Premier League (FPL) decision-support system combining data, prediction models, optimization and an AI reasoning layer.

> **Status:** Active development / research prototype  
> **Current strategic direction:** Replace the V1–V5 brute-force optimizer with a fast constraint-based optimizer and build a reliable weekly decision pipeline.

## Vision

The end product should not merely answer “who are the 15 best players?”

It should answer:

> Given my current squad, budget, fixtures, expected minutes, player roles, risk, future schedule and available chips, what is the best FPL decision?

The system is deliberately split into two layers:

- **Python/model layer:** data collection, feature engineering, predictions, xMins, optimization, constraints and structured outputs.
- **AI/ChatGPT layer:** interpretation, context, explanation, challenge of model results, transfer/captain/chip discussion.

**Model = calculation and search. AI = interpretation, context and decision support.**

## What already exists

The project has successfully built:

- current FPL player-data ingestion
- GW1 historical live-data retrieval
- GW2 player predictions
- availability features
- xMins/start probability features
- rotation-risk features
- initial squad/Wildcard optimizer experiments

Recent successful pipeline outputs have contained 616 players.

## V1–V5: what we learned

V1–V5 are **development versions, not different Wildcards**.

All versions attempted variants of brute-force candidate generation and positional combination. They became too slow because the search space exploded.

Typical progression:

- V1: ~140 optimizer candidates; pandas/DataFrame operations became the bottleneck.
- V2: stronger availability/xMins filtering, but combination search remained slow.
- V3: positional combinations such as 45 GKP, 1,000 DEF, 1,000 MID, 816 FWD; combining groups remained expensive.
- V4: more aggressive filtering; still too slow during cross-position combination.
- V5: 97 active candidates, with 66 GKP / 8,000 DEF / 8,000 MID / 1,140 FWD combinations; still reached hundreds of thousands of partial DEF combinations and stalled during group combination.

**Conclusion:** Do not keep patching brute-force. Change the optimization method.

## Current principle

> **Do not optimize for maximum complexity. Optimize for maximum useful signal per unit of computation.**

The target is a model that captures important FPL mechanics while running in seconds rather than several minutes.

## Planned pipeline

FPL API → current data → historical data → features → availability/xMins → predictions → fixtures/context → squad/transfer/chip optimizer → weekly report → AI analysis.

## Major planned capabilities

### Optimizer
- MILP/ILP or another exact/efficient constraint solver
- 15-player squad
- 2 GKP / 5 DEF / 5 MID / 3 FWD
- budget constraint
- max 3 players per club
- valid starting XI and bench
- captain/vice-captain
- normal-transfer mode
- Wildcard mode
- Free Hit mode
- Bench Boost mode
- multi-GW objective
- optional risk/differential mode

### Player point routes

The optimizer must understand *why* players score, not treat same-position players as interchangeable.

**DEF**
- clean sheets
- goals
- assists
- bonus
- defensive contribution / DefCon
- set pieces
- attacking positioning
- crosses/key passes
- expected minutes

**MID**
- goals/xG
- assists/xA
- shots
- chances created/key passes
- set pieces
- penalties
- bonus
- clean-sheet potential
- defensive contribution where relevant
- role and expected minutes

**FWD**
- goals/xG
- shots/shots in box
- big chances
- assists/xA
- penalties
- bonus
- expected minutes
- fixture context

**GKP**
- clean-sheet probability
- saves
- goals conceded
- bonus
- penalty-save potential
- expected minutes
- value

Useful archetypes include offensive full-backs, defensive-action monsters, set-piece centre-backs, clean-sheet defenders, elite attackers, creators, talismans and value picks.

### xMins / availability
The current implementation has availability, xMins, start probability and rotation-risk features, but the current xMins logic is not considered final.

Future target: a proper minutes model using recent minutes, starts, rotation patterns, injury status, squad context and fixture congestion.

### Uncertainty and ownership
Add:
- prediction uncertainty / variance
- ownership
- Effective Ownership where useful
- safe vs aggressive optimization modes
- captaincy risk/reward
- differential strategy

### Multi-Gameweek planning
Wildcard should not automatically maximize only one Gameweek.

Use a short horizon such as GW+1 through GW+5 with decreasing weights, then validate the weighting historically.

### Chip strategy
The system should decide **whether a chip should be used**, not just generate a chip team.

Compare:
- use Wildcard now
- keep Wildcard and use normal transfers
- save for a better future opportunity
- other available chip strategies

### Fixtures/context
Prefer stronger underlying team-strength/context signals over relying only on coarse FDR.

Potential inputs:
- xG scored/conceded
- home/away splits
- fixture run
- clean-sheet probability
- attacking environment
- rotation/congestion

### Backtesting
Before trusting the system, validate:
- predicted vs actual player points
- predicted vs actual minutes
- optimizer decisions vs actual Gameweeks
- value models
- captain model
- transfer strategy
- chip strategy

## Automation goal

Eventually one weekly runner should perform the pipeline automatically. The user should not need to open and run many scripts manually every Gameweek.

## GitHub goal

The repository should be clean and understandable.

Keep V1–V5 as historical reference under `legacy/` or git history rather than as competing current scripts.

Include:
- README
- architecture documentation
- setup/dependencies
- tests
- current pipeline
- legacy versions
- example outputs
- clear data/privacy notes

## Important implementation rule

Do not start by writing another giant optimizer script.

First inspect the current codebase, identify reusable components, define clean data contracts, then implement the new optimizer as a separate, testable module.

