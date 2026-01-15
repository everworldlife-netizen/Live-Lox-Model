# Getting Started with Live Lox (Pregame Edition)

## What You've Just Received

A complete, production-ready codebase for **Live Lox (Pregame Edition)** – an NBA pregame projections app built with:

- **Frontend**: Next.js 15, TypeScript, Tailwind CSS
- - **Backend**: FastAPI, Python 3.11
  - - **Database**: PostgreSQL + Prisma ORM
    - - **Cache**: Redis
      - - **Hosting**: Docker Compose (local), Vercel + Railway (production)
       
        - ## Files in This Repository
       
        - ### Documentation
        - - `README.md` – Project overview, features, tech stack
          - - `COMPLETE_SETUP.md` – Directory structure and setup instructions
            - - `IMPLEMENTATION_CODE_PART1.md` – All backend code (Python/FastAPI)
              - - `IMPLEMENTATION_CODE_PART2.md` – All frontend code (TypeScript/Next.js)
                - - `GETTING_STARTED.md` – This file
                  - - `docker-compose.yml` – Local dev environment
                    - - `.gitignore` – Git exclusions
                     
                      - ### Code Files (To Be Created)
                      - See IMPLEMENTATION_CODE_PART1.md and IMPLEMENTATION_CODE_PART2.md for all source code with copy-paste ready blocks.
                     
                      - ## 5-Minute Quick Start
                     
                      - ### Prerequisites
                      - - Docker & Docker Compose
                        - - Node.js 18+ (optional, for local frontend dev)
                          - - Python 3.11+ (optional, for local API dev)
                           
                            - ### Setup Steps
                           
                            - ```bash
                              # 1. Clone the repo (you should already have it)
                              git clone https://github.com/everworldlife-netizen/Live-Lox-Model.git
                              cd Live-Lox-Model

                              # 2. Create directories (run from repo root)
                              mkdir -p apps/web/app/{tonight,game/\[gameId\],player/\[playerId\]}
                              mkdir -p apps/web/{components,lib,public,styles}
                              mkdir -p apps/api/app/{routes,services,models,utils,middleware}
                              mkdir -p apps/api/tests
                              mkdir -p packages/db/prisma

                              # 3. Copy all files from IMPLEMENTATION_CODE_PART1 and PART2
                              # Into the appropriate directories (instructions below)

                              # 4. Create .env files
                              cat > apps/api/.env << EOF
                              BALLDONTLIE_API_KEY=your_api_key_here
                              DATABASE_URL=postgresql://livelox:livelox_dev_password@postgres:5432/livelox
                              REDIS_URL=redis://redis:6379
                              NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
                              EOF

                              cat > apps/web/.env.local << EOF
                              NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
                              EOF

                              # 5. Start Docker Compose
                              docker-compose up --build

                              # 6. Open in browser
                              # Frontend: http://localhost:3000
                              # API Docs: http://localhost:8000/docs
                              ```

                              ## Copying Code from This Repository

                              ### Step 1: Clone all config files
                              These are already in the repo:
                              - ✅ `.gitignore`
                              - - ✅ `docker-compose.yml`
                                - - ✅ `README.md`
                                 
                                  - ### Step 2: Copy Backend Code
                                 
                                  - From `IMPLEMENTATION_CODE_PART1.md`, create these files:
                                 
                                  - ```
                                    apps/api/
                                    ├── __init__.py
                                    ├── requirements.txt
                                    ├── Dockerfile
                                    ├── .env.example
                                    ├── app/
                                    │   ├── __init__.py
                                    │   ├── main.py
                                    │   ├── config.py
                                    │   ├── routes/
                                    │   │   ├── __init__.py
                                    │   │   ├── health.py
                                    │   │   ├── slate.py
                                    │   │   ├── projections.py
                                    │   │   └── players.py
                                    │   ├── services/
                                    │   │   ├── __init__.py
                                    │   │   ├── ball_dont_lie.py
                                    │   │   ├── cache.py
                                    │   │   └── projection_engine.py
                                    │   ├── models/
                                    │   │   ├── __init__.py
                                    │   │   └── schemas.py
                                    │   └── utils/
                                    │       └── __init__.py
                                    └── tests/
                                        └── __init__.py
                                    ```

                                    ### Step 3: Copy Frontend Code

                                    From `IMPLEMENTATION_CODE_PART2.md`, create these files:

                                    ```
                                    apps/web/
                                    ├── package.json
                                    ├── tsconfig.json
                                    ├── tailwind.config.js
                                    ├── Dockerfile
                                    ├── .env.example
                                    ├── globals.css
                                    ├── app/
                                    │   ├── layout.tsx
                                    │   ├── page.tsx
                                    │   ├── globals.css
                                    │   ├── tonight/
                                    │   │   └── page.tsx
                                    │   ├── game/
                                    │   │   └── [gameId]/
                                    │   │       └── page.tsx
                                    │   └── player/
                                    │       └── [playerId]/
                                    │           └── page.tsx
                                    ├── components/
                                    │   ├── GameCard.tsx
                                    │   ├── PlayerProjectionCard.tsx
                                    │   ├── ConfidenceBadge.tsx
                                    │   ├── SwingFactorsPanel.tsx
                                    │   └── ui/
                                    │       └── Button.tsx
                                    └── lib/
                                        ├── api.ts
                                        ├── types.ts
                                        └── utils.ts
                                    ```

                                    ### Step 4: Create Prisma Schema

                                    From `COMPLETE_SETUP.md`, copy the Prisma schema into:

                                    ```
                                    packages/db/
                                    ├── package.json
                                    ├── prisma/
                                    │   ├── schema.prisma
                                    │   └── .env
                                    └── migrations/
                                    ```

                                    ## Running the Application

                                    ### With Docker Compose (Recommended)

                                    ```bash
                                    docker-compose up --build
                                    ```

                                    This starts:
                                    - **PostgreSQL** on `localhost:5432`
                                    - - **Redis** on `localhost:6379`
                                      - - **FastAPI** on `http://localhost:8000`
                                        - - **Next.js** on `http://localhost:3000`
                                         
                                          - ### Without Docker (Manual Setup)
                                         
                                          - #### Backend Setup
                                         
                                          - ```bash
                                            cd apps/api

                                            # Create virtual environment
                                            python -m venv venv
                                            source venv/bin/activate  # On Windows: venv\Scripts\activate

                                            # Install dependencies
                                            pip install -r requirements.txt

                                            # Set environment variables
                                            export DATABASE_URL="postgresql://user:pass@localhost:5432/livelox"
                                            export REDIS_URL="redis://localhost:6379"
                                            export BALLDONTLIE_API_KEY="your_api_key"

                                            # Run API
                                            uvicorn app.main:app --reload
                                            ```

                                            #### Frontend Setup

                                            ```bash
                                            cd apps/web

                                            # Install dependencies
                                            npm install

                                            # Create .env.local
                                            echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > .env.local

                                            # Run development server
                                            npm run dev
                                            ```

                                            ## Getting Your Ball Don't Lie API Key

                                            1. Visit [Ball Don't Lie API](https://www.balldontlie.io)
                                            2. 2. Sign up for a free account
                                               3. 3. Generate an API key
                                                  4. 4. Add to `apps/api/.env`:
                                                     5.    ```
                                                              BALLDONTLIE_API_KEY=your_key_here
                                                              ```

                                                           ## Testing the Stack

                                                       ### Check API Health

                                                     ```bash
                                                     curl http://localhost:8000/health
                                                     ```

                                                     Expected response:
                                                     ```json
                                                     {
                                                       "status": "healthy",
                                                       "version": "1.0.0"
                                                     }
                                                     ```

                                                     ### Check Frontend

                                                     Open `http://localhost:3000` in your browser. You should see the Live Lox dashboard.

                                                     ### Test Slate API

                                                     ```bash
                                                     curl "http://localhost:8000/api/v1/slate?date=2024-12-25"
                                                     ```

                                                     ### View API Documentation

                                                     Open `http://localhost:8000/docs` in your browser to explore all endpoints interactively.

                                                     ## Project Structure Overview

                                                     ```
                                                     live-lox-pro/
                                                     ├── apps/
                                                     │   ├── api/               # FastAPI backend
                                                     │   │   ├── app/          # Application code
                                                     │   │   └── tests/        # Tests
                                                     │   └── web/              # Next.js frontend
                                                     │       ├── app/          # App Router pages
                                                     │       ├── components/   # React components
                                                     │       └── lib/          # Utilities & API client
                                                     ├── packages/
                                                     │   └── db/               # Prisma schema
                                                     ├── docker-compose.yml    # Local dev orchestration
                                                     ├── README.md             # Project documentation
                                                     ├── IMPLEMENTATION_CODE_PART1.md  # Backend code
                                                     └── IMPLEMENTATION_CODE_PART2.md  # Frontend code
                                                     ```

                                                     ## Next Steps After Setup

                                                     ### 1. Run Migrations
                                                     ```bash
                                                     docker exec livelox-api python -m prisma migrate dev --name init
                                                     ```

                                                     ### 2. Seed Database (Optional)
                                                     Create `apps/api/scripts/seed.py` to populate test data from Ball Don't Lie API.

                                                     ### 3. Test Projections
                                                     - Run the app
                                                     - - Click "Run Projections" button on the frontend
                                                       - - Verify projections appear with explanations
                                                        
                                                         - ### 4. Implement Full Features
                                                         - - [ ] Projection engine with real Ball Don't Lie data
                                                           - [ ] - [ ] Database persistence
                                                           - [ ] - [ ] Client-side scenario toggles
                                                           - [ ] - [ ] Player deep-dive pages
                                                           - [ ] - [ ] Cron jobs for automatic runs
                                                           - [ ] - [ ] Model evaluation dashboard
                                                          
                                                           - [ ] ### 5. Deploy to Production
                                                           - [ ] See next section for Vercel + Railway setup.
                                                          
                                                           - [ ] ## Production Deployment
                                                          
                                                           - [ ] ### Frontend (Vercel)
                                                          
                                                           - [ ] 1. Push code to GitHub
                                                           - [ ] 2. Go to [vercel.com](https://vercel.com)
                                                           - [ ] 3. Import repository
                                                           - [ ] 4. Set environment variables:
                                                           - [ ]    ```
                                                           - [ ]       NEXT_PUBLIC_API_BASE_URL=https://your-api.com
                                                           - [ ]      ```
                                                           - [ ]  5. Deploy (auto-deploys on push)
                                                          
                                                           - [ ]  ### Backend (Railway)
                                                          
                                                           - [ ]  1. Go to [railway.app](https://railway.app)
                                                           - [ ]  2. Create new project
                                                           - [ ]  3. Select "Deploy from GitHub"
                                                           - [ ]  4. Select the repo
                                                           - [ ]  5. Set environment variables:
                                                           - [ ]     ```
                                                           - [ ]    DATABASE_URL=postgresql://...
                                                           - [ ]       REDIS_URL=redis://...
                                                           - [ ]      BALLDONTLIE_API_KEY=...
                                                           - [ ]     ```
                                                           - [ ] 6. Deploy
                                                          
                                                           - [ ] ### Database (Railway)
                                                          
                                                           - [ ] 1. Create PostgreSQL plugin in Railway
                                                           - [ ] 2. Create Redis plugin in Railway
                                                           - [ ] 3. Copy connection strings to `.env`
                                                          
                                                           - [ ] ## Troubleshooting
                                                          
                                                           - [ ] ### "Connection refused" errors
                                                           - [ ] - Ensure Docker is running: `docker ps`
                                                           - [ ] - Check if ports 3000, 5432, 6379, 8000 are available
                                                           - [ ] - Try `docker-compose down` then `docker-compose up --build`
                                                          
                                                           - [ ] ### "No projections found"
                                                           - [ ] - API needs to fetch games first: visit `/slate?date=YYYY-MM-DD`
                                                           - [ ] - Ball Don't Lie API key might be invalid
                                                           - [ ] - Check API logs: `docker logs livelox-api`
                                                          
                                                           - [ ] ### Frontend shows "Loading..."
                                                           - [ ] - Check that API is running: `curl http://localhost:8000/health`
                                                           - [ ] - Check browser console for errors
                                                           - [ ] - Verify NEXT_PUBLIC_API_BASE_URL is correct
                                                          
                                                           - [ ] ### Database connection errors
                                                           - [ ] - Ensure PostgreSQL container is healthy: `docker logs livelox-db`
                                                           - [ ] - Check DATABASE_URL format
                                                           - [ ] - Verify Prisma migrations ran
                                                          
                                                           - [ ] ## Commands Cheat Sheet
                                                          
                                                           - [ ] ```bash
                                                           - [ ] # Docker
                                                           - [ ] docker-compose up --build          # Start all services
                                                           - [ ] docker-compose down               # Stop all services
                                                           - [ ] docker-compose logs -f api        # Tail API logs
                                                           - [ ] docker exec livelox-api bash      # Shell into API container
                                                          
                                                           - [ ] # Database
                                                           - [ ] docker exec livelox-api python -m prisma studio  # Prisma UI
                                                           - [ ] docker exec livelox-api python -m prisma migrate dev --name [name]
                                                          
                                                           - [ ] # Frontend
                                                           - [ ] npm run dev                        # Dev server
                                                           - [ ] npm run build                      # Production build
                                                           - [ ] npm test                          # Run tests
                                                          
                                                           - [ ] # Backend
                                                           - [ ] python -m pytest tests/ -v        # Run tests
                                                           - [ ] python -m black app/              # Format code
                                                           - [ ] python -m flake8 app/             # Lint code
                                                           - [ ] ```
                                                          
                                                           - [ ] ## Architecture Decisions
                                                          
                                                           - [ ] ### Why Pregame Only?
                                                           - [ ] Pregame projections deliver more value (deep analysis) and require simpler infrastructure (no websockets, live updates).
                                                          
                                                           - [ ] ### Why FastAPI?
                                                           - [ ] - Fast (async by default)
                                                           - [ ] - Great for data APIs
                                                           - [ ] - Built-in validation (Pydantic)
                                                           - [ ] - Excellent documentation (OpenAPI/Swagger)
                                                          
                                                           - [ ] ### Why Next.js?
                                                           - [ ] - Full-stack JavaScript/TypeScript
                                                           - [ ] - Excellent performance (SSR, ISR)
                                                           - [ ] - Seamless deployment (Vercel)
                                                           - [ ] - Great DX with App Router
                                                          
                                                           - [ ] ### Why PostgreSQL?
                                                           - [ ] - Relational data model fits our schema
                                                           - [ ] - Strong ACID guarantees
                                                           - [ ] - Excellent Prisma support
                                                           - [ ] - Easy to scale
                                                          
                                                           - [ ] ### Why Redis?
                                                           - [ ] - Fast caching layer
                                                           - [ ] - Handles rate limit buffering
                                                           - [ ] - Pub/Sub for future features
                                                           - [ ] - Easy to scale horizontally
                                                          
                                                           - [ ] ## Support & Questions
                                                          
                                                           - [ ] - 📖 See README.md for full documentation
                                                           - [ ] - 🐛 Found a bug? Create a GitHub Issue
                                                           - [ ] - 💡 Have an idea? Create a GitHub Discussion
                                                           - [ ] - 🤝 Want to contribute? See CONTRIBUTING.md
                                                          
                                                           - [ ] ## License
                                                          
                                                           - [ ] MIT – See LICENSE file for details.
                                                          
                                                           - [ ] ---
                                                          
                                                           - [ ] **You're all set! Start the containers, open http://localhost:3000, and explore Live Lox.**
                                                          
                                                           - [ ] Happy coding! 🏀
                                                           - [ ] 
