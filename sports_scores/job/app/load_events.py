import datetime
import requests
import logging
import logging.config
import psycopg
from psycopg.rows import tuple_row
from shared_models.models import Team, Teams
from shared_models.utils import get_headers


def team_id_lookup(event_team_obj: dict, all_teams:list[Team], league:str) -> str:
    """
    This is ugly spaghetti code, but works with the try/except that calls it
    Currently failing if we have unknown teams
    """
    if "uid" in event_team_obj.keys():
        return [x for x in all_teams if x.uid == event_team_obj["uid"]][0].id
    elif "id" in event_team_obj.keys():
        return [x for x in all_teams if str(x.number) == event_team_obj["id"] and x.league.name==league][0].id


def score_exctract(score) -> int|None:
    """
    ... because god forbid we're consistent in how we represent the score of a game...
    """
    _score = None
    if score:
        if isinstance(score, dict) and "value" in score.keys():
            _score = score.get("value")
        else:
            _score = score
        try:
            return int(_score)
        except ValueError:
            return None
    else:
        return None


def parse_event_teams(teams: list[dict], all_teams:list[Team], league:str) -> dict:
    """
    Make sure we get the home/away teams correct
    """
    team0_id = team_id_lookup(teams[0], all_teams, league)
    team0_score = score_exctract(teams[0].get("score"))
    team1_id = team_id_lookup(teams[1], all_teams, league)
    team1_score = score_exctract(teams[1].get("score"))
    
    if teams[0]["homeAway"] == "home":
        return {"home": {"id": team0_id, "score": team0_score},
                "away": {"id": team1_id, "score": team1_score}}
    else:
        return {"home": {"id": team1_id,"score": team1_score},
                "away": {"id": team0_id, "score": team0_score}}

def parse_event(event_record: dict, all_teams:list[Team], league:str) -> dict:
    """
    Pull the values I want out of the event record from the API
    """
    _teams = parse_event_teams(event_record['competitions'][0]['competitors'], all_teams, league)
    _date = datetime.datetime.strptime(event_record["date"],"%Y-%m-%dT%H:%MZ")
    if event_record.get("status"):
        _status = event_record['status']['type']['description']
    elif _date > datetime.datetime.now():
        _status = "future"
    else:
        _status = "unknown"
    return {
        "id":event_record["id"],
        "uid":event_record.get("uid"),
        "date":_date,
        "name":event_record["name"],
        "short_name":event_record["shortName"],
        "season":event_record["season"].get("slug"),
        "status":_status,
        "home_team_id":_teams["home"]["id"],
        "away_team_id":_teams["away"]["id"],
        "home_score":_teams["home"]["score"],
        "away_score":_teams["away"]["score"],
    }

def event_to_row(event_record):
    """
    Assmble the table-row and append the postgres ID values for the FK relationships
    """
    return (event_record['id'],
            event_record['uid'],
            event_record['date'],
            event_record['name'],
            event_record['short_name'],
            event_record['season'],
            event_record['status'],
            event_record['home_team_id'],
            event_record['away_team_id'],
            event_record['home_score'],
            event_record['away_score'])

# Update Event Records
def upsert_events(db_conn_string:str, event_rows:list[tuple], logger:logging.Logger):
    with psycopg.connect(db_conn_string) as conn:
        with conn.cursor(row_factory=tuple_row) as cur:
            cur.executemany(
                """
                INSERT INTO events (
                    id, uid, date, name, short_name, season, status,
                    home_team_id, away_team_id, home_score, away_score
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET uid = EXCLUDED.uid,
                    season = EXCLUDED.season,
                    status = EXCLUDED.status,
                    home_score = EXCLUDED.home_score,
                    away_score = EXCLUDED.away_score
                """,
                event_rows,
            )
        conn.commit() 
        logger.info(f"udpated database with {len(event_rows)} records")   


def run_download(cfg):
    logging.config.dictConfig(cfg.LOG_CONFIG)
    logger = logging.getLogger(__name__)
    logger.info("Sport Scores Job Starting")
    # Create DB Connection String
    db_conn_string =cfg.DATABASE_URL

    # Extract the teams from the database
    my_teams = Teams.get_selected(db_conn_string)
    len(my_teams.teams)
    logger.info(f"Found {len(my_teams.teams)} teams to track in the database")

    all_teams = Teams.get_all(db_conn_string)
    len(all_teams.teams)
    logger.info(f"Found {len(all_teams.teams)} total teams in the database")

    # GET Upcoming Events
    event_rows = []
    my_team_ids = [x.id for x in my_teams.teams]
    for team in my_teams.teams:
        logger.info(f"Extracting events for {team.name} in {team.league.name}")
        team_url = f"{team.league.teams_url}/{team.number}"
        r = requests.get(team_url, headers=get_headers(), verify=False)
        if not r.status_code == 200:
            logger.error(f"Unable to extract team data from the API for {team.name} in {team.league.name} - non 200 response code: {r.status_code}")
        try:
            next_event = r.json()['team']['nextEvent'][0]
        except Exception as e:
            logger.error(f"failed to extract next event for {team.name} in {team.league.name} with error: {e}")
            continue
        try:
            event_data = parse_event(next_event, all_teams.teams, team.league.name)
            event_rows.append(event_to_row(event_data))
        except Exception as e:
            logger.error(f"failed to parse next event for {team.name} in {team.league.name} with error: {e}")
    
        # Extract recent events from the Scores API
        r = requests.get(team.league.scoreboard_url, headers=get_headers(), verify=False)
        if not r.status_code == 200:
            logger.error(f"Unable to extract scoreboard URL for {team.league.name} - non 200 response code: {r.status_code}")
    
        _events = r.json().get('events')
        if _events:
            for event in _events:
                try:
                    event_data = parse_event(event, all_teams.teams, team.league.name)
                    if event_data['home_team_id'] in my_team_ids or event_data['away_team_id'] in my_team_ids:
                        event_rows.append(event_to_row(event_data))
                except Exception as e:
                    logger.error(f"failed to parse next event in {team.league.name} with error: {e}")
    upsert_events(db_conn_string, event_rows, logger)
    logger.info("Sport Scores Job Complete")
    


