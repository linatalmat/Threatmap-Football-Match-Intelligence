# Dictionnaire des données

## matches
| Champ | Type | Description |
|---|---|---|
| match_id | int | Identifiant unique du match |
| match_date | date | Date du match |
| home_team.home_team_name | str | Équipe à domicile |
| home_score | int | Buts à domicile |
| ... | | |

## events (commun à tous les événements)
| Champ | Type | Description |
|---|---|---|
| id | str (uuid) | Identifiant de l'événement |
| type.name | str | Pass, Shot, Pressure, Duel... |
| location | [x, y] | Position sur un terrain 120 × 80 |
| team.name / player.name | str | Équipe et joueur |
| minute / second | int | Moment de l'événement |

## shots (événements où type.name = "Shot")
| Champ | Type | Description |
|---|---|---|
| shot.statsbomb_xg | float | xG calculé par StatsBomb (0 à 1) |
| shot.outcome.name | str | Goal, Saved, Off T, Blocked... |
| shot.body_part.name | str | Pied droit, pied gauche, tête |
| shot.type.name | str | Jeu ouvert, coup franc, penalty, corner |
| shot.end_location | [x, y, z] | Où le tir se termine |coc