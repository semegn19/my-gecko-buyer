# The check server, as a container. Keyless: nothing secret is configured.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
RUN pip install --no-cache-dir uv

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY buyer ./buyer
COPY server ./server
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
# Bind the port the platform hands us; Render/Railway set PORT, local defaults to 8000.
CMD ["sh", "-c", "python server/check_server.py --transport streamable-http --host 0.0.0.0 --port ${PORT:-8000}"]
