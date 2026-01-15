# Live Lox - Complete Setup Guide

This document provides the complete directory structure and all files needed to set up Live Lox (Pregame Edition).

## Quick Directory Structure Creation

Run these commands from the repository root:

```bash
# Create all directories
mkdir -p apps/web/app/{tonight,game/\[gameId\],player/\[playerId\]}
mkdir -p apps/web/{components,lib,public,styles}
mkdir -p apps/api/app/{routes,services,models,utils,middleware}
mkdir -p apps/api/tests
mkdir -p packages/db/prisma
mkdir -p .github/workflows

# Create empty __init__.py files for Python
touch apps/api/app/__init__.py
touch apps/api/app/routes/__init__.py
touch apps/api/app/services/__init__.py
touch apps/api/app/models/__init__.py
touch apps/api/app/utils/__init__.py
touch apps/api/app/middleware/__init__.py
touch apps/api/tests/__init__.py
```

## Files to Create (in order)

### 1. ROOT LEVEL FILES

#### apps/api/.env.example
```
BALLDONTLIE_API_KEY=your_api_key_here
DATABASE_URL=postgresql://livelox:livelox_dev_password@localhost:5432/livelox
REDIS_URL=redis://localhost:6379
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

#### apps/api/requirements.txt
```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
httpx==0.25.2
redis==5.0.1
aioredis==2.0.1
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
black==23.12.0
flake8==6.1.0
```

#### apps/api/Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### apps/web/.env.example
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

#### apps/web/package.json
```json
{
  "name": "live-lox-web",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "jest",
    "test:watch": "jest --watch"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "next": "15.0.0",
    "typescript": "^5.3.3",
    "@types/react": "^18.2.37",
    "@types/node": "^20.10.6",
    "tailwindcss": "^3.4.1",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "@radix-ui/react-slot": "^2.0.2",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.2.1",
    "lucide-react": "^0.294.0"
  },
  "devDependencies": {
    "@types/jest": "^29.5.11",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0",
    "@testing-library/react": "^14.1.2",
    "@testing-library/jest-dom": "^6.1.5"
  }
}
```

#### apps/web/tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "jsx": "react-jsx",
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["**/*.ts", "**/*.tsx"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

#### apps/web/tailwind.config.js
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        slate: {
          950: "#030712",
          900: "#0f172a",
        },
      },
    },
  },
  plugins: [],
};
```

#### apps/web/Dockerfile
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --omit=dev

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["npm", "start"]
```

#### packages/db/package.json
```json
{
  "name": "@livelox/db",
  "version": "1.0.0",
  "private": true,
  "devDependencies": {
    "@prisma/cli": "5.7.1",
    "prisma": "5.7.1"
  }
}
```

#### packages/db/prisma/schema.prisma
```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-python"
}

model Game {
  id            String   @id @default(cuid())
  date          DateTime @db.Date
  startTime     DateTime

  homeTeamId    String
  homeTeam      Team     @relation("HomeTeam", fields: [homeTeamId], references: [id])

  awayTeamId    String
  awayTeam      Team     @relation("AwayTeam", fields: [awayTeamId], references: [id])

  status        String   @default("scheduled")
  homeScore     Int?
  awayScore     Int?

  projectionRuns ProjectionRun[]
  playerProjections PlayerProjection[]

  @@index([date])
  @@index([startTime])
}

model Team {
  id            String   @id
  name          String
  abbrev        String   @unique
  logoUrl       String?

  homeGames    Game[]   @relation("HomeTeam")
  awayGames    Game[]   @relation("AwayTeam")
  players      Player[]

  @@index([abbrev])
}

model Player {
  id            String   @id
  name          String
  teamId        String
  team          Team     @relation(fields: [teamId], references: [id])
  position      String?

  projections   PlayerProjection[]

  @@index([teamId])
}

model ProjectionRun {
  id            String   @id @default(cuid())
  runTimestamp  DateTime @default(now())
  slateDate     DateTime @db.Date
  notes         String?
  version       String   @default("v1")

  assumptions   Assumption[]
  projections   PlayerProjection[]

  @@index([slateDate])
  @@index([runTimestamp])
}

model PlayerProjection {
  id                String   @id @default(cuid())

  projectionRun     ProjectionRun @relation(fields: [projectionRunId], references: [id], onDelete: Cascade)
  projectionRunId   String

  player            Player    @relation(fields: [playerId], references: [id])
  playerId          String

  game              Game      @relation(fields: [gameId], references: [id])
  gameId            String

  minutesProj       Float
  minutesStdDev     Float?
  ptsProj           Float
  rebProj           Float
  astProj           Float
  stlProj           Float?
  blkProj           Float?
  praProj           Float

  confidence        String
  reasons           Json
  risks             Json

  seasonAvgPts      Float?
  recentAvgPts      Float?
  paceAdjustment    Float?
  injuryStatus      String?

  createdAt         DateTime  @default(now())

  @@unique([projectionRunId, playerId, gameId])
  @@index([playerId])
  @@index([gameId])
}

model Assumption {
  id                String   @id @default(cuid())
  projectionRun     ProjectionRun @relation(fields: [projectionRunId], references: [id], onDelete: Cascade)
  projectionRunId   String

  key               String
  value             Json

  @@index([projectionRunId])
}
```

## Next Steps

1. Copy all content from the sections below
2. 2. Create files in the specified locations
   3. 3. Run `docker-compose up --build` from the root directory
      4. 4. Frontend will be at http://localhost:3000
         5. 5. API will be at http://localhost:8000
            6. 6. API docs at http://localhost:8000/docs
              
               7. ## Additional Files to Create
              
               8. Due to space constraints, the following files should be created with the provided code samples:
              
               9. - `apps/api/app/main.py` - FastAPI entry point
                  - - `apps/api/app/config.py` - Configuration
                    - - `apps/api/app/routes/health.py`, `slate.py`, `projections.py`, `players.py` - API endpoints
                      - - `apps/api/app/services/ball_dont_lie.py`, `projection_engine.py`, `cache.py` - Business logic
                        - - `apps/api/app/models/schemas.py` - Pydantic models
                          - - `apps/web/app/layout.tsx`, `page.tsx` - Next.js pages
                            - - `apps/web/app/tonight/page.tsx` - Slate view
                              - - `apps/web/app/game/[gameId]/page.tsx` - Game detail
                                - - `apps/web/components/*.tsx` - React components
                                  - - `apps/web/lib/api.ts`, `lib/types.ts` - Frontend utilities
                                   
                                    - See individual file documentation files for complete code.
                                   
                                    - ## Database Migration
                                   
                                    - After setting up Docker:
                                   
                                    - ```bash
                                      # Inside the api container
                                      docker exec livelox-api python -m prisma migrate dev --name init
                                      ```

                                      ## Running Tests

                                      ```bash
                                      # Backend
                                      docker exec livelox-api pytest tests/ -v

                                      # Frontend
                                      docker exec livelox-web npm test
                                      ```

                                      ## Deployment

                                      See DEPLOYMENT.md for production setup.
                                      
