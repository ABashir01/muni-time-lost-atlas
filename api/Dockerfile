FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY api/src ./api/src
COPY pipeline/src ./pipeline/src

RUN python -m pip install --upgrade pip \
  && python -m pip install --no-cache-dir . uvicorn

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "muni_lta_api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
