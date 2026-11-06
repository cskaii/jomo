#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
[ -f backend/.env ] || cp backend/.env.example backend/.env
[ -f frontend/.env.local ] || cp frontend/.env.example frontend/.env.local
(cd frontend && npm ci)
printf '%s\n' 'Dependencies installed. See README.md before starting services. No sample rows inserted.'
