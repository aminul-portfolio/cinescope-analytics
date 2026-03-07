# CineScope Analytics

> A SaaS-style movie discovery platform with a staff analytics dashboard and a data engineering mini-pipeline — built with Django.

**Raw events → ETL → Gold layer → Dashboard + Exports + Observability**

![Home](images/cinescope_homepage_combined.png)

---

## For Hiring Managers

This is not a basic CRUD web app. CineScope is a **data product** designed to demonstrate practical capability across **Data Analytics**, **Business Intelligence**, and **Junior Data Engineering** workflows.

It captures raw user engagement signals, transforms them through an ETL process into a gold-layer metrics table, and surfaces those results in a staff analytics dashboard with KPI reporting, CSV exports, and ETL observability.

### What this project proves

**Data Analyst / BI**
- Builds a KPI dashboard from product activity data
- Tracks user behaviour across a session-based funnel: **Search → Detail → Watch → Signup**
- Supports date filtering, ranked tables, and CSV exports for reporting workflows
- Applies confidence-aware ranking for top-rated content

**Analytics Engineer / Junior Data Engineer**
- Implements a real ETL command: `build_daily_metrics`
- Reads from raw activity and engagement tables
- Writes curated daily aggregates into a gold table: `DailyMetric`
- Logs pipeline execution into `ETLRunLog` with status, duration, row count, and error visibility
- Exposes pipeline health directly in the analytics interface

### Interview story in one sentence

> *“Raw events and engagement signals flow into a daily aggregation job, which writes a gold table consumed by a dashboard, with ETL run logging and basic data health checks.”*

---

## Screenshots

<table>
  <tr>
    <td width="50%" valign="top" align="center">
      <img src="images/dasboard.png" alt="Analytics Dashboard" width="100%"><br>
      <b>Analytics Dashboard</b>
      <br><br>

      <img src="images/movie_detail.png" alt="Movie Detail" width="100%"><br>
      <b>Movie Detail</b>
      <br><br>

      <img src="images/about.PNG" alt="About" width="100%"><br>
      <b>About</b>
    </td>

    <td width="50%" valign="top" align="center">
      <img src="images/cinescope_analytics_combined_full.png" alt="Full Walkthrough" width="100%"><br>
      <b>Full Walkthrough</b>
    </td>
  </tr>
</table>

---

## Core Features

### 1) Movie Discovery Experience
- Home page with hero slider and curated content rows
- Recent, top-rated, and most-watched content sections
- Full movie catalogue with keyword search
- Search across title, cast, description, and genre
- Filter options for category, year, genre, duration, and watch availability
- Smart result ordering when filters are active:
  - rating
  - rating count
  - views
  - recency
- Movie detail pages with:
  - trailer embed
  - watch/download links
  - related content recommendations

### 2) Ratings & User Interaction
- Per-user rating model: one rating per movie per user
- Users can update their existing rating later
- Live AJAX updates across the UI
- Comment feed structure prepared for moderation workflows

### 3) Staff Analytics Dashboard
- Preset date ranges: **7 / 30 / 90 days**
- KPI cards for:
  - total views (all-time)
  - watches in range
  - favorites in range
  - active users
  - watch-available movie count
- Session-based product funnel:
  - Search
  - Detail
  - Watch
  - Signup
- Top tables:
  - top movies by watches
  - top movies by favorites
  - top-rated movies using confidence weighting
- Data health checks:
  - missing posters
  - missing trailers
  - movies with no watch links
  - unrated movies
- CSV exports for:
  - watches
  - favorites
  - top-rated movies
- Embedded ETL run log with:
  - success/fail status
  - duration
  - rows updated
  - error messages
  - run timestamp

---

## Data Engineering Pipeline

### Pipeline Architecture

```text
Raw Layer                              Gold Layer          Observability
──────────────────────────────         ──────────────      ─────────────
Event (search/detail/watch/signup)                         ETLRunLog
WatchHistory                      ──▶  DailyMetric    ──▶  (status, duration,
Favorite                               (daily aggs)        rows, errors)
MovieRating
