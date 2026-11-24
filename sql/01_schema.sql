CREATE TABLE IF NOT EXISTS competitions(
    competition_id INT ,
    season_id INT ,
    competition_name TEXT NOT NULL , 
    season_name TEXT NOT NULL,
    country_name TEXT,
    PRIMARY KEY (competition_id, season_id)
);

CREATE TABLE IF NOT EXISTS teams(
    team_id INT PRIMARY KEY, 
    team_name TEXT NOT NULL 
);

CREATE TABLE IF NOT EXISTS players (
    player_id       INT PRIMARY KEY,
    player_name     TEXT NOT NULL,
    player_nickname TEXT,
    country_name    TEXT
);

CREATE TABLE IF NOT EXISTS matches (
    match_id       INT PRIMARY KEY,
    competition_id INT NOT NULL,
    season_id      INT NOT NULL,
    match_date     DATE NOT NULL,
    kick_off       TIME,
    match_week     INT,
    home_team_id   INT NOT NULL REFERENCES teams(team_id),
    away_team_id   INT NOT NULL REFERENCES teams(team_id),
    home_score     INT,
    away_score     INT,
    stadium_name   TEXT,
    referee_name   TEXT,
    FOREIGN KEY (competition_id, season_id)
        REFERENCES competitions(competition_id, season_id)
);

CREATE TABLE IF NOT EXISTS events (
    event_id           UUID PRIMARY KEY,
    match_id           INT NOT NULL REFERENCES matches(match_id),
    event_index        INT NOT NULL,
    period             INT,
    minute             INT,
    second             INT,
    type_name          TEXT NOT NULL,
    team_id            INT REFERENCES teams(team_id),
    player_id          INT REFERENCES players(player_id),
    possession         INT,
    possession_team_id INT REFERENCES teams(team_id),
    play_pattern       TEXT,
    location_x         REAL,
    location_y         REAL,
    under_pressure     BOOLEAN DEFAULT FALSE,
    details            JSONB
);

CREATE TABLE IF NOT EXISTS shots (
    event_id     UUID PRIMARY KEY REFERENCES events(event_id),
    match_id     INT NOT NULL REFERENCES matches(match_id),
    team_id      INT NOT NULL REFERENCES teams(team_id),
    player_id    INT REFERENCES players(player_id),
    minute       INT,
    x            REAL,
    y            REAL,
    end_x        REAL,
    end_y        REAL,
    end_z        REAL,
    body_part    TEXT,
    shot_type    TEXT,
    technique    TEXT,
    outcome      TEXT,
    first_time   BOOLEAN DEFAULT FALSE,
    statsbomb_xg REAL
);

CREATE INDEX IF NOT EXISTS idx_events_match ON events(match_id);
CREATE INDEX IF NOT EXISTS idx_events_type  ON events(type_name);
CREATE INDEX IF NOT EXISTS idx_events_team  ON events(team_id);
CREATE INDEX IF NOT EXISTS idx_shots_team   ON shots(team_id);
CREATE INDEX IF NOT EXISTS idx_shots_match  ON shots(match_id);