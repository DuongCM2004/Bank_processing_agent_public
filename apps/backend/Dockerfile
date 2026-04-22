FROM python:3.13-slim AS dev

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/apps/backend/src

WORKDIR /app/apps/backend

COPY apps/backend/requirements.txt ./requirements.txt

RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY apps/backend/alembic.ini ./alembic.ini
COPY apps/backend/alembic ./alembic
COPY apps/backend/src ./src

EXPOSE 8003

CMD ["python", "-m", "uvicorn", "ops_agent.main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"]
