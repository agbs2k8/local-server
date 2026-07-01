import datetime
from typing import Optional
from pydantic import BaseModel
import psycopg
from .utils import str_like_query

class Event(BaseModel):
    id: int
    uid: Optional[str] = None
    date: datetime.datetime
    name: str
    short_name: Optional[str] = None
    season: Optional[str] = None
    status: Optional[str] = "scheduled"
    home_team_id: Optional[str] = None
    away_team_id: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None

    @staticmethod
    def row_to_event(row: tuple) -> "Event":
        return Event(
            id=row[0],
            uid=row[1],
            date=row[2],
            name=row[3],
            short_name=row[4],
            season=row[5],
            status=row[6],
            home_team_id=row[7],
            away_team_id=row[8],
            home_score=row[9],
            away_score=row[10]
        )
    

class League(BaseModel):
    id: Optional[str] = None
    name: str
    display_name: Optional[str] = None
    teams_url: Optional[str] = None
    scoreboard_url: Optional[str] = None

    def __repr__(self) -> str:
        return f"<League {self.name}>"


class Team(BaseModel):
    id: Optional[str] = None
    number: Optional[int] = None
    uid: Optional[str] = None
    name: str
    display_name: Optional[str] = None
    logo_path: Optional[str] = None
    league: League
    user_selection: bool = False
    last_event: Optional[Event] = None
    next_event: Optional[Event] = None

    def to_dict(self) -> dict:
        return self.model_dump()
    
    @staticmethod
    def row_to_team(row: tuple) -> "Team":
        _league = League(
            id=row[7],
            name=row[8],
            display_name=row[9],
            teams_url=row[10],
            scoreboard_url=row[11]
        )
        return Team(
            id=row[0],
            number=row[1],
            uid=row[2],
            name=row[3],
            display_name=row[4],
            logo_path=row[5],
            league=_league,
            user_selection=row[6]
        )

    @staticmethod
    def get_team(team:str, league:str, connection_string:str) -> Optional["Team"]:
        team = str_like_query(team)
        league_name = str(league).strip().upper()
        with psycopg.connect(connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT teams.id, teams.number, teams.uid, teams.name, teams.display_name, teams.logo_path, teams.user_selection,"
                    "leagues.id, leagues.name, leagues.display_name, leagues.teams_url, leagues.scoreboard_url "
                    "FROM public.teams "
                    "JOIN public.leagues ON leagues.id = teams.league_id "
                    "WHERE teams.name ILIKE %s AND leagues.name = %s;",
                    (team, league_name),
                )
                row = cur.fetchone()
                if row:
                    return Team.row_to_team(row)
        return None
    
    @staticmethod
    def get_team_and_events(team:str, league: str, connection_string:str) -> Optional["Team"]:
        team = str_like_query(team)
        league_name = str(league).strip().upper()
        with psycopg.connect(connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT t.id, t.number, t.uid, t.name, t.display_name, t.logo_path, t.user_selection, "
                                "l.id, l.name, l.display_name, l.teams_url, l.scoreboard_url, "
                                "last_event.id AS last_event_id,"
                                "last_event.uid AS last_event_uid,"
                                "last_event.date AS last_event_date,"
                                "last_event.name AS last_event_name,"
                                "last_event.short_name AS last_event_short_name,"
                                "last_event.season AS last_event_season,"
                                "last_event.status AS last_event_status,"
                                "last_event.home_team_id AS last_event_home_team_id,"
                                "last_event.away_team_id AS last_event_away_team_id,"
                                "last_event.home_score AS last_event_home_score,"
                                "last_event.away_score AS last_event_away_score,"
                                "next_event.id AS next_event_id,"
                                "next_event.uid AS next_event_uid,"
                                "next_event.date AS next_event_date,"
                                "next_event.name AS next_event_name,"
                                "next_event.short_name AS next_event_short_name,"
                                "next_event.season AS next_event_season,"
                                "next_event.status AS next_event_status,"
                                "next_event.home_team_id AS next_event_home_team_id,"
                                "next_event.away_team_id AS next_event_away_team_id,"
                                "next_event.home_score AS next_event_home_score,"
                                "next_event.away_score AS next_event_away_score "
                            "FROM teams t "
                            "JOIN leagues l ON t.league_id = l.id "
                            "LEFT JOIN LATERAL ("
                                "SELECT e.* FROM events e "
                                "WHERE"
                                    "(e.home_team_id = t.id OR e.away_team_id = t.id) AND e.status ILIKE 'Final' "
                                "ORDER BY e.date DESC, e.id DESC LIMIT 1 ) AS last_event ON TRUE "
                            "LEFT JOIN LATERAL ("
                                "SELECT e.* FROM events e "
                                "WHERE"
                                    "(e.home_team_id = t.id OR e.away_team_id = t.id) AND (e.status ILIKE 'Scheduled' OR e.status ILIKE 'future') "
                                "ORDER BY e.date ASC, e.id ASC LIMIT 1) AS next_event ON TRUE "
                            "WHERE t.name ILIKE %s AND l.name = %s;",
                            (team, league_name),
                )
                row = cur.fetchone()
                if row:
                    # Team Obj [0:13]
                    # Last Event Obj [12:23]
                    # Next Event Obj [23:]
                    _team = Team.row_to_team(row[0:12])
                    if row[12] is not None:
                        _team.last_event = Event.row_to_event(row[12:23])
                    if row[23] is not None:
                        _team.next_event = Event.row_to_event(row[23:])
                    return _team
        return None


class Teams(BaseModel):
    teams: list[Team]

    @staticmethod
    def get_selected(connection_string:str) -> "Teams":
        with psycopg.connect(connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT teams.id, teams.number, teams.uid, teams.name, teams.display_name, teams.logo_path, teams.user_selection,"
                    "leagues.id, leagues.name, leagues.display_name, leagues.teams_url, leagues.scoreboard_url "
                    "FROM public.teams "
                    "JOIN public.leagues ON leagues.id = teams.league_id "
                    "WHERE teams.user_selection=TRUE;",
                )
                rows = cur.fetchall()
        if rows:
            return Teams(teams=[Team.row_to_team(row) for row in rows])
        else:
            return Teams(teams=[])
        
    @staticmethod
    def get_all(connection_string:str) -> "Teams":
        with psycopg.connect(connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT teams.id, teams.number, teams.uid, teams.name, teams.display_name, teams.logo_path, teams.user_selection,"
                    "leagues.id, leagues.name, leagues.display_name, leagues.teams_url, leagues.scoreboard_url "
                    "FROM public.teams "
                    "JOIN public.leagues ON leagues.id = teams.league_id;",
                )
                rows = cur.fetchall()
        if rows:
            return Teams(teams=[Team.row_to_team(row) for row in rows])
        else:
            return Teams(teams=[])