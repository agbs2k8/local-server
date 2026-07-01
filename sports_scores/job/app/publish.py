from zoneinfo import ZoneInfo
import logging
import logging.config
import requests
import psycopg
from psycopg.rows import tuple_row

QUERY = """SELECT
            t.id, t.number, t.uid, t.name, t.display_name, t.logo_path, t.user_selection,
            l.id, l.name, l.display_name, l.teams_url, l.scoreboard_url,
            last_event.id AS last_event_id,
            last_event.uid AS last_event_uid,
            last_event.date AS last_event_date,
            last_event.name AS last_event_name,
            last_event.short_name AS last_event_short_name,
            last_event.season AS last_event_season,
            last_event.status AS last_event_status,
            last_event.home_team_id AS last_event_home_team_id,
            last_event.away_team_id AS last_event_away_team_id,
            last_event.home_score AS last_event_home_score,
            last_event.away_score AS last_event_away_score,
            next_event.id AS next_event_id,
            next_event.uid AS next_event_uid,
            next_event.date AS next_event_date,
            next_event.name AS next_event_name,
            next_event.short_name AS next_event_short_name,
            next_event.season AS next_event_season,
            next_event.status AS next_event_status,
            next_event.home_team_id AS next_event_home_team_id,
            next_event.away_team_id AS next_event_away_team_id,
            next_event.home_score AS next_event_home_score,
            next_event.away_score AS next_event_away_score
        FROM teams t
        JOIN leagues l ON t.league_id = l.id
        LEFT JOIN LATERAL (
            SELECT e.*
            FROM events e
            WHERE
                (e.home_team_id = t.id OR e.away_team_id = t.id)
                AND (e.date < NOW() and e.date > NOW() - INTERVAL '1 week')
            ORDER BY e.date DESC, e.id DESC
            LIMIT 1
        ) AS last_event ON TRUE
        LEFT JOIN LATERAL (
            SELECT e.*
            FROM events e
            WHERE
                (e.home_team_id = t.id OR e.away_team_id = t.id)
                AND e.date >= NOW()
            ORDER BY e.date ASC, e.id ASC
            LIMIT 1
        ) AS next_event ON TRUE
        WHERE t.user_selection = TRUE AND 
        (last_event.id IS NOT NULL OR next_event.id IS NOT NULL);"""


def get_selected_teams_and_events(db_conn_string):
    with psycopg.connect(db_conn_string) as conn:
        with conn.cursor(row_factory=tuple_row) as cur:
            cur.execute(QUERY)
            rows = cur.fetchall()
            return rows


def utc_to_local_string(_date):
    _date = _date.replace(tzinfo=ZoneInfo("UTC"))
    return _date.astimezone(ZoneInfo("America/Chicago")).strftime("%b %d %Y @ %I:%M %p")
       

def process_row(row:tuple):
    if row[12]:
        _last = {
            "date":utc_to_local_string(row[14]),
            "name":row[15],
            "score": f"{row[21]}-{row[22]}",
        }
    else:
        _last = None
    if row[23]:
        _next = {
            "date":utc_to_local_string(row[25]),
            "name":row[26]
        }
    else:
        _next = None
    return (_last, _next)


def build_trmnl_payload(last_events, next_events):
    _last = sorted([x for x in last_events if x is not None],
                   key=lambda x: x['date'])
    _next = sorted([x for x in next_events if x is not None],
                   key=lambda x: x['date'])
    core_payload = {"last": {x:_last[x] for x in range(len(_last))},
                    "next": {x:_next[x] for x in range(len(_next))}}
    return {"merge_variables": core_payload}

def run_upload(cfg):
    logging.config.dictConfig(cfg.LOG_CONFIG)
    logger = logging.getLogger(__name__)
    logger.info("Sport Scores Upload Starting")

    # Create DB Connection String
    db_conn_string =cfg.DATABASE_URL
    # Get the user-selected teams and their last/next events
    logger.info("Retrieving user-selected teams and their last/next events from the database")
    selected_teams_and_events = get_selected_teams_and_events(db_conn_string)
    last, next = zip(*[process_row(row) for row in selected_teams_and_events])
    logger.info(f"Retrieved {len(last)} complete events and {len(next)} upcoming events for user-selected teams")
    # Prep data to upload for TRMNL
    logging.info("Preparing data for TRMNL payload")
    payload = build_trmnl_payload(last, next)
    # Upload to TRMNL
    logging.info("Uploading data to TRMNL webhook")
    try:
        response = requests.post(cfg.WEBHOOK_URL, json=payload, verify=False)
        response.raise_for_status()
        logging.debug(f"Webhook response from {cfg.WEBHOOK_URL}: {response.status_code} - {response.text}")
        logging.info("Data successfully sent to webhook.")
    except requests.RequestException as e:
        logging.error(f"Error sending data to webhook: {e}")

    
    