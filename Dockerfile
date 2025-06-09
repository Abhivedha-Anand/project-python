# Use official lightweight Python image
FROM python:3.11-slim
 
# Set working directory
WORKDIR /app
 
# Install apt dependencies for building and XML handling
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libxml2-dev \
        libxslt-dev \
        libffi-dev \
        apt-utils \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*
 
# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
# Copy rest of the app
COPY . .
 
# Expose port
EXPOSE 5000
RUN chmod -R a+w /app
 
# Start the app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
 
