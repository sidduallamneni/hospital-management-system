FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DB_PATH=/data/hms.db PORT=8080
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY templates templates
COPY static static
RUN useradd -m hms && mkdir /data && chown hms /data
USER hms
VOLUME /data
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8080/health')" || exit 1
# 1 worker: SQLite is a single-file DB. Use PostgreSQL/RDS for multi-replica scaling.
CMD ["sh","-c","gunicorn -w 1 --threads 4 -b 0.0.0.0:${PORT} app:app"]
