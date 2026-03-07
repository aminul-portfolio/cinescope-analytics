# CineScope Analytics

A SaaS-style movie discovery platform with a staff analytics dashboard and a data engineering mini-pipeline, built with Django.

**Raw events → ETL → Gold layer → Dashboard + Exports + Observability**

---

## Overview

CineScope is a data product, not a basic CRUD app. It captures raw user engagement signals, transforms them through an ETL pipeline into a gold-layer metrics table, and surfaces those results in a staff analytics dashboard with KPI reporting, CSV exports, and pipeline observability.

The project is structured around a pattern common in analytics engineering: raw activity data flows into a daily aggregation job, the job writes curated output into a `DailyMetric` table, and that table is consumed by a dashboard with filtering, ranked tables, and data health checks. Pipeline execution is logged in `ETLRunLog` with status, duration, row count, and error visibility.

---

## What This Demonstrates

### Data Analyst / BI
- KPI dashboard built from product activity data with preset date ranges (7 / 30 / 90 days)
- Session-based funnel tracking across Search → Detail → Watch → Signup
- Ranked content tables with confidence-weighted rating scores
- Date-filtered exports to CSV for reporting workflows
- Data health checks surfaced directly in the dashboard interface

### Analytics Engineer / Junior Data Engineer
- ETL management command (`build_daily_metrics`) that reads from raw activity and engagement tables and writes aggregated daily records to a gold table
- `ETLRunLog` tracks each run's status, duration, rows written, and any error output
- Pipeline health is visible within the analytics interface, not just in logs
- Schema designed to separate raw, intermediate, and gold layers

---

## Features

### Movie Discovery
- Home page with hero section and curated content rows (recent, top-rated, most-watched)
- Full catalogue with keyword search across title, cast, description, and genre
- Filters for category, year, genre, duration, and watch availability
- Smart result ordering when filters are active: rating, rating count, views, recency
- Movie detail pages with trailer embed, watch/download links, and related content

### Ratings & Interaction
- Per-user rating model — one rating per movie per user, updatable
- Live AJAX rating updates across the UI
- Comment feed structure prepared for moderation workflows

### Staff Analytics Dashboard
- KPI cards: total views, watches in range, favourites in range, active users, watch-available count
- Session funnel: Search → Detail → Watch → Signup
- Top tables: movies by watches, movies by favourites, top-rated using confidence weighting
- Data health checks: missing posters, missing trailers, no watch links, unrated movies
- CSV exports for watches, favourites, and top-rated movies
- Embedded ETL run log with status, duration, rows updated, error messages, and timestamp

---

## Data Pipeline Architecture

```
Raw Layer                                Gold Layer        Observability
─────────────────────────────────        ──────────────    ─────────────────────
Event (search / detail / watch /                           ETLRunLog
  signup)                           ──▶  DailyMetric  ──▶  status, duration,
WatchHistory                             (daily aggs)      rows written, errors
Favourite
MovieRating
```

The `build_daily_metrics` management command is the core pipeline job. It aggregates the raw layer on a daily grain and upserts into `DailyMetric`. Each run appends a row to `ETLRunLog` regardless of outcome, so pipeline health is queryable.

---

## Tech Stack

- **Backend:** Django, Python
- **Database:** SQLite (development) — swap to PostgreSQL for production
- **Frontend:** Bootstrap, AJAX for live rating updates
- **Pipeline:** Django management command (`build_daily_metrics`)
- **Exports:** CSV via Django's `StreamingHttpResponse`

---

## Getting Started

```bash
git clone <repo-url>
cd cinescope
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py seed_data          # loads demo movies and activity
python manage.py build_daily_metrics  # runs the ETL pipeline
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/` for the discovery experience and `/dashboard/` for the analytics interface (staff login required).

---

## Project Structure

```
cinescope/
├── movies/          # Movie catalogue, ratings, watch history
├── analytics/       # DailyMetric model, ETL command, dashboard views
├── events/          # Raw event capture (search, detail, watch, signup)
├── templates/
└── static/
```

---

## Screenshots

![Home](images/cinescope_homepage_combined.png)

| | |
|---|---|
| ![Movie Detail](images/movie_detail.png) | ![Dashboard](images/dasboard.png) |
| Movie Detail | Analytics Dashboard |
| ![About](images/about.PNG) | ![Full Walkthrough](images/cinescope_analytics_combined_full.png) |
| About | Full Walkthrough |
