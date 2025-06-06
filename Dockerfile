# Use an official Python base image
FROM python:3.10-slim
 
# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
 
# Set working directory
WORKDIR /app
 
# Copy project files into the container
COPY . /app
 
# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*
 
# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install flask pandas openpyxl itsdangerous
 
# Expose the port Flask runs on
EXPOSE 5000
 
# Run the Flask app
CMD ["python", "app.py"]
