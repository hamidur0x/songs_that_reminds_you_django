#!/usr/bin/env bash
set -o errexit

echo "Checking DJANGO_SECRET_KEY..."

if [ -z "${DJANGO_SECRET_KEY:-}" ]; then
    echo "ERROR: DJANGO_SECRET_KEY is MISSING during build!"
    exit 1
else
    echo "SUCCESS: DJANGO_SECRET_KEY is available during build."
fi

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput