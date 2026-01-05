# Production-ready Django Dockerfile
FROM python:3.11-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /wellnessapp

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /wellnessapp/
RUN pip install --upgrade pip && \
    pip install gunicorn && \
    pip install -r requirements.txt

# Copy project files
COPY . /wellnessapp/

# Expose port 8000
EXPOSE 8000

# Run migrations and start Gunicorn
CMD python manage.py makemigrations --noinput && \
    python manage.py migrate --noinput && \
    gunicorn WellnessApplication.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
