FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MAOO_NO_LLM_MODE=true \
    MAOO_MOCK_API_BASE_URL=http://mock-api:8001 \
    MAOO_FILE_WORKSPACE_ROOT=/tmp/workspace

COPY . /app
RUN pip install --no-cache-dir -e .[dev]

RUN mkdir -p /tmp/workspace /app/runtime/logs /app/runtime/traces /app/runtime/sqlite

CMD ["sh", "-lc", "tail -f /dev/null"]

