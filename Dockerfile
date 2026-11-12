FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app . .
# Build-time only values so collectstatic can load the settings; never used at runtime.
RUN DJANGO_SECRET_KEY=build-only DJANGO_ALLOWED_HOSTS=build.invalid python manage.py collectstatic --noinput
USER app
EXPOSE 8000
CMD ["gunicorn", "fithub.wsgi", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
