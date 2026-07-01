SELECT
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
 (last_event.id IS NOT NULL OR next_event.id IS NOT NULL);

/*WHERE t.name ILIKE 'twins' and l.name = 'MLB';*/

/*WHERE t.user_selection = TRUE;*/