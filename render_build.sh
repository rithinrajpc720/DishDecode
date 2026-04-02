#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files with Whitenoise
echo "Collecting static files... 🚀"
python manage.py collectstatic --no-input
echo "Static files collected! ✅"
