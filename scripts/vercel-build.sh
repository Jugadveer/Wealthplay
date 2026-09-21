#!/usr/bin/env bash
#
# Vercel build.
#
# Runs before the Python function is packaged, so everything it produces ends up
# inside the deployed bundle. Three things have to happen here and nowhere else:
# a serverless function cannot write to disk at request time, so the React build
# and the collected static files must already exist when a request arrives.
#
#   1. Build the React app into  static/react/
#   2. Collect static into       staticfiles/     (what WhiteNoise serves)
#   3. Apply migrations and create the cache table
#
# Step 3 needs DATABASE_URL to be set in the Vercel project. It is skipped with a
# warning rather than failing the build when it is missing, so a first deploy
# still comes up and tells you what is wrong instead of erroring opaquely.

set -euo pipefail

echo "--- building the frontend ---"
npm --prefix frontend ci
npm --prefix frontend run build

echo "--- collecting static files ---"
python manage.py collectstatic --noinput --clear

# Vercel serves the output directory at the site root, so `staticfiles/` alone
# would publish the bundle at /react/assets/... while the built HTML asks for
# /static/react/assets/.... Nesting it under `public/static` lines the two up,
# which lets the CDN serve the assets directly and keeps them out of the
# function entirely. WhiteNoise still serves them from inside the bundle if a
# request ever reaches Django.
echo "--- publishing static files for the CDN ---"
rm -rf public
mkdir -p public
cp -r staticfiles public/static

if [ -n "${DATABASE_URL:-}" ]; then
  echo "--- applying migrations ---"
  python manage.py migrate --noinput

  # The cache backend is a database table when REDIS_URL is unset, which is the
  # right default on serverless: an in-memory cache is discarded between
  # invocations, so it would never register a hit.
  echo "--- ensuring the cache table exists ---"
  python manage.py createcachetable

  echo "--- seeding content ---"
  python manage.py seed_scenarios || echo "    (no seed command; skipping)"
else
  echo "!!! DATABASE_URL is not set."
  echo "!!! Migrations were skipped and the app will fail at runtime."
  echo "!!! Add a Postgres URL in the Vercel project settings and redeploy."
fi

echo "--- build complete ---"
