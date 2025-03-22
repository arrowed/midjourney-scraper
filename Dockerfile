##### stage 1: Build assemble, test

FROM python:slim-bookworm as build
# pull in uv binaries
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY . .
RUN uv sync --frozen --no-install-project --no-dev
RUN ls -laht /app

##### Stage 2: Final/runtime

FROM python:3.13-slim-bookworm as final

WORKDIR /app

# directory with a .env file to pull config and secrets from
VOLUME /app/env

# root dir of wallpapers
VOLUME /app/wallpapers

COPY --from=build /app /app

RUN chmod +x /app/*.py && \
    chmod +x /app/entrypoint.sh

ENTRYPOINT [ "/app/entrypoint.sh"]