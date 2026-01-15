# Live Lox - Complete Implementation Code (Part 2 - Frontend)

## Frontend Code

### apps/web/app/layout.tsx

```typescript
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Live Lox – Pregame Edition",
  description: "NBA pregame projections and insights",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-white">
        {children}
      </body>
    </html>
  );
}
```

### apps/web/app/page.tsx

```typescript
import { redirect } from "next/navigation";

export default function Home() {
  redirect("/tonight");
}
```

### apps/web/app/tonight/page.tsx

```typescript
"use client";

import { useEffect, useState } from "react";
import { GameCard } from "@/components/GameCard";
import { SwingFactorsPanel } from "@/components/SwingFactorsPanel";
import { Button } from "@/components/ui/Button";
import { fetchSlate, runProjections } from "@/lib/api";

interface Game {
  id: string;
  date: string;
  startTime: string;
  homeTeam: { id: string; name: string; abbrev: string };
  awayTeam: { id: string; name: string; abbrev: string };
  status: string;
}

interface Slate {
  date: string;
  games: Game[];
  runTimestamp: string | null;
}

export default function TonightPage() {
  const [slate, setSlate] = useState<Slate | null>(null);
  const [projectionRun, setProjectionRun] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSlate = async () => {
      try {
        const today = new Date().toISOString().split("T")[0];
        const data = await fetchSlate(today);
        setSlate(data);
      } catch (err) {
        setError("Failed to load slate");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadSlate();
  }, []);

  const handleRunProjections = async () => {
    if (!slate) return;

    setRunning(true);
    try {
      const result = await runProjections(slate.date);
      setProjectionRun(result);
    } catch (err) {
      setError("Failed to run projections");
      console.error(err);
    } finally {
      setRunning(false);
    }
  };

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-950 flex items-center justify-center">
        <p className="text-slate-400">Loading slate...</p>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-slate-950 flex items-center justify-center">
        <p className="text-red-400">{error}</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Live Lox</h1>
          <p className="text-slate-400">Pregame Edition – Tonight's Projections</p>
        </div>

        {/* Swing Factors */}
        {projectionRun && (
          <SwingFactorsPanel projections={projectionRun.projections} />
        )}

        {/* Run Button */}
        <div className="mb-8">
          <Button
            onClick={handleRunProjections}
            disabled={running}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            {running ? "Running Projections..." : "Run Projections"}
          </Button>
          {projectionRun && (
            <p className="text-slate-400 text-sm mt-2">
              Last run: {new Date(projectionRun.runTimestamp).toLocaleString()}
            </p>
          )}
        </div>

        {/* Games Grid */}
        {slate && slate.games.length > 0 ? (
          <div className="grid gap-4">
            {slate.games.map((game) => (
              <GameCard
                key={game.id}
                game={game}
                projections={
                  projectionRun?.projections.filter(
                    (p: any) => p.gameId === game.id
                  ) || []
                }
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-slate-400">No games scheduled for today</p>
          </div>
        )}
      </div>
    </main>
  );
}
```

### apps/web/components/GameCard.tsx

```typescript
import Link from "next/link";

interface GameCardProps {
  game: {
    id: string;
    homeTeam: { name: string; abbrev: string };
    awayTeam: { name: string; abbrev: string };
    startTime: string;
  };
  projections: any[];
}

export function GameCard({ game, projections }: GameCardProps) {
  const startTime = new Date(game.startTime).toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    meridiem: "short",
  });

  const playerCount = projections.length;

  return (
    <Link href={`/game/${game.id}`}>
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 hover:border-slate-700 transition">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className="text-right">
              <p className="font-bold text-lg">{game.awayTeam.abbrev}</p>
              <p className="text-xs text-slate-400">Away</p>
            </div>
            <p className="text-slate-600 font-light">@</p>
            <div className="text-left">
              <p className="font-bold text-lg">{game.homeTeam.abbrev}</p>
              <p className="text-xs text-slate-400">Home</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-slate-400">{startTime}</p>
          </div>
        </div>

        {projections.length > 0 && (
          <div className="text-xs text-slate-500 mt-2">
            {playerCount} player projections available
          </div>
        )}
      </div>
    </Link>
  );
}
```

### apps/web/components/PlayerProjectionCard.tsx

```typescript
import { ConfidenceBadge } from "./ConfidenceBadge";

interface PlayerProjectionCardProps {
  projection: {
    id: string;
    playerName: string;
    ptsProj: number;
    rebProj: number;
    astProj: number;
    praProj: number;
    minutesProj: number;
    confidence: "HIGH" | "MEDIUM" | "LOW";
    reasons: string[];
    risks: string[];
  };
}

export function PlayerProjectionCard({
  projection,
}: PlayerProjectionCardProps) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
      <div className="flex items-start justify-between mb-3">
        <div>
          <p className="font-semibold text-lg">{projection.playerName}</p>
          <p className="text-xs text-slate-400">
            {projection.minutesProj.toFixed(1)} MIN projected
          </p>
        </div>
        <ConfidenceBadge level={projection.confidence} />
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-4">
        <div className="bg-slate-800 rounded p-2 text-center">
          <p className="text-xs text-slate-400">PTS</p>
          <p className="font-bold">{projection.ptsProj.toFixed(1)}</p>
        </div>
        <div className="bg-slate-800 rounded p-2 text-center">
          <p className="text-xs text-slate-400">REB</p>
          <p className="font-bold">{projection.rebProj.toFixed(1)}</p>
        </div>
        <div className="bg-slate-800 rounded p-2 text-center">
          <p className="text-xs text-slate-400">AST</p>
          <p className="font-bold">{projection.astProj.toFixed(1)}</p>
        </div>
        <div className="bg-slate-800 rounded p-2 text-center md:col-span-2">
          <p className="text-xs text-slate-400">PRA</p>
          <p className="font-bold">{projection.praProj.toFixed(1)}</p>
        </div>
      </div>

      {/* Why & Risks */}
      <div className="grid md:grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-xs font-semibold text-slate-300 mb-1">Why this projection</p>
          <ul className="text-xs text-slate-400 space-y-1">
            {projection.reasons.map((reason, i) => (
              <li key={i}>• {reason}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold text-slate-300 mb-1">What could break this</p>
          <ul className="text-xs text-slate-400 space-y-1">
            {projection.risks.map((risk, i) => (
              <li key={i}>• {risk}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
```

### apps/web/components/ConfidenceBadge.tsx

```typescript
interface ConfidenceBadgeProps {
  level: "HIGH" | "MEDIUM" | "LOW";
}

export function ConfidenceBadge({ level }: ConfidenceBadgeProps) {
  const colors = {
    HIGH: "bg-green-900 text-green-100",
    MEDIUM: "bg-yellow-900 text-yellow-100",
    LOW: "bg-red-900 text-red-100",
  };

  return (
    <span className={`text-xs font-semibold px-2 py-1 rounded ${colors[level]}`}>
      {level}
    </span>
  );
}
```

### apps/web/components/SwingFactorsPanel.tsx

```typescript
interface SwingFactorsPanelProps {
  projections: any[];
}

export function SwingFactorsPanel({ projections }: SwingFactorsPanelProps) {
  if (projections.length === 0) {
    return null;
  }

  const injuryCount = projections.filter(
    (p) => p.injuryStatus && p.injuryStatus !== "healthy"
  ).length;

  const lowConfidenceCount = projections.filter(
    (p) => p.confidence === "LOW"
  ).length;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 mb-8">
      <h2 className="text-xl font-bold mb-4">Tonight's 3 Swing Factors</h2>

      <div className="grid md:grid-cols-3 gap-4 text-sm">
        <div className="bg-slate-800 rounded p-4">
          <p className="text-slate-400 text-xs font-semibold mb-2">Injuries</p>
          <p className="text-2xl font-bold">{injuryCount}</p>
          <p className="text-xs text-slate-500 mt-1">players with injury status</p>
        </div>

        <div className="bg-slate-800 rounded p-4">
          <p className="text-slate-400 text-xs font-semibold mb-2">Low Confidence</p>
          <p className="text-2xl font-bold">{lowConfidenceCount}</p>
          <p className="text-xs text-slate-500 mt-1">volatile projections</p>
        </div>

        <div className="bg-slate-800 rounded p-4">
          <p className="text-slate-400 text-xs font-semibold mb-2">Total Players</p>
          <p className="text-2xl font-bold">{projections.length}</p>
          <p className="text-xs text-slate-500 mt-1">in projection run</p>
        </div>
      </div>
    </div>
  );
}
```

### apps/web/components/ui/Button.tsx

```typescript
import { ReactNode } from "react";

interface ButtonProps {
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
  children: ReactNode;
}

export function Button({
  onClick,
  disabled = false,
  className = "",
  children,
}: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`px-4 py-2 rounded font-semibold transition ${className}`}
    >
      {children}
    </button>
  );
}
```

### apps/web/lib/api.ts

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export async function fetchSlate(date: string) {
  const res = await fetch(`${API_BASE}/api/v1/slate?date=${date}`);
  if (!res.ok) throw new Error("Failed to fetch slate");
  return res.json();
}

export async function runProjections(date: string) {
  const res = await fetch(`${API_BASE}/api/v1/projections/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ slateDate: date }),
  });
  if (!res.ok) throw new Error("Failed to run projections");
  return res.json();
}

export async function fetchProjections(date: string) {
  const res = await fetch(`${API_BASE}/api/v1/projections/latest?date=${date}`);
  if (!res.ok) throw new Error("Failed to fetch projections");
  return res.json();
}

export async function fetchPlayer(playerId: string) {
  const res = await fetch(`${API_BASE}/api/v1/player/${playerId}`);
  if (!res.ok) throw new Error("Failed to fetch player");
  return res.json();
}
```

### apps/web/lib/types.ts

```typescript
export interface Team {
  id: string;
  name: string;
  abbrev: string;
  logoUrl?: string;
}

export interface Game {
  id: string;
  date: string;
  startTime: string;
  homeTeam: Team;
  awayTeam: Team;
  status: string;
  homeScore?: number;
  awayScore?: number;
}

export interface PlayerProjection {
  id: string;
  playerId: string;
  playerName: string;
  gameId: string;
  minutesProj: number;
  minutesStdDev?: number;
  ptsProj: number;
  rebProj: number;
  astProj: number;
  stlProj?: number;
  blkProj?: number;
  praProj: number;
  confidence: "HIGH" | "MEDIUM" | "LOW";
  reasons: string[];
  risks: string[];
  injuryStatus?: string;
  seasonAvgPts?: number;
  recentAvgPts?: number;
}

export interface ProjectionRun {
  id: string;
  runTimestamp: string;
  slateDate: string;
  version: string;
  projections: PlayerProjection[];
  assumptions: Record<string, any>;
}

export interface Slate {
  date: string;
  games: Game[];
  runTimestamp?: string;
}
```

### apps/web/globals.css

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

html {
  scroll-behavior: smooth;
}

body {
  @apply bg-slate-950 text-white;
}

button {
  @apply focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-950;
}

a {
  @apply hover:opacity-80 transition;
}
```

## Running the Application

1. Clone the repo
2. 2. Create `.env` files in `apps/api` and `apps/web` using the `.env.example` files
   3. 3. Add your Ball Don't Lie API key
      4. 4. Run `docker-compose up --build` from the root
         5. 5. Frontend: http://localhost:3000
            6. 6. API: http://localhost:8000
               7. 7. API Docs: http://localhost:8000/docs
                 
                  8. ## Next Steps
                 
                  9. 1. Create all files from Part 1 and Part 2
                     2. 2. Run Docker Compose to verify the stack works
                        3. 3. Implement database integration with Prisma
                           4. 4. Add Prisma migration for initial schema
                              5. 5. Wire up Ball Don't Lie API calls
                                 6. 6. Implement projection calculation logic
                                    7. 7. Add unit tests for projection engine
                                       8. 8. Deploy to production (Vercel for frontend, Railway for API)
                                         
                                          9. ## File Checklist
                                         
                                          10. ### Backend (Part 1)
                                          11. - [x] main.py
                                              - [ ] - [x] config.py
                                              - [ ] - [x] models/schemas.py
                                              - [ ] - [x] routes/health.py
                                              - [ ] - [x] routes/slate.py
                                              - [ ] - [x] routes/projections.py
                                              - [ ] - [x] routes/players.py
                                              - [ ] - [x] services/ball_dont_lie.py
                                              - [ ] - [x] services/cache.py
                                              - [ ] - [x] services/projection_engine.py
                                             
                                              - [ ] ### Frontend (Part 2)
                                              - [ ] - [x] app/layout.tsx
                                              - [ ] - [x] app/page.tsx
                                              - [ ] - [x] app/tonight/page.tsx
                                              - [ ] - [x] components/GameCard.tsx
                                              - [ ] - [x] components/PlayerProjectionCard.tsx
                                              - [ ] - [x] components/ConfidenceBadge.tsx
                                              - [ ] - [x] components/SwingFactorsPanel.tsx
                                              - [ ] - [x] components/ui/Button.tsx
                                              - [ ] - [x] lib/api.ts
                                              - [ ] - [x] lib/types.ts
                                              - [ ] - [x] globals.css
                                              - [ ] 
