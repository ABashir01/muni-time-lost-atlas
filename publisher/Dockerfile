FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY api/src ./api/src
COPY pipeline/src ./pipeline/src
COPY db ./db
COPY dbt ./dbt
COPY fixtures ./fixtures
COPY publisher ./publisher

RUN python -m pip install --upgrade pip \
  && python -m pip install --no-cache-dir . uvicorn

RUN chmod +x /app/publisher/*.sh \
  && mkdir -p /app/artifacts /var/run/muni-lta

CMD ["sh", "-lc", "while true; do sleep 3600; done"]
