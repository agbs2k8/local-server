SELECT 
    events.*,
    home_team.*,
    away_team.*
FROM events
JOIN teams AS home_team ON events.home_team_id = home_team.id
JOIN teams AS away_team ON events.away_team_id = away_team.id
/*WHERE home_team.name = 'Lynx' OR away_team.name = 'Lynx';*/
WHERE home_team.name = 'Twins' OR away_team.name = 'Twins';