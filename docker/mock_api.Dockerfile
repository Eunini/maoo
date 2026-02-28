FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY . /app
RUN pip install --no-cache-dir fastapi uvicorn pydantic

EXPOSE 8001
CMD ["python", "-m", "mock_api.server"]

