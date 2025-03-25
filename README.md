# Discord Midjourney Wallpaper Downloader

## installing

> python -m venv venv \
> source venv/bin/activate \
> pip install --upgrade pip \
> pip install -r requirements.txt

## Configuring

Duplicate `.env-template` to `.env` and define

- `WALLPAPER_OUTPUT_DIR` The local path to write the images to
- `DISCORD_USER_TOKEN` Your discord token. Open discord and use dev tools to find it (anything with an `Authorization` header)
- `DISCORD_CHANNELS` Comma separated list of pairs of channel configurations, as pipe delimited pairs ie 111|channel1,222|channel2 Find these by copying the link to a channel and taking the last component
- `NOTIFY_SERVER` If you want to push notifications from the downloading process to somewhere else. Blank is fine
- `NOTIFY_SERVER_TOKEN` Your http `Authorization` header value to the `NOTIFY_SERVER`

There are other CLI overrides MJ_OPTS, MJ_COMMAND, COMMAND_OPTS

## Running

> python sync.py

## Backprocessing

Useful to debug the server component

> python backprocess.py

## Running with docker

```sh
docker build . -t midjourney-scraper
docker run -it -v ./data:/app/data -v .:/app/env midjourney-scraper
```
