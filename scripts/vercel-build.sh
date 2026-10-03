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

# Pick the interpreter that can actually import the installed packages.
#
# The platform installs the function's dependencies against one Python and may
# put a different one first on PATH — here, packages built for CPython 3.14.7
# while `python3` resolved to 3.12.14. Pure-Python packages do not care, so
# Django imported and the build looked fine; `psycopg-binary` is a compiled
# extension built for one ABI, and it failed with "Error loading psycopg2 or
# psycopg module" only once collectstatic loaded the models.
#
# So the test is a compiled package, not just Django, and every candidate is
# tried before giving up and installing.
# Both compiled packages are in the probe on purpose. Django is pure Python and
# imports under any version, so testing it alone is what let a 3.12 interpreter
# look correct while the 3.14-built psycopg wheel could not load.
#
# Keep this list matched to requirements.txt. It briefly asked for pandas after
# pandas had been removed, so nothing could satisfy it and every build fell
# through to the install path below.
probe() {
    "$1" -c 'import django, psycopg, curl_cffi' 2>/dev/null
}

PY=''
for candidate in \
    python3.14 python3.13 python3.12 python3 python \
    /uv/python/versions/*/bin/python3
do
    path=$(command -v "$candidate" 2>/dev/null || { [ -x "$candidate" ] && echo "$candidate"; })
    [ -n "$path" ] || continue
    if probe "$path"; then
        PY="$path"
        echo "--- using $("$PY" --version), which can import the installed packages ---"
        break
    fi
done

if [ -z "$PY" ]; then
    # Nothing here has a working set, so build one. Slower, and it always
    # produces wheels matching the interpreter that will run them.
    PY=$(command -v python3 || command -v python)
    echo "--- no interpreter had the dependencies; installing for $("$PY" --version) ---"

    # uv manages the interpreter on this platform and refuses a plain pip
    # install into it (PEP 668, "externally-managed-environment"), so use uv
    # when it is present and only then fall back to pip.
    if command -v uv >/dev/null 2>&1; then
        uv pip install --python "$PY" --quiet -r requirements.txt
    else
        "$PY" -m pip install --disable-pip-version-check -q \
            --break-system-packages -r requirements.txt
    fi
fi

echo "--- building the frontend ---"
npm --prefix frontend ci
npm --prefix frontend run build

echo "--- collecting static files ---"
"$PY" manage.py collectstatic --noinput --clear

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
  "$PY" manage.py migrate --noinput

  # The cache backend is a database table when REDIS_URL is unset, which is the
  # right default on serverless: an in-memory cache is discarded between
  # invocations, so it would never register a hit.
  echo "--- ensuring the cache table exists ---"
  "$PY" manage.py createcachetable

  echo "--- seeding content ---"
  "$PY" manage.py seed_scenarios || echo "    (no seed command; skipping)"
else
  echo "!!! DATABASE_URL is not set."
  echo "!!! Migrations were skipped and the app will fail at runtime."
  echo "!!! Add a Postgres URL in the Vercel project settings and redeploy."
fi

echo "--- build complete ---"
