FROM python:3.13-slim

# No .pyc files; print logs immediately instead of buffering them
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first so this layer is cached until requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Don't run as root inside the container
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

CMD ["sh", "entrypoint.sh"]
