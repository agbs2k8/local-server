SELECT
    COUNT(id),
    league_id
FROM teams
GROUP BY league_id