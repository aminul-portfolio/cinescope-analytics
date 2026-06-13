# CineScope Analytics — Render Data Fix

## Problem

The Render deployment loads the app but shows no movies, genres, or analytics because the production SQLite database is empty after `migrate`.

## Models (app: `movie`)

| Model | Purpose |
|-------|---------|
| `Movie` | Movie catalogue (title, poster, rating, slug, etc.) |
| `Genre` | Genre tags (M2M on Movie) |
| `DailyMetric` | Gold-layer daily analytics aggregates |
| `ETLRunLog` | ETL pipeline run history |
| `Event`, `WatchHistory`, `Favorite` | Raw engagement data (seeded by `seed_demo_analytics`) |

## Fixture

`fixtures/cinescope_movies.json` — exported from local DB:

- 4 Genre records
- 17 Movie records

## Render Shell commands (run in order)

Open **Render Dashboard → cinescope-analytics → Shell**, then run:

```bash
python manage.py migrate
python manage.py loaddata fixtures/cinescope_movies.json
python manage.py seed_demo_analytics --users 100 --days 30
python manage.py build_daily_metrics
```

## Verify after loading

```bash
python manage.py shell -c "from movie.models import Movie, Genre; print('Movies:', Movie.objects.count()); print('Genres:', Genre.objects.count())"
```

Expected: `Movies: 17`, `Genres: 4`

Then open https://cinescope-analytics.onrender.com/ and confirm homepage carousels and `/movies/` list show titles.

## Notes

- `seed_demo_analytics` requires movies to exist first (run `loaddata` before it).
- `build_daily_metrics` aggregates raw events/watch/favorite data into `DailyMetric`.
- Movie poster files live under `media/movies/` locally; ensure uploaded media is present on Render or posters may 404 (DB records will still load).
