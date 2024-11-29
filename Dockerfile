# Use official Python runtime as base image
FROM python:3.10-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_NO_CACHE_DIR 1

# Set work directory
WORKDIR /app

# Install system dependencies for faster-whisper and audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    git \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project files
COPY . .

# Create temp directory for file uploads
RUN mkdir -p /tmp/uploads

# Expose the application port
EXPOSE 8000

# Use non-root user for security
RUN useradd -m appuser
USER appuser

# Use uvicorn as the ASGI server
CMD ["uvicorn", "main:app", "--reload","--host", "0.0.0.0", "--port", "8000"]