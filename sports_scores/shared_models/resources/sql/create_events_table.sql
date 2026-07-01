CREATE TABLE IF NOT EXISTS events (
    id INT NOT NULL PRIMARY KEY,
    uid VARCHAR(50) UNIQUE NOT NULL,
    date TIMESTAMP NOT NULL,
    name VARCHAR(255) NOT NULL,
    short_name VARCHAR(50) NOT NULL,
    season VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    home_team_id VARCHAR(50) NOT NULL,
    away_team_id VARCHAR(50) NOT NULL,
    FOREIGN KEY (home_team_id) REFERENCES teams(id),
    FOREIGN KEY (away_team_id) REFERENCES teams(id),
    home_score INT,
    away_score INT
);