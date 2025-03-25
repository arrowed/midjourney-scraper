#!/bin/sh

if [ ! -f "/app/.env" ]
then
    ln -s /app/env/.env /app/.env
fi

cd /app
. .venv/bin/activate

. /app/.env

if [ -z "$MJ_COMMAND" ]
then
    MJ_COMMAND=scrape
fi

python mj.py --env /app/.env $MJ_OPTS $MJ_COMMAND $COMMAND_OPTS
