#!/bin/sh

if [ ! -f "/app/.env" ]
then
    ln -s /app/env/.env /app/.env
fi

cd /app
. .venv/bin/activate
python sync.py