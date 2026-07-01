import logging
import fastapi
from config import cfg
from shared_models.models import Event, Team

logger = logging.getLogger(__name__)

router = fastapi.APIRouter()


@router.get("/liveness")
async def liveness():
    return {"message": "ok"}


@router.get("/readiness")
async def readiness():
    return {"message": "ok"}


@router.get("/team", 
            response_model=Team, 
            summary="Get a specific team by Name",
            description="Entire team object")
async def get_team(
    league: str = fastapi.Query(..., description="The league of the team to retrieve"),
    team: str = fastapi.Query(..., description="The name of the team to retrieve")):
    """
    Return a specific team
    """
    logger.info("Loading team %s in league %s from database", team, league)
    _team = Team.get_team_and_events(team, league, cfg.DATABASE_URL)
    if _team:
        return _team
    else:
        raise fastapi.HTTPException(status_code=404, detail=f"Team {team} not found")



