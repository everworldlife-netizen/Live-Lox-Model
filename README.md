# Live Lox (Pregame Edition)

**NBA Pregame Projections & Insights – An Intelligent Friend Before Tipoff**

Live Lox is a production-ready, full-stack application designed to deliver expertly crafted pregame player projections and team insights. Built with modern tech (Next.js, FastAPI, Postgres, Redis), it emphasizes clarity, confidence, and process-based NBA analysis.

## Key Features

✅ **Pregame Only** – No live play-by-play, no in-game updates; perfect clarity before tipoff  
✅ **Expert Explanations** – Every projection includes "why this matters" and "what could change" in plain English  
✅ **Confidence Cues** – HIGH / MEDIUM / LOW confidence labels backed by transparent heuristics  
✅ **Smart Toggles** – "If player OUT?", "Close game?", "Blowout risk?" – instant client-side recalculation  
✅ **Streaks & Probability** – Evaluate fragility of hot streaks; conditional probability models for role changes  
✅ **Projection Snapshots** – Timestamped runs stored for future comparison vs. actuals; enables continuous improvement  

## Tech Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| Frontend | Next.js 15 (App Router) + TypeScript + Shadcn UI + Tailwind | Type-safety, premium UX, fast prototyping |
| Backend | FastAPI (Python) + Pydantic | REST clarity, async-friendly, validation |
| Database | Postgres + Prisma ORM | Relational integrity, type-safe queries, easy migrations |
| Cache | Redis | API rate-limit buffering, projection caching |
| Workers | APScheduler / Celery (v1.1) | Scheduled projection runs |
| Auth | JWT via NextAuth.js (internal) | Lightweight, Prisma-friendly |
| Hosting | Docker Compose (local), Vercel + Railway (production) | Reproducible, scalable |

## Quick Start

### Prerequisites
- Docker & Docker Compose
- - Node.js 18+ (for local frontend dev)
  - - Python 3.11+ (for local API dev)
    - - PostgreSQL 14+ (if not using Docker)
     
      - ### Local Development (Docker Compose)
     
      - ```bash
        # Clone
        git clone https://github.com/everworldlife-netizen/Live-Lox-Model.git
        cd Live-Lox-Model

        # Create .env file (see apps/api/.env.example and apps/web/.env.example)
        cp apps/api/.env.example apps/api/.env
        cp apps/web/.env.example apps/web/.env

        # Start all services (postgres, redis, api, web)
        docker-compose up --build

        # Frontend: http://localhost:3000
        # API: http://localhost:8000
        # API Docs: http://localhost:8000/docs
        ```

        ### Manual Setup (No Docker)

        See [DEPLOYMENT.md](./DEPLOYMENT.md) for full local setup, database migrations, and production deployment instructions.

        ## Project Structure

        ```
        live-lox-pro/
        ├── apps/
        │   ├── api/              # FastAPI backend (Python)
        │   │   ├── app/
        │   │   │   ├── main.py              # FastAPI app entry
        │   │   │   ├── config.py            # Settings
        │   │   │   ├── routes/              # API endpoints
        │   │   │   ├── services/            # Business logic (Ball Don't Lie, projections, cache)
        │   │   │   ├── models/              # Pydantic schemas
        │   │   │   └── utils/               # Helpers
        │   │   ├── tests/                   # Pytest suite
        │   │   ├── requirements.txt
        │   │   ├── Dockerfile
        │   │   └── .env.example
        │   │
        │   └── web/              # Next.js frontend (TypeScript)
        │       ├── app/
        │       │   ├── tonight/              # Main slate view
        │       │   ├── game/[gameId]/        # Game detail + player projections
        │       │   └── player/[playerId]/    # Player deep dive (v1.1)
        │       ├── components/               # Reusable UI (Shadcn-based)
        │       ├── lib/                      # API client, types, utils
        │       ├── public/                   # Static assets
        │       ├── Dockerfile
        │       ├── tailwind.config.js
        │       └── .env.example
        │
        ├── packages/
        │   └── db/
        │       ├── prisma/
        │       │   └── schema.prisma         # Shared database schema
        │       └── migrations/               # Prisma migrations
        │
        ├── docker-compose.yml                # Local dev orchestration
        ├── .gitignore
        ├── README.md (this file)
        └── DEPLOYMENT.md                     # Production setup & CI/CD
        ```

        ## API Overview

        ### Core Endpoints

        **GET /api/v1/health**
        Health check.

        **GET /api/v1/slate?date=YYYY-MM-DD**
        Fetch tonight's slate of games.

        ```json
        {
          "date": "2024-12-25",
          "games": [
            {
              "id": "game_123",
              "date": "2024-12-25",
              "startTime": "2024-12-25T19:30:00Z",
              "homeTeam": { "id": "1", "name": "Lakers", "abbrev": "LAL" },
              "awayTeam": { "id": "2", "name": "Celtics", "abbrev": "BOS" },
              "status": "scheduled"
            }
          ],
          "runTimestamp": null
        }
        ```

        **POST /api/v1/projections/run**
        Trigger projection run (async in v1.1).

        **GET /api/v1/projections/latest?date=YYYY-MM-DD**
        Fetch latest projections for a date with explanations.

        ```json
        {
          "id": "run_12345",
          "runTimestamp": "2024-12-25T18:00:00Z",
          "slateDate": "2024-12-25",
          "version": "v1",
          "projections": [
            {
              "id": "proj_456",
              "playerId": "player_789",
              "playerName": "LeBron James",
              "gameId": "game_123",
              "minutesProj": 32.5,
              "minutesStdDev": 4.2,
              "ptsProj": 24.3,
              "rebProj": 8.1,
              "astProj": 7.2,
              "praProj": 39.6,
              "confidence": "HIGH",
              "reasons": [
                "Stable usage from last 10 games (consistent 32.8 min/game)",
                "Opponent (Celtics) ranks 22nd in pace – fewer possessions expected, but elite 108.9 DRTG limits scoring upside"
              ],
              "risks": [
                "Questionable on injury report – 85% projection if plays; if OUT, role vacuum impacts team spacing"
              ],
              "injuryStatus": "questionable",
              "seasonAvgPts": 24.1,
              "recentAvgPts": 25.2
            }
          ],
          "assumptions": {
            "pace_adjustment_factor": 0.95,
            "blowout_probability": 0.08,
            "minutes_downgrade_for_questionable": 0.85
          }
        }
        ```

        **GET /api/v1/player/{playerId}**
        Player profile + recent stats + streaks.

        ### Swagger/OpenAPI Docs
        Visit http://localhost:8000/docs (after running API).

        ## Projection Logic (v1)

        ### Inputs
        - **Season baseline**: Per-game averages from team's current season
        - - **Recent form**: Last 10 games (weighted 0.4), season avg (weighted 0.6)
          - - **Opponent context**: Defensive rating per position (if available from advanced stats)
            - - **Pace adjustment**: Team pace vs. opponent pace (Ball Don't Lie doesn't expose directly; proxy via rankings)
              - - **Injury status**: Questionable (-15%), out (0%), etc.
                - - **Minutes estimate**: Starter (expected 30–35 min) vs. bench (15–22 min) based on role inference
                 
                  - ### Calculation (Example: Points)
                 
                  - ```
                    ppg = (0.6 × season_avg_pts + 0.4 × recent_avg_pts)
                        × (minutes_proj / baseline_minutes)
                        × pace_factor
                        × defense_factor
                    ```

                    Where:
                    - `pace_factor = opponent_pace / 100` (normalized to league average)
                    - - `defense_factor = 110 / opponent_drtg` (lower defense rating = smaller multiplier)
                     
                      - ### Confidence Rules
                     
                      - | Level | Criteria |
                      - |-------|----------|
                      - | **HIGH** | 10+ games played, <15% minutes variance, healthy, clear role |
                      - | **MEDIUM** | 5–9 games, 15–25% variance, or mild injury concern |
                      - | **LOW** | <5 games, >25% variance, out/questionable, major role change |
                     
                      - ### Why This Matters
                     
                      - ✨ **Transparent**: Each projection shows the formula; fans & analysts can audit.
                      - ✨ **Process-based**: Emphasizes repetition of actions (consistent usage) over noise.
                      - ✨ **Conditional**: Injuries, blowout risk, pace – all adjustable and explained.
                     
                      - See [PROJECTION_GUIDE.md](./PROJECTION_GUIDE.md) for deep dives on advanced models (v1.1: conditional probabilities, role-based adjustments, RAG explanations).
                     
                      - ## Client-Side Toggles (Instant Feedback)
                     
                      - When viewing a game, users can toggle scenarios to see instant recalculation:
                     
                      - - **"If [Player] OUT"**: Removes player from slate, recalculates usage vacuum impact on teammates
                        - - **"Close Game"**: Adjusts minutes upward (higher stakes), reduces blowout downgrade
                          - - **"Blowout Risk"**: Reduces projected minutes for bench players if team strength delta >15%
                           
                            - These use React state + stored assumptions for sub-millisecond feedback.
                           
                            - ## Database Schema
                           
                            - See `packages/db/prisma/schema.prisma` for the full Prisma schema. Key tables:
                           
                            - - **games**: Game records (id, date, teams, status)
                              - - **players**: Player roster (id, name, team, position)
                                - - **projection_runs**: Timestamped projection batches
                                  - - **player_projections**: Individual player projections + confidence + explanations
                                    - - **assumptions**: Metadata per run (pace factor, blowout threshold, etc.)
                                      - - **player_stats**: Historical stats for evaluation (v1.1 feature)
                                       
                                        - ## Testing
                                       
                                        - ### Frontend (Jest + React Testing Library)
                                        - ```bash
                                          cd apps/web
                                          npm run test
                                          ```

                                          ### Backend (Pytest)
                                          ```bash
                                          cd apps/api
                                          pip install -r requirements-dev.txt
                                          pytest tests/ -v
                                          ```

                                          ## Deployment

                                          ### Production (Vercel + Railway)

                                          1. **Frontend**: Deploy `apps/web` to Vercel (auto-builds on push)
                                          2. 2. **API**: Deploy `apps/api` to Railway or your VPS (see [DEPLOYMENT.md](./DEPLOYMENT.md))
                                             3. 3. **Database**: Managed Postgres (Railway, AWS RDS, etc.)
                                                4. 4. **Redis**: Managed Redis (Railway, Upstash, etc.)
                                                  
                                                   5. See [DEPLOYMENT.md](./DEPLOYMENT.md) for step-by-step production setup, CI/CD, and monitoring.
                                                  
                                                   6. ## Roadmap
                                                  
                                                   7. ### v1 (Current)
                                                   8. ✅ Pregame-only slate + game cards
                                                   9. ✅ Basic player projections (PTS, REB, AST, MIN)
                                                   10. ✅ Confidence labels (HIGH / MEDIUM / LOW)
                                                   11. ✅ "Why" & "what could break" explanations
                                                   12. ✅ Client-side scenario toggles
                                                   13. ✅ Projection snapshots for evaluation
                                                   14. ✅ Ball Don't Lie integration + caching
                                                  
                                                   15. ### v1.1 (Next)
                                                   16. 🚀 Cron jobs for automatic projection runs (9 AM, 4 PM, 6:30 PM ET)
                                                   17. 🚀 Deep player profiles with streak charts
                                                   18. 🚀 Advanced projection models (conditional probabilities, role-based variance)
                                                   19. 🚀 Injury impact modeling (usage vacuum, team spacing changes)
                                                   20. 🚀 Comparison: projections vs. actuals (model evaluation dashboard)
                                                   21. 🚀 RAG for smart, contextual explanations (fine-tuned on NBA process tape)
                                                  
                                                   22. ### v2+
                                                   23. 💡 League-wide model sharing (GitHub/API for analysts)
                                                   24. 💡 Custom league settings (scoring, lineup constraints)
                                                   25. 💡 Player comps (cluster players by role, age, stats)
                                                   26. 💡 Fantasy optimizer integration
                                                   27. 💡 Mobile app (React Native)
                                                  
                                                   28. ## Contributing
                                                  
                                                   29. We welcome contributions! Please:
                                                  
                                                   30. 1. Fork the repo
                                                       2. 2. Create a feature branch (`git checkout -b feat/your-feature`)
                                                          3. 3. Write tests (backend: Pytest, frontend: Jest)
                                                             4. 4. Commit with clear messages
                                                                5. 5. Open a PR with a description
                                                                  
                                                                   6. See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.
                                                                  
                                                                   7. ## FAQ
                                                                  
                                                                   8. **Q: Why only pregame?**
                                                                   9. A: Pregame projections are where the most value is. Live updates require different infrastructure (websockets, real-time stats) and muddy the clarity. Our focus is deep, honest pregame insights.
                                                                  
                                                                   10. **Q: How do you handle player injuries?**
                                                                   11. A: We flag injuries from Ball Don't Lie (questionable, probable, out) and apply downgrade factors (e.g., –15% for questionable). In v1.1, we'll model usage vacuum (if a player is out, who gets their minutes?).
                                                                  
                                                                   12. **Q: Can I use this for DFS/betting?**
                                                                   13. A: Yes, but with caution. Projections are tools, not guarantees. Always do your own research and never bet more than you can afford to lose.
                                                                  
                                                                   14. **Q: How accurate are the projections?**
                                                                   15. A: v1 uses transparent, process-based logic (not ML black boxes). We track all projections vs. actuals; you can audit our model. See [EVALUATION.md](./EVALUATION.md) for 2024–2025 performance.
                                                                  
                                                                   16. **Q: Can I self-host?**
                                                                   17. A: Absolutely. Docker Compose is production-ready. See [DEPLOYMENT.md](./DEPLOYMENT.md).
                                                                  
                                                                   18. ## License
                                                                  
                                                                   19. MIT License. See [LICENSE](./LICENSE) for details.
                                                                  
                                                                   20. ## Contact
                                                                  
                                                                   21. Questions? Ideas? Bugs?
                                                                  
                                                                   22. - **Twitter/X**: [[Your Twitter Handle]](https://twitter.com/everworldlife)
                                                                       - - **Email**: [[your-email@example.com]]
                                                                         - - **GitHub Issues**: [everworldlife-netizen/Live-Lox-Model/issues](https://github.com/everworldlife-netizen/Live-Lox-Model/issues)
                                                                          
                                                                           - ---

                                                                           **Built with ❤️ by the Live Lox team. Made for NBA fans who think deeply about the game.**
                                                                           
