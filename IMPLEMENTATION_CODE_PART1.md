# Live Lox - Complete Implementation Code (Part 1)

## Backend Code

### apps/api/app/main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.routes import health, slate, projections, players
from app.services.cache import init_redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Live Lox API...")
    await init_redis()
    yield
    logger.info("Shutting down Live Lox API...")

app = FastAPI(
    title="Live Lox API (Pregame Edition)",
    version="1.0.0",
    description="NBA pregame projections and insights",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(slate.router, prefix="/api/v1", tags=["slate"])
app.include_router(projections.router, prefix="/api/v1", tags=["projections"])
app.include_router(players.router, prefix="/api/v1", tags=["players"])

@app.get("/")
def root():
    return {"status": "Live Lox API running", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```

### apps/api/app/config.py

```python
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://livelox:livelox_dev_password@localhost:5432/livelox"
    )

    # Ball Don't Lie
    BALLDONTLIE_API_KEY: str = os.getenv("BALLDONTLIE_API_KEY", "")
    BALLDONTLIE_BASE_URL: str = "https://api.balldontlie.io/v1"

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    CACHE_TTL: int = 3600

    # CORS
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost",
        "http://127.0.0.1:3000"
    ]

    # Projection
    PROJECTION_VERSION: str = "v1"

    class Config:
        env_file = ".env"

settings = Settings()
```

### apps/api/app/models/schemas.py

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

class ConfidenceEnum(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class TeamResponse(BaseModel):
    id: str
    name: str
    abbrev: str
    logoUrl: Optional[str] = None

class GameResponse(BaseModel):
    id: str
    date: str
    startTime: datetime
    homeTeam: TeamResponse
    awayTeam: TeamResponse
    status: str
    homeScore: Optional[int] = None
    awayScore: Optional[int] = None

class SlateResponse(BaseModel):
    date: str
    games: List[GameResponse]
    runTimestamp: Optional[datetime] = None

class PlayerProjectionResponse(BaseModel):
    id: str
    playerId: str
    playerName: str
    gameId: str

    minutesProj: float
    minutesStdDev: Optional[float] = None
    ptsProj: float
    rebProj: float
    astProj: float
    stlProj: Optional[float] = None
    blkProj: Optional[float] = None
    praProj: float

    confidence: ConfidenceEnum
    reasons: List[str]
    risks: List[str]
    injuryStatus: Optional[str] = None
    seasonAvgPts: Optional[float] = None
    recentAvgPts: Optional[float] = None

class ProjectionRunResponse(BaseModel):
    id: str
    runTimestamp: datetime
    slateDate: str
    version: str
    projections: List[PlayerProjectionResponse]
    assumptions: dict

class ProjectionRunRequest(BaseModel):
    slateDate: str
    notes: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str
```

### apps/api/app/routes/health.py

```python
from fastapi import APIRouter
from app.models.schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", version="1.0.0")
```

### apps/api/app/routes/slate.py

```python
from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
from app.models.schemas import SlateResponse, GameResponse, TeamResponse
from app.services.ball_dont_lie import bdl_client
from app.services.cache import cache_get, cache_set

router = APIRouter()

@router.get("/slate", response_model=SlateResponse)
async def get_slate(date: str = Query(..., description="Date in YYYY-MM-DD format")):
    """Fetch tonight's slate of games."""

    cache_key = f"slate:{date}"
    cached = await cache_get(cache_key)
    if cached:
        return SlateResponse(**cached)

    try:
        games_data = await bdl_client.get_games(date)

        games = []
        for game in games_data.get("data", []):
            game_obj = GameResponse(
                id=str(game["id"]),
                date=date,
                startTime=datetime.fromisoformat(game["date"]),
                homeTeam=TeamResponse(
                    id=str(game["home_team"]["id"]),
                    name=game["home_team"]["full_name"],
                    abbrev=game["home_team"]["abbreviation"],
                ),
                awayTeam=TeamResponse(
                    id=str(game["visitor_team"]["id"]),
                    name=game["visitor_team"]["full_name"],
                    abbrev=game["visitor_team"]["abbreviation"],
                ),
                status=game["status"],
            )
            games.append(game_obj)

        response = SlateResponse(date=date, games=games)
        await cache_set(cache_key, response.dict(), ttl=3600)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### apps/api/app/routes/projections.py

```python
from fastapi import APIRouter, Query, HTTPException
from datetime import datetime
from app.models.schemas import ProjectionRunResponse, ProjectionRunRequest, PlayerProjectionResponse

router = APIRouter()

@router.post("/projections/run")
async def run_projections(req: ProjectionRunRequest):
    """Trigger a projection run for a given date."""
    # TODO: Implement DB save and projection calculation
    return {
        "status": "success",
        "message": "Projections queued",
        "run_id": "run_temp_12345"
    }

@router.get("/projections/latest", response_model=ProjectionRunResponse)
async def get_latest_projections(
    date: str = Query(..., description="Date in YYYY-MM-DD format")
):
    """Fetch latest projection run for a date."""
    # TODO: Query from DB
    raise HTTPException(status_code=404, detail="No projections found for this date")

@router.get("/projections/run/{run_id}", response_model=ProjectionRunResponse)
async def get_projection_run(run_id: str):
    """Fetch a specific projection run."""
    # TODO: Query from DB
    raise HTTPException(status_code=404, detail="Projection run not found")
```

### apps/api/app/routes/players.py

```python
from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import PlayerProjectionResponse

router = APIRouter()

@router.get("/player/{player_id}")
async def get_player(player_id: str):
    """Fetch player profile + recent stats."""
    # TODO: Query from Ball Don't Lie and DB
    return {
        "id": player_id,
        "name": "Player Name",
        "recentGames": 10,
        "avgPoints": 20.5,
        "avgRebounds": 5.2,
        "avgAssists": 3.1,
        "streak": "3-game 20+ PPG streak"
    }
```

### apps/api/app/services/ball_dont_lie.py

```python
import httpx
import asyncio
from datetime import datetime
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class BallDontLieClient:
    def __init__(self):
        self.base_url = settings.BALLDONTLIE_BASE_URL
        self.api_key = settings.BALLDONTLIE_API_KEY
        self.max_retries = 3
        self.timeout = httpx.Timeout(10.0)

    async def _make_request(self, endpoint: str, params: dict = None, method: str = "GET"):
        """Make HTTP request with retries and exponential backoff."""
        headers = {"Authorization": self.api_key}
        url = f"{self.base_url}{endpoint}"

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(headers=headers, timeout=self.timeout) as client:
                    response = await client.request(method, url, params=params)

                    if response.status_code == 429:
                        wait_time = 2 ** attempt
                        logger.warning(f"Rate limited. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue

                    response.raise_for_status()
                    return response.json()
            except Exception as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

    async def get_games(self, date: str):
        """Fetch games for a given date."""
        params = {"dates[]": date}
        return await self._make_request("/games", params=params)

    async def get_teams(self):
        """Fetch all teams."""
        return await self._make_request("/teams")

    async def get_players(self):
        """Fetch all players."""
        return await self._make_request("/players")

    async def get_player_stats(self, player_id: str, seasons: list = None):
        """Fetch player stats."""
        params = {"player_ids[]": player_id}
        if seasons:
            params["seasons[]"] = seasons
        return await self._make_request("/stats", params=params)

    async def get_season_stats(self, player_id: str, season: int):
        """Get season average stats for a player."""
        params = {"player_ids[]": player_id, "seasons[]": season}
        return await self._make_request("/season_averages", params=params)

bdl_client = BallDontLieClient()
```

### apps/api/app/services/cache.py

```python
import redis.asyncio as redis
from app.config import settings
import logging
import json

logger = logging.getLogger(__name__)

redis_client = None

async def init_redis():
    global redis_client
    try:
        redis_client = await redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("Redis connected")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        redis_client = None

async def cache_get(key: str):
    if not redis_client:
        return None
    try:
        value = await redis_client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.error(f"Cache get failed: {e}")
    return None

async def cache_set(key: str, value: dict, ttl: int = 3600):
    if not redis_client:
        return
    try:
        await redis_client.setex(key, ttl, json.dumps(value))
    except Exception as e:
        logger.error(f"Cache set failed: {e}")

async def cache_delete(key: str):
    if not redis_client:
        return
    try:
        await redis_client.delete(key)
    except Exception as e:
        logger.error(f"Cache delete failed: {e}")
```

### apps/api/app/services/projection_engine.py

```python
import logging
from typing import Dict, Tuple, List

logger = logging.getLogger(__name__)

class ProjectionEngine:
    """Core projection calculation logic."""

    def __init__(self):
        self.season = 2024

    def project_player(self, player: dict, game: dict, stats_data: dict, context: dict) -> dict:
        """Project a player's stats for a given game."""

        season_avg = self._extract_season_avg(stats_data)
        recent_avg = self._extract_recent_avg(stats_data)

        minutes_proj, minutes_stddev = self._project_minutes(
            player,
            stats_data,
            context.get("injury_status", "healthy"),
            context.get("role", "bench"),
        )

        pts_proj = self._project_points(
            season_avg,
            recent_avg,
            minutes_proj,
            context.get("pace_factor", 1.0),
            context.get("opponent_defense_rating", 110),
        )

        reb_proj = self._project_rebounds(
            season_avg,
            recent_avg,
            minutes_proj,
            player.get("position"),
        )

        ast_proj = self._project_assists(
            season_avg,
            recent_avg,
            minutes_proj,
            context.get("usage_rate", 0.2),
        )

        confidence, reasons, risks = self._evaluate_confidence(
            player,
            stats_data,
            minutes_proj,
            context,
        )

        return {
            "minutesProj": round(minutes_proj, 1),
            "minutesStdDev": round(minutes_stddev, 1) if minutes_stddev else None,
            "ptsProj": round(pts_proj, 1),
            "rebProj": round(reb_proj, 1),
            "astProj": round(ast_proj, 1),
            "praProj": round(pts_proj + reb_proj + ast_proj, 1),
            "confidence": confidence,
            "reasons": reasons,
            "risks": risks,
            "seasonAvgPts": round(season_avg.get("pts", 0), 1),
            "recentAvgPts": round(recent_avg.get("pts", 0), 1),
        }

    def _extract_season_avg(self, stats_data: dict) -> dict:
        """Extract season-to-date averages."""
        if not stats_data or "data" not in stats_data:
            return {}

        avg = stats_data["data"][0] if stats_data["data"] else {}
        return {
            "pts": avg.get("pts", 0),
            "reb": avg.get("reb", 0),
            "ast": avg.get("ast", 0),
            "min": avg.get("min", 0),
        }

    def _extract_recent_avg(self, stats_data: dict, games: int = 10) -> dict:
        """Extract last N games average."""
        return self._extract_season_avg(stats_data)

    def _project_minutes(
        self,
        player: dict,
        stats_data: dict,
        injury_status: str,
        role: str,
    ) -> Tuple[float, float]:
        """Project minutes played with injury and role adjustments."""

        baseline_min = 28.0

        injury_multiplier = {
            "healthy": 1.0,
            "questionable": 0.85,
            "probable": 0.95,
            "out": 0.0,
        }.get(injury_status, 1.0)

        is_starter = baseline_min > 25
        role_multiplier = 1.0 if is_starter else 0.9

        minutes_proj = baseline_min * injury_multiplier * role_multiplier
        stddev = minutes_proj * 0.15

        return (minutes_proj, stddev)

    def _project_points(
        self,
        season_avg: dict,
        recent_avg: dict,
        minutes_proj: float,
        pace_factor: float,
        opp_drtg: float,
    ) -> float:
        """Project points using weighted average + pace/defense adjustments."""

        baseline_ppg = season_avg.get("pts", 0) * 0.6 + recent_avg.get("pts", 0) * 0.4
        baseline_min = season_avg.get("min", 30)

        if baseline_min == 0:
            return 0.0

        minutes_ratio = minutes_proj / baseline_min if baseline_min > 0 else 1.0

        league_avg_drtg = 110
        defense_factor = league_avg_drtg / max(opp_drtg, 100)

        pts_proj = baseline_ppg * minutes_ratio * pace_factor * defense_factor

        return pts_proj

    def _project_rebounds(
        self,
        season_avg: dict,
        recent_avg: dict,
        minutes_proj: float,
        position: str,
    ) -> float:
        """Project rebounds with position weighting."""

        baseline_reb = season_avg.get("reb", 0) * 0.6 + recent_avg.get("reb", 0) * 0.4
        baseline_min = season_avg.get("min", 30)

        if baseline_min == 0:
            return 0.0

        minutes_ratio = minutes_proj / baseline_min
        reb_proj = baseline_reb * minutes_ratio

        if position and position.upper() == "C":
            reb_proj *= 1.1

        return reb_proj

    def _project_assists(
        self,
        season_avg: dict,
        recent_avg: dict,
        minutes_proj: float,
        usage_rate: float,
    ) -> float:
        """Project assists with usage weighting."""

        baseline_ast = season_avg.get("ast", 0) * 0.6 + recent_avg.get("ast", 0) * 0.4
        baseline_min = season_avg.get("min", 30)

        if baseline_min == 0:
            return 0.0

        minutes_ratio = minutes_proj / baseline_min
        ast_proj = baseline_ast * minutes_ratio * (usage_rate / 0.2)

        return ast_proj

    def _evaluate_confidence(
        self,
        player: dict,
        stats_data: dict,
        minutes_proj: float,
        context: dict,
    ) -> Tuple[str, List[str], List[str]]:
        """Evaluate confidence level and generate explanations."""

        reasons = []
        risks = []
        confidence = "MEDIUM"

        if context.get("games_played", 0) >= 20:
            reasons.append("Established role with 20+ games played")
            confidence = "HIGH"
        else:
            risks.append("Limited sample size")
            confidence = "LOW"

        injury = context.get("injury_status", "healthy")
        if injury != "healthy":
            risks.append(f"Player listed as {injury}")
            confidence = "LOW"

        if context.get("opponent_pace") == "fast":
            reasons.append("Opponent plays fast pace – more possessions expected")

        return (confidence, reasons, risks)

projection_engine = ProjectionEngine()
```

## Continue to Part 2 for Frontend Code

See IMPLEMENTATION_CODE_PART2.md for Next.js/TypeScript implementation.
