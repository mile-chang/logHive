# Simplified Dockerfile for LogHive
# Single-stage build since no C compilation is needed for pure Python dependencies
FROM python:3.11-slim

# Python environment variables (Docker best practices)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create non-root user for security
RUN useradd -m -u 1000 loghive && \
    mkdir -p /app /app/data /app/logs && \
    chown -R loghive:loghive /app

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=loghive:loghive app.py .
COPY --chown=loghive:loghive config.py .
COPY --chown=loghive:loghive models.py .
COPY --chown=loghive:loghive gunicorn_config.py .
COPY --chown=loghive:loghive tools/migrate_db.py .
COPY --chown=loghive:loghive tools/clean_db.py .
COPY --chown=loghive:loghive tools/update_passwords.py .
COPY --chown=loghive:loghive templates/ ./templates/
COPY --chown=loghive:loghive static/ ./static/

# Copy entrypoint script
COPY --chown=loghive:loghive docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Switch to non-root user
USER loghive

# Expose port (documentation only, actual port set via docker-compose)
EXPOSE 5100

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5100/').read()" || exit 1

# Set entrypoint
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command
CMD ["gunicorn", "-c", "gunicorn_config.py", "app:app"]
