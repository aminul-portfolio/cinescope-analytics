# CineScope Analytics

> A SaaS-style movie discovery platform with a staff analytics dashboard and a data engineering mini-pipeline — built with Django.

**Raw events → ETL → Gold layer → Dashboard + Exports + Observability**

![Home](images/cinescope_homepage_combined.png)

---

## For Hiring Managers

This is not a CRUD web app. CineScope is a **data product** — it captures raw engagement signals, runs a scheduled ETL pipeline to build a gold aggregates layer, and surfaces the results in a KPI dashboard with CSV exports and ETL observability. Here's what that means for each role:

**Data Analyst / BI**
— KPI dashboard with watches, favorites, active users, top movies/genres/categories, and a session-based product funnel (Search → Detail → Watch → Signup). Date range selectors, smart ordering, and CSV exports ready for downstream reporting.

**Analytics Engineer / Junior Data Engineer**
— A real ETL job (`build_daily_metrics` management command) that reads raw event and engagement tables and writes aggregated daily metrics to a `DailyMetric` gold table. Every run is logged to `ETLRunLog` with status, duration, row count, and error messages — surfaced directly on the analytics page.

**The interview story in one sentence:**
> *"Raw events and engagement signals flow into a daily aggregation job, which writes a gold table consumed by a dashboard, with ETL run logging and basic data health checks."*

---

## Screenshots

| | |
|---|---|
| ![Movie Detail](images/movie_detail.png) | ![Dashboard](images/dasboard.png) |
| Movie Detail | Analytics Dashboard |
| ![About](images/about.PNG) | ![Full Walkthrough](images/cinescope_analytics_combined_full.png) |
| About | Full Walkthrough |

---

## Features

### Movie Discovery
- Home page with hero slider and curated rows (recent, top-rated, most watched)
- Full catalog with keyword search across title, cast, description, and genre
- Filters: category, year, genre, max duration, watch availability
- Smart result ordering when filters are active: rating → rating count → views → recency
- Movie detail pages with trailer embed, watch/download links, and related content

### Ratings & Comments
- Per-user ratings (one per movie, updatable) with live AJAX updates across the UI
- Comment feed with a moderation-ready structure

### Staff Analytics Dashboard
- **Date ranges**: 7 / 30 / 90 days
- **KPIs**: total views (all-time), watches + favorites (range), active users (7d vs range), watch-available count
- **Product funnel**: Search → Detail → Watch → Signup (session-based)
- **Top tables**: top movies by watches, by favorites, and all-time top rated with rating-count confidence weighting
- **Data health panel**: flags missing posters, missing trailers, movies with no watch links, and unrated movies
- **CSV exports**: Watches, Favorites, Top Rated
- **ETL Run Log**: status (success/fail), duration, rows updated, error message, run timestamp

---

## Data Engineering Pipeline

### Architecture

```
Raw Layer                              Gold Layer          Observability
──────────────────────────────         ──────────────      ─────────────
Event (search/detail/watch/signup)                         ETLRunLog
WatchHistory                      ──▶  DailyMetric    ──▶  (status, duration,
Favorite                               (daily aggs)        rows, errors)
MovieRating
```

### Running the ETL

```bash
# Yesterday (default)
python manage.py build_daily_metrics

# Specific day
python manage.py build_daily_metrics --day 2026-03-07

# Backfill from first available signal to today
python manage.py build_daily_metrics --backfill

# Custom date range
python manage.py build_daily_metrics --from 2026-03-01 --to 2026-03-07
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

The analytics dashboard is available to staff users at `/analytics/`.

---

## Tech Stack

| | |
|---|---|
| **Backend** | Python 3.11+, Django 5.x |
| **Frontend** | Bootstrap 5 (dark SaaS theme), Swiper.js, Chart.js |
| **Database** | SQLite (local dev) |

---

## Project Structure

```
cinescope-analytics/
└─ src/
   ├─ Imdb/        # Django project config (settings, urls, wsgi, asgi)
   ├─ movie/       # Main app — models, views, templates, analytics, ETL
   ├─ static/      # CSS, JS, assets
   ├─ templates/   # Global templates (base.html, etc.)
   ├─ images/      # README screenshots
   ├─ media/       # Uploaded images (local dev only, gitignored)
   ├─ manage.py
   └─ requirements.txt
```
