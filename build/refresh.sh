#!/usr/bin/env bash
# Refresh a snapshot end-to-end: fetch sources -> build -> correlate.
# Loads secrets from .env (gitignored) if present, and prompts for any missing
# OpenAlex credentials. Usage:
#   build/refresh.sh            # full refresh (fetch + build + correlate)
#   build/refresh.sh --no-fetch # rebuild from existing data/sources CSVs only
set -euo pipefail
cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -a; . ./.env; set +a
fi

if [ -z "${OPENALEX_API_KEY:-}" ]; then
  read -rp "OpenAlex API key (blank = rate-limited public pool): " OPENALEX_API_KEY || true
  export OPENALEX_API_KEY
fi
if [ -z "${OPENALEX_MAILTO:-}" ]; then
  read -rp "OpenAlex contact email (optional, for polite pool): " OPENALEX_MAILTO || true
  export OPENALEX_MAILTO
fi

if [ "${1:-}" != "--no-fetch" ]; then
  echo ">> fetching sources ..."
  python3 build/fetch_sources.py
fi
echo ">> building snapshot ..."
python3 build/build_snapshot.py
echo ">> correlation study ..."
python3 build/correlate.py
echo ">> done."
