import datetime
import requests
import logging
import logging.config
import psycopg
from psycopg.rows import tuple_row
from shared_models.models import Team, Teams
from shared_models.utils import get_headers
from .load_events import parse_event, event_to_row, upsert_events


def get_schedules(cfg):
    logging.config.dictConfig(cfg.LOG_CONFIG)
    logger = logging.getLogger(__name__)
    logger.info("Sport Scores Schedule Download Starting")
    # Create DB Connection String
    db_conn_string =cfg.DATABASE_URL

    # Extract the teams from the database
    my_teams = Teams.get_selected(db_conn_string)
    len(my_teams.teams)
    logger.info(f"Found {len(my_teams.teams)} teams to track in the database")

    all_teams = Teams.get_all(db_conn_string)
    len(all_teams.teams)
    logger.info(f"Found {len(all_teams.teams)} total teams in the database")

    event_rows = []
    my_team_ids = [x.id for x in my_teams.teams]
    for team in my_teams.teams:
        logger.info(f"Extracting schedule for {team.name} in {team.league.name}")
        team_url = f"{team.league.teams_url}/{team.number}/schedule"
        r = requests.get(team_url, headers=get_headers(), verify=False)
        if not r.status_code == 200:
            logger.error(f"Unable to extract schedule from the API for {team.name} in {team.league.name} - non 200 response code: {r.status_code}")
    
        _events = r.json().get('events')
        if _events:
            for event in _events:
                try:
                    event_data = parse_event(event, all_teams.teams, team.league.name)
                    if event_data['date'] > datetime.datetime.now():
                        event_rows.append(event_to_row(event_data))
                except Exception as e:
                    logger.error(f"failed to parse next event in {team.league.name} with error: {e}")
    upsert_events(db_conn_string, event_rows, logger)
    logger.info(f"Updated database with {len(event_rows)} scheduled events.")