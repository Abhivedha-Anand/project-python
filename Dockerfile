# Use official lightweight Python image
FROM python:3.11-slim
 
# Set working directory
WORKDIR /app
 
# Install apt deps for pandas excel support
RUN apt-get update \
    && apt-get install -y build-essential libxml2-dev libxslt-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*
 
# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
 
# Copy everything else
COPY . .
 
# Expose port
EXPOSE 5000
 
# Specify default command
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
