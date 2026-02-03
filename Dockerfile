FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY examples /app/examples

RUN pip install --no-cache-dir uv \
    && uv pip install --system -e .

ENTRYPOINT ["scheduler"]
CMD ["run", "--config", "examples/scheduler.toml"]
