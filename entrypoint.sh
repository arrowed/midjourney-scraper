#!/bin/sh

if [ ! -f "/app/.env" ]; then
    ln -s /app/env/.env /app/.env
fi

find /app

cd /app
source venv/bin/activate
python sync.py