#!/bin/sh
set -e                      # stop immediately if any command fails

alembic upgrade head        # bring the database up to date
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1