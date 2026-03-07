# CineScope Analytics

> A SaaS-style movie discovery platform with staff analytics, event tracking, and a data engineering mini-pipeline — built with Django.

**Raw events → ETL → Gold layer → Dashboard + Exports**

![Home](images/cinescope_homepage_combined.png)

---

## What is this?

CineScope is a full-stack Django project that goes beyond a standard CRUD app. It combines a polished movie discovery product with a staff-only analytics dashboard and a real data engineering pipeline — designed to demonstrate end-to-end delivery for **Data Analyst**, **Analytics Engineer**, and **Junior Data Engineer** roles.

---

## Screenshots

| Home                                            | Movie Detail |
|-------------------------------------------------|-------------|
| ![Home](images/cinescope_homepage_combined.png) | ![Movie Detail](images/movie_detail.png) |

| Analytics Dashboard | About |
|---------------------|-------|
| ![Dashboard](images/dashboard.png) | ![About](images/about.PNG) |

> Full walkthrough: `images/cinescope_analytics_combined_full.png`

---

## Why this project matters for hiring

### Data Analyst / BI
- KPI dashboard: views, watches, favorites, active users, top genres/categories/movies
- Funnel analysis: Search → Detail → Watch → Signup
- CSV exports ready for downstream reporting workflows

### Analytics Engineer / Junior Data Engineer
- Event tracking with fact-style data capture
- `build_daily_metrics` management command aggregates raw events into a `DailyMetric` gold table
- `ETLRunLog` table stores run metadata (status, duration, rows updated) — surfaced in the dashboard
- "Raw vs ETL" trend chart illustrates the operational analytics pattern

### Data Scientist (adjacent)
- Produces clean, structured signals suitable for future ML work: recommendations, ranking, cohort analysis

---

## Features

### Movie Discovery (User-facing)
- Hero slider with curated sections on the home page
- Catalog with keyword search across title, cast, description, and genre
- Filters: category, year, genre, max duration, watch availability
- Smart ordering — top-rated results surface first when filtering or searching
- Movie detail page with trailer embed, watch/download links, and related content

### Ratings & Comments
- Per-user rating system (one rating per movie, updatable)
- Live rating updates via AJAX
- SaaS-style comment feed with moderation-ready structure

### Staff Analytics Dashboard
- Date range selector: 7 / 30 / 90 days
- **KPIs**: total views, watches, favorites, active users (7d vs selected range), watch-available count
- **Funnel**: session-based conversion from Search → Detail → Watch → Signup
- **Top tables**: top movies by watches, by favorites, and all-time top rated (with rating count confidence weighting)
- **Data health panel**: flags missing posters, missing trailers, movies with no watch links, unrated movies
- **CSV exports**: Watches, Favorites, Top Rated

### Data Engineering Pipeline (ETL)
- Django management command: `python manage.py build_daily_metrics`
- Aggregates raw event data into `DailyMetric` (gold layer)
- Supports backfill for historical date ranges
- `ETLRunLog` records every run — status, duration, rows written — displayed on the analytics page

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Django 5.x |
| Frontend | Bootstrap 5 (dark SaaS theme), Swiper.js, Chart.js |
| Database | SQLite (local dev) |

---

## Project Structure

```
cinescope-analytics/
└─ src/
   ├─ Imdb/          # Django project config (settings, urls, wsgi, asgi)
   ├─ movie/         # Main app — models, views, templates, analytics, ETL
   ├─ static/        # CSS, JS, images
   ├─ templates/     # Global templates (base.html, etc.)
   ├─ images/        # README screenshots
   ├─ media/         # Uploaded images (local dev only, gitignored)
   ├─ manage.py
   └─ requirements.txt
```

---

## Getting Started

```bash
git clone https://github.com/your-username/cinescope-analytics.git
cd cinescope-analytics/src

pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

To seed the gold layer after collecting events:

```bash
python manage.py build_daily_metrics
# Backfill a date range:
python manage.py build_daily_metrics --start 2024-01-01 --end 2024-03-31
```

The analytics dashboard is accessible to staff users at `/analytics/`.

---

## Data Model Overview

```
UserEvent (raw)  ──▶  build_daily_metrics  ──▶  DailyMetric (gold)
WatchHistory                                      ETLRunLog (observability)
Favorite
Rating
Comment
```

---

## Roadmap

- [ ] PostgreSQL support for production deployments
- [ ] Celery-based scheduled ETL runs
- [ ] Cohort retention charts
- [ ] REST API for external BI tool integration (Metabase, Superset)