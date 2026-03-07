# CineScope Analytics

A Django data product that captures raw user engagement, runs a daily ETL pipeline into a gold-layer metrics table, and surfaces the results in a staff analytics dashboard — with KPI reporting, CSV exports, and pipeline observability built in.

**Raw events → ETL → Gold layer → Dashboard + Exports + Observability**

---

## Overview

CineScope is a data product, not a basic CRUD app. It captures raw user engagement signals, transforms them through an ETL pipeline into a gold-layer metrics table, and surfaces those results in a staff analytics dashboard with KPI reporting, CSV exports, and pipeline observability.

The project is structured around a pattern common in analytics engineering: raw activity data flows into a daily aggregation job, the job writes curated output into a `DailyMetric` table, and that table is consumed by a dashboard with filtering, ranked tables, and data health checks. Pipeline execution is logged in `ETLRunLog` with status, duration, row count, and error visibility.

---

## What This Demonstrates

### Data Analyst / Business Intelligence
- KPI dashboard driven by product activity data, with preset date ranges (7 / 30 / 90 days)
- Session-based funnel tracking: Search → Detail → Watch → Signup
- Confidence-weighted ranking for top-rated content (avoids naive average bias)
- Date-filtered CSV exports ready for use in reporting workflows
- Data quality checks surfaced inside the dashboard: missing posters, missing trailers, unrated titles

### Analytics Engineer / Junior Data Engineer
- `build_daily_metrics` ETL command reads from raw activity and engagement tables and writes aggregated daily records to a gold table (`DailyMetric`)
- `ETLRunLog` records each run's status, duration, row count, and any error output — queryable, not just logged to console
- Pipeline health is visible within the analytics interface itself
- Schema separates raw activity data from aggregated reporting output, following a layered analytics design pattern.

---

## How to Review This Project

If you are short on time, the highest-signal areas are:

| What to look at | Where |
|---|---|
| ETL pipeline logic | `analytics/management/commands/build_daily_metrics.py` |
| Gold table + run log models | `analytics/models.py` |
| Dashboard view and KPI queries | `analytics/views.py` |
| Raw event capture | `events/models.py` |
| Confidence-weighted ranking | `analytics/views.py` → top-rated query |

Run `python manage.py build_daily_metrics` after seeding to see the pipeline execute and write to both `DailyMetric` and `ETLRunLog`.

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
- Data quality checks: missing posters, missing trailers, no watch links, unrated movies
- CSV exports for watches, favourites, and top-rated movies
- Embedded ETL run log with status, duration, rows written, error messages, and timestamp

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

| Layer | Technology | Notes |
|---|---|---|
| Backend | Python 3, Django 5 | ORM used for all queries; `Count`, `Sum`, `annotate`, `TruncDate` used across KPI and trend queries |
| Database | SQLite | Development database; swap to PostgreSQL for production by updating `DATABASES` in `settings.py` |
| Pipeline | Django management command | `build_daily_metrics` — daily grain, upsert pattern, ETL run logging |
| Aggregation | Django ORM + `annotate` / `values` | `Count`, `Avg`, `F`, `Case/When` used across KPI and ranking queries |
| Ranking | Composite sort | Top-rated ordered by `-rating`, `-rating_count`, `-views_count` — higher review volume breaks ties, avoiding bias toward single-review outliers |
| Exports | Python `csv` module + `StreamingHttpResponse` | Memory-safe for large result sets |
| Frontend | Bootstrap 5, vanilla JS fetch (AJAX) | Rating updates without page reload |

---

## Getting Started

**macOS / Linux**

```bash
git clone <repo-url>
cd cinescope-analytics
python3 -m venv .venv && source .venv/bin/activate
cd src
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py build_daily_metrics
python manage.py createsuperuser
python manage.py runserver
```

**Windows**

```bat
git clone <repo-url>
cd cinescope-analytics
python -m venv .venv
.venv\Scripts\activate
cd src
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py build_daily_metrics
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/` for the discovery experience and `http://127.0.0.1:8000/dashboard/` for the analytics interface (staff login required).

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

## Interview Story

> *"I built an event capture layer that logs search, detail, watch, and signup activity. A daily management command aggregates those raw tables into a gold-layer metrics table and logs each run's status and duration. A staff dashboard consumes that layer to show KPIs, a session funnel, ranked content, data quality flags, and CSV exports — mirroring the kind of workflow you'd usually implement with dbt, Airflow, and a warehouse."*

---

## Role Fit

The focus of this project is the data layer — how events are captured, how they are aggregated, and how the results are made useful to a business user. A dashboard like this gives a content or product team direct visibility into what is performing, where users drop off, and whether the underlying data is healthy — without waiting on an ad hoc query. Django is used as infrastructure; the pipeline, schema design, and reporting layer are the main focus.

---

## Best Role Fit

| Role | Why this project is relevant |
|---|---|
| Data Analyst | KPI dashboard, funnel analysis, CSV exports, confidence-weighted ranking |
| BI Developer | Gold-layer consumption pattern, date-range filtering, data quality checks |
| Analytics Engineer | Layered analytics design, ETL command, `DailyMetric` aggregation, run logging |
| Junior Data Engineer | Pipeline design, raw-to-gold transformation, observability via `ETLRunLog` |
| Data Engineer (Graduate) | End-to-end ownership of a pipeline from event capture to reporting layer |

---

## Ownership Notice

This project was designed and developed by **Aminul Islam Sumon** as part of his professional data analytics and Django portfolio.

Copyright © 2026 Aminul Islam Sumon. All rights reserved.

This repository is shared for portfolio, learning, and review purposes only. No part of this codebase may be copied, redistributed, modified, or used commercially without prior written permission from the author.

---

## Author

**Aminul Islam Sumon**  
Python Developer | Data Analytics & Django Projects

- GitHub: https://github.com/aminul-portfolio
- LinkedIn: https://www.linkedin.com/in/aminul-islam-a71a871a2

---

## Screenshots

![Home](images/cinescope_homepage_combined.png)

<table>
<tr>
<td width="50%" valign="top">

**Analytics Dashboard**
![Analytics Dashboard](images/dashboard.png)

</td>
<td width="50%" rowspan="3" valign="top">

**Full Walkthrough**
![Full Walkthrough](images/cinescope_analytics_combined_full.png)

</td>
</tr>
<tr>
<td valign="top">

**Movie Detail**
![Movie Detail](images/movie_detail.png)

</td>
</tr>
<tr>
<td valign="top">

**About**
![About](images/about.PNG)

</td>
</tr>
</table>