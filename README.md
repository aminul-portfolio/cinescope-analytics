# CineScope Analytics

A Django-based movie discovery platform that demonstrates product analytics, ETL pipeline design, and dashboard reporting in a portfolio-ready data product.

**Raw events → ETL → Gold layer → Dashboard + Exports + Observability**

---

## Overview

CineScope is not a basic CRUD app. It is a **data product** built to demonstrate practical skills across **Data Analysis**, **Business Intelligence**, **Analytics Engineering**, and **Junior Data Engineering**.

The application captures raw user engagement signals, transforms them through an ETL pipeline into a gold-layer metrics table, and surfaces those results in a staff analytics dashboard with KPI reporting, ranked tables, CSV exports, and pipeline observability.

The project follows a common analytics pattern: raw activity data flows into a daily aggregation job, the job writes curated output into a `DailyMetric` table, and that table is consumed by a dashboard with filtering, reporting, and data health checks. Pipeline execution is logged in `ETLRunLog` with status, duration, row count, and error visibility.

---

## What This Demonstrates

### Data Analyst / BI
- KPI dashboard built from product activity data with preset date ranges
- Session-based funnel tracking across **Search → Detail → Watch → Signup**
- Ranked content tables with confidence-weighted rating scores
- Date-filtered CSV exports for reporting workflows
- Data health checks surfaced directly in the dashboard interface

### Analytics Engineer / Junior Data Engineer
- ETL management command (`build_daily_metrics`) that reads from raw activity and engagement tables and writes aggregated daily records to a gold table
- `ETLRunLog` tracks each run's status, duration, rows written, and any error output
- Pipeline health is visible in the analytics interface, not only in terminal logs
- Separation of raw signals, transformed metrics, and observable ETL execution

---

## Interview Story

Raw engagement events flow into a daily ETL job that builds a gold-layer metrics table consumed by a staff analytics dashboard, with ETL logging and data health visibility.

---

## Features

### Movie Discovery
- Home page with hero section and curated content rows
- Recent, top-rated, and most-watched movie sections
- Full catalogue with keyword search across title, cast, description, and genre
- Filters for category, year, genre, duration, and watch availability
- Smart result ordering when filters are active: rating, rating count, views, recency
- Movie detail pages with trailer embed, watch/download links, and related content

### Ratings & Interaction
- Per-user rating model: one rating per movie per user, updatable
- Live AJAX rating updates across the UI
- Comment feed structure prepared for moderation workflows

### Staff Analytics Dashboard
- KPI cards for total views, watches in range, favourites in range, active users, and watch-available count
- Session funnel: **Search → Detail → Watch → Signup**
- Top tables for movies by watches, movies by favourites, and top-rated content using confidence weighting
- Data health checks for missing posters, missing trailers, no watch links, and unrated movies
- CSV exports for watches, favourites, and top-rated movies
- Embedded ETL run log with status, duration, rows written, error messages, and timestamp

---

## Data Pipeline Architecture

```text
Raw Layer                                Gold Layer        Observability
─────────────────────────────────        ──────────────    ─────────────────────
Event (search / detail / watch /                           ETLRunLog
signup)                            ──▶  DailyMetric  ──▶  status, duration,
WatchHistory                              (daily aggs)     rows written, errors
Favourite
MovieRating
