#!/usr/bin/env bash
set -o errexit

echo "=== CineScope Analytics — Render Build Script ==="

echo "Step 1: Installing dependencies..."
pip install -r requirements.txt

echo "Step 2: Collecting static files..."
python manage.py collectstatic --noinput

echo "Step 3: Running database migrations..."
python manage.py migrate --noinput

echo "Step 4: Seeding demo analytics data..."
python manage.py seed_demo_analytics

echo "Step 5: Building daily metrics..."
python manage.py build_daily_metrics

echo "=== Build complete ==="
