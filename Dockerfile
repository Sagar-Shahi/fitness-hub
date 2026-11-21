FROM node:22-alpine AS frontend
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY vite.config.js ./
COPY frontend ./frontend
RUN npm run build

FROM python:3.15-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 app
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=app:app . .
COPY --from=frontend --chown=app:app /app/static/bundles /app/static/bundles
# Build-time only values so collectstatic can load the settings; never used at runtime.
RUN DJANGO_SECRET_KEY=build-only DJANGO_ALLOWED_HOSTS=build.invalid python manage.py collectstatic --noinput
RUN chown app:app /app
USER app
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn fithub.wsgi --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-1} --threads ${GUNICORN_THREADS:-4} --access-logfile -"]
