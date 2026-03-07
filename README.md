# CineScope Analytics — Movie Discovery + Product Analytics (Django)

> **SaaS-style movie discovery platform** with **staff analytics**, **event tracking**, and a **Data Engineering mini-pipeline** — built with Django.  
> **Raw events → ETL → Gold layer → Dashboard + Exports + Observability**

![Home](images/cinescope_homepage_combined.png)

---

## Hiring Summary (DA + DE Focus)

This project is intentionally **not just a CRUD web app**. It is a **data product** that demonstrates:

### ✅ Data Analyst / BI Outcomes
- **KPI dashboard**: watches, favorites, active users, top categories/genres/movies
- **Product funnel** (session-based): **Search → Detail → Watch → Signup**
- **Smart ordering**: top-rated results surface first when filtering/searching
- **CSV exports** for reporting workflows (top watches / favorites / top rated)

### ✅ Data Engineer / Analytics Engineer Outcomes
- **Raw event capture** (fact-style tracking via `Event`)
- **ETL job** (Django management command) builds a **gold table**: `DailyMetric`
- **ETL observability** via `ETLRunLog` (status, duration, rows updated, error message) surfaced in the dashboard
- **Raw vs ETL trend** pattern (operational analytics): dashboard shows both raw-series and ETL-series

**DE story you can tell in interviews:**  
> “Built a small analytics pipeline: raw events and engagement signals → daily aggregates (gold layer) → dashboard + exports, with ETL logging and basic freshness checks.”

---

## Screenshots

Screenshots are stored in `images/`.

- **Home**  
  ![Home](images/cinescope_homepage_combined.png)

- **Movie Detail**  
  ![Movie Detail](images/movie_detail.png)

- **Analytics Dashboard**  
  ![Analytics Dashboard](images/dasboard.png)

- **About**  
  ![About](images/about.PNG)

- **Full walkthrough**  
  ![Full walkthrough](images/cinescope_analytics_combined_full.png)

---

## What the App Does

### Movie Discovery (User-facing)
- Home page with **hero slider** + curated rows (recent/top/most watched)
- Catalog with:
  - Keyword search across **title, cast, description, genre**
  - Filters: **category, year, genre, max duration, watch availability**
  - **Smart ordering**: when filters/search are active, results prioritize:
    1) rating  
    2) rating count  
    3) views  
    4) recency
- Movie detail:
  - Trailer embed (if provided)
  - Watch/download links
  - Related + recommended content

### Ratings + Comments (Engagement signals)
- **Per-user rating**: one rating per user per movie (update allowed)
- Rating aggregates update across UI + analytics
- **Comment feed** + SaaS-style comment form (moderation-ready)

### Staff Analytics Dashboard (Manager / Analyst view)
- Date ranges: **7 / 30 / 90 days**
- KPIs:
  - Total views (all time)
  - Watches + favorites (selected range)
  - Active users (7d vs selected range)
  - Watch-available count
- Funnel (session-based):
  - Search → Detail → Watch → Signup
- Top tables:
  - Top movies by watches (range)
  - Top movies by favorites (range)
  - Top rated (all-time, with rating-count confidence)
- Data health panel:
  - Missing posters, missing trailers
  - No watch links
  - Unrated movies
- **CSV exports** (enterprise reporting):
  - Watches CSV, Favorites CSV, Top Rated CSV
- **ETL Run Log** (operations):
  - Status (success/fail), duration, rows, error message, time started

---

## Data Engineering Mini-Pipeline (ETL)

### Data flow
- **Raw layer (events + engagement signals)**:
  - `Event` (search/detail/watch/signup)
  - `WatchHistory`, `Favorite`, `MovieRating`
- **Gold layer**:
  - `DailyMetric` (daily aggregates for dashboard + future BI)
- **Observability**:
  - `ETLRunLog` tracks every run: duration, rows updated, status, error

### Run ETL
```bash
# Build metrics for yesterday (default behavior)
python manage.py build_daily_metrics

# Build metrics for a specific day
python manage.py build_daily_metrics --day 2026-03-07

# Backfill from first available signal date to today
python manage.py build_daily_metrics --backfill

# Custom range
python manage.py build_daily_metrics --from 2026-03-01 --to 2026-03-07

Tech Stack

Python 3.11+

Django 5.x

Bootstrap 5 (dark SaaS theme)

Swiper.js (hero slider)

Chart.js (analytics charts)

SQLite (local development)

cinescope-analytics/
└─ src/
   ├─ Imdb/          # Django project config (settings/urls/wsgi/asgi)
   ├─ movie/         # Main app (models, views, templates, analytics, ETL)
   ├─ static/        # CSS/JS/assets
   ├─ templates/     # Global templates (base.html etc.)
   ├─ images/        # README screenshots
   ├─ media/         # Uploaded images (local dev; gitignored)
   ├─ manage.py
   └─ requirements.txt