FROM python:3.12-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.11.6 /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

COPY pyproject.toml README.md ./
RUN uv sync --no-install-project --no-dev

COPY . ./

FROM python:3.12-slim-bookworm

WORKDIR /app

RUN useradd --create-home appuser

COPY --from=builder --chown=appuser:appuser /app /app

USER appuser

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

CMD ["/bin/sh", "-c", "exec fastapi run main.py --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]