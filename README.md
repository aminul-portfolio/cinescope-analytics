# CineScope Analytics — Movie Discovery + Product Analytics (Django)

> A SaaS-style movie discovery platform with staff analytics, event tracking, and a data engineering mini-pipeline — built with Django.  
> **Raw events → ETL → Gold layer → Dashboard + Exports + ETL Run Log**

![Home](src/images/cinescope_homepage_combined.png)

---

## What is this?

**CineScope Analytics** is a full-stack Django product built to demonstrate **Data Analyst** and **Junior Data Engineer / Analytics Engineer** capabilities — not just CRUD.

It combines:
- A polished movie discovery experience (search, filters, ratings, comments)
- A **staff-only analytics dashboard** (KPIs, funnel, top tables, exports)
- A **DE mini-pipeline** that transforms raw events into daily aggregates (`DailyMetric`) with **ETL observability** (`ETLRunLog`)

---

## Screenshots

Screenshots are stored in `src/images/`.

- **Home**  
  ![Home](src/images/cinescope_homepage_combined.png)

- **Movie Detail**  
  ![Movie Detail](src/images/movie_detail.png)

- **Analytics Dashboard**  
  ![Analytics](src/images/dasboard.png)

- **About**  
  ![About](src/images/about.PNG)

- **Full walkthrough**  
  ![Full walkthrough](src/images/cinescope_analytics_combined_full.png)

---

## Why this project is hiring-relevant

### ✅ Data Analyst / BI
- KPI dashboard: **views, watches, favorites, active users, top categories/genres/movies**
- Funnel analysis: **Search → Detail → Watch → Signup** (session-based)
- **CSV exports** for reporting workflows and downstream analysis

### ✅ Analytics Engineer / Junior Data Engineer
- Event tracking (fact-style capture) + operational analytics patterns
- **ETL job (`build_daily_metrics`)** builds daily aggregates into `DailyMetric` (gold layer)
- **ETL Run Log (`ETLRunLog`)** records status, duration, rows updated, and errors
- Dashboard includes **Raw vs ETL** trend view + **ETL observability** section

### ✅ Data Scientist (supporting, not ML-heavy)
- Produces clean, structured signals suitable for future ML (ranking, recommendations, cohorts)
- No fake ML claims — positioned correctly

---

## Key Features

### 🎬 Movie Discovery (User-facing)
- Modern homepage with **hero slider** + curated sections
- Movie catalog with:
  - Keyword search across **title, cast, description, genre**
  - Filters: **category, year, genre, max duration, watch availability**
  - **Smart ordering**: top-rated results surface first when filtering/searching
- Movie detail page with:
  - Trailer embed
  - Watch/download links
  - Related + recommended content

### ⭐ Ratings + 💬 Comments
- **Per-user rating**: one rating per user per movie (updatable)
- Live rating updates (AJAX) across UI
- SaaS-style comment feed + comment form (moderation-ready)

### 📊 Staff Analytics Dashboard
- Date ranges: **7 / 30 / 90 days**
- KPIs:
  - Total views
  - Watches + favorites (range-based)
  - Active users (7d vs selected range)
  - Watch-available count
- Funnel (session-based):
  - Search → Detail → Watch → Signup
- Top tables:
  - Top movies by watches
  - Top movies by favorites
  - Top rated (all-time; includes rating_count for confidence)
- Data Health panel:
  - Missing posters, missing trailers
  - No watch links
  - Unrated movies
- **CSV exports**:
  - Watches CSV, Favorites CSV, Top Rated CSV

### 🏗️ Data Engineering Mini-Pipeline (ETL)
- Management command: `build_daily_metrics`
- Builds daily aggregated metrics into `DailyMetric` (gold layer)
- Supports backfill + custom date ranges
- ETL run log shown in dashboard (status + duration + rows written)

---

## Tech Stack

- Python 3.11+
- Django 5.x
- Bootstrap 5 (dark SaaS theme)
- Swiper.js (hero slider)
- Chart.js (analytics charts)
- SQLite (local development)

---

## Project Structure

```text
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