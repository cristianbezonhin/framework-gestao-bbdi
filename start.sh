#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python -m scripts.seed
exec uvicorn app:app --host 0.0.0.0 --port "${PORT:-18090}" --reload
