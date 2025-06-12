# # # Use official lightweight Python image
# # FROM python:3.11-slim
 
# # # Set working directory
# # WORKDIR /app
 
# # # Install apt dependencies for building and XML handling
# # RUN apt-get update \
# #     && apt-get install -y --no-install-recommends \
# #         build-essential \
# #         libxml2-dev \
# #         libxslt-dev \
# #         libffi-dev \
# #         apt-utils \
# #         ca-certificates \
# #     && rm -rf /var/lib/apt/lists/*
 
# # # Copy requirements and install
# # COPY requirements.txt .
# # RUN pip install --no-cache-dir -r requirements.txt
 
# # # Copy rest of the app
# # COPY . .
 
# # # Expose port
# # EXPOSE 5000
# # RUN chmod -R a+w /app
 
# # # Start the app
# # CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
 


# # ✅ Use lightweight Python base image
# FROM python:3.11-slim

# # ✅ Set working directory
# WORKDIR /app

# # ✅ Install system dependencies (required for Excel libraries and build tools)
# RUN apt-get update \
#     && apt-get install -y --no-install-recommends \
#         build-essential \
#         libxml2-dev \
#         libxslt-dev \
#         libffi-dev \
#         libjpeg-dev \                
#         libopenjp2-7 \             
#         zlib1g-dev \                 
#         apt-utils \
#         ca-certificates \
#     && rm -rf /var/lib/apt/lists/*

# # ✅ Copy and install Python dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # ✅ Copy app source code
# COPY . .

# # ✅ Create writable directory at runtime (use /tmp if Excel needs write access)
# # Optional: Pre-create /tmp Excel files if needed, or let your app handle copying them
# RUN mkdir -p /tmp

# # ✅ Expose Flask port
# EXPOSE 5000

# # ✅ Use gunicorn for production
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]




# ✅ Use lightweight Python base image
FROM python:3.11-slim-bullseye

# ✅ Set working directory
WORKDIR /app


RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libxml2-dev \
        libxslt-dev \
        libffi-dev \
        apt-utils \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ✅ Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Copy app source code
COPY . .

# ✅ Create writable directory at runtime (use /tmp if Excel needs write access)
# Optional: Pre-create /tmp Excel files if needed, or let your app handle copying them
RUN mkdir -p /tmp

# ✅ Expose Flask port
EXPOSE 5000

# ✅ Use gunicorn for production
CMD ["python", "app.py"]
