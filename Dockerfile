FROM python:3.13-slim

WORKDIR /app

# directory with a .env file to pull config and secrets from
VOLUME /app/env

# root dir of wallpapers
VOLUME /app/wallpapers

COPY entrypoint.sh /app/entrypoint.sh
COPY requirements.txt /app/requirements.txt

RUN python -m venv /app/venv && \
    python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY *.py /app
RUN chmod +x /app/*.py && \
    chmod +x /app/entrypoint.sh

ENTRYPOINT [ "/app/entrypoint.sh"]