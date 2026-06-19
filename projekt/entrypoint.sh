#!/bin/sh
set -e

echo "Applying database migrations..."
python manage.py migrate --no-input

echo "Seeding sample data (skipped if already exists)..."
python manage.py seed_data

echo "Starting development server..."
exec python manage.py runserver 0.0.0.0:8000